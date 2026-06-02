from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_workflow_db
from app.schemas.tickets import (
    FarmTicketCreateRequest,
    FarmTicketListResponse,
    FarmTicketResponse,
    TicketMutationResponse,
    TicketStatusUpdateRequest,
)


router = APIRouter(tags=["tickets"])
logger = logging.getLogger(__name__)
DEFAULT_FARMER_ID = "FM001"


def _table_columns(db: Session, table_name: str) -> set[str]:
    inspector = inspect(db.bind)
    if not inspector.has_table(table_name):
        raise HTTPException(status_code=500, detail=f"Table '{table_name}' is not available")
    return {str(col["name"]) for col in inspector.get_columns(table_name)}


def _normalize_status(value: Any, fallback: str) -> str:
    text_value = str(value).strip().upper() if value is not None else ""
    return text_value or fallback


def _row_to_response(row: dict[str, Any]) -> FarmTicketResponse:
    known = {
        "ticket_id",
        "farmer_name",
        "farmer_email",
        "query",
        "crop_type",
        "location",
        "weather",
        "status",
        "ticket_status",
        "workflow_state",
        "risk_level",
        "ai_confidence",
        "resume_url",
        "created_at",
        "updated_at",
    }

    ticket_status = _normalize_status(row.get("ticket_status", row.get("status")), "OPEN")
    workflow_state = _normalize_status(
        row.get("workflow_state"),
        "WAITING" if ticket_status == "IN_PROGRESS" else ("CLOSED" if ticket_status == "CLOSED" else "WAITING"),
    )

    # If ticket is closed, expose CLOSED workflow state even when DB has legacy WAITING/COMPLETED values.
    if ticket_status == "CLOSED":
        workflow_state = "CLOSED"

    return FarmTicketResponse(
        ticket_id=int(row.get("ticket_id") or 0),
        farmer_name=str(row.get("farmer_name") or ""),
        farmer_email=str(row.get("farmer_email") or ""),
        query=str(row.get("query") or ""),
        crop_type=str(row.get("crop_type") or ""),
        location=str(row.get("location") or ""),
        weather=str(row.get("weather") or ""),
        ticket_status=ticket_status,
        workflow_state=workflow_state,
        risk_level=(str(row.get("risk_level")) if row.get("risk_level") is not None else None),
        ai_confidence=(float(row.get("ai_confidence")) if row.get("ai_confidence") is not None else None),
        resume_url=(str(row.get("resume_url")) if row.get("resume_url") is not None else None),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        extra={key: value for key, value in row.items() if key not in known},
    )


def _latest_ticket_row(db: Session, ticket_id: int) -> dict[str, Any]:
    result = db.execute(
        text("SELECT * FROM farm_tickets WHERE ticket_id = :ticket_id LIMIT 1"),
        {"ticket_id": ticket_id},
    ).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return dict(result)


def _find_duplicate_with_resume_url(
    db: Session,
    *,
    ticket_id: int,
    farmer_name: str,
    farmer_email: str,
    query: str,
    crop_type: str,
    location: str,
    weather: str,
    created_after: datetime,
) -> dict[str, Any] | None:
    """Find a near-duplicate ticket created by N8N that already has a resume_url."""
    result = db.execute(
        text(
            """
            SELECT *
            FROM farm_tickets
            WHERE ticket_id != :ticket_id
              AND farmer_name = :farmer_name
              AND farmer_email = :farmer_email
              AND query = :query
              AND crop_type = :crop_type
              AND location = :location
              AND weather = :weather
              AND resume_url IS NOT NULL
              AND created_at >= :created_after
            ORDER BY created_at DESC NULLS LAST, ticket_id DESC
            LIMIT 1
            """
        ),
        {
            "ticket_id": ticket_id,
            "farmer_name": farmer_name,
            "farmer_email": farmer_email,
            "query": query,
            "crop_type": crop_type,
            "location": location,
            "weather": weather,
            "created_after": created_after,
        },
    ).mappings().first()
    return dict(result) if result else None


def _update_ticket_state(db: Session, ticket_id: int, values: dict[str, Any]) -> None:
    columns = _table_columns(db, "farm_tickets")
    normalized_values = dict(values)

    # Backward compatibility for older schemas that use `status` instead of `ticket_status`.
    if "ticket_status" in normalized_values and "ticket_status" not in columns and "status" in columns:
        normalized_values["status"] = normalized_values["ticket_status"]

    filtered = {key: value for key, value in normalized_values.items() if key in columns}
    if not filtered:
        return

    assignments = ", ".join(f"{key} = :{key}" for key in filtered.keys())
    filtered["ticket_id"] = ticket_id
    db.execute(
        text(f"UPDATE farm_tickets SET {assignments} WHERE ticket_id = :ticket_id"),
        filtered,
    )


async def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    timeout_seconds = max(settings.n8n_workflow_timeout_seconds, 5)
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", "").lower():
            try:
                return response.json()
            except ValueError:
                # Some webhooks return JSON content-type with non-JSON body.
                # Treat this as a non-fatal parse issue so ticket creation remains successful.
                return {"raw_response": response.text}
        return {"raw_response": response.text}


@router.get("/tickets", response_model=FarmTicketListResponse)
async def list_tickets(db: Session = Depends(get_workflow_db)) -> FarmTicketListResponse:
    try:
        _table_columns(db, "farm_tickets")
        rows = db.execute(
            text("SELECT * FROM farm_tickets ORDER BY created_at DESC NULLS LAST, ticket_id DESC LIMIT 500")
        ).mappings().all()
    except SQLAlchemyError as exc:
        logger.exception("tickets_list_failed")
        raise HTTPException(status_code=500, detail="Failed to load tickets") from exc

    return FarmTicketListResponse(success=True, records=[_row_to_response(dict(row)) for row in rows])


@router.post("/tickets", response_model=TicketMutationResponse)
async def create_ticket(payload: FarmTicketCreateRequest, db: Session = Depends(get_workflow_db)) -> TicketMutationResponse:
    ticket_id = int(datetime.now(timezone.utc).timestamp() * 1000)
    now = datetime.now(timezone.utc)

    # Webhook payload prepared but not sent (N8N handles tickets via database polling/triggers)
    # Uncomment below if you configure N8N to return resume_url in response instead of creating a new record
    # webhook_payload: dict[str, Any] = {...}

    try:
        columns = _table_columns(db, "farm_tickets")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to inspect farm_tickets table") from exc

    record_data: dict[str, Any] = {
        "ticket_id": ticket_id,
        "farmer_id": DEFAULT_FARMER_ID,
        "farmer_name": payload.farmer_name,
        "farmer_email": payload.farmer_email,
        "query": payload.query,
        "crop_type": payload.crop_type,
        "location": payload.location,
        "weather": payload.weather,
        "ticket_status": "OPEN",
        "status": "OPEN",
        "workflow_state": "WAITING",
        "risk_level": "MEDIUM",
        "ai_confidence": 0.0,
        "created_at": now,
        "updated_at": now,
    }

    filtered = {key: value for key, value in record_data.items() if key in columns}
    if not filtered:
        raise HTTPException(status_code=500, detail="farm_tickets table columns are not compatible")

    insert_cols = ", ".join(filtered.keys())
    insert_vals = ", ".join(f":{key}" for key in filtered.keys())

    try:
        db.execute(text(f"INSERT INTO farm_tickets ({insert_cols}) VALUES ({insert_vals})"), filtered)
        db.commit()
        logger.info("tickets_insert_success", extra={"ticket_id": ticket_id})
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("tickets_insert_failed")
        raise HTTPException(status_code=500, detail="Failed to create ticket") from exc

    # Trigger N8N workflow to create execution and populate resume_url.
    # N8N is configured to UPDATE this record with resume_url asynchronously.
    webhook_url = (settings.n8n_workflow_webhook_url or "").strip()
    if webhook_url:
        webhook_payload: dict[str, Any] = {
            "event": "farm-ticket",
            "ticket_id": ticket_id,
            "farmer_id": DEFAULT_FARMER_ID,
            "ticket_status": "OPEN",
            "workflow_state": "WAITING",
            "farmer_name": payload.farmer_name,
            "farmer_email": payload.farmer_email,
            "query": payload.query,
            "crop_type": payload.crop_type,
            "location": payload.location,
            "weather": payload.weather,
        }
        try:
            logger.info("tickets_n8n_posting", extra={"ticket_id": ticket_id, "url": webhook_url})
            webhook_result = await _post_json(webhook_url, webhook_payload)
            logger.info("tickets_n8n_response", extra={"ticket_id": ticket_id, "response": str(webhook_result)[:500]})
            
            # Check if resume_url came in the response
            if isinstance(webhook_result, dict) and webhook_result.get("resume_url"):
                resume_url_value = webhook_result.get("resume_url")
                if "resume_url" in columns:
                    logger.info("tickets_updating_resume_url_from_response", extra={"ticket_id": ticket_id, "resume_url": str(resume_url_value)[:80]})
                    db.execute(
                        text("UPDATE farm_tickets SET resume_url = :resume_url, updated_at = :updated_at WHERE ticket_id = :ticket_id"),
                        {"resume_url": str(resume_url_value), "updated_at": now, "ticket_id": ticket_id},
                    )
                    db.commit()
                    logger.info("tickets_update_success", extra={"ticket_id": ticket_id})
            else:
                # N8N doesn't return resume_url in response; it will UPDATE the record asynchronously.
                # Poll the database for up to 5 seconds for N8N to populate resume_url.
                import asyncio
                for attempt in range(10):
                    await asyncio.sleep(0.5)
                    updated_row = _latest_ticket_row(db, ticket_id)
                    if updated_row.get("resume_url"):
                        logger.info("tickets_resume_url_populated_async", extra={"ticket_id": ticket_id, "attempt": attempt + 1})
                        break
                else:
                    logger.warning("tickets_resume_url_not_populated", extra={"ticket_id": ticket_id, "reason": "N8N did not populate resume_url within 5 seconds"})
                    
        except httpx.HTTPError as exc:
            logger.warning("tickets_n8n_webhook_failed", extra={"ticket_id": ticket_id, "error": str(exc)})
        except Exception as exc:
            # N8N follow-up errors must not fail the API after DB commit succeeds.
            logger.warning("tickets_n8n_postprocess_failed", extra={"ticket_id": ticket_id, "error": str(exc)})

    row = _latest_ticket_row(db, ticket_id)

    # Some N8N workflows create a second row (with resume_url) instead of updating
    # the row inserted above. Reconcile to a single canonical row.
    if not row.get("resume_url"):
        duplicate_row = _find_duplicate_with_resume_url(
            db,
            ticket_id=ticket_id,
            farmer_name=payload.farmer_name,
            farmer_email=payload.farmer_email,
            query=payload.query,
            crop_type=payload.crop_type,
            location=payload.location,
            weather=payload.weather,
            created_after=now - timedelta(minutes=2),
        )
        if duplicate_row:
            try:
                db.execute(text("DELETE FROM farm_tickets WHERE ticket_id = :ticket_id"), {"ticket_id": ticket_id})
                db.commit()
                row = duplicate_row
                logger.info(
                    "tickets_duplicate_reconciled",
                    extra={
                        "source_ticket_id": ticket_id,
                        "canonical_ticket_id": row.get("ticket_id"),
                    },
                )
            except SQLAlchemyError:
                db.rollback()
                logger.warning(
                    "tickets_duplicate_reconcile_failed",
                    extra={"source_ticket_id": ticket_id, "canonical_ticket_id": duplicate_row.get("ticket_id")},
                )

    logger.info("tickets_create_complete", extra={"ticket_id": ticket_id, "resume_url_populated": bool(row.get("resume_url"))})
    return TicketMutationResponse(success=True, message="Ticket created and workflow paused", record=_row_to_response(row))


