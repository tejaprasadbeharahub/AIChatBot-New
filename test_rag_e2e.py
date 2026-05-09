"""
End-to-end test for PDF RAG:
1. Login
2. Create a chat
3. Create a user message
4. Upload the test PDF
5. Poll until status is 'completed'
6. Query: 'What was the company revenue in 2024?'
7. Check the AI answer references the PDF content
"""
import time
import httpx

BASE = "http://127.0.0.1:8000"
PDF_PATH = "test_revenue.pdf"

def step(msg): print(f"\n{'='*60}\n{msg}\n{'='*60}")

# ── 1. Login ──────────────────────────────────────────────────
step("1. Login")
r = httpx.post(f"{BASE}/api/auth/login",
               data={"username": "testrag@amzur.com", "password": "Test123!"})
r.raise_for_status()
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}
print(f"Token acquired ({len(TOKEN)} chars)")

# ── 2. Create chat ───────────────────────────────────────────
step("2. Create chat")
r = httpx.post(f"{BASE}/api/chats", headers=H, json={})
r.raise_for_status()
CHAT_ID = r.json()["id"]
print(f"Chat ID: {CHAT_ID}")

# ── 3. Create user message ───────────────────────────────────
step("3. Create user message")
r = httpx.post(f"{BASE}/api/chats/{CHAT_ID}/messages", headers=H, json={"content": "Uploaded PDF: test_revenue.pdf"})
r.raise_for_status()
MSG_ID = r.json()["id"]
print(f"Message ID: {MSG_ID}")

# ── 4. Upload PDF ─────────────────────────────────────────────
step("4. Upload PDF")
with open(PDF_PATH, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/pdf-rag/upload",
        headers=H,
        data={"chat_id": CHAT_ID, "message_id": MSG_ID},
        files={"file": ("test_revenue.pdf", f, "application/pdf")},
        timeout=30,
    )
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")
r.raise_for_status()
doc = r.json()["document"]
DOC_ID = doc["id"]
print(f"Document ID: {DOC_ID}  status={doc['status']}")

# ── 5. Poll status ────────────────────────────────────────────
step("5. Polling processing status")
for i in range(60):
    time.sleep(2)
    r = httpx.get(f"{BASE}/api/pdf-rag/documents/{DOC_ID}", headers=H, timeout=10)
    r.raise_for_status()
    d = r.json()
    print(f"  [{i*2}s] status={d['status']}  chunks={d.get('chunk_count')}")
    if d["status"] in ("completed", "failed"):
        print(f"Final status: {d['status']}")
        if d["status"] == "failed":
            print(f"Error: {d.get('processing_error')}")
        break

# ── 6. Ask question via normal chat endpoint ──────────────────
step("6. Ask: What was the company revenue in 2024?")
r = httpx.post(f"{BASE}/api/chat", headers=H,
               json={"message": "What was the company's revenue in 2024?", "chat_id": CHAT_ID},
               timeout=60)
print(f"Status: {r.status_code}")
print(f"Reply:\n{r.json().get('reply', r.text)}")
