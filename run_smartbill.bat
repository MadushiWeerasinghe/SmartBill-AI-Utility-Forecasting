@echo off
echo ========================================
echo   SmartBill Django Server Startup
echo ========================================
echo.

REM Change to project directory
cd /d "C:\Users\LENOVO\Desktop\Smart Bill"

echo [1/4] Making migrations...
python manage.py makemigrations

echo.
echo [2/4] Applying migrations...
python manage.py migrate

echo.
echo [3/4] Collecting static files (skip if not needed)...
REM python manage.py collectstatic --noinput

echo.
echo [4/4] Starting Django server...
echo.
echo ========================================
echo   Server starting...
echo   Open: http://127.0.0.1:8000
echo   Admin: http://127.0.0.1:8000/admin
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver

pause
