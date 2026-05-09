# AI Image Generation Implementation Guide

## Overview

This document describes the implementation of AI image generation using Google Gemini 2.0 Image Generation model integrated into the AIChatBot application.

## Architecture

### Backend Components

#### 1. Database Model (`app/models/generated_image.py`)
- **Table**: `generated_images`
- **Fields**:
  - `id`: Unique identifier for each generated image
  - `message_id`: Reference to the chat message
  - `chat_id`: Reference to the chat thread
  - `prompt`: The image generation prompt
  - `image_url`: URL/path to the generated image
  - `image_path`: Storage path for the image file
  - `status`: Generation status (pending, completed, failed)
  - `error_message`: Error details if generation failed
  - `generation_timestamp`: When generation was requested
  - `completion_timestamp`: When generation completed

#### 2. Repository (`app/repositories/generated_image_repo.py`)
Database access layer for generated images with functions:
- `create_generated_image()`: Create a new pending image record
- `get_generated_image()`: Retrieve image by ID
- `get_images_for_message()`: Get images for a specific message
- `get_images_for_chat()`: Get all images in a chat thread
- `update_image_completion()`: Update status after generation
- `delete_generated_image()`: Delete image record and file

#### 3. Service (`app/services/image_generation_service.py`)
Core business logic for image generation:
- `validate_image_prompt()`: Validate prompt format and length
- `generate_image_from_prompt()`: Start async image generation
- `_generate_image_async()`: Async generation worker task
- `get_image_storage_directory()`: Manage local image storage
- Rate limiting checks per chat and per day
- Error handling and logging

#### 4. API Endpoints (`app/api/image_generation.py`)
RESTful API endpoints:

- **POST `/api/image-generation/generate`**
  - Request: `ImageGenerationRequest` with prompt, chat_id, message_id
  - Response: `GeneratedImageResponse` with initial pending status
  - Purpose: Start image generation task

- **GET `/api/image-generation/{image_id}`**
  - Response: `GeneratedImageResponse` with current status
  - Purpose: Check generation progress/status

- **GET `/api/image-generation/chat/{chat_id}/images`**
  - Query param: `limit` (default: 50)
  - Response: List of `GeneratedImageResponse`
  - Purpose: Retrieve all images for a chat

- **GET `/api/image-generation/download/{image_id}`**
  - Response: Image file (PNG)
  - Purpose: Download completed image

- **DELETE `/api/image-generation/{image_id}`**
  - Response: Success message
  - Purpose: Delete image record and file

#### 5. Configuration (`app/core/config.py`)
Environment variables:
- `GOOGLE_GENERATIVE_AI_KEY`: Google Generative AI API key (required)
- `IMAGE_GEN_MAX_PER_CHAT`: Maximum generations per chat (default: 10)
- `IMAGE_GEN_MAX_PER_DAY`: Maximum generations per day (default: 50)
- `IMAGE_GEN_TIMEOUT_SECONDS`: Generation timeout (default: 120)
- `IMAGE_STORAGE_DIR`: Directory for saving generated images (default: `./generated_images`)

#### 6. Database Migration
Migration file: `alembic/versions/d1e2f3g4h5i6_create_generated_images_table.py`
- Creates `generated_images` table with proper indexes
- Creates `image_generation_status` enum type
- Handles upgrades and downgrades

### Frontend Components

#### 1. Types (`src/types/image_generation.ts`)
TypeScript interfaces:
- `GeneratedImage`: Complete image data
- `ImageGenerationRequest`: Request payload
- `ImageGenerationResponse`: API response
- `GenerationStatus`: Status union type

#### 2. API Client (`src/api/image_generation.ts`)
API communication functions:
- `generateImage()`: Start image generation
- `getImageStatus()`: Poll image generation status
- `getChatGeneratedImages()`: Fetch chat images
- `downloadGeneratedImage()`: Download image blob
- `deleteGeneratedImage()`: Delete image

#### 3. Components

**GeneratedImageDisplay.tsx**
- Displays generated images with status handling
- Shows loading spinner during generation
- Shows error state with error message
- Displays completed image with actions (expand, delete)
- Shows prompt text with image

**ImageGenerationPrompt.tsx**
- Collapsible form for image generation prompts
- Textarea input with character counter (max 2000)
- Generate and Cancel buttons with validation
- Prevents submission when disabled or prompt too short
- Loading state feedback

#### 4. Styling (`src/components/chat/ImageGeneration.css`)
Complete styling for:
- Toggle button and form
- Input controls with focus states
- Loading spinner animation
- Error display styling
- Image display with hover actions
- Responsive design for mobile

### Integration Points

## Setup Instructions

### 1. Backend Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** in `.env`:
   ```env
   GOOGLE_GENERATIVE_AI_KEY=your_gemini_api_key_here
   IMAGE_GEN_MAX_PER_CHAT=10
   IMAGE_GEN_MAX_PER_DAY=50
   IMAGE_GEN_TIMEOUT_SECONDS=120
   IMAGE_STORAGE_DIR=./generated_images
   ```

