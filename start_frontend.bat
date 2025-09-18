@echo off
echo Web Crawler Search Engine - Frontend Startup
echo ================================================

cd frontend

echo Installing dependencies...
call npm install

if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check Node.js installation.
    pause
    exit /b 1
)

echo.
echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo ================================================

call npm start

pause
