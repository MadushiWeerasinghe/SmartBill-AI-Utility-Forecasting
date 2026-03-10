import re
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q, Avg
from django.core.exceptions import PermissionDenied
from .models import Bill, Budget, UtilityAccount
from .ml_utils import (
    predict_electricity_bill, 
    predict_water_bill, 
    predict_mobile_bill,
    detect_anomaly,
    predict_payment_risk
)
from datetime import datetime, date, timedelta
import calendar
import json

# ==========================================
# AUTOMATIC AI ANALYSIS HELPER FUNCTION
# ==========================================

def analyze_bill_automatically(bill):
    """
    AUTOMATIC AI ANALYSIS - Works for ALL utility types
    PRIORITY 1: Overdue detection (highest priority)
    PRIORITY 2: Amount/Units thresholds
    PRIORITY 3: AI-based analysis for electricity
    """
    
    # ========== PRIORITY 1: CHECK IF OVERDUE (HIGHEST PRIORITY) ==========
    from datetime import date, datetime
    
    # Convert due_date to date object if it's a string
    due_date = bill.due_date
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except:
            due_date = None
    
    if not bill.is_paid and due_date and due_date < date.today():
        # Bill is OVERDUE! Mark as High Risk immediately
        bill.late_payment_risk = 'High Risk'
        bill.is_anomaly = True
        bill.save()
        return True, 'High Risk'
    
    # If bill is paid, always Low Risk
    if bill.is_paid:
        bill.late_payment_risk = 'Low Risk'
        bill.is_anomaly = False
        bill.save()
        return False, 'Low Risk'
    
    # ========== PRIORITY 2 & 3: ELECTRICITY BILLS (AI-BASED) ==========
    if bill.utility_type == 'electricity' and bill.units_consumed > 0:
        try:
            # Run ML anomaly detection
            is_anomaly = detect_anomaly(
                float(bill.bill_amount), 
                float(bill.units_consumed), 
                int(bill.billing_month)
            )
            
            # Run ML payment risk prediction
            payment_risk = predict_payment_risk(
                float(bill.bill_amount), 
                float(bill.units_consumed), 
                int(bill.billing_month)
            )
            
            # Update bill with AI results
            bill.is_anomaly = is_anomaly
            bill.late_payment_risk = payment_risk
            bill.save()
            
            return is_anomaly, payment_risk
            
        except Exception as e:
            print(f"❌ Electricity AI Error: {e}")
            return False, 'Low Risk'
    
    # ========== WATER BILLS (THRESHOLD-BASED) ==========
    elif bill.utility_type == 'water':
        try:
            is_anomaly = False
            payment_risk = 'Low Risk'
            
            # High Risk thresholds for water
            if bill.bill_amount > 15000 or bill.units_consumed > 100:
                payment_risk = 'High Risk'
                is_anomaly = True
            # Medium Risk thresholds for water
            elif bill.bill_amount > 8000 or bill.units_consumed > 50:
                payment_risk = 'Medium Risk'
                is_anomaly = False
            
            # Update bill
            bill.is_anomaly = is_anomaly
            bill.late_payment_risk = payment_risk
            bill.save()
            
            return is_anomaly, payment_risk
            
        except Exception as e:
            print(f"❌ Water Analysis Error: {e}")
            return False, 'Low Risk'
    
    # ========== MOBILE BILLS (THRESHOLD-BASED) ==========
    elif bill.utility_type == 'mobile':
        try:
            is_anomaly = False
            payment_risk = 'Low Risk'
            
            # High Risk thresholds for mobile
            if bill.bill_amount > 5000:
                payment_risk = 'High Risk'
                is_anomaly = True
            # Medium Risk thresholds for mobile
            elif bill.bill_amount > 3000:
                payment_risk = 'Medium Risk'
                is_anomaly = False
            
            # Update bill
            bill.is_anomaly = is_anomaly
            bill.late_payment_risk = payment_risk
            bill.save()
            
            return is_anomaly, payment_risk
            
        except Exception as e:
            print(f"❌ Mobile Analysis Error: {e}")
            return False, 'Low Risk'
    
    # Default for unknown types
    return False, 'Low Risk'

# ==========================================
# VIEW FUNCTIONS
# ==========================================

