(
echo from django.core.management.base import BaseCommand
echo from bills.models import Bill
echo from bills.ml_utils import detect_anomaly, predict_payment_risk
echo.
echo class Command^(BaseCommand^):
echo     help = 'Analyze all electricity bills'
echo.
echo     def handle^(self, *args, **kwargs^):
echo         self.stdout.write^('Starting analysis...'^ )
echo         bills = Bill.objects.filter^(utility_type='electricity'^)
echo         analyzed = 0
echo         high_risk = 0
echo         for bill in bills:
echo             try:
echo                 anomaly = detect_anomaly^(bill.bill_amount, bill.units_consumed, bill.billing_month^)
echo                 risk = predict_payment_risk^(bill.bill_amount, bill.units_consumed, bill.billing_month^)
echo                 bill.is_anomaly = anomaly
echo                 bill.late_payment_risk = risk
echo                 bill.save^(^)
echo                 analyzed += 1
echo                 if risk == 'High Risk':
echo                     high_risk += 1
echo             except: pass
echo         self.stdout.write^('Analyzed: ' + str^(analyzed^) + ', High Risk: ' + str^(high_risk^^)
) > bills\management\commands\analyze_bills.py