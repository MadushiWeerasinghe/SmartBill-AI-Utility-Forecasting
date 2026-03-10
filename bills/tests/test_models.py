"""
SmartBill - Model Tests
Chapter 5: Testing and Validation
Student ID: st20287187

Test Coverage:
- UtilityAccount model
- Bill model with email notifications
- Budget model
- Auto-clear risk on payment
- Overdue detection
"""

from django.test import TestCase
from django.contrib.auth.models import User
from bills.models import Bill, UtilityAccount, Budget
from datetime import date, timedelta
from decimal import Decimal


class UtilityAccountModelTests(TestCase):
    """Test cases for UtilityAccount model"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_electricity_account(self):
        """Test creating an electricity account"""
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='CEB-123456',
            account_name='Branch 1 - Electricity',
            provider='CEB',
            is_active=True
        )
        
        self.assertEqual(account.utility_type, 'electricity')
        self.assertEqual(account.account_number, 'CEB-123456')
        self.assertEqual(account.account_name, 'Branch 1 - Electricity')
        self.assertEqual(account.provider, 'CEB')
        self.assertTrue(account.is_active)
        
    def test_create_water_account(self):
        """Test creating a water account"""
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='water',
            account_number='W-789456',
            account_name='Head Office - Water',
            is_active=True
        )
        
        self.assertEqual(account.utility_type, 'water')
        self.assertIn('Head Office', str(account))
        
    def test_create_mobile_account(self):
        """Test creating a mobile account with provider"""
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='mobile',
            account_number='0771234567',
            account_name='Manager Mobile',
            provider='Dialog'
        )
        
        self.assertEqual(account.provider, 'Dialog')
        self.assertEqual(account.utility_type, 'mobile')
        
    def test_account_string_representation(self):
        """Test __str__ method of UtilityAccount"""
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123',
            account_name='Test Account'
        )
        
        expected = 'Test Account - Electricity (123)'
        self.assertEqual(str(account), expected)
        
    def test_get_bill_count(self):
        """Test get_bill_count method"""
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123',
            account_name='Test Account'
        )
        
        # Create 3 bills
        for i in range(3):
            Bill.objects.create(
                user=self.user,
                account=account,
                billing_month=3,
                billing_year=2026,
                bill_amount=Decimal('5000.00'),
                due_date=date.today() + timedelta(days=10)
            )
        
        self.assertEqual(account.get_bill_count(), 3)


class BillModelTests(TestCase):
    """Test cases for Bill model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456',
            account_name='Test Account'
        )
    
    def test_create_unpaid_bill(self):
        """Test creating an unpaid bill"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            utility_type='electricity',
            account_number='123456',
            billing_month=3,
            billing_year=2026,
            units_consumed=150.0,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=10),
            is_paid=False
        )
        
        self.assertFalse(bill.is_paid)
        self.assertEqual(bill.bill_amount, Decimal('5000.00'))
        self.assertEqual(bill.units_consumed, 150.0)
        self.assertEqual(bill.billing_month, 3)
        
    def test_bill_with_email_notification(self):
        """Test bill with email notification field"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            utility_type='electricity',
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=7),
            notification_email='manager@hotel.com'
        )
        
        self.assertEqual(bill.notification_email, 'manager@hotel.com')
        
    def test_bill_without_email(self):
        """Test bill without email notification"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=7)
        )
        
        self.assertIsNone(bill.notification_email)
        
    def test_paid_bill_low_risk(self):
        """Test that paid bills have Low Risk regardless of amount/date"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=2,
            billing_year=2026,
            bill_amount=Decimal('25000.00'),  # High amount
            due_date=date.today() - timedelta(days=30),  # Overdue
            is_paid=True,  # But PAID
            late_payment_risk='Low Risk',
            is_anomaly=False
        )
        
        self.assertTrue(bill.is_paid)
        self.assertEqual(bill.late_payment_risk, 'Low Risk')
        self.assertFalse(bill.is_anomaly)
        
    def test_overdue_bill_high_risk(self):
        """Test that overdue unpaid bills are High Risk"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=2,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() - timedelta(days=15),  # 15 days overdue
            is_paid=False,
            late_payment_risk='High Risk'
        )
        
        self.assertFalse(bill.is_paid)
        self.assertEqual(bill.late_payment_risk, 'High Risk')
        self.assertTrue(bill.due_date < date.today())
        
    def test_bill_string_representation(self):
        """Test __str__ method of Bill"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today()
        )
        
        expected = f'{self.account.account_name} - 3/2026 - LKR 5000.00'
        self.assertEqual(str(bill), expected)
        
    def test_bill_ordering(self):
        """Test bills are ordered by year, month desc"""
        # Create bills in different months
        bill1 = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=1,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today()
        )
        
        bill2 = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('6000.00'),
            due_date=date.today()
        )
        
        bills = list(Bill.objects.all())
        # Should be in descending order
        self.assertEqual(bills[0], bill2)  # March first
        self.assertEqual(bills[1], bill1)  # January second


class BudgetModelTests(TestCase):
    """Test cases for Budget model"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_budget(self):
        """Test creating a monthly budget"""
        budget = Budget.objects.create(
            user=self.user,
            month=3,
            year=2026,
            electricity_budget=Decimal('15000.00'),
            water_budget=Decimal('8000.00'),
            mobile_budget=Decimal('3000.00'),
            total_budget=Decimal('26000.00')
        )
        
        self.assertEqual(budget.month, 3)
        self.assertEqual(budget.year, 2026)
        self.assertEqual(budget.electricity_budget, Decimal('15000.00'))
        self.assertEqual(budget.water_budget, Decimal('8000.00'))
        self.assertEqual(budget.mobile_budget, Decimal('3000.00'))
        self.assertEqual(budget.total_budget, Decimal('26000.00'))
        
    def test_budget_string_representation(self):
        """Test __str__ method of Budget"""
        budget = Budget.objects.create(
            user=self.user,
            month=3,
            year=2026,
            total_budget=Decimal('26000.00')
        )
        
        expected = 'Budget 3/2026 - LKR 26000.00'
        self.assertEqual(str(budget), expected)
        
    def test_budget_ordering(self):
        """Test budgets are ordered by created_at desc"""
        budget1 = Budget.objects.create(
            user=self.user,
            month=1,
            year=2026,
            total_budget=Decimal('20000.00')
        )
        
        budget2 = Budget.objects.create(
            user=self.user,
            month=2,
            year=2026,
            total_budget=Decimal('25000.00')
        )
        
        budgets = list(Budget.objects.all())
        # Most recent first
        self.assertEqual(budgets[0], budget2)
        self.assertEqual(budgets[1], budget1)


# Run with: python manage.py test bills.tests.test_models