def login_view(request):
    """User login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'bills/login.html')

def logout_view(request):
    """User logout"""
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    """Main dashboard showing statistics and charts with account filters - ALL BILLS VISIBLE"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # CHANGED: Show all bills to all users
    user_bills = Bill.objects.all()
    
    this_month_bills = user_bills.filter(
        billing_month=current_month,
        billing_year=current_year
    )
    
    # Calculate statistics
    total_bills = user_bills.count()
    unpaid_bills = user_bills.filter(is_paid=False).count()
    high_risk_bills = user_bills.filter(late_payment_risk='High Risk').count()
    anomalies = user_bills.filter(is_anomaly=True).count()
    
    monthly_total = this_month_bills.aggregate(
        total=Sum('bill_amount')
    )['total'] or 0
    
    # CHANGED: Show all accounts to all users
    electricity_accounts = UtilityAccount.objects.filter(
        utility_type='electricity',
        is_active=True
    )
    water_accounts = UtilityAccount.objects.filter(
        utility_type='water',
        is_active=True
    )
    mobile_accounts = UtilityAccount.objects.filter(
        utility_type='mobile',
        is_active=True
    )
    
    # Bills by utility type (all accounts combined)
    electricity_bills = user_bills.filter(utility_type='electricity')
    water_bills = user_bills.filter(utility_type='water')
    mobile_bills = user_bills.filter(utility_type='mobile')
    
    # Function to get last 6 months data for ALL accounts combined
    def get_last_6_months_data_all(utility_type):
        months = []
        amounts = []
        now = datetime.now()
        
        for i in range(5, -1, -1):
            target_month = now.month - i
            target_year = now.year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            month_bills = user_bills.filter(
                utility_type=utility_type,
                billing_month=target_month,
                billing_year=target_year
            )
            
            total = month_bills.aggregate(total=Sum('bill_amount'))['total'] or 0
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_label = f"{month_names[target_month-1]} {target_year}"
            
            months.append(month_label)
            amounts.append(float(total))
        
        return months, amounts
    
    # Function to get data for a SPECIFIC account
    def get_account_data(account):
        amounts = []
        now = datetime.now()
        
        for i in range(5, -1, -1):
            target_month = now.month - i
            target_year = now.year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            month_bills = account.bills.filter(
                billing_month=target_month,
                billing_year=target_year
            )
            
            total = month_bills.aggregate(total=Sum('bill_amount'))['total'] or 0
            amounts.append(float(total))
        
        return amounts
    
    # Get chart data for ALL accounts
    electricity_months, electricity_amounts = get_last_6_months_data_all('electricity')
    water_months, water_amounts = get_last_6_months_data_all('water')
    mobile_months, mobile_amounts = get_last_6_months_data_all('mobile')
    
    # Prepare per-account data for JavaScript
    all_accounts_data = {
        'electricity': {},
        'water': {},
        'mobile': {}
    }
    
    # Electricity accounts data
    for account in electricity_accounts:
        all_accounts_data['electricity'][str(account.id)] = {
            'amounts': get_account_data(account),
            'count': account.bills.count()
        }
    
    # Water accounts data
    for account in water_accounts:
        all_accounts_data['water'][str(account.id)] = {
            'amounts': get_account_data(account),
            'count': account.bills.count()
        }
    
    # Mobile accounts data
    for account in mobile_accounts:
        all_accounts_data['mobile'][str(account.id)] = {
            'amounts': get_account_data(account),
            'count': account.bills.count()
        }
    
    context = {
        'total_bills': total_bills,
        'unpaid_bills': unpaid_bills,
        'high_risk_bills': high_risk_bills,
        'anomalies': anomalies,
        'monthly_total': monthly_total,
        'electricity_count': electricity_bills.count(),
        'water_count': water_bills.count(),
        'mobile_count': mobile_bills.count(),
        
        # Accounts for dropdowns
        'electricity_accounts': electricity_accounts,
        'water_accounts': water_accounts,
        'mobile_accounts': mobile_accounts,
        
        # Chart data (ALL accounts combined - default view)
        'electricity_months': json.dumps(electricity_months),
        'electricity_amounts': json.dumps(electricity_amounts),
        'water_months': json.dumps(water_months),
        'water_amounts': json.dumps(water_amounts),
        'mobile_months': json.dumps(mobile_months),
        'mobile_amounts': json.dumps(mobile_amounts),
        
        # Per-account data for filtering
        'all_accounts_data': json.dumps(all_accounts_data),
    }
    
    return render(request, 'bills/dashboard.html', context)

@login_required
def add_bill(request):
    """Add a new bill with account selection - ALL ACCOUNTS VISIBLE"""
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        billing_month = int(request.POST.get('billing_month'))
        billing_year = int(request.POST.get('billing_year'))
        units_consumed = float(request.POST.get('units_consumed', 0))
        bill_amount = float(request.POST.get('bill_amount'))
        due_date = request.POST.get('due_date')
        is_paid = request.POST.get('is_paid') == 'on'
        
        # ✅ NEW: Get optional email address for notifications
        notification_email = request.POST.get('notification_email', '').strip()
        
        # CHANGED: Get account without user filter
        account = get_object_or_404(UtilityAccount, id=account_id)
        
        # Create bill linked to account
        bill = Bill.objects.create(
            user=request.user,
            account=account,
            utility_type=account.utility_type,
            account_number=account.account_number,
            billing_month=billing_month,
            billing_year=billing_year,
            units_consumed=units_consumed,
            bill_amount=bill_amount,
            due_date=due_date,
            is_paid=is_paid,
            notification_email=notification_email if notification_email else None  # ✅ Save email
        )

        # AUTOMATIC AI ANALYSIS - Just one line!
        is_anomaly, payment_risk = analyze_bill_automatically(bill)

        # Show warnings to user
        if is_anomaly:
            messages.warning(request, '⚠️ Anomaly detected! This bill is unusually high.')

        if payment_risk == 'High Risk':
            messages.warning(request, '🚨 High risk of late payment detected!')
        
        # ✅ Show email notification status
        if notification_email:
            messages.success(request, f'✅ Bill added to {account.account_name}! Email reminders will be sent to: {notification_email}')
        else:
            messages.success(request, f'✅ Bill added successfully to {account.account_name}!')
        
        return redirect('bill_list')
    
    # GET request - show form
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # CHANGED: Get all accounts (no user filter)
    electricity_accounts = UtilityAccount.objects.filter(
        utility_type='electricity',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    water_accounts = UtilityAccount.objects.filter(
        utility_type='water',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    mobile_accounts = UtilityAccount.objects.filter(
        utility_type='mobile',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    # Prepare JSON for JavaScript
    electricity_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in electricity_accounts
    ]
    water_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in water_accounts
    ]
    mobile_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in mobile_accounts
    ]
    
    context = {
        'current_month': current_month,
        'current_year': current_year,
        'months': range(1, 13),
        'years': range(2020, 2030),
        'electricity_accounts_json': json.dumps(electricity_json),
        'water_accounts_json': json.dumps(water_json),
        'mobile_accounts_json': json.dumps(mobile_json),
    }
    
    return render(request, 'bills/add_bill.html', context)

@login_required
def bill_list(request):
    """List all bills with filtering - WITH OVERDUE DETECTION"""
    from datetime import date
    
    bills = Bill.objects.filter(user=request.user).order_by('-billing_year', '-billing_month', '-created_at')
    
    # Check and update overdue bills automatically
    for bill in bills:
        if not bill.is_paid and bill.due_date and bill.due_date < date.today():
            if bill.late_payment_risk != 'High Risk':
                bill.late_payment_risk = 'High Risk'
                bill.is_anomaly = True
                bill.save()
    
    filter_type = None
    filter_value = None
    
    utility_filter = request.GET.get('utility')
    if utility_filter:
        bills = bills.filter(utility_type=utility_filter)
        filter_type = 'Utility Type'
        filter_value = utility_filter.title()
    
    status_filter = request.GET.get('status')
    if status_filter == 'unpaid':
        bills = bills.filter(is_paid=False)
        filter_type = 'Payment Status'
        filter_value = 'Unpaid Bills'
    elif status_filter == 'paid':
        bills = bills.filter(is_paid=True)
        filter_type = 'Payment Status'
        filter_value = 'Paid Bills'
    elif status_filter == 'overdue':
        # NEW: Filter for overdue bills only
        bills = bills.filter(is_paid=False, due_date__lt=date.today())
        filter_type = 'Payment Status'
        filter_value = 'Overdue Bills'
    
    risk_filter = request.GET.get('risk')
    if risk_filter == 'high':
        bills = bills.filter(late_payment_risk='High Risk')
        filter_type = 'Risk Level'
        filter_value = 'High Risk Bills'
    
    month_filter = request.GET.get('month')
    if month_filter == 'current':
        current_month = datetime.now().month
        current_year = datetime.now().year
        bills = bills.filter(billing_month=current_month, billing_year=current_year)
        filter_type = 'Time Period'
        filter_value = 'This Month'
    
    # Calculate days overdue for each bill
    today = date.today()
    bills_with_overdue = []
    for bill in bills:
        bill.days_overdue = 0
        if not bill.is_paid and bill.due_date and bill.due_date < today:
            bill.days_overdue = (today - bill.due_date).days
        bills_with_overdue.append(bill)
    
    total_amount = bills.aggregate(total=Sum('bill_amount'))['total'] or 0
    total_count = bills.count()
    overdue_count = bills.filter(is_paid=False, due_date__lt=today).count()
    
    context = {
        'bills': bills_with_overdue,
        'utility_filter': utility_filter,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'month_filter': month_filter,
        'filter_type': filter_type,
        'filter_value': filter_value,
        'total_amount': total_amount,
        'total_count': total_count,
        'overdue_count': overdue_count,
    }
    
    return render(request, 'bills/bill_list.html', context)


