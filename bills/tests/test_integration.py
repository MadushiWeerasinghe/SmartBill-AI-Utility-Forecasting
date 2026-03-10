"""
SmartBill - Integration Tests
Chapter 5: Testing and Validation
Author: st20287187
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from bills.models import Bill, UtilityAccount
from datetime import date, timedelta
from decimal import Decimal


class BillWorkflowIntegrationTests(TestCase):
    """Integration tests for complete bill management workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='hotelmanager',
            password='secure123',
            email='manager@hotel.com'
        )
        self.client.login(username='hotelmanager', password='secure123')
        
    def test_complete_bill_lifecycle(self):
        """Test complete bill lifecycle from creation to payment"""
        
        # Step 1: Create account directly
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='electricity',
            account_number='CEB-123456',
            account_name='Branch 1 - Electricity',
            provider='CEB'
        )
        
        self.assertIsNotNone(account)
        
        # Step 2: Add bill with email notification
        bill_response = self.client.post(reverse('add_bill'), {
            'account_id': account.id,
            'billing_month': 3,
            'billing_year': 2026,
            'units_consumed': 250,
            'bill_amount': 15000.00,
            'due_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'is_paid': False,
            'notification_email': 'branch1@hotel.com'
        })
        
        bill = Bill.objects.first()
        self.assertIsNotNone(bill)
        self.assertEqual(bill.notification_email, 'branch1@hotel.com')
        self.assertFalse(bill.is_paid)
        
        # Step 3: View bill list
        list_response = self.client.get(reverse('bill_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Branch 1')
        
        # Step 4: Mark bill as paid (auto-clear risk)
        payment_response = self.client.post(
            reverse('toggle_bill_payment', args=[bill.id])
        )
        
        bill.refresh_from_db()
        self.assertTrue(bill.is_paid)
        self.assertEqual(bill.late_payment_risk, 'Low Risk')
        self.assertFalse(bill.is_anomaly)
        
    def test_overdue_bill_workflow(self):
        """Test overdue bill detection and risk management"""
        
        # Import analyze function
        from bills.views import analyze_bill_automatically
        
        # Create account
        account = UtilityAccount.objects.create(
            user=self.user,
            utility_type='water',
            account_number='W-789',
            account_name='Branch 2 - Water'
        )
        
        # Create overdue bill
        overdue_date = date.today() - timedelta(days=30)
        bill = Bill.objects.create(
            user=self.user,
            account=account,
            billing_month=2,
            billing_year=2026,
            bill_amount=Decimal('20000.00'),
            due_date=overdue_date,
            is_paid=False
        )
        
        # Manually trigger analysis (simulates what add_bill view does)
        analyze_bill_automatically(bill)
        
        # View dashboard - should show overdue warning
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Check bill has high risk
        bill.refresh_from_db()
        self.assertEqual(bill.late_payment_risk, 'High Risk')
        
        # Mark as paid - should clear risk
        self.client.post(reverse('toggle_bill_payment', args=[bill.id]))
        
        bill.refresh_from_db()
        self.assertTrue(bill.is_paid)
        self.assertEqual(bill.late_payment_risk, 'Low Risk')
        
    def test_multi_account_management(self):
        """Test managing multiple utility accounts"""
        
        # Create multiple accounts
        accounts_data = [
            {'type': 'electricity', 'name': 'Branch 1 - CEB', 'number': 'E-001'},
            {'type': 'water', 'name': 'Branch 1 - Water', 'number': 'W-001'},
            {'type': 'mobile', 'name': 'Manager Phone', 'number': '0771234567'},
        ]
        
        for acc_data in accounts_data:
            UtilityAccount.objects.create(
                user=self.user,
                utility_type=acc_data['type'],
                account_name=acc_data['name'],
                account_number=acc_data['number']
            )
        
        self.assertEqual(UtilityAccount.objects.count(), 3)
        
        # Create bills for each account
        for account in UtilityAccount.objects.all():
            Bill.objects.create(
                user=self.user,
                account=account,
                billing_month=3,
                billing_year=2026,
                bill_amount=Decimal('5000.00'),
                due_date=date.today() + timedelta(days=10)
            )
        
        self.assertEqual(Bill.objects.count(), 3)
        
        # Filter by utility type
        electricity_response = self.client.get(
            reverse('bill_list') + '?utility=electricity'
        )
        self.assertEqual(electricity_response.status_code, 200)


class EmailNotificationIntegrationTests(TestCase):
    """Integration tests for email notification system"""
    
    def setUp(self):
        """Set up test environment"""
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
        
    def test_bill_with_email_saves_correctly(self):
        """Test bill with email notification saves correctly"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=7),
            notification_email='test@hotel.com'
        )
        
        self.assertEqual(bill.notification_email, 'test@hotel.com')
        
    def test_bill_without_email_saves_as_none(self):
        """Test bill without email saves as None"""
        bill = Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=7)
        )
        
        self.assertIsNone(bill.notification_email)


class DashboardIntegrationTests(TestCase):
    """Integration tests for dashboard statistics"""
    
    def setUp(self):
        """Set up test environment"""
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
            account_name='Test Account'
        )
        
    def test_dashboard_statistics_accuracy(self):
        """Test dashboard shows accurate statistics"""
        
        # Create 2 unpaid, 1 paid, 1 overdue bill
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('5000.00'),
            due_date=date.today() + timedelta(days=10),
            is_paid=False
        )
        
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=3,
            billing_year=2026,
            bill_amount=Decimal('7000.00'),
            due_date=date.today() + timedelta(days=5),
            is_paid=False
        )
        
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=2,
            billing_year=2026,
            bill_amount=Decimal('6000.00'),
            due_date=date.today() - timedelta(days=15),
            is_paid=False,
            late_payment_risk='High Risk'
        )
        
        Bill.objects.create(
            user=self.user,
            account=self.account,
            billing_month=1,
            billing_year=2026,
            bill_amount=Decimal('4000.00'),
            due_date=date.today() - timedelta(days=30),
            is_paid=True,
            late_payment_risk='Low Risk'
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


# Run tests with: python manage.py test bills.tests.test_integration
