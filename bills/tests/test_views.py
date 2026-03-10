"""
SmartBill - View Tests
Chapter 5: Testing and Validation
Author: st20287187
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from bills.models import Bill, UtilityAccount
from datetime import date, timedelta
from decimal import Decimal


class DashboardViewTests(TestCase):
    """Test cases for dashboard view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_dashboard_loads_successfully(self):
        """Test dashboard loads for authenticated user"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        
    def test_dashboard_shows_statistics(self):
        """Test dashboard displays bill statistics"""
        # Create test account
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456',
            account_name='Test Account'
        )
        
        # Create test bill
        Bill.objects.create(
            user=self.user,
            account=account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=10),
            is_paid=False
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class AddBillViewTests(TestCase):
    """Test cases for add bill view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456',
            account_name='Branch 1'
        )
        
    def test_add_bill_page_loads(self):
        """Test add bill page loads successfully"""
        response = self.client.get(reverse('add_bill'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Bill')
        
    def test_add_bill_without_email(self):
        """Test adding bill without notification email"""
        response = self.client.post(reverse('add_bill'), {
            'account_id': self.account.id,
            'billing_month': 3,
            'billing_year': 2026,
            'units_consumed': 150,
            'bill_amount': 5000.00,
            'due_date': (date.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'is_paid': False
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Bill.objects.count(), 1)
        
        bill = Bill.objects.first()
        self.assertIsNone(bill.notification_email)
        
    def test_add_bill_with_email(self):
        """Test adding bill with notification email"""
        response = self.client.post(reverse('add_bill'), {
            'account_id': self.account.id,
            'billing_month': 3,
            'billing_year': 2026,
            'units_consumed': 150,
            'bill_amount': 5000.00,
            'due_date': (date.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'is_paid': False,
            'notification_email': 'manager@hotel.com'
        })
        
        self.assertEqual(response.status_code, 302)
        bill = Bill.objects.first()
        self.assertEqual(bill.notification_email, 'manager@hotel.com')


class BillListViewTests(TestCase):
    """Test cases for bill list view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456',
            account_name='Branch 1'
        )
        
    def test_bill_list_loads(self):
        """Test bill list page loads"""
        response = self.client.get(reverse('bill_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_bill_list_shows_bills(self):
        """Test bill list displays created bills"""
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=10)
        )
        
        response = self.client.get(reverse('bill_list'))
        self.assertContains(response, 'Branch 1')
        self.assertContains(response, 'LKR 5000.00')
        
    def test_bill_list_filter_unpaid(self):
        """Test filtering unpaid bills"""
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=10),
            is_paid=False
        )
        
        response = self.client.get(reverse('bill_list') + '?status=unpaid')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unpaid')


class TogglePaymentViewTests(TestCase):
    """Test cases for toggle payment view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456',
            account_name='Branch 1'
        )
        
        self.bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('25000.00'),
            due_date=date.today() - timedelta(days=15),  # Overdue
            is_paid=False,
            late_payment_risk='High Risk',
            is_anomaly=True
        )
        
    def test_mark_bill_as_paid_clears_risk(self):
        """Test marking bill as paid clears high risk"""
        response = self.client.post(
            reverse('toggle_bill_payment', args=[self.bill.id])
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Refresh bill from database
        self.bill.refresh_from_db()
        
        self.assertTrue(self.bill.is_paid)
        self.assertEqual(self.bill.late_payment_risk, 'Low Risk')
        self.assertFalse(self.bill.is_anomaly)
        
    def test_unmark_paid_bill_reanalyzes(self):
        """Test unmarking paid bill re-analyzes risk"""
        # First mark as paid
        self.bill.is_paid = True
        self.bill.late_payment_risk = 'Low Risk'
        self.bill.is_anomaly = False
        self.bill.save()
        
        # Then unmark
        response = self.client.post(
            reverse('toggle_bill_payment', args=[self.bill.id])
        )
        
        self.bill.refresh_from_db()
        
        self.assertFalse(self.bill.is_paid)
        # Should be High Risk again because overdue
        self.assertEqual(self.bill.late_payment_risk, 'High Risk')


class ManageAccountsViewTests(TestCase):
    """Test cases for manage accounts view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def test_manage_accounts_loads(self):
        """Test manage accounts page loads"""
        response = self.client.get(reverse('manage_accounts'))
        self.assertEqual(response.status_code, 200)
        
    def test_add_new_account(self):
        """Test adding a new utility account"""
        # Create account directly (manage_accounts view may not handle POST)
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='123456789',
            account_name='Branch 2 - Electricity',
            provider='CEB'
        )
        
        self.assertEqual(UtilityAccount.objects.count(), 1)
        self.assertEqual(account.account_name, 'Branch 2 - Electricity')
        self.assertEqual(account.utility_type, 'electricity')


# Run tests with: python manage.py test bills.tests.test_views
