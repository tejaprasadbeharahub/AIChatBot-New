import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.nl_sql import (
    DBConnectionCreate,
    DBConnectionRead,
    DBConnectionUpdate,
    DBConnectionValidationResponse,
    ExecuteNLQueryRequest,
    ExecuteNLQueryResponse,
    SQLQueryExecutionRead,
    SQLQueryHistoryResponse,
    SchemaMetadataResponse,
    OperationApprovalRequest,
    ApproveOperationRequest,
    ApprovalStatusResponse,
    AIResponseValidationFailure,
)
from app.services.sql import nl_sql_service

router = APIRouter(prefix="/nl-sql", tags=["nl-sql"])
logger = logging.getLogger(__name__)


@router.get("/connections", response_model=list[DBConnectionRead])
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DBConnectionRead]:
    return nl_sql_service.list_connections(db, current_user.id)


@router.post("/connections", response_model=DBConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: DBConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DBConnectionRead:
    try:
        return nl_sql_service.create_connection(db, current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/connections/{connection_id}", response_model=DBConnectionRead)
def update_connection(
    connection_id: uuid.UUID,
    payload: DBConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DBConnectionRead:
    try:
        return nl_sql_service.update_connection(db, current_user.id, connection_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        nl_sql_service.delete_connection(db, current_user.id, connection_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/connections/{connection_id}/validate", response_model=DBConnectionValidationResponse)
def validate_connection(
    connection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DBConnectionValidationResponse:
    try:
        success, message = nl_sql_service.test_connection(db, current_user.id, connection_id)
        return DBConnectionValidationResponse(success=success, message=message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/connections/{connection_id}/schema", response_model=SchemaMetadataResponse)
def get_schema_metadata(
    connection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchemaMetadataResponse:
    try:
        schema = nl_sql_service.build_schema_metadata(db, current_user.id, connection_id)
        return SchemaMetadataResponse(connection_id=connection_id, tables=schema)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Schema discovery failed: {exc}") from exc


@router.post("/query", response_model=ExecuteNLQueryResponse)
def execute_nl_query(
    payload: ExecuteNLQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecuteNLQueryResponse:
    try:
        chat_id, user_message_id, assistant_message_id, reply, execution, approval_request = nl_sql_service.execute_nl_query(
            db,
            user=current_user,
            connection_id=payload.connection_id,
            question=payload.question,
            chat_id=payload.chat_id,
            max_rows=payload.max_rows,
        )
        return ExecuteNLQueryResponse(
            chat_id=chat_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            reply=reply,
            execution=SQLQueryExecutionRead.model_validate(execution),
            approval_request=OperationApprovalRequest(
                operation_type=approval_request.operation_type,
                risk_level=approval_request.risk_level,
                risk_messages=approval_request.risk_messages,
                generated_sql=approval_request.generated_sql,
                sql_explanation=approval_request.sql_explanation,
                user_question=approval_request.question,
            ) if approval_request else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except nl_sql_service.NLSQLExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while executing NL-SQL query")
        raise HTTPException(status_code=500, detail=f"Unexpected NL-SQL error: {exc}") from exc


@router.get("/history", response_model=SQLQueryHistoryResponse)
def get_query_history(
    chat_id: uuid.UUID | None = Query(default=None),
    connection_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SQLQueryHistoryResponse:
    items = nl_sql_service.list_query_history(
        db,
        user_id=current_user.id,
        chat_id=chat_id,
        connection_id=connection_id,
        limit=limit,
    )
    return SQLQueryHistoryResponse(items=[SQLQueryExecutionRead.model_validate(item) for item in items])
