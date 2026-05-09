# Attachment System Implementation Guide

## Overview

A comprehensive attachment system has been implemented for the AI Chatbot application, enabling users to upload and share various file types within chat conversations. The system is modular, scalable, and designed to support future AI analysis features.

## Architecture

### Backend Architecture

#### Database Layer
- **Model**: `Attachment` (SQLAlchemy ORM)
  - Stores metadata: file name, type, MIME type, size, storage path
  - One-to-many relationship with `Message` (cascade delete)
  - Fields: id, message_id, file_name, file_type, mime_type, file_size, storage_path, upload_timestamp

- **Migration**: Alembic migration `create_attachments_table.py`
  - Creates PostgreSQL table with proper indexing
  - Foreign key constraint with cascade delete for data integrity

#### Repository Layer
- **Module**: `attachment_repo.py`
- **Functions**:
  - `create_attachment()` - Insert new attachment record
  - `get_attachment()` - Retrieve single attachment by ID
  - `get_attachments_for_message()` - Get all attachments for a message
  - `get_attachments_for_chat()` - Get all attachments for a chat thread
  - `delete_attachment()` - Delete attachment record
  - `delete_attachments_for_message()` - Bulk delete for a message

#### Service Layer
- **Module**: `attachment_service.py`
- **Key Functions**:
  - `validate_file_type()` - Check extension and MIME type against allowlist
  - `validate_file_size()` - Verify file doesn't exceed configured limit
  - `process_and_store_attachment()` - Full upload pipeline:
    1. Validate file size
    2. Check file type/extension/MIME
    3. Generate unique storage path
    4. Save file to disk
    5. Create database record
    6. Return attachment metadata
  - `delete_attachment_with_file()` - Remove both file and record
  - `get_upload_directory()` - Ensure upload directory exists

- **Supported File Types**:
  - **Image**: .jpg, .jpeg, .png, .gif, .webp, .svg
  - **Video**: .mp4, .webm, .mov, .avi
  - **Code**: .py, .js, .ts, .java, .cpp, .go, .rb, .php, .sql, .html, .css, .json, .yaml, .xml, .txt
  - **Document**: .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt, .csv
  - **Formula**: .tex, .txt, .md

#### API Layer
- **Router**: `attachment.py`
- **Endpoints**:
  - `POST /api/attachments/upload` - Upload new attachment
    - Form data: message_id, file_type, file
    - Returns: AttachmentMetadata with id, file_name, mime_type, file_size, etc.
  - `GET /api/attachments/download/{attachment_id}` - Download file
    - Returns: FileResponse with proper MIME type
  - `DELETE /api/attachments/{attachment_id}` - Delete attachment
    - Removes file and database record
  - `GET /api/attachments/message/{message_id}` - List message attachments
    - Returns: Array of AttachmentMetadata

#### Configuration
- **File**: `.env`
  - `MAX_UPLOAD_MB=20` - Maximum file size (default: 20MB)
  - `UPLOAD_DIR=./uploads` - Storage directory (default: ./uploads in project root)
- **Code**: `core/config.py`
  - Settings class reads environment variables
  - LRU cache ensures singleton instance

### Frontend Architecture

#### Components

**AttachmentUploadButton.tsx**
- Dropdown menu with file type options
- File input filtering by type
- Handles file selection and passes to parent
- Props:
  - `onAttachmentSelect(file, fileType)` - Callback on file selection
  - `disabled?: boolean` - Disable during upload/send

**AttachmentPreview.tsx**
- Displays different previews based on file type:
  - **Image**: Renders `<img>` with max-height: 300px
  - **Video**: Renders `<video>` with controls
  - **Code/Formula/Document**: Shows file icon, name, size, download button
- Props:
  - `attachment: Attachment` - Metadata object
  - `onDownload?(attachmentId)` - Optional download callback

#### API Integration
- **Module**: `api/chat.ts`
- **New Functions**:
  - `uploadAttachment(messageId, fileType, file)` - POST FormData
  - `downloadAttachment(attachmentId)` - GET blob, trigger download
  - `deleteAttachment(attachmentId)` - DELETE attachment

