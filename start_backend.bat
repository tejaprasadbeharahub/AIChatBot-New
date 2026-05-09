@echo off
cd /d "d:\WorkSpace\AIChatBot-New\backend"
"d:\WorkSpace\AIChatBot-New\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
