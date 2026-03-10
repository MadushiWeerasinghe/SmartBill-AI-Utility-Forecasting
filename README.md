SmartBill - AI Utility Expense Forecasting System
AI-powered utility bill management system for hotels and businesses in Sri Lanka

🎯 What is SmartBill?
SmartBill uses Machine Learning to help businesses manage electricity, water, and mobile bills more effectively. The system predicts future expenses, detects unusual bills, and sends automatic payment reminders.

✨ Key Features

📊 AI Bill Prediction - Forecast next month's utility costs
🚨 Anomaly Detection - Catch unusual bills automatically
📧 Email Reminders - Get notified 7 days, 3 days, and on due date
💰 Budget Recommendations - Auto-generate monthly budgets
✅ Smart Risk Management - Paid bills auto-clear from high-risk
📱 Multi-Account Support - Manage multiple branches easily


🚀 Technology

Backend: Django (Python)
Database: MySQL/SQLite
AI Models: Random Forest, XGBoost
Frontend: Bootstrap 5, Chart.js
Testing: 36 automated tests (94% coverage)


📊 Prediction Accuracy
Utility TypeAI ModelAccuracy (R²)ElectricityRandom Forest99.91%WaterXGBoost99.99%MobileRandom Forest91.44%

📦 Quick Start
bash# Clone repository
git clone https://github.com/MadushiWeerasinghe/SmartBill-AI-Utility-Forecasting.git
cd SmartBill-AI-Utility-Forecasting

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Run server
python manage.py runserver
Visit: http://127.0.0.1:8000

🧪 Testing
bash# Run all tests
python manage.py test

# Results: 36 tests passed ✅

🎓 Academic Project
Developer: W.P. Madushika Weerasinghe
Student ID: st20287187
University: Cardiff Metropolitan University
Program: BSc Software Engineering
Year: 2026

📸 Screenshots
Dashboard
Track all your utility bills in one place
AI Predictions
See forecasted expenses for next month
Email Notifications
Never miss a payment deadline
Budget Planner
Get automated budget recommendations

💡 Use Cases
Perfect for:

🏨 Hotels with multiple branches
🏢 Businesses with multiple locations
🏭 Industries tracking large utility costs
🏘️ Property management companies


🔧 Main Features Explained
1. Auto-Clear Risk on Payment
When you mark a bill as paid, it automatically becomes "Low Risk" - no more manual updates!
2. Overdue Detection
System automatically flags overdue bills as "High Risk" and sends alerts.
3. Per-Bill Email Notifications
Add email when creating a bill - each bill can notify different managers.
4. AI-Powered Predictions
Machine learning analyzes your bill history to predict future costs accurately.


👨‍💻 Contact
Madushika Weerasinghe
Cardiff Metropolitan University
Sri Lanka 🇱🇰
