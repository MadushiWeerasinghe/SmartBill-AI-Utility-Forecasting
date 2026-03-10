from django.core.management.base import BaseCommand
from bills.models import Bill
from datetime import date

class Command(BaseCommand):
    help = 'Mark all overdue unpaid bills as High Risk'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('CHECKING FOR OVERDUE BILLS'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        
        today = date.today()
        
        # Find all unpaid bills past their due date
        overdue_bills = Bill.objects.filter(
            is_paid=False,
            due_date__lt=today
        )
        
        if not overdue_bills.exists():
            self.stdout.write(self.style.SUCCESS('✅ No overdue bills found!'))
            self.stdout.write(self.style.SUCCESS('All unpaid bills are still within due date.'))
            return
        
        self.stdout.write(f'Found {overdue_bills.count()} overdue bills:')
        self.stdout.write('')
        
        updated = 0
        already_marked = 0
        
        for bill in overdue_bills:
            days_overdue = (today - bill.due_date).days
            
            # Mark as High Risk if not already
            if bill.late_payment_risk != 'High Risk':
                bill.late_payment_risk = 'High Risk'
                bill.is_anomaly = True
                bill.save()
                updated += 1
                
                self.stdout.write(
                    self.style.ERROR(
                        f'  🚨 MARKED HIGH RISK: {bill.utility_type.upper()} - '
                        f'{bill.billing_month}/{bill.billing_year} - '
                        f'LKR {bill.bill_amount} - '
                        f'Due: {bill.due_date} ({days_overdue} days overdue)'
                    )
                )
            else:
                already_marked += 1
                self.stdout.write(
                    f'  ⚠️  Already High Risk: {bill.utility_type} - '
                    f'{bill.billing_month}/{bill.billing_year} - '
                    f'{days_overdue} days overdue'
                )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ OVERDUE CHECK COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Total overdue bills found: {overdue_bills.count()}')
        self.stdout.write(self.style.WARNING(f'Newly marked as High Risk: {updated}'))
        self.stdout.write(f'Already marked: {already_marked}')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        if updated > 0:
            self.stdout.write(self.style.SUCCESS('💡 TIP: Refresh your dashboard to see the updated High Risk count!'))
