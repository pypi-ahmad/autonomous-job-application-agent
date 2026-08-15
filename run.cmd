@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Is Python installed and on PATH?
        pause
        exit /b 1
    )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency install failed. See errors above.
    pause
    exit /b 1
)

rem python-jobspy pins an old numpy that has no working Windows wheel for
rem modern Python; install it without pulling that pin back in (see requirements.txt).
".venv\Scripts\python.exe" -m pip install --no-deps python-jobspy
if errorlevel 1 (
    echo python-jobspy install failed. See errors above.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example - add your API keys there before using cloud models.
)

echo Starting Streamlit app...
".venv\Scripts\python.exe" -m streamlit run app.py

pause
