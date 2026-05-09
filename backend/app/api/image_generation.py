import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.repositories import generated_image_repo
from app.schemas.generated_image import (
    GeneratedImageResponse,
    ImageGenerationRequest,
)
from app.services import image_generation_service

router = APIRouter(prefix="/image-generation", tags=["image-generation"])
logger = logging.getLogger(__name__)


@router.post("/generate")
async def generate_image(
    request: ImageGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedImageResponse:
    """
    Generate an AI image from a text prompt using Gemini 2.0.
    
    - **prompt**: The image description/prompt (2-2000 characters)
    - **chat_id**: The chat thread to associate the image with
    - **message_id**: The message to associate the image with
    """
    try:
        # Validate prompt
        if not image_generation_service.validate_image_prompt(request.prompt):
            raise HTTPException(
                status_code=400,
                detail="Invalid prompt: must be between 2 and 2000 characters",
            )

        # Start async generation
        image_id = await image_generation_service.generate_image_from_prompt(
            db=db,
            prompt=request.prompt,
            message_id=str(request.message_id),
            chat_id=str(request.chat_id),
        )

        # Return initial pending status
        image = generated_image_repo.get_generated_image(db, uuid.UUID(image_id))
        if not image:
            raise HTTPException(status_code=500, detail="Failed to create image record")

        return GeneratedImageResponse(
            id=image.id,
            status=image.status,
            prompt=image.prompt,
            image_url=image.image_url,
            message_id=image.message_id,
            generation_timestamp=image.generation_timestamp,
            completion_timestamp=image.completion_timestamp,
            error_message=image.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image generation request failed")
        raise HTTPException(
            status_code=500, detail=f"Image generation failed: {str(e)}"
        )


@router.get("/{image_id}")
async def get_image_status(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedImageResponse:
    """
    Get the status and details of a generated image.
    """
    try:
        img_uuid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image_id format")

    image = image_generation_service.get_generated_image(db, img_uuid)

    return GeneratedImageResponse(
        id=image.id,
        status=image.status,
        prompt=image.prompt,
        image_url=image.image_url,
        message_id=image.message_id,
        generation_timestamp=image.generation_timestamp,
        completion_timestamp=image.completion_timestamp,
        error_message=image.error_message,
    )


@router.get("/chat/{chat_id}/images")
async def get_chat_images(
    chat_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GeneratedImageResponse]:
    """
    Get all generated images for a chat thread.
    """
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    images = image_generation_service.get_chat_generated_images(db, chat_uuid, limit=limit)

    return [
        GeneratedImageResponse(
            id=img.id,
            status=img.status,
            prompt=img.prompt,
            image_url=img.image_url,
            message_id=img.message_id,
            generation_timestamp=img.generation_timestamp,
            completion_timestamp=img.completion_timestamp,
            error_message=img.error_message,
        )
        for img in images
    ]


@router.get("/download/{image_id}")
async def download_generated_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Download a generated image file.
    """
    try:
        img_uuid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image_id format")

    image = image_generation_service.get_generated_image(db, img_uuid)

    if image.status != "completed" or not image.image_path:
        raise HTTPException(
            status_code=404, detail="Generated image is not available"
        )

    # Get full file path
    image_dir = image_generation_service.get_image_storage_directory()
    file_path = image_dir / f"{image_id}.png"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(
        path=file_path,
        filename=f"generated-{image_id}.png",
        media_type="image/png",
    )


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Delete a generated image and its associated file.
    """
    try:
        img_uuid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image_id format")

    success = image_generation_service.delete_generated_image(db, img_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Generated image not found")

    return {"message": "Image deleted successfully"}
