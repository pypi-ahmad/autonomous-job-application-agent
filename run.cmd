@echo off
setlocal
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo uv not found. Install it from https://docs.astral.sh/uv/ and re-run.
    pause
    exit /b 1
)

echo Installing dependencies (uv sync)...
uv sync --frozen
if errorlevel 1 (
    echo Dependency install failed. See errors above.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example - add your API keys there before using cloud models.
)

echo Starting Streamlit app on port 8843...
uv run streamlit run app.py --server.port 8843

pause
