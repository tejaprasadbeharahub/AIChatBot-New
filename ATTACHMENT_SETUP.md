# Attachment System - Quick Start Guide

## Prerequisites

Ensure your environment is set up with:
- Python 3.9+ (backend)
- Node.js 18+ (frontend)
- PostgreSQL running
- Virtual environment activated

## Setup Steps

### 1. Apply Database Migration

Run the Alembic migration to create the `attachments` table:

```bash
cd backend
alembic upgrade head
```

This will:
- Create the `attachments` table
- Add indexes for query optimization
- Set up cascade delete relationships

### 2. Verify Configuration

Check `.env` file has correct upload settings:

```env
# File uploads
MAX_UPLOAD_MB=20
UPLOAD_DIR=./uploads
```

The `./uploads` directory will be created automatically on first upload.

### 3. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --host localhost --port 8000
```

The backend will:
- Load all models including Attachment
- Register new API routes under `/api/attachments`
- Create uploads directory if needed

### 4. Start Frontend

```bash
cd frontend
npm run dev -- --host localhost --port 5173
```

The frontend will:
- Load new components (AttachmentUploadButton, AttachmentPreview)
- Enable file upload UI in chat composer
- Display attachments in messages

### 5. Test Attachment System

1. Open http://localhost:5173 in browser
2. Login or register
3. Start a new chat
4. Click the attachment button (📎) next to the message input
5. Select "📷 Image" and choose an image file
6. Type a message
7. Click Send
8. Verify:
   - Image preview appears in your message
   - Response appears from assistant
   - File saved to `./uploads` directory

## File Organization

After first upload, your project structure will include:

```
project_root/
├── uploads/              # New directory
│   └── abc12345/        # Message ID prefix
│       └── uuid1.jpg    # Uploaded file
├── backend/
├── frontend/
├── .env
└── ATTACHMENT_SYSTEM.md
```

## Troubleshooting

### Issue: "Attachment upload failed: Permission denied"

**Solution**: Ensure the `uploads` directory is writable:
```bash
# Linux/Mac
chmod 755 uploads

# Windows: Right-click > Properties > Security > Modify permissions
```

### Issue: "File type not allowed"

**Solution**: Check file extension is in allowed list:
- Images: .jpg, .jpeg, .png, .gif, .webp, .svg
- Videos: .mp4, .webm, .mov, .avi
- Code: .py, .js, .ts, .java, .cpp, .go, .rb, .php, .sql, .html, .css, .json, .yaml, .xml, .txt
- Documents: .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt, .csv
- Formulas: .tex, .txt, .md

### Issue: "File size exceeds limit of 20MB"

**Solution**: Either:
- Upload a smaller file
- Update `MAX_UPLOAD_MB` in `.env` (not recommended > 100)
- Restart backend after changing `.env`

### Issue: Attachment button not showing

**Solution**: 
- Ensure frontend is running on same localhost:5173
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console (F12) for JS errors
- Verify all .tsx files compiled without errors

### Issue: Upload succeeds but file not displayed

**Solution**:
- Check backend logs for errors
- Verify `./uploads` directory exists
- Ensure file was actually saved to disk
- Check browser console for API errors

## Key Files Modified/Created

### Backend
- `app/models/attachment.py` - NEW: SQLAlchemy model
- `app/schemas/attachment.py` - NEW: Pydantic schemas
- `app/repositories/attachment_repo.py` - NEW: Data access layer
- `app/services/attachment_service.py` - NEW: Business logic
- `app/api/attachment.py` - NEW: API endpoints
- `app/models/message.py` - MODIFIED: Added relationship
- `app/schemas/message.py` - MODIFIED: Added attachments field
- `app/main.py` - MODIFIED: Registered router
- `alembic/versions/create_attachments_table.py` - NEW: Migration
- `.env` - MODIFIED: Added MAX_UPLOAD_MB, UPLOAD_DIR

### Frontend
- `src/components/chat/AttachmentUploadButton.tsx` - NEW
- `src/components/chat/AttachmentPreview.tsx` - NEW
- `src/types/chat.ts` - MODIFIED: Added Attachment type
- `src/api/chat.ts` - MODIFIED: Added upload/download/delete functions
- `src/App.tsx` - MODIFIED: Integrated attachment handling
- `src/index.css` - MODIFIED: Added attachment styles

## Development Notes

### Adding New File Types

To support additional file types, edit `app/services/attachment_service.py`:

```python
ALLOWED_FILE_TYPES = {
    "your_type": {
        "extensions": {".ext1", ".ext2"},
        "mimes": {"mime/type1", "mime/type2"},
    },
}
```

Then update the Literal type in `src/types/chat.ts`:

```typescript
file_type: Literal["image", "video", "code", "formula", "document", "your_type"]
```

### Changing Upload Size Limit

1. Edit `.env`: `MAX_UPLOAD_MB=50` (example)
2. Restart backend
3. Frontend will automatically respect new limit

### Implementing Cloud Storage

When ready to move from disk storage:

1. Extend `attachment_service.py`:
   - Replace `save_uploaded_file()` with S3/Azure upload
   - Update `get_file_path()` to return signed URL
   - Update `delete_uploaded_file()` for cloud deletion

2. Update `.env`:
   - Add cloud credentials
   - Change UPLOAD_DIR to bucket name

3. Update API routes if needed for pre-signed URLs

## Database Backup

Before deployment, back up your attachments:

```bash
# PostgreSQL backup
pg_dump aichatbot_db > backup.sql

# Files backup
cp -r uploads/ uploads_backup/
```

## Next Steps

1. Test all file types with real files
2. Verify attachment display in different browsers
3. Test with large files near 20MB limit
4. Monitor disk usage of uploads directory
5. Implement attachment deletion by users
6. Add retention policies if needed
7. Consider cloud storage migration plan

## Performance Tuning

For production, consider:

```python
# In config.py
max_upload_mb: int = 50  # Increase if needed
# But keep reasonable to prevent memory issues

# In attachment_service.py
# Stream large files instead of loading to memory
async def save_uploaded_file_stream(file, path, chunk_size=1024*1024):
    # Read and write in chunks for memory efficiency
```

## Support

For issues or questions:
1. Check ATTACHMENT_SYSTEM.md documentation
2. Review error messages in browser console (F12)
3. Check backend logs for detailed errors
4. Verify all migrations applied: `alembic history`
5. Test with simple files first (small JPGs, PDFs)
