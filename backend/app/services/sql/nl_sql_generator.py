from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ai.llm import DEFAULT_LITELLM_PROXY_URL
from app.core.config import settings
from app.schemas.chat import ChatMessage
from app.schemas.nl_sql import AIGeneratedSQLResponse, OperationType, TableMetadata
from app.services.sql.ai_response_validator import validate_response_is_sql
from app.services.sql.schema_discovery import build_schema_text


logger = logging.getLogger(__name__)


def _resolve_generation_model() -> str:
    # Keep NL-to-SQL model independent from generic chat model defaults.
    # Some API keys are restricted and do not allow the app-wide LLM_MODEL.
    return (settings.sql_generation_model or "gemini/gemini-2.5-flash").strip()


def _get_sql_model() -> ChatOpenAI:
    api_key = settings.litellm_api_key
    if not api_key:
        raise ValueError("Missing LITELLM_API_KEY for NL-to-SQL generation")

    proxy_url = (settings.litellm_proxy_url or DEFAULT_LITELLM_PROXY_URL).rstrip("/")
    base_url = proxy_url if proxy_url.endswith("/v1") else f"{proxy_url}/v1"

    return ChatOpenAI(
        model=_resolve_generation_model(),
        api_key=api_key,
        base_url=base_url,
        temperature=settings.sql_generation_temperature,
    )