@login_required
def predict_bill(request):
    """Predict future bills based on account history - ALL ACCOUNTS VISIBLE"""
    prediction = None
    prediction_json = None
    
    if request.method == 'POST':
        utility_type = request.POST.get('utility_type')
        account_id = request.POST.get('account_id')
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        
        # CHANGED: Get account without user filter
        account = get_object_or_404(UtilityAccount, id=account_id)
        
        # Get historical data from account (last 6 months)
        bills = account.bills.order_by('-billing_year', '-billing_month')[:6]
        
        if bills.exists():
            # Calculate average units from history
            avg_units = bills.aggregate(avg=Avg('units_consumed'))['avg'] or 0
            
            # Convert to float (FIX FOR FLOAT32 ISSUE)
            avg_units = float(avg_units) if avg_units else 0.0
            
            # Use average as predicted units
            predicted_units = avg_units
            
            # Predict bill amount based on utility type
            if utility_type == 'electricity':
                predicted_amount = predict_electricity_bill(predicted_units, month, year)
                accuracy = '99.91%'
            elif utility_type == 'water':
                predicted_amount = predict_water_bill(predicted_units, month, year)
                accuracy = '100%'
            else:  # mobile
                predicted_amount = predict_mobile_bill(account.provider or 'Dialog', month, year)
                predicted_units = 0.0  # Not applicable for mobile
                accuracy = '92.99%'
            
            if predicted_amount:
                # Convert all to regular Python float (FIX FLOAT32 ISSUE)
                predicted_amount = float(predicted_amount)
                recommended_budget = float(predicted_amount * 1.1)
                safety_buffer = float(recommended_budget - predicted_amount)
                
                prediction = {
                    'utility': str(utility_type.title()),
                    'account_id': int(account.id),
                    'account_name': str(account.account_name),
                    'account_number': str(account.account_number),
                    'month': int(month),
                    'year': int(year),
                    'avg_units': float(avg_units),
                    'predicted_units': float(predicted_units),
                    'predicted_bill': float(predicted_amount),
                    'recommended_budget': float(round(recommended_budget, 2)),
                    'safety_buffer': float(round(safety_buffer, 2)),
                    'accuracy': str(accuracy),
                }
                
                # Store as JSON for PDF generation
                prediction_json = json.dumps(prediction)
        else:
            messages.warning(request, '⚠️ No historical data found for this account. Please add some bills first!')
    
    # CHANGED: Get all accounts (no user filter)
    electricity_accounts = UtilityAccount.objects.filter(
        utility_type='electricity',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    water_accounts = UtilityAccount.objects.filter(
        utility_type='water',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    mobile_accounts = UtilityAccount.objects.filter(
        utility_type='mobile',
        is_active=True
    ).values('id', 'account_name', 'account_number')
    
    # Prepare JSON for JavaScript
    electricity_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in electricity_accounts
    ]
    water_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in water_accounts
    ]
    mobile_json = [
        {'id': acc['id'], 'name': acc['account_name'], 'number': acc['account_number']}
        for acc in mobile_accounts
    ]
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    context = {
        'prediction': prediction,
        'prediction_json': prediction_json,
        'current_month': current_month,
        'current_year': current_year,
        'months': range(1, 13),
        'years': range(2024, 2031),
        'electricity_accounts_json': json.dumps(electricity_json),
        'water_accounts_json': json.dumps(water_json),
        'mobile_accounts_json': json.dumps(mobile_json),
    }
    
    return render(request, 'bills/predict.html', context)

