@echo off
echo Starting Event Ticketing System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "app.py" (
    echo ERROR: app.py not found
    echo Please ensure you're in the correct directory
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create data directory if it doesn't exist
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads

echo.
echo Starting Flask application...
echo Open your browser and go to: http://localhost:5005
echo.
echo Default Admin Login:
echo Email: admin@example.com
echo Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
python app.py

pause