# Environment Variables Setup for AI Image Generation

Add these environment variables to your `.env` file in the project root:

```env
# Google Generative AI Configuration (REQUIRED for image generation)
GOOGLE_GENERATIVE_AI_KEY=your_google_generative_ai_api_key_here

# Image Generation Settings (Optional - defaults shown)
IMAGE_GEN_MAX_PER_CHAT=10              # Maximum image generations per chat thread
IMAGE_GEN_MAX_PER_DAY=50               # Maximum image generations per day
IMAGE_GEN_TIMEOUT_SECONDS=120          # Timeout for generation requests
IMAGE_STORAGE_DIR=./generated_images   # Directory to store generated images
```

## How to Get Google Generative AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click on "Get API key" button
3. Create a new API key or use existing one
4. Copy the API key
5. Add it to `.env` as `GOOGLE_GENERATIVE_AI_KEY=your_key_here`

## Alternatively (via Google Cloud Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Generative Language API"
4. Create a service account or use existing
5. Generate an API key
6. Add to `.env`

## Install Required Package

The `google-generativeai` package has already been added to `requirements.txt`. Install it with:

```bash
pip install google-generativeai
```

Or if running the full setup:

```bash
pip install -r requirements.txt
```

## Verify Setup

Run the backend with:

```bash
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

Check that no import errors occur. The image generation endpoints should be available at:
- POST `/api/image-generation/generate`
- GET `/api/image-generation/{image_id}`
- GET `/api/image-generation/chat/{chat_id}/images`
- GET `/api/image-generation/download/{image_id}`
- DELETE `/api/image-generation/{image_id}`

## Rate Limiting Configuration

### Per-Chat Limit
- Default: 10 images per chat
- Adjust: Set `IMAGE_GEN_MAX_PER_CHAT=<number>`
- Prevents: Generating too many images in a single conversation

### Per-Day Limit  
- Default: 50 images total per day
- Adjust: Set `IMAGE_GEN_MAX_PER_DAY=<number>`
- Prevents: Excessive API usage and costs

## Storage Configuration

### Image Storage Directory
- Default: `./generated_images` (relative to project root)
- Adjust: Set `IMAGE_STORAGE_DIR=/absolute/path/or/relative/path`
- Auto-created: Directory is automatically created if it doesn't exist

### Storage Location Examples
```env
# Relative to project root
IMAGE_STORAGE_DIR=./generated_images

# Absolute path on Linux/Mac
IMAGE_STORAGE_DIR=/var/ai-chatbot/images

# Absolute path on Windows
IMAGE_STORAGE_DIR=C:\ai-chatbot\images

# Relative to home directory
IMAGE_STORAGE_DIR=~/ai-chatbot/generated_images
```

## Timeout Configuration

Image generation timeout in seconds:
- Default: 120 seconds (2 minutes)
- Adjust: Set `IMAGE_GEN_TIMEOUT_SECONDS=<seconds>`
- Recommendation: Keep between 60-180 seconds

## Database Migration

After setting up environment variables and before starting the server, run the migration:

```bash
cd backend
alembic upgrade head
```

This creates the `generated_images` table in your PostgreSQL database.

## Troubleshooting

### "GOOGLE_GENERATIVE_AI_KEY is not configured"
- Error appears when trying to generate an image
- **Solution**: Add `GOOGLE_GENERATIVE_AI_KEY` to `.env` file
- Verify the key is correct by testing in Google AI Studio

### "Maximum image generations per chat reached"
- Error appears after reaching limit
- **Solution**: Increase `IMAGE_GEN_MAX_PER_CHAT` or delete old images

### Permission denied saving image files
- Error in logs when trying to save generated image
- **Solution**: Check write permissions on `IMAGE_STORAGE_DIR`
- For Linux/Mac: `chmod 755 ./generated_images`
- For Windows: Right-click folder → Properties → Security → Edit permissions

### Image generation times out
- Generation takes too long or fails with timeout error
- **Solution**: 
  - Increase `IMAGE_GEN_TIMEOUT_SECONDS`
  - Check API quota in Google Cloud Console
  - Try simpler/shorter prompts
  - Check network connectivity

## Complete Example .env

Here's a complete example with all image generation variables:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/aichatbot_db

# JWT & Security
JWT_SECRET_KEY=your_jwt_secret_key_here
SECRET_KEY=your_secret_key_here

# LiteLLM / Chat Model
LITELLM_API_KEY=your_litellm_key
LITELLM_PROXY_URL=http://localhost:4000/v1
LLM_MODEL=gpt-4-turbo-preview

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Gemini / Image Generation
GOOGLE_GENERATIVE_AI_KEY=your_google_generative_ai_key_here
GEMINI_API_KEY=your_gemini_api_key

# Image Generation Configuration
IMAGE_GEN_MAX_PER_CHAT=10
IMAGE_GEN_MAX_PER_DAY=50
IMAGE_GEN_TIMEOUT_SECONDS=120
IMAGE_STORAGE_DIR=./generated_images

# File Upload Configuration
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=20

# App Configuration
APP_NAME=Amzur AI Chatbot
ENVIRONMENT=development
CHAT_MEMORY_TURNS=5

# Frontend
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

## Next Steps

1. ✅ Backend implementation complete
2. ✅ Frontend components created
3. ⏳ **TODO**: Integrate image generation into App.tsx chat flow
4. ⏳ **TODO**: Add image generation button to chat interface
5. ⏳ **TODO**: Handle polling for image generation status
6. ⏳ **TODO**: Display generated images in chat messages
7. ⏳ **TODO**: Test end-to-end flow
8. ⏳ **TODO**: Add CSS styling to main index.css

See `AI_IMAGE_GENERATION_IMPLEMENTATION.md` for complete technical documentation.