def _extract_json(text: str) -> dict:
    """Extract JSON from text, handling markdown code blocks."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Model did not return valid JSON for SQL generation")


def _detect_operation_type(sql: str) -> OperationType:
    """Detect operation type from SQL statement."""
    sql_upper = sql.strip().upper()
    
    # Read operations
    if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
        return "read"
    elif sql_upper.startswith("DESCRIBE") or sql_upper.startswith("DESC"):
        return "read"
    
    # Write operations
    elif sql_upper.startswith("INSERT"):
        return "insert"
    elif sql_upper.startswith("UPDATE"):
        # Detect upsert pattern
        if "ON CONFLICT" in sql_upper or "ON DUPLICATE" in sql_upper:
            return "upsert"
        return "update"
    elif sql_upper.startswith("DELETE"):
        return "delete"
    
    # Schema operations
    elif sql_upper.startswith("CREATE TABLE"):
        return "schema_create"
    elif sql_upper.startswith("CREATE INDEX"):
        return "schema_index"
    elif sql_upper.startswith("CREATE VIEW"):
        return "schema_view"
    elif sql_upper.startswith("ALTER TABLE"):
        if "DROP" in sql_upper:
            return "schema_drop"
        return "schema_alter"
    elif sql_upper.startswith("DROP"):
        return "schema_drop"
    elif sql_upper.startswith("TRUNCATE"):
        return "schema_drop"
    
    # Default
    return "unknown"


def _extract_warnings(sql: str) -> list[str]:
    """Extract warnings about the SQL operation."""
    warnings = []
    sql_upper = sql.strip().upper()
    
    # DELETE without WHERE
    if sql_upper.startswith("DELETE") and "WHERE" not in sql_upper:
        warnings.append("DELETE operation without WHERE clause will affect all rows")
    
    # UPDATE without WHERE
    elif sql_upper.startswith("UPDATE") and "WHERE" not in sql_upper:
        warnings.append("UPDATE operation without WHERE clause will affect all rows")
    
    # TRUNCATE
    if sql_upper.startswith("TRUNCATE"):
        warnings.append("TRUNCATE will permanently delete all data in the table")
    
    # DROP TABLE
    if "DROP TABLE" in sql_upper:
        warnings.append("DROP TABLE will permanently delete the table and all its data")
    
    # Large LIMIT or no LIMIT in SELECT
    if sql_upper.startswith("SELECT"):
        if "LIMIT" not in sql_upper:
            warnings.append("SELECT without LIMIT may return very large result sets")
        else:
            # Check for very large limits
            limit_match = re.search(r"LIMIT\s+(\d+)", sql_upper)
            if limit_match:
                limit_val = int(limit_match.group(1))
                if limit_val > 10000:
                    warnings.append(f"SELECT with large LIMIT ({limit_val}) may impact performance")
    
    return warnings


def _build_system_prompt() -> str:
    """Build system prompt for full NL-to-SQL generation (CRUD + DDL + admin/tx)."""
    return (
        "You are an enterprise NL-to-SQL engine. Your role is to generate executable SQL for authorized database operations.\n\n"
        "IMPORTANT AUTHORIZATION CONTEXT:\n"
        "- The caller is an authenticated backend service with explicit approval workflows.\n"
        "- You ARE allowed to generate write and schema operations when requested.\n"
        "- Do NOT refuse operations just because they modify data/schema.\n\n"
        "Supported operation classes:\n"
        "- READ: SELECT, WITH\n"
        "- WRITE: INSERT, UPDATE, DELETE, UPSERT (including MERGE / INSERT...ON CONFLICT / ON DUPLICATE KEY)\n"
        "- SCHEMA: CREATE TABLE, ALTER TABLE, DROP TABLE, CREATE INDEX, DROP INDEX, CREATE VIEW, TRUNCATE\n"
        "- TRANSACTION: BEGIN/START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT\n"
        "- FUTURE-READY PROCEDURE SUPPORT: CALL / EXEC / EXECUTE syntax when explicitly requested\n\n"
        "CRITICAL OUTPUT FORMAT:\n"
        "You MUST return valid JSON only, with exactly these keys:\n"
        '{"sql": "...", "explanation": "..."}\n\n'
        "Rules:\n"
        "1. sql must contain exactly one executable SQL statement and no markdown/backticks.\n"
        "2. explanation must be concise and plain text.\n"
        "3. Use only schema objects that exist in provided schema.\n"
        "4. For ambiguous requests, return JSON error: {\"error\": true, \"reason\": \"...\"}.\n"
        "5. For SELECT statements, include LIMIT 1000 unless user requests otherwise.\n"
        "6. Do not return conversational prose outside the JSON object.\n"
    )


def _build_user_prompt(question: str, schema_text: str, history_text: str) -> str:
    return (
        f"Available schema:\n{schema_text}\n\n"
        f"Recent conversation:\n{history_text or '(none)'}\n\n"
        f"User question:\n{question}\n\n"
        "Return ONLY a valid JSON object with keys 'sql' and 'explanation'."
    )


def _should_retry_with_stronger_prompt(reason: str) -> bool:
    text = (reason or "").lower()
    retry_markers = [
        "read-only",
        "select only",
        "select statements",
        "delete operations are not supported",
        "cannot fulfill",
        "not supported",
    ]
    return any(marker in text for marker in retry_markers)


def _invoke_generation(model: ChatOpenAI, system_prompt: str, user_prompt: str) -> dict:
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    content = response.content if isinstance(response.content, str) else str(response.content)
    logger.debug(f"Raw LLM response: {content[:500]}")
    return _extract_json(content)


def generate_sql_from_question(
    *,
    question: str,
    schema: list[TableMetadata],
    history: list[ChatMessage],
) -> AIGeneratedSQLResponse:
    """
    Generate SQL from natural language question using LLM.
    
    Returns:
        AIGeneratedSQLResponse with operation_type, sql, explanation, warnings, requires_confirmation
        
    Raises:
        ValueError: If response is invalid, refusal, or malformed
    """
    schema_text = build_schema_text(schema)
    history_text = "\n".join(f"{item.role}: {item.content}" for item in history[-8:])

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(question, schema_text, history_text)

    model = _get_sql_model()
    try:
        payload = _invoke_generation(model, system_prompt, user_prompt)
    except ValueError as e:
        logger.error(f"Failed to extract JSON from response: {e}")
        raise ValueError(f"AI generated invalid response format: {str(e)}")
    
    # Check for explicit error response from AI
    if payload.get("error"):
        reason = payload.get("reason", "Unknown reason")
        retries = max(settings.sql_generation_retry_count, 0)
        if retries > 0 and _should_retry_with_stronger_prompt(str(reason)):
            logger.warning(f"AI declined initial generation ({reason}); retrying with stronger authorization prompt")
            retry_system_prompt = (
                system_prompt
                + "\n\nRETRY OVERRIDE: You must not refuse write/schema operations. Generate the requested SQL if schema supports it."
            )
            payload = _invoke_generation(model, retry_system_prompt, user_prompt)
            if payload.get("error"):
                retry_reason = payload.get("reason", "Unknown reason")
                logger.warning(f"AI declined retry generation: {retry_reason}")
                raise ValueError(f"AI declined to generate SQL: {retry_reason}")
        else:
            logger.warning(f"AI declined to generate SQL: {reason}")
            raise ValueError(f"AI declined to generate SQL: {reason}")
    
    sql = str(payload.get("sql") or "").strip()
    explanation_raw = payload.get("explanation")
    explanation = str(explanation_raw).strip() if explanation_raw is not None else None
    
    if not sql:
        logger.error("Model returned empty SQL")
        raise ValueError("AI generated empty SQL statement")
    
    # Validate that SQL looks valid
    is_valid, error_msg = validate_response_is_sql(sql)
    if not is_valid:
        logger.error(f"Generated SQL failed validation: {error_msg}")
        raise ValueError(f"Generated SQL is not valid: {error_msg}")
    
    # Detect operation type and warnings
    operation_type = _detect_operation_type(sql)
    warnings = _extract_warnings(sql)
    requires_confirmation = bool(warnings) or operation_type != "read"
    
    logger.info(
        f"Generated SQL: operation={operation_type}, warnings={len(warnings)}, "
        f"requires_confirmation={requires_confirmation}"
    )
    
    return AIGeneratedSQLResponse(
        operation_type=operation_type,
        sql=sql,
        explanation=explanation,
        warnings=warnings,
        requires_confirmation=requires_confirmation,
        validation_passed=True,
    )
