@echo off
echo ========================================
echo   SmartBill - First Time Setup
echo ========================================
echo.

REM Change to project directory
cd /d "C:\Users\LENOVO\Desktop\Smart Bill"

echo [1/5] Installing required packages...
pip install django scikit-learn pandas numpy xgboost pillow

echo.
echo [2/5] Creating migrations...
python manage.py makemigrations

echo.
echo [3/5] Applying migrations to database...
python manage.py migrate

echo.
echo [4/5] Setup complete!
echo.
echo ========================================
echo   Setup Complete!
echo   Now you can run: run_smartbill.bat
echo ========================================
echo.

pause