#### State Management
- **In App.tsx**:
  - `pendingAttachments` - List of files awaiting upload
  - `isUploadingAttachment` - Boolean flag
  - `handleAttachmentSelect()` - Add to pending list
  - `handleDownloadAttachment()` - Trigger download
  - Modified `handleSubmit()`:
    1. Send text message first
    2. Upload pending attachments to message
    3. Update UI with attachment metadata
    4. Clear pending list

#### Types
- **chat.ts**:
  - `Attachment` type with id, file_name, file_type, mime_type, file_size, upload_timestamp
  - Updated `Message` type includes `attachments: Attachment[]`

#### Styling
- **CSS Classes** in `index.css`:
  - `.attachment-upload-wrapper` - Container for button and menu
  - `.attachment-btn` - Clip emoji button (📎)
  - `.attachment-menu` - Dropdown menu (initially hidden)
  - `.attachment-menu.open` - Visible dropdown state
  - `.attachment-preview` - Container for preview content
  - `.attachment-image/.attachment-video` - Responsive media
  - `.attachment-file-info` - File metadata display
  - `.pending-attachments` - List of files to upload
  - `.pending-attachment` - Individual pending file pill
  - `.message-attachments` - Container in chat bubble
  - `.composer-input-wrapper` - Groups textarea and pending list
  - `.composer` - Updated grid with 3 columns (textarea, upload btn, send btn)

## File Storage

### Directory Structure
```
uploads/
├── [UUID_prefix_1]/
│   ├── [random_uuid_1].jpg
│   └── [random_uuid_2].pdf
├── [UUID_prefix_2]/
│   └── [random_uuid_3].mp4
```

### Storage Path Format
- Subdirectory: First 8 characters of message UUID (for organization)
- Filename: Random UUID + original extension (prevents collisions)
- Full path stored in database for retrieval

### Example
- Message ID: `1fdef5aa-cb28-41ac-9ab5-d653aa08966b`
- Original filename: `photo.jpg`
- Storage path: `1fdef5aa/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`

## Data Flow

### Upload Flow
```
User selects file
    ↓
AttachmentUploadButton callback
    ↓
Add to pendingAttachments state
    ↓
User sends message
    ↓
Send text message first (POST /api/chat)
    ↓
For each pending attachment:
    - POST /api/attachments/upload (FormData)
    - Validate on server (type, size, extension, MIME)
    - Save file to disk
    - Create DB record
    - Return metadata
    ↓
Update message state with attachment metadata
    ↓
Clear pending list
    ↓
Display attachments in chat bubble
```

### Display Flow
```
Message received from API
    ↓
Message includes attachments array
    ↓
Render message bubble
    ↓
For each attachment:
    - Render AttachmentPreview component
    - Show appropriate preview (image, video, file info)
    ↓
User can download/view attachment
```

## Validation

### Frontend Validation
- File type selection enforces accept attribute
- File size displayed before upload
- Failed uploads show error message (non-blocking)

### Backend Validation
1. **Type Validation**:
   - File extension must match allowlist
   - MIME type must match allowlist
   - Both must align with requested file_type

2. **Size Validation**:
   - File size ≤ MAX_UPLOAD_MB (default: 20)
   - Returns 413 Payload Too Large if exceeded

3. **Security**:
   - Generated random filename (prevents directory traversal)
   - Files stored outside web root
   - Download endpoint requires authentication
   - Message ownership not yet enforced (enhancement opportunity)

## Configuration

### Environment Variables
```env
# File uploads
MAX_UPLOAD_MB=20          # Maximum upload size in megabytes
UPLOAD_DIR=./uploads      # Storage directory path
```

### Programmatic Configuration
```python
# In core/config.py
max_upload_mb: int = 20
upload_dir: Optional[str] = None
```

## Error Handling

