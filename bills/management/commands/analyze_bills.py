from django.core.management.base import BaseCommand
from bills.models import Bill
from bills.ml_utils import detect_anomaly, predict_payment_risk

class Command(BaseCommand):
    help = 'Analyze ALL bills (electricity, water, mobile) for anomalies and payment risk'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Starting Analysis for ALL Utility Bills'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        # Get all bills
        all_bills = Bill.objects.all()
        
        if not all_bills.exists():
            self.stdout.write(self.style.ERROR('No bills found!'))
            return
        
        # Counters
        analyzed = 0
        high_risk_count = 0
        anomaly_count = 0
        
        electricity_count = 0
        water_count = 0
        mobile_count = 0
        
        self.stdout.write('')
        
        # Analyze each bill
        for bill in all_bills:
            try:
                # ========== ELECTRICITY (AI-BASED) ==========
                if bill.utility_type == 'electricity' and bill.units_consumed > 0:
                    is_anomaly = detect_anomaly(
                        bill.bill_amount, 
                        bill.units_consumed, 
                        bill.billing_month
                    )
                    
                    payment_risk = predict_payment_risk(
                        bill.bill_amount, 
                        bill.units_consumed, 
                        bill.billing_month
                    )
                    
                    bill.is_anomaly = is_anomaly
                    bill.late_payment_risk = payment_risk
                    bill.save()
                    
                    electricity_count += 1
                
                # ========== WATER (THRESHOLD-BASED) ==========
                elif bill.utility_type == 'water':
                    is_anomaly = False
                    payment_risk = 'Low Risk'
                    
                    if bill.bill_amount > 15000 or bill.units_consumed > 100:
                        payment_risk = 'High Risk'
                        is_anomaly = True
                    elif bill.bill_amount > 8000 or bill.units_consumed > 50:
                        payment_risk = 'Medium Risk'
                    
                    bill.is_anomaly = is_anomaly
                    bill.late_payment_risk = payment_risk
                    bill.save()
                    
                    water_count += 1
                
                # ========== MOBILE (THRESHOLD-BASED) ==========
                elif bill.utility_type == 'mobile':
                    is_anomaly = False
                    payment_risk = 'Low Risk'
                    
                    if bill.bill_amount > 5000:
                        payment_risk = 'High Risk'
                        is_anomaly = True
                    elif bill.bill_amount > 3000:
                        payment_risk = 'Medium Risk'
                    
                    bill.is_anomaly = is_anomaly
                    bill.late_payment_risk = payment_risk
                    bill.save()
                    
                    mobile_count += 1
                
                else:
                    continue
                
                analyzed += 1
                
                # Show High Risk bills
                if payment_risk == 'High Risk':
                    high_risk_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ⚠️  HIGH RISK: {bill.utility_type.upper()} - '
                            f'{bill.billing_month}/{bill.billing_year} - '
                            f'LKR {bill.bill_amount} - '
                            f'{bill.units_consumed} units'
                        )
                    )
                
                # Show Anomalies
                if is_anomaly:
                    anomaly_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  🔴 ANOMALY: {bill.utility_type.upper()} - '
                            f'{bill.billing_month}/{bill.billing_year} - '
                            f'{bill.units_consumed} units'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error analyzing bill {bill.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Analysis Complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Total bills analyzed: {analyzed}')
        self.stdout.write(f'  - Electricity: {electricity_count}')
        self.stdout.write(f'  - Water: {water_count}')
        self.stdout.write(f'  - Mobile: {mobile_count}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(f'🚨 High Risk bills: {high_risk_count}'))
        self.stdout.write(self.style.ERROR(f'⚠️  Anomalies detected: {anomaly_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Risk Thresholds:')
        self.stdout.write('  Electricity: AI-based (ML models)')
        self.stdout.write('  Water: High Risk if Amount > 15,000 OR Units > 100')
        self.stdout.write('  Mobile: High Risk if Amount > 5,000')
        self.stdout.write(self.style.SUCCESS('=' * 60))
