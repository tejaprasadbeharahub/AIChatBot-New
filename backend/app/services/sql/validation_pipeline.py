"""
SQL Query Validation Pipeline Module

Orchestrates multi-stage validation of SQL queries:
1. AI response validation (detect non-SQL, refusals, etc.)
2. SQL syntax validation
3. Schema validation
4. Safety validation
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services.sql.ai_response_validator import (
    validate_and_log_response,
    classify_ai_response,
    AIResponseType,
)
from app.schemas.nl_sql import AIResponseValidationFailure

logger = logging.getLogger(__name__)


class ValidationPipelineError(Exception):
    """Base exception for validation pipeline errors."""
    pass


class AIResponseValidationError(ValidationPipelineError):
    """Raised when AI response validation fails."""
    pass


def handle_ai_response_validation_failure(
    error_message: str,
    ai_response_preview: str,
    classification: AIResponseType,
) -> AIResponseValidationFailure:
    """
    Create a user-friendly validation failure response.
    
    Args:
        error_message: Technical error message
        ai_response_preview: First part of the AI response
        classification: Classification of the response type
        
    Returns:
        AIResponseValidationFailure with user-friendly messaging
    """
    
    error_type_map = {
        AIResponseType.REFUSAL: "ai_refused",
        AIResponseType.EXPLANATION: "explanation_only",
        AIResponseType.CLARIFICATION: "clarification_needed",
        AIResponseType.INVALID_SQL: "invalid_sql",
        AIResponseType.MALFORMED: "malformed_response",
        AIResponseType.CONVERSATIONAL: "conversational_response",
    }
    
    user_friendly_map = {
        AIResponseType.REFUSAL: (
            "The AI declined to generate a query for this request. "
            "This might be due to complexity, ambiguity, or safety concerns. "
            "Try rephrasing your question or breaking it into smaller steps."
        ),
        AIResponseType.EXPLANATION: (
            "The AI provided an explanation instead of a query. "
            "Please ask a specific database question (e.g., 'Show users from New York')."
        ),
        AIResponseType.CLARIFICATION: (
            "The AI needs clarification about your request. "
            "Please provide more specific table or column names."
        ),
        AIResponseType.INVALID_SQL: (
            "The generated SQL contains syntax errors. "
            "The AI may have misunderstood your request. Try asking differently."
        ),
        AIResponseType.MALFORMED: (
            "The AI response was not properly formatted. "
            "Please try your question again."
        ),
        AIResponseType.CONVERSATIONAL: (
            "The AI provided a conversational response instead of SQL. "
            "Please ask a database-specific question."
        ),
    }
    
    suggested_action_map = {
        AIResponseType.REFUSAL: "Try a different question or break down the request",
        AIResponseType.EXPLANATION: "Ask for data directly (e.g., 'Show me all customers')",
        AIResponseType.CLARIFICATION: "Specify exact table and column names",
        AIResponseType.INVALID_SQL: "Rephrase the question more clearly",
        AIResponseType.MALFORMED: "Retry your question",
        AIResponseType.CONVERSATIONAL: "Ask for specific data from a table",
    }
    
    return AIResponseValidationFailure(
        success=False,
        error_type=error_type_map.get(classification, "unknown"),
        error_message=error_message,
        user_friendly_message=user_friendly_map.get(
            classification,
            "The AI response could not be processed. Please try again."
        ),
        ai_response_preview=ai_response_preview[:500],
        suggested_action=suggested_action_map.get(classification),
    )


def validate_ai_response_with_pipeline(
    ai_response: str,
    label: str = "AI Response",
) -> tuple[bool, Optional[AIResponseValidationFailure]]:
    """
    Run validation pipeline on AI response.
    
    Args:
        ai_response: Raw text from AI
        label: Label for logging context
        
    Returns:
        (is_valid, failure_response): Tuple of validation status and failure details if invalid
    """
    
    # Stage 1: AI response validation
    is_valid, error_msg = validate_and_log_response(ai_response, label)
    
    if not is_valid:
        classification = classify_ai_response(ai_response)
        failure = handle_ai_response_validation_failure(
            error_message=error_msg,
            ai_response_preview=ai_response[:500],
            classification=classification,
        )
        
        logger.warning(
            f"{label} validation failed at Stage 1 (AI Response Validation): "
            f"classification={classification}, error={error_msg}"
        )
        
        return False, failure
    
    logger.debug(f"{label} passed all validation stages")
    return True, None
