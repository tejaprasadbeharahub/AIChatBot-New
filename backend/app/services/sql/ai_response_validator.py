"""
AI Response Validation Module

Validates AI-generated responses before SQL execution.
Detects non-SQL text, refusals, explanations, and malformed output.
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AIResponseType(str, Enum):
    """Classification of AI response content."""
    VALID_SQL = "valid_sql"
    REFUSAL = "refusal"
    EXPLANATION = "explanation"
    CLARIFICATION = "clarification"
    INVALID_SQL = "invalid_sql"
    MALFORMED = "malformed"
    CONVERSATIONAL = "conversational"


class AIResponseValidationError(Exception):
    """Raised when AI response validation fails."""
    pass


# Common refusal patterns
REFUSAL_PATTERNS = [
    r"i\s+cannot\s+fulfill",
    r"i\s+can\s+only\s+generate",
    r"i\s+cannot\s+generate",
    r"i\s+cannot\s+create",
    r"not\s+able\s+to",
    r"unable\s+to",
    r"i\s+don'?t\s+have\s+access",
    r"permission\s+denied",
    r"not\s+allowed",
    r"this\s+is\s+not\s+supported",
    r"this\s+request\s+is\s+not\s+supported",
    r"i\s+can\s+only\s+help",
    r"i\s+cannot\s+assist",
    r"cannot\s+assist",
]

# Common explanation/clarification patterns
EXPLANATION_PATTERNS = [
    r"^here'?s\s+the\s+sql",
    r"^here\s+is\s+the\s+sql",
    r"^here\s+is\s+a\s+sql",
    r"^the\s+query\s+",
    r"^this\s+query\s+",
    r"^to\s+do\s+this",
    r"^explanation:",
    r"^clarification:",
    r"^note:",
    r"^important:",
    r"^warning:",
    r"^please\s+note",
    r"^let\s+me",
    r"^i\s+would",
    r"^you\s+can",
    r"^to\s+clarify",
]

# Valid SQL start keywords
VALID_SQL_STARTS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", 
    "DROP", "TRUNCATE", "WITH", "EXEC", "CALL", "DESCRIBE", "DESC",
    "MERGE", "BEGIN", "START", "COMMIT", "ROLLBACK", "SAVEPOINT"
]


def is_valid_sql_start(text: str) -> bool:
    """Check if text starts with a valid SQL keyword."""
    stripped = text.strip().upper()
    return any(stripped.startswith(keyword) for keyword in VALID_SQL_STARTS)


def detect_refusal(text: str) -> bool:
    """Detect if text contains a refusal message."""
    text_lower = text.lower()
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_explanation(text: str) -> bool:
    """Detect if text starts with explanation/clarification patterns."""
    text_lower = text.lower().strip()
    for pattern in EXPLANATION_PATTERNS:
        if re.match(pattern, text_lower):
            return True
    return False


def detect_clarification_request(text: str) -> bool:
    """Detect if text is asking for clarification."""
    patterns = [
        r"could\s+you\s+clarify",
        r"could\s+you\s+provide",
        r"do\s+you\s+mean",
        r"which\s+table",
        r"which\s+column",
        r"are\s+you\s+asking",
        r"need\s+clarification",
        r"need\s+more\s+details",
        r"could\s+you\s+specify",
        r"what\s+do\s+you\s+mean",
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)


def detect_common_conversational_markers(text: str) -> bool:
    """Detect common conversational markers that indicate non-SQL content."""
    patterns = [
        r"^(hello|hi|hey|thanks|thank\s+you)",
        r"^(i\s+would\s+be\s+happy|i\s+will\s+help|i\s+can\s+help)",
        r"^(however|but|and|in\s+addition|furthermore)",
        r"^(as\s+requested|per\s+your\s+request)",
        r"sorry,",
        r"my\s+apologies",
    ]
    text_lower = text.lower().strip()
    return any(re.match(pattern, text_lower) for pattern in patterns)


def is_likely_plain_english(text: str) -> bool:
    """
    Heuristic: Check if text is mostly plain English without SQL keywords.
    
    Returns True if text appears to be English prose rather than SQL.
    """
    text_stripped = text.strip()
    
    # Check for SQL keywords
    sql_keywords = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE",
        "JOIN", "GROUP", "ORDER", "LIMIT", "OFFSET", "UNION"
    ]
    
    keywords_found = sum(1 for kw in sql_keywords if kw in text_stripped.upper())
    
    # If few SQL keywords but many periods/question marks, likely prose
    punctuation_count = text_stripped.count('.') + text_stripped.count('?') + text_stripped.count('!')
    word_count = len(text_stripped.split())
    
    # Heuristic: if > 50% lines end with period/question and few SQL keywords, it's prose
    if keywords_found < 2 and word_count > 20 and punctuation_count > word_count * 0.2:
        return True
    
    return False


def classify_ai_response(text: str) -> AIResponseType:
    """
    Classify the type of AI response.
    
    Returns:
        AIResponseType: Classification of the response content.
    """
    text_stripped = text.strip()
    
    if not text_stripped:
        return AIResponseType.MALFORMED
    
    # Check for refusal first
    if detect_refusal(text_stripped):
        return AIResponseType.REFUSAL
    
    # Check for clarification request
    if detect_clarification_request(text_stripped):
        return AIResponseType.CLARIFICATION
    
    # Check if it starts with valid SQL
    if is_valid_sql_start(text_stripped):
        return AIResponseType.VALID_SQL
    
    # Check for explanation patterns
    if detect_explanation(text_stripped):
        return AIResponseType.EXPLANATION
    
    # Check for conversational markers
    if detect_common_conversational_markers(text_stripped):
        return AIResponseType.CONVERSATIONAL
    
    # Check if it's plain English prose
    if is_likely_plain_english(text_stripped):
        return AIResponseType.CONVERSATIONAL
    
    # Check if it looks like invalid SQL
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|WITH)\b", text_stripped, flags=re.IGNORECASE):
        return AIResponseType.INVALID_SQL
    
    # Default to malformed
    return AIResponseType.MALFORMED


def validate_response_is_sql(text: str) -> tuple[bool, Optional[str]]:
    """
    Validate that response is valid SQL.
    
    Returns:
        (is_valid, error_message): True if valid SQL, False with error message otherwise.
    """
    classification = classify_ai_response(text)
    
    if classification == AIResponseType.VALID_SQL:
        return True, None
    
    error_messages = {
        AIResponseType.REFUSAL: "AI refused to generate SQL. This operation may not be supported or requires clarification.",
        AIResponseType.EXPLANATION: "AI provided explanation instead of executable SQL. Please try a clearer request.",
        AIResponseType.CLARIFICATION: "AI needs clarification on your request. Please be more specific.",
        AIResponseType.INVALID_SQL: "AI generated invalid SQL syntax.",
        AIResponseType.MALFORMED: "AI response is not properly formatted or empty.",
        AIResponseType.CONVERSATIONAL: "AI provided conversational response instead of SQL. Please ask a specific database question.",
    }
    
    error_msg = error_messages.get(classification, f"Invalid response type: {classification}")
    return False, error_msg


def validate_and_log_response(text: str, label: str = "AI Response") -> tuple[bool, Optional[str]]:
    """
    Validate response and log details for debugging.
    
    Args:
        text: The AI response text
        label: Label for logging context
        
    Returns:
        (is_valid, error_message)
    """
    classification = classify_ai_response(text)
    logger.debug(f"{label} Classification: {classification}")
    logger.debug(f"{label} Content (first 200 chars): {text[:200]}")
    
    is_valid, error_msg = validate_response_is_sql(text)
    
    if not is_valid:
        logger.warning(f"{label} Validation Failed: {error_msg}")
    
    return is_valid, error_msg


def extract_sql_from_response(text: str) -> Optional[str]:
    """
    Attempt to extract valid SQL from a response that may contain explanatory text.
    
    This is a fallback for AI responses that mix SQL with prose.
    
    Returns:
        SQL string if found, None otherwise.
    """
    lines = text.split('\n')
    sql_lines = []
    in_sql_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if we're entering a SQL block
        if any(stripped.upper().startswith(kw) for kw in VALID_SQL_STARTS):
            in_sql_block = True
        
        if in_sql_block:
            sql_lines.append(line)
            # Check for end of SQL (semicolon or certain keywords that indicate end)
            if stripped.endswith(';'):
                break
    
    if sql_lines:
        extracted = '\n'.join(sql_lines).strip()
        if is_valid_sql_start(extracted):
            return extracted
    
    return None
