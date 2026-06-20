@echo off
echo Starting Industry Data Reasoning Agent API...
set PYTHONPATH=src
uvicorn api:app --reload
pause