3. **Run database migration**:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Start backend**:
   ```bash
   python -m uvicorn app.main:app --host localhost --port 8000
   ```

### 2. Frontend Setup

1. **CSS already included**: The image generation styles are in `src/components/chat/ImageGeneration.css`

2. **Integration in App.tsx**: Add image generation to your chat component

3. **Start frontend**:
   ```bash
   npm run dev
   ```

## Usage Flow

### User Perspective
1. User opens chat window
2. Clicks "🖼️ Generate Image" button
3. Enters image description (2-2000 characters)
4. Clicks "Generate Image"
5. See loading spinner while image is being generated
6. Once complete, image appears in chat with prompt text
7. Can expand, download, or delete the generated image

### Technical Flow
1. Frontend calls `POST /api/image-generation/generate` with prompt
2. Backend creates pending record and starts async task
3. Backend calls Google Gemini 2.0 Image Generation API
4. Image is generated and saved locally
5. Database record is updated with completion status
6. Frontend polls `GET /api/image-generation/{image_id}` for status updates
7. When complete, image URL is displayed
8. User can download or delete the image

## Rate Limiting

The implementation includes built-in rate limiting:
- **Per Chat**: Maximum `IMAGE_GEN_MAX_PER_CHAT` generations per chat thread
- **Per Day**: Maximum `IMAGE_GEN_MAX_PER_DAY` generations per day (across all chats)

These can be configured via environment variables.

## Error Handling

### Backend Error Scenarios
1. **Invalid Prompt**: Prompt too short (<2 chars) or too long (>2000 chars)
2. **Rate Limit Exceeded**: Too many generations in chat or per day
3. **API Key Missing**: GOOGLE_GENERATIVE_AI_KEY not set
4. **Generation Failure**: Error from Gemini API is captured and logged
5. **Storage Error**: Failure to save image locally is logged but doesn't block

### Frontend Error Scenarios
1. **Network Error**: Displayed to user with error message
2. **Generation Failed**: Shows error state with failure details
3. **Validation Error**: Button disabled if prompt invalid
4. **Status Check Failed**: Retries polling with backoff

## Security Considerations

1. **API Key Protection**: Stored in environment variables, never exposed to frontend
2. **Prompt Validation**: Server-side validation of prompt content
3. **File Storage**: Images stored on server, not publicly accessible
4. **Authentication**: All endpoints require valid JWT token
5. **Rate Limiting**: Prevents abuse and excessive API usage
6. **Enum Status**: Status can only be 'pending', 'completed', or 'failed'

## Future Enhancements

Possible improvements for future versions:
1. Image prompt refinement UI (keywords, style, quality settings)
2. Image variation generation (similar to prompt)
3. Image editing capabilities
4. Public image gallery/sharing
5. Batch image generation
6. Scheduled generation tasks
7. Image quality/resolution options
8. Negative prompts support
9. Image annotation and metadata
10. Integration with other Gemini multimodal models

## Troubleshooting

### Image generation returns "No images generated"
- Check that GOOGLE_GENERATIVE_AI_KEY is set correctly
- Verify Gemini API is enabled in Google Cloud Console
- Check API quota limits in Google Cloud

### Images not being saved locally
- Verify IMAGE_STORAGE_DIR directory has write permissions
- Check disk space availability
- Review logs for storage errors

### Polling never completes
- Check that backend is running
- Verify JWT token is valid
- Check browser console for network errors
- Review backend logs for async task errors

### Rate limit hit quickly
- Adjust IMAGE_GEN_MAX_PER_CHAT and IMAGE_GEN_MAX_PER_DAY
- Implement user-specific rate limiting if needed
- Add quota reset mechanism for daily limits

## Performance Considerations

1. **Async Generation**: Image generation happens asynchronously so chat UI remains responsive
2. **Polling Strategy**: Frontend should implement exponential backoff for status checks
3. **Image Caching**: Consider caching generated images in browser local storage
4. **Database Indexing**: Indexes on message_id and chat_id for fast lookups
5. **File Storage**: Regular cleanup of old generated images recommended

## Testing

### Unit Tests Needed
- Prompt validation logic
- Rate limit checking
- Database CRUD operations
- API endpoint contracts

### Integration Tests Needed
- End-to-end generation flow
- Error handling and recovery
- Status polling mechanism
- File storage and retrieval

## Dependencies

### Backend
- `google-generativeai`: Google's official SDK for Generative AI
- `fastapi`: Web framework
- `sqlalchemy`: ORM
- `pydantic`: Data validation

### Frontend
- `react`: UI framework
- `typescript`: Type safety
- `vite`: Build tool

## Notes

- Image generation can take 30-120 seconds depending on prompt complexity
- Each generation consumes API quota from Google Cloud
- Generated images are stored locally in `./generated_images` directory
- Database stores both local path and URL references
- Async tasks are processed using asyncio (can be upgraded to Celery for distributed processing)
- CORS is configured to allow frontend origins
