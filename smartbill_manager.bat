@echo off
title SmartBill Django Server
color 0A

:menu
cls
echo ========================================
echo      SMARTBILL - DJANGO MANAGER
echo ========================================
echo.
echo  1. Start Server (Quick Start)
echo  2. Make Migrations + Migrate + Start
echo  3. Create Superuser
echo  4. Open Admin Panel in Browser
echo  5. Stop Server (if running)
echo  6. Exit
echo.
echo ========================================
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto full_start
if "%choice%"=="3" goto create_superuser
if "%choice%"=="4" goto open_admin
if "%choice%"=="5" goto stop_server
if "%choice%"=="6" goto exit

echo Invalid choice! Try again...
timeout /t 2
goto menu

:start_server
cls
echo ========================================
echo   Starting Django Server...
echo ========================================
cd /d "C:\Users\LENOVO\Desktop\Smart Bill"
echo.
echo Server starting at: http://127.0.0.1:8000
echo Admin panel at: http://127.0.0.1:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver
pause
goto menu

:full_start
cls
echo ========================================
echo   Full Startup (Migrations + Server)
echo ========================================
cd /d "C:\Users\LENOVO\Desktop\Smart Bill"
echo.
echo [1/3] Making migrations...
python manage.py makemigrations
echo.
echo [2/3] Applying migrations...
python manage.py migrate
echo.
echo [3/3] Starting server...
echo.
echo Server starting at: http://127.0.0.1:8000
echo Admin panel at: http://127.0.0.1:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver
pause
goto menu

:create_superuser
cls
echo ========================================
echo   Create Superuser Account
echo ========================================
cd /d "C:\Users\LENOVO\Desktop\Smart Bill"
echo.
python manage.py createsuperuser
echo.
pause
goto menu

:open_admin
cls
echo ========================================
echo   Opening Admin Panel...
echo ========================================
start http://127.0.0.1:8000/admin
echo.
echo Admin panel opened in browser!
echo Login with your superuser credentials.
echo.
pause
goto menu

:stop_server
cls
echo ========================================
echo   Stopping Server...
echo ========================================
echo Press Ctrl+C in the server window to stop it
echo Or close the command prompt window
echo.
pause
goto menu

:exit
cls
echo ========================================
echo   Thank you for using SmartBill!
echo ========================================
echo.
timeout /t 2
exit
