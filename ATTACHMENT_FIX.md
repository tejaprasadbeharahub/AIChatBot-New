# Attachment System - Setup & Fix Guide

## Issue Description
Images and attachments are not being sent with chat messages. Only the text message is being sent, and you see: "I'm sorry, but as a text-based AI, I can't see images."

## Root Causes & Fixes

### 1. Database Migration Not Applied (MAIN CAUSE)

The `attachments` table doesn't exist in your database yet.

**Solution: Run the migration**

```bash
cd d:\WorkSpace\AIChatBot-New\backend

# Run Alembic migration to create attachments table
alembic upgrade head
```

You should see output like:
```
INFO [alembic.migration] Context impl PostgresqlImpl with dialect postgresql
INFO [alembic.migration] Will assume transactional DDL is supported by backend
INFO [alembic.migration] Running upgrade c4e8a6f4a2b1 -> create_attachments_table, Add attachments table
```

### 2. Backend Code Updates Applied

The backend has been updated to:
- ✅ Return `user_message_id` in chat responses (needed for attachments)
- ✅ Properly capture and return message IDs
- ✅ Support attachment file uploads

### 3. Frontend Code Updates Applied  

The frontend has been updated to:
- ✅ Use correct message ID for attachment upload (not chat ID)
- ✅ Show attachment upload button in composer
- ✅ Display pending attachments before sending
- ✅ Upload attachments after message is sent
- ✅ Show better error messages for upload failures
- ✅ Display attachment previews in messages

## Complete Setup Steps

### Step 1: Stop Current Servers

Kill any running backend/frontend servers:

```powershell
# PowerShell
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 2: Apply Database Migration

```powershell
cd d:\WorkSpace\AIChatBot-New\backend
alembic upgrade head
```

Verify migration succeeded - you should see the upgrade message.

### Step 3: Create Uploads Directory

The system will auto-create this, but you can pre-create it:

```powershell
# In project root
New-Item -ItemType Directory -Force -Path ".\uploads"
```

### Step 4: Verify .env Configuration

Check `d:\WorkSpace\AIChatBot-New\.env` has these settings:

```env
MAX_UPLOAD_MB=20
UPLOAD_DIR=./uploads
```

### Step 5: Start Backend (Fresh)

```powershell
cd d:\WorkSpace\AIChatBot-New\backend

# Set environment variable
$env:DATABASE_URL='postgresql://postgres:JesusTeja%40123456789@localhost:5432/aichatbot_db'

# Start without reload to ensure clean state
python -m uvicorn app.main:app --host localhost --port 8000
```

Wait for message: `Uvicorn running on http://localhost:8000`

### Step 6: Start Frontend (Fresh)

In a NEW terminal:

```powershell
cd d:\WorkSpace\AIChatBot-New\frontend

npm run dev -- --host localhost --port 5173
```

Wait for message: `Local: http://localhost:5173/`

### Step 7: Test Attachment System

1. Open http://localhost:5173 in browser
2. Login with your account
3. Start a new chat or open existing one
4. **Type a message** (e.g., "Here is my photo")
5. **Click the attachment button (📎)** next to the input
6. Select **"📷 Image"**
7. Choose an image file (.jpg, .png, .gif, .webp)
8. **Verify**: 
   - ✅ Filename appears in "Pending Attachments" section
   - ✅ Attachment button shows selected file
9. **Click Send**
10. **Verify**:
    - ✅ Text message appears in bubble
    - ✅ Image preview appears below text
    - ✅ AI response is received
    - ✅ No error messages

## Troubleshooting

### Error: "Invalid message_id format"

**Cause**: Database migration wasn't applied; attachments table doesn't exist

**Fix**: Run `alembic upgrade head`

### Error: "File type not allowed"

**Cause**: Wrong file extension or MIME type

**Fix**: Use supported extensions:
- Images: .jpg, .jpeg, .png, .gif, .webp, .svg
- Videos: .mp4, .webm, .mov, .avi  
- Code: .py, .js, .ts, .java, .cpp, .txt, .json, .html, .css
- Documents: .pdf, .doc, .docx, .xls, .xlsx, .csv
- Formulas: .tex, .txt, .md

### Error: "File size exceeds limit of 20MB"

**Cause**: File is too large