@login_required
def download_prediction_pdf(request):
    """Generate and download prediction PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from io import BytesIO
    
    if request.method == 'POST':
        prediction_data = json.loads(request.POST.get('prediction_data', '{}'))
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4169E1'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("SmartBill - Bill Prediction Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Account Info
        account_data = [
            ['Account Information', ''],
            ['Utility Type:', prediction_data.get('utility', 'N/A')],
            ['Account Name:', prediction_data.get('account_name', 'N/A')],
            ['Account Number:', prediction_data.get('account_number', 'N/A')],
            ['Prediction For:', f"{prediction_data.get('month')}/{prediction_data.get('year')}"],
        ]
        
        account_table = Table(account_data, colWidths=[2.5*inch, 3.5*inch])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4169E1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(account_table)
        elements.append(Spacer(1, 20))
        
        # Prediction Results
        prediction_results = [
            ['Prediction Results', ''],
            ['Average Units (Last 6 months):', f"{prediction_data.get('avg_units', 0):.2f}"],
            ['Predicted Units:', f"{prediction_data.get('predicted_units', 0):.2f}"],
            ['Predicted Bill Amount:', f"LKR {prediction_data.get('predicted_bill', 0):.2f}"],
            ['Recommended Budget (+ 10%):', f"LKR {prediction_data.get('recommended_budget', 0):.2f}"],
            ['Safety Buffer:', f"LKR {prediction_data.get('safety_buffer', 0):.2f}"],
            ['AI Accuracy:', prediction_data.get('accuracy', 'N/A')],
        ]
        
        prediction_table = Table(prediction_results, colWidths=[2.5*inch, 3.5*inch])
        prediction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (-1, 3), 12),
        ]))
        elements.append(prediction_table)
        elements.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF value
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Bill_Prediction_{prediction_data.get("account_name")}_{prediction_data.get("month")}_{prediction_data.get("year")}.pdf"'
        response.write(pdf)
        
        return response
    
    return redirect('predict_bill')

@login_required
def generate_budget(request):
    """Generate budget forecast with perfect layout - 3/6 months or custom"""
    forecast = None
    
    # Get all accounts for the dropdown (as JSON)
    all_accounts = UtilityAccount.objects.filter(is_active=True).values(
        'id', 'utility_type', 'account_name', 'account_number'
    )
    all_accounts_list = list(all_accounts)
    
    if request.method == 'POST':
        utility_type = request.POST.get('utility_type')
        account_id = request.POST.get('account_id')
        forecast_months = int(request.POST.get('forecast_months', 6))
        start_month = int(request.POST.get('start_month'))
        year = int(request.POST.get('year'))
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Determine which accounts to forecast
        accounts_to_forecast = []
        
        if account_id == 'ALL':
            # All utilities, all accounts
            accounts_to_forecast = UtilityAccount.objects.filter(is_active=True)
            utility_name = "All Utilities"
            account_name = "All Accounts"
        elif account_id.startswith('ALL_'):
            # All accounts of specific utility
            util_type = account_id.split('_')[1].lower()
            accounts_to_forecast = UtilityAccount.objects.filter(
                is_active=True, 
                utility_type=util_type
            )
            utility_name = util_type.title()
            account_name = f"All {util_type.title()} Accounts"
        else:
            # Single account
            account = get_object_or_404(UtilityAccount, id=account_id)
            accounts_to_forecast = [account]
            utility_name = account.utility_type.title()
            account_name = f"{account.account_name} ({account.account_number})"
        
        # Generate forecast
        account_forecasts = []
        grand_total = 0
        
        for account in accounts_to_forecast:
            # Get historical data (last 6 months)
            bills = Bill.objects.filter(account=account).order_by('-billing_year', '-billing_month')[:6]
            
            if bills.exists():
                avg_units = bills.aggregate(avg=Avg('units_consumed'))['avg'] or 0
                avg_amount = bills.aggregate(avg=Avg('bill_amount'))['avg'] or 0
            else:
                avg_units = 50 if account.utility_type != 'mobile' else 0
                avg_amount = 5000
            
            # Generate forecast for specified months
            monthly_data = []
            total_units = 0
            total_amount = 0
            
            for i in range(forecast_months):
                month = start_month + i
                forecast_year = year
                
                if month > 12:
                    month = month - 12
                    forecast_year = year + 1
                
                predicted_units = float(avg_units)
                predicted_amount = float(avg_amount)
                buffer = predicted_amount * 0.1
                budget = predicted_amount + buffer
                
                monthly_data.append({
                    'name': month_names[month - 1],
                    'year': forecast_year,
                    'units': predicted_units,
                    'amount': predicted_amount,
                    'buffer': buffer,
                    'budget': budget,
                })
                
                total_units += predicted_units
                total_amount += predicted_amount
            
            total_buffer = total_amount * 0.1
            total_budget = total_amount + total_buffer
            grand_total += total_budget
            
            account_forecasts.append({
                'account_name': account.account_name,
                'account_number': account.account_number,
                'utility_type': account.utility_type,
                'months': monthly_data,
                'total_units': total_units,
                'total_amount': total_amount,
                'total_buffer': total_buffer,
                'total_budget': total_budget,
                'unit_label': 'kWh' if account.utility_type == 'electricity' else 'm³' if account.utility_type == 'water' else 'N/A',
            })
        
        # Calculate end month for display
        end_month = start_month + forecast_months - 1
        end_year = year
        while end_month > 12:
            end_month -= 12
            end_year += 1
        
        period_text = f"{month_names[start_month - 1]} {year} - {month_names[end_month - 1]} {end_year} ({forecast_months} months)"
        
        forecast = {
            'utility_name': utility_name,
            'account_name': account_name,
            'period_text': period_text,
            'accounts': account_forecasts,
            'total_budget': grand_total,
            'monthly_average': grand_total / forecast_months if forecast_months > 0 else 0,
        }
        
        messages.success(request, f'✅ {forecast_months}-month forecast generated!')
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    context = {
        'forecast': forecast,
        'all_accounts_json': json.dumps(all_accounts_list),
        'current_month': current_month,
        'current_year': current_year,
        'years': range(2024, 2030),
    }
    
    return render(request, 'bills/budget.html', context)


# ==========================================
# MULTI-ACCOUNT MANAGEMENT FUNCTIONS
# ==========================================

@login_required
def manage_accounts(request):
    """View all utility accounts - ALL ACCOUNTS VISIBLE"""
    # CHANGED: Show all accounts (no user filter)
    electricity_accounts = UtilityAccount.objects.filter(
        utility_type='electricity',
        is_active=True
    )
    water_accounts = UtilityAccount.objects.filter(
        utility_type='water',
        is_active=True
    )
    mobile_accounts = UtilityAccount.objects.filter(
        utility_type='mobile',
        is_active=True
    )
    
    context = {
        'electricity_accounts': electricity_accounts,
        'water_accounts': water_accounts,
        'mobile_accounts': mobile_accounts,
    }
    
    return render(request, 'bills/manage_accounts.html', context)

@login_required
def add_account(request):
    """Add new utility account with validation - ALL MEMBERS CAN ADD"""
    if request.method == 'POST':
        utility_type = request.POST.get('utility_type')
        account_number = request.POST.get('account_number', '').strip()
        account_name = request.POST.get('account_name', '').strip()
        provider = request.POST.get('provider', '')
        
        # VALIDATION RULES
        validation_passed = True
        error_message = None
        
        if utility_type == 'mobile':
            # Sri Lankan mobile: exactly 10 digits, starts with 07
            if not re.match(r'^07[0-9]{8}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid mobile number! Must be exactly 10 digits and start with 07 (e.g., 0771234567)'
        
        elif utility_type == 'electricity':
            # CEB account: 6-15 digits
            if not re.match(r'^[0-9]{6,15}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid CEB account number! Must be 6-15 digits (e.g., 123456789)'
        
        elif utility_type == 'water':
            # Water account: 4-20 characters (letters, numbers, dash)
            if not re.match(r'^[0-9A-Za-z\-]{4,20}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid water account number! Must be 4-20 characters (e.g., WTR-001)'
        
        # Check if validation failed
        if not validation_passed:
            messages.error(request, error_message)
            return redirect('add_account')
        
        # CHANGED: Check for duplicates globally (not per user)
        if UtilityAccount.objects.filter(
            utility_type=utility_type,
            account_number=account_number
        ).exists():
            messages.error(request, f'❌ Account {account_number} already exists!')
            return redirect('add_account')
        
        # Validation passed - create account
        UtilityAccount.objects.create(
            user=request.user,
            utility_type=utility_type,
            account_number=account_number,
            account_name=account_name,
            provider=provider
        )
        
        messages.success(request, f'✅ Account "{account_name}" ({account_number}) added successfully!')
        return redirect('manage_accounts')
    
    return render(request, 'bills/add_account.html')

@login_required
def account_detail(request, account_id):
    """View account details and all bills - ALL ACCOUNTS VISIBLE"""
    # CHANGED: Get account without user filter
    account = get_object_or_404(UtilityAccount, id=account_id)
    bills = account.bills.all()[:12]
    
    total_bills = account.bills.count()
    total_amount = account.get_total_amount()
    avg_amount = account.bills.aggregate(avg=Avg('bill_amount'))['avg'] or 0
    unpaid_bills = account.bills.filter(is_paid=False).count()
    
    context = {
        'account': account,
        'bills': bills,
        'total_bills': total_bills,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'unpaid_bills': unpaid_bills,
    }
    
    return render(request, 'bills/account_detail.html', context)

@login_required
def bulk_import_bills(request, account_id):
    """Import 12 months of bills at once - WITH AUTOMATIC AI"""
    account = get_object_or_404(UtilityAccount, id=account_id)
    
    if request.method == 'POST':
        bills_added = 0
        high_risk_detected = 0
        anomalies_detected = 0
        
        for i in range(1, 13):
            month = request.POST.get(f'month_{i}')
            year = request.POST.get(f'year_{i}')
            units = request.POST.get(f'units_{i}')
            amount = request.POST.get(f'amount_{i}')
            
            if month and year and amount:
                try:
                    due_month = int(month) + 1 if int(month) < 12 else 1
                    due_year = int(year) if int(month) < 12 else int(year) + 1
                    due_date = date(due_year, due_month, 15)
                    
                    # Create bill
                    bill = Bill.objects.create(
                        user=request.user,
                        account=account,
                        billing_month=int(month),
                        billing_year=int(year),
                        units_consumed=float(units or 0),
                        bill_amount=Decimal(str(amount)),
                        due_date=due_date,
                        is_paid=True
                    )
                    
                    # AUTOMATIC AI ANALYSIS
                    is_anomaly, payment_risk = analyze_bill_automatically(bill)
                    
                    if payment_risk == 'High Risk':
                        high_risk_detected += 1
                    if is_anomaly:
                        anomalies_detected += 1
                    
                    bills_added += 1
                except Exception as e:
                    print(f"Error adding bill: {e}")
        
        if bills_added > 0:
            success_msg = f'✅ Added {bills_added} bills to {account.account_name}!'
            if high_risk_detected > 0:
                success_msg += f' ⚠️ {high_risk_detected} High Risk detected!'
            if anomalies_detected > 0:
                success_msg += f' 🔴 {anomalies_detected} Anomalies detected!'
            messages.success(request, success_msg)
        
        return redirect('account_detail', account_id=account.id)
    
    context = {
        'account': account,
        'months': range(1, 13),
        'years': range(2020, 2031),
    }
    
    return render(request, 'bills/bulk_import_bills.html', context)

# ==========================================
# MARK BILL AS PAID/UNPAID - ALL MEMBERS
# ==========================================

@login_required
def toggle_bill_payment(request, bill_id):
    """Toggle bill payment status - ALL MEMBERS CAN MARK AS PAID/UNPAID"""
    if request.method == 'POST':
        # CHANGED: Get bill without user filter
        bill = get_object_or_404(Bill, id=bill_id)
        
        # Toggle payment status
        bill.is_paid = not bill.is_paid
        bill.save()
        
        status = "paid" if bill.is_paid else "unpaid"
        messages.success(request, f'✅ Bill marked as {status}!')
        
        return redirect('bill_list')
    
    return redirect('bill_list')

# ==========================================
# ADMIN-ONLY ACCOUNT MANAGEMENT
# ==========================================

@login_required
def edit_account(request, account_id):
    """Edit account - ADMIN ONLY"""
    # Check if user is admin
    if not request.user.is_superuser:
        messages.error(request, '❌ Permission denied! Only admins can edit accounts.')
        return redirect('manage_accounts')
    
    # CHANGED: Get account without user filter
    account = get_object_or_404(UtilityAccount, id=account_id)
    
    if request.method == 'POST':
        account_number = request.POST.get('account_number', '').strip()
        account_name = request.POST.get('account_name', '').strip()
        provider = request.POST.get('provider', '')
        
        # Validate account name
        if not account_name:
            messages.error(request, '❌ Account name is required!')
            return redirect('edit_account', account_id=account_id)
        
        # Validate account number (same validation as add_account)
        validation_passed = True
        error_message = None
        
        if account.utility_type == 'mobile':
            if not re.match(r'^07[0-9]{8}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid mobile number! Must be exactly 10 digits and start with 07'
        
        elif account.utility_type == 'electricity':
            if not re.match(r'^[0-9]{6,15}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid CEB account number! Must be 6-15 digits'
        
        elif account.utility_type == 'water':
            if not re.match(r'^[0-9A-Za-z\-]{4,20}$', account_number):
                validation_passed = False
                error_message = '❌ Invalid water account number! Must be 4-20 characters'
        
        # Check if validation failed
        if not validation_passed:
            messages.error(request, error_message)
            return redirect('edit_account', account_id=account_id)
        
        # Check for duplicates (only if account number changed)
        if account_number != account.account_number:
            if UtilityAccount.objects.filter(
                utility_type=account.utility_type,
                account_number=account_number
            ).exclude(id=account.id).exists():
                messages.error(request, f'❌ Account number {account_number} already exists!')
                return redirect('edit_account', account_id=account_id)
        
        # Update account
        account.account_number = account_number
        account.account_name = account_name
        if account.utility_type == 'mobile':
            account.provider = provider
        account.save()
        
        # Update all bills linked to this account
        account.bills.update(account_number=account_number)
        
        messages.success(request, f'✅ Account "{account_name}" updated successfully!')
        return redirect('account_detail', account_id=account.id)
    
    context = {
        'account': account,
    }
    
    return render(request, 'bills/edit_account.html', context)

@login_required
def delete_account(request, account_id):
    """Delete account - ADMIN ONLY"""
    if not request.user.is_superuser:
        messages.error(request, '❌ Permission denied! Only admins can delete accounts.')
        return redirect('manage_accounts')
    
    if request.method == 'POST':
        # CHANGED: Get account without user filter
        account = get_object_or_404(UtilityAccount, id=account_id)
        
        account_name = account.account_name
        account.delete()
        
        messages.success(request, f'✅ Account "{account_name}" deleted successfully!')
        return redirect('manage_accounts')
    
    return redirect('manage_accounts')

@login_required
def delete_bill(request, bill_id):
    """Delete bill - ADMIN ONLY"""
    if not request.user.is_superuser:
        messages.error(request, '❌ Permission denied! Only admins can delete bills.')
        return redirect('bill_list')
    
    if request.method == 'POST':
        # CHANGED: Get bill without user filter
        bill = get_object_or_404(Bill, id=bill_id)
        
        account_name = bill.account.account_name if bill.account else 'Unknown'
        bill_info = f"{account_name} - {bill.billing_month}/{bill.billing_year}"
        
        bill.delete()
        
        messages.success(request, f'✅ Bill deleted: {bill_info}')
        return redirect('bill_list')
    
    return redirect('bill_list')

@login_required
def edit_bill(request, bill_id):
    """Edit bill - ADMIN ONLY"""
    if not request.user.is_superuser:
        messages.error(request, '❌ Permission denied! Only admins can edit bills.')
        return redirect('bill_list')
    
    # CHANGED: Get bill without user filter
    bill = get_object_or_404(Bill, id=bill_id)
    
    if request.method == 'POST':
        units_consumed = float(request.POST.get('units_consumed', 0))
        bill_amount = float(request.POST.get('bill_amount'))
        is_paid = request.POST.get('is_paid') == 'on'
        
        # Update bill
        bill.units_consumed = units_consumed
        bill.bill_amount = bill_amount
        bill.is_paid = is_paid
        bill.save()
        
        messages.success(request, f'✅ Bill updated successfully!')
        return redirect('bill_list')
    
    context = {
        'bill': bill,
    }
    
    return render(request, 'bills/edit_bill.html', context)

# ==========================================
# USER MANAGEMENT
# ==========================================

@staff_member_required
def user_management(request):
    users = User.objects.all().select_related()
    groups = Group.objects.all()
    
    context = {
        'users': users,
        'groups': groups,
    }
    
    return render(request, 'bills/user_management.html', context)

@staff_member_required
def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f'❌ Username "{username}" already exists!')
            return redirect('user_management')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            group = Group.objects.get_or_create(name='Admin')[0]
        elif role == 'manager':
            user.is_staff = True
            group = Group.objects.get_or_create(name='Finance Manager')[0]
        else:
            group = Group.objects.get_or_create(name='Finance Executive')[0]
        
        user.groups.add(group)
        user.save()
        
        messages.success(request, f'✅ User "{username}" created successfully!')
        return redirect('user_management')
    
    return redirect('user_management')

@staff_member_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        if user == request.user:
            messages.error(request, '❌ You cannot delete your own account!')
            return redirect('user_management')
        
        username = user.username
        user.delete()
        messages.success(request, f'✅ User "{username}" deleted successfully!')
    
    return redirect('user_management')

@staff_member_required
def reset_password(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_password = request.POST.get('new_password')
        
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f'✅ Password reset for "{user.username}"!')
    
    return redirect('user_management')