### Frontend
- Upload failures shown as warnings (don't block message send)
- Download failures show error toast
- Invalid file types rejected by input accept attribute

### Backend
- 400 Bad Request: Invalid file_type, validation failure
- 413 Payload Too Large: File exceeds size limit
- 404 Not Found: Attachment/file doesn't exist
- 500 Internal Server Error: Disk/database errors

## Future Enhancements

1. **Message Ownership Verification**
   - Verify current user owns message before allowing download/delete

2. **AI Analysis**
   - Extract text from documents (OCR)
   - Analyze code snippets (syntax highlighting, complexity)
   - Parse LaTeX formulas
   - Generate video summaries

3. **Cloud Storage**
   - Integrate S3/Azure Blob for scalable storage
   - Use pre-signed URLs for downloads
   - Enable CDN distribution

4. **Advanced Features**
   - Drag-and-drop upload
   - Multiple file selection
   - Upload progress bar
   - Attachment search/filtering
   - Attachment retention policies

5. **Media Processing**
   - Thumbnail generation for images/videos
   - Video compression
   - Document preview rendering
   - Formula LaTeX rendering

## Testing

### Manual Testing Steps

1. **Upload Image**:
   - Click attachment button → Image option
   - Select .jpg/.png file
   - Verify preview shows filename
   - Send message
   - Verify image renders in bubble

2. **Upload Video**:
   - Click attachment button → Video option
   - Select .mp4 file
   - Verify preview shows filename
   - Send message
   - Verify video player in bubble

3. **Upload Code**:
   - Click attachment button → Code option
   - Select .py/.js file
   - Verify preview shows file info
   - Send message
   - Verify download button present

4. **File Size Limit**:
   - Attempt to upload file > 20MB
   - Verify error message
   - Confirm message not sent

5. **Invalid Type**:
   - Attempt to upload .exe as image
   - Verify rejection/error
   - Confirm message not sent

## Performance Considerations

- **File Size Limit**: 20MB default prevents memory issues during upload
- **Storage Path Grouping**: UUID prefix subdirectories prevent single directory with too many files
- **Cascade Delete**: Attachments automatically deleted when message deleted
- **Lazy Loading**: Attachments only fetched with message history
- **No Duplicate Storage**: Each attachment gets unique filename

## Security Considerations

- File validation prevents script injection
- Random filename generation prevents directory traversal
- MIME type checking adds defense in depth
- Extension allowlist prevents executable uploads
- Upload directory outside web root
- Future: Add virus scanning, message ownership verification

## Database Schema

```sql
CREATE TABLE attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,  -- image|video|code|formula|document
  mime_type VARCHAR(100) NOT NULL,
  file_size INTEGER NOT NULL,
  storage_path VARCHAR(500) NOT NULL,
  upload_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  INDEX idx_message_id (message_id)
);
```

## API Documentation

### Upload Attachment
```
POST /api/attachments/upload

Form Data:
- message_id: string (UUID of message)
- file_type: string (image|video|code|formula|document)
- file: File (binary file data)

Response (200):
{
  "id": "uuid",
  "file_name": "photo.jpg",
  "file_type": "image",
  "mime_type": "image/jpeg",
  "file_size": 1024000,
  "upload_timestamp": "2026-05-09T10:30:00Z"
}

Errors:
- 400: Invalid file_type or validation failed
- 413: File exceeds size limit
- 500: Server error
```

### Download Attachment
```
GET /api/attachments/download/{attachment_id}

Response (200): Binary file stream
- Header: Content-Type: {mime_type}
- Header: Content-Disposition: attachment; filename="..."

Errors:
- 404: Attachment not found
```

### Delete Attachment
```
DELETE /api/attachments/{attachment_id}

Response (200):
{ "message": "Attachment deleted successfully" }

Errors:
- 404: Attachment not found
```

### List Message Attachments
```
GET /api/attachments/message/{message_id}

Response (200):
[
  {
    "id": "uuid",
    "file_name": "code.py",
    "file_type": "code",
    "mime_type": "text/plain",
    "file_size": 2048,
    "upload_timestamp": "2026-05-09T10:30:00Z"
  }
]
```

## Implementation Checklist

- [x] Database model created
- [x] Alembic migration created
- [x] Repository layer implemented
- [x] Service layer with validation implemented
- [x] API endpoints implemented
- [x] Frontend components created
- [x] File upload integration
- [x] File preview components
- [x] Chat integration
- [x] Styling added
- [x] Type definitions updated
- [x] Environment variables configured
- [ ] Database migration executed
- [ ] End-to-end testing completed
- [ ] Production deployment