@router.post("/resume-ticket", response_model=TicketMutationResponse)
async def resume_ticket(payload: TicketStatusUpdateRequest, db: Session = Depends(get_workflow_db)) -> TicketMutationResponse:
    row = _latest_ticket_row(db, payload.ticket_id)
    resume_url = row.get("resume_url")
    
    if not resume_url:
        raise HTTPException(
            status_code=400, 
            detail="Workflow is initializing. Please wait 10-15 seconds and try again."
        )

    resume_payload = {"ticket_id": payload.ticket_id, "ticket_status": payload.ticket_status}

    try:
        await _post_json(str(resume_url), resume_payload)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        # N8N returns 409 when a waiting execution was already resumed.
        # Treat it as idempotent success so UI actions don't fail on retries.
        if status_code == 409:
            logger.info("tickets_n8n_resume_already_resumed", extra={"ticket_id": payload.ticket_id})
        elif status_code in {404, 410}:
            raise HTTPException(status_code=400, detail="Resume link is invalid or expired. Create a new ticket.") from exc
        else:
            raise HTTPException(status_code=502, detail=f"Failed to resume N8N workflow (upstream {status_code})") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Failed to reach N8N resume endpoint") from exc

    now = datetime.now(timezone.utc)
    try:
        _update_ticket_state(
            db,
            payload.ticket_id,
            {
                "ticket_status": "IN_PROGRESS",
                "workflow_state": "RUNNING",
                "updated_at": now,
            },
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update ticket state") from exc

    updated = _latest_ticket_row(db, payload.ticket_id)
    return TicketMutationResponse(success=True, message="Workflow resumed successfully", record=_row_to_response(updated))


@router.post("/close-ticket", response_model=TicketMutationResponse)
async def close_ticket(payload: TicketStatusUpdateRequest, db: Session = Depends(get_workflow_db)) -> TicketMutationResponse:
    row = _latest_ticket_row(db, payload.ticket_id)
    resume_url = row.get("resume_url")

    if not resume_url:
        raise HTTPException(
            status_code=400,
            detail="Workflow resume link is missing. Please create a new ticket if this one is stale.",
        )

    resume_payload = {"ticket_id": payload.ticket_id, "ticket_status": payload.ticket_status}

    try:
        await _post_json(str(resume_url), resume_payload)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        # N8N returns 409 when a waiting execution was already resumed.
        # Treat it as idempotent success so UI actions don't fail on retries.
        if status_code == 409:
            logger.info("tickets_n8n_close_already_resumed", extra={"ticket_id": payload.ticket_id})
        elif status_code in {404, 410}:
            raise HTTPException(status_code=400, detail="Resume link is invalid or expired. Create a new ticket.") from exc
        else:
            raise HTTPException(status_code=502, detail=f"Failed to close N8N workflow (upstream {status_code})") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Failed to reach N8N resume endpoint") from exc

    now = datetime.now(timezone.utc)

    try:
        _update_ticket_state(
            db,
            payload.ticket_id,
            {
                "ticket_status": "CLOSED",
                "workflow_state": "CLOSED",
                "updated_at": now,
            },
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to close ticket") from exc

    updated = _latest_ticket_row(db, payload.ticket_id)
    return TicketMutationResponse(success=True, message="Ticket closed", record=_row_to_response(updated))