**Fix**: Either:
- Use a smaller file (< 20MB)
- Update `.env`: `MAX_UPLOAD_MB=100` (then restart backend)

### Attachment Button Not Showing

**Cause**: Frontend not recompiled

**Fix**: 
- Stop frontend
- Clear browser cache (Ctrl+Shift+Delete)
- Restart frontend
- Hard refresh browser (Ctrl+F5)

### Attachment Uploads but Image Doesn't Display

**Cause**: Browser trying to load from wrong URL

**Fix**: 
- Check browser console (F12) for errors
- Check backend logs for upload success message
- Verify file exists in `./uploads` directory

### Attachment Menu Won't Open

**Cause**: CSS not loaded or JavaScript error

**Fix**:
- Hard refresh browser (Ctrl+F5)
- Open DevTools (F12) → Console tab
- Look for JavaScript errors
- Report any errors

## Verify Everything Works

### Backend Verification

Check logs show no errors:
- ✅ "Application startup complete"
- ✅ POST requests to `/api/attachments/upload` succeed
- ✅ No 500 errors in logs

### Frontend Verification

Check browser console (F12):
- ✅ No red errors
- ✅ Attachment upload logs appear on send
- ✅ Pending attachments show before send
- ✅ Uploaded attachments show after send

### Database Verification

Open PostgreSQL and check:
```sql
-- Should show recent migrations
SELECT version, description FROM alembic_version;

-- Should return number of attachments
SELECT COUNT(*) FROM attachments;

-- Should show the table structure
\d attachments
```

### File System Verification

Check `./uploads` directory:
```powershell
# Should contain subdirectories after uploads
Get-ChildItem -Path ".\uploads" -Recurse
```

## Configuration Reference

### Backend Configuration (.env)

```env
# Maximum upload size
MAX_UPLOAD_MB=20

# Storage directory  
UPLOAD_DIR=./uploads

# Optional: Database settings
DATABASE_URL=postgresql://postgres:JesusTeja%40123456789@localhost:5432/aichatbot_db

# Optional: LiteLLM settings
LITELLM_PROXY_URL=http://litellm.amzur.com:4000
```

### Code Changes Applied

**Backend:**
- `app/schemas/chat.py` - Added `user_message_id` to ChatResponse
- `app/services/chat_service.py` - Captures and returns message ID
- `app/models/attachment.py` - Attachment ORM model (NEW)
- `app/schemas/attachment.py` - Attachment validation schemas (NEW)
- `app/repositories/attachment_repo.py` - Data access layer (NEW)
- `app/services/attachment_service.py` - File handling logic (NEW)
- `app/api/attachment.py` - API endpoints (NEW)
- `app/main.py` - Registered attachment router
- `alembic/versions/create_attachments_table.py` - Database migration (NEW)

**Frontend:**
- `src/api/chat.ts` - Added `user_message_id` to response type
- `src/App.tsx` - Uses correct message ID for attachment upload
- `src/types/chat.ts` - Attachment type defined
- `src/components/chat/AttachmentUploadButton.tsx` - Upload UI (NEW)
- `src/components/chat/AttachmentPreview.tsx` - Preview component (NEW)
- `src/index.css` - Attachment styling (NEW)

## Testing Checklist

- [ ] Database migration applied (`alembic upgrade head`)
- [ ] Backend started without errors
- [ ] Frontend started without errors  
- [ ] Can login to chat
- [ ] Attachment button (📎) visible in chat
- [ ] Can select file type from dropdown
- [ ] Can choose file from dialog
- [ ] Pending attachment shows before send
- [ ] Message sends successfully
- [ ] Image appears in message bubble
- [ ] AI responds with message (not image error)
- [ ] Multiple attachments work
- [ ] Different file types work
- [ ] No errors in browser console
- [ ] No errors in backend terminal
- [ ] Files exist in `./uploads` directory

## Next Steps

If everything works:
1. ✅ Attachment system is ready
2. ✅ Test with different file types
3. ✅ Verify uploads persist in database
4. ✅ Check file sizes are reasonable
5. ✅ Consider implementing cloud storage for production

If issues persist:
1. Check all troubleshooting steps above
2. Review browser console errors (F12)
3. Review backend terminal logs
4. Verify database migration ran successfully
5. Check file permissions on `./uploads` directory
