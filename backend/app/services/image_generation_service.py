import base64
import asyncio
import io
import logging
import uuid
from pathlib import Path

import requests
from fastapi import HTTPException
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import generated_image_repo

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_image_storage_directory() -> Path:
    """Get or create image storage directory"""
    image_dir = settings.image_storage_dir or "./generated_images"
    path = Path(image_dir)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_image_prompt(prompt: str) -> bool:
    """Validate image generation prompt"""
    if not prompt or not prompt.strip():
        return False

    # Simple safety check: reject very short prompts and extremely long ones
    prompt_len = len(prompt.strip())
    if prompt_len < 2 or prompt_len > 2000:
        return False

    return True


async def generate_image_from_prompt(
    db: Session,
    prompt: str,
    message_id: str,
    chat_id: str,
) -> str:
    """
    Generate an image using Google Gemini 2.0 Image Generation model.
    Returns the generated image ID.
    """
    # Convert string IDs to UUID
    try:
        message_uuid = uuid.UUID(message_id) if isinstance(message_id, str) else message_id
        chat_uuid = uuid.UUID(chat_id) if isinstance(chat_id, str) else chat_id
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid message_id or chat_id format",
        )

    # Validate prompt
    if not validate_image_prompt(prompt):
        raise HTTPException(
            status_code=400,
            detail="Invalid prompt: must be between 2 and 2000 characters",
        )

    # Check rate limits
    existing_images = generated_image_repo.get_images_for_chat(db, chat_uuid)
    if len(existing_images) >= settings.image_gen_max_per_chat:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum image generations per chat ({settings.image_gen_max_per_chat}) reached",
        )

    # Create pending record
    image_record = generated_image_repo.create_generated_image(
        db=db,
        prompt=prompt,
        message_id=message_uuid,
        chat_id=chat_uuid,
    )

    # Schedule background generation without blocking the API response.
    asyncio.create_task(
        _generate_image_async(image_record.id, prompt)
    )

    return str(image_record.id)


async def _generate_image_async(
    image_id: uuid.UUID, prompt: str
) -> None:
    """Asynchronously generate image using LiteLLM API"""
    try:
        logger.info(f"Starting image generation for {image_id} with prompt: {prompt[:100]}...")

        import json
        from PIL import Image as PILImage
        from app.db.session import _make_session_factory

        # Create a new database session for this async task
        SessionFactory = _make_session_factory()
        db = SessionFactory()

        try:
            # Get credentials from settings
            api_key = settings.litellm_api_key
            model = settings.image_gen_model
            proxy_url = settings.litellm_proxy_url
            
            if not api_key or not model or not proxy_url:
                raise Exception(
                    "LITELLM_API_KEY, IMAGE_GEN_MODEL, or LITELLM_PROXY_URL not configured"
                )

            logger.info(f"Using model: {model}")
            logger.info(f"Using proxy URL: {proxy_url}")

            # Call LiteLLM API for image generation
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model,
                "prompt": prompt,
                "n": 1,
                "size": "1024x576"
            }

            # Try both endpoint formats
            endpoints = [
                f"{proxy_url}/v1/images/generations",  # OpenAI-compatible format
                f"{proxy_url}/image/generation",        # Alternative format
            ]

            response = None
            error_msg = None

            for endpoint in endpoints:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = await asyncio.to_thread(
                        requests.post,
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=120,
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Success with endpoint: {endpoint}")
                        break
                    else:
                        error_msg = f"Status {response.status_code}: {response.text}"
                        logger.warning(f"Failed with {endpoint}: {error_msg}")
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"Error with {endpoint}: {error_msg}")
                    continue

            if not response or response.status_code != 200:
                raise Exception(f"LiteLLM API failed: {error_msg or 'Unknown error'}")

            response_data = response.json()
            logger.info(f"LiteLLM response: {json.dumps(response_data, indent=2)[:500]}")

            # Extract image from response
            image = None
            
            if "data" in response_data and len(response_data["data"]) > 0:
                image_data = response_data["data"][0]
                logger.info(f"Image data keys: {list(image_data.keys())}")
                
                # Handle both base64 and URL responses
                if "b64_json" in image_data:
                    logger.info("Using b64_json format")
                    image_bytes = base64.b64decode(image_data["b64_json"])
                    image = PILImage.open(io.BytesIO(image_bytes))
                elif "url" in image_data:
                    logger.info(f"Downloading from URL: {image_data['url']}")
                    img_response = await asyncio.to_thread(
                        requests.get,
                        image_data["url"],
                        timeout=30,
                    )
                    image = PILImage.open(io.BytesIO(img_response.content))
                else:
                    raise Exception(f"Unexpected image data format. Keys: {list(image_data.keys())}")
            else:
                raise Exception(f"No images in response. Response: {response_data}")

            if not image:
                raise Exception("Failed to extract image")

            # Save image to local storage
            image_dir = get_image_storage_directory()
            image_filename = f"{image_id}.png"
            image_path = image_dir / image_filename
            storage_path = f"generated_images/{image_filename}"

            # Save image
            await asyncio.to_thread(image.save, str(image_path), format="PNG")
            logger.info(f"Image saved successfully to {image_path}, size: {image.size}")

            # Update record with completion status
            generated_image_repo.update_image_completion(
                db=db,
                image_id=image_id,
                status="completed",
                image_url=f"/api/image-generation/download/{image_id}",
                image_path=storage_path,
            )

            logger.info(f"Image generation completed successfully for {image_id}")

        finally:
            db.close()

    except Exception as e:
        error_message = str(e)
        logger.error(f"Image generation failed for {image_id}: {error_message}", exc_info=True)
        
        # Try to create a session to update the error status
        try:
            from app.db.session import _make_session_factory
            SessionFactory = _make_session_factory()
            db = SessionFactory()
            try:
                generated_image_repo.update_image_completion(
                    db=db,
                    image_id=image_id,
                    status="failed",
                    error_message=error_message,
                )
            finally:
                db.close()
        except Exception as db_error:
            logger.error(f"Failed to update database with error status: {db_error}")


def get_generated_image(db: Session, image_id: uuid.UUID):
    """Retrieve generated image record"""
    image = generated_image_repo.get_generated_image(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Generated image not found")
    return image


def get_chat_generated_images(db: Session, chat_id: uuid.UUID, limit: int = 50):
    """Retrieve all generated images for a chat"""
    return generated_image_repo.get_images_for_chat(db, chat_id, limit=limit)


def delete_generated_image(db: Session, image_id: uuid.UUID) -> bool:
    """Delete a generated image record and file"""
    image = generated_image_repo.get_generated_image(db, image_id)
    if not image:
        return False

    # Try to delete file if it exists
    if image.image_path:
        try:
            file_path = Path(image.image_path)
            if not file_path.is_absolute():
                file_path = get_image_storage_directory() / image.image_path
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete image file for {image_id}: {str(e)}")

    # Delete database record
    return generated_image_repo.delete_generated_image(db, image_id)
