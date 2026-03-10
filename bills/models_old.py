from django.db import models
from django.contrib.auth.models import User

class UtilityAccount(models.Model):
    """Store multiple utility accounts per user"""
    UTILITY_TYPES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('mobile', 'Mobile'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPES)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=200, help_text="e.g., 'Head Office', 'Branch 1', 'Factory'")
    provider = models.CharField(max_length=100, blank=True, help_text="For mobile: Dialog, Mobitel, etc.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['utility_type', 'account_name']
        unique_together = ['user', 'utility_type', 'account_number']
    
    def __str__(self):
        return f"{self.get_utility_type_display()} - {self.account_name} ({self.account_number})"
    
    def get_bill_count(self):
        return self.bills.count()
    
    def get_last_six_months_bills(self):
        return self.bills.order_by('-billing_year', '-billing_month')[:6]
    
    def get_total_amount(self):
        return self.bills.aggregate(total=models.Sum('bill_amount'))['total'] or 0


class Bill(models.Model):
    UTILITY_CHOICES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('mobile', 'Mobile'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # NEW: Multi-account support (optional for backward compatibility)
    account = models.ForeignKey(
        UtilityAccount, 
        on_delete=models.CASCADE, 
        related_name='bills',
        null=True,
        blank=True
    )
    
    # OLD: Keep for backward compatibility
    utility_type = models.CharField(max_length=20, choices=UTILITY_CHOICES, null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    
    billing_month = models.IntegerField()
    billing_year = models.IntegerField()
    units_consumed = models.FloatField(default=0)
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    is_anomaly = models.BooleanField(default=False)
    late_payment_risk = models.CharField(max_length=20, default='Low')
    
    # Additional fields
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-billing_year', '-billing_month', '-created_at']
    
    def __str__(self):
        if self.account:
            return f"{self.account.account_name} - {self.billing_month}/{self.billing_year} - LKR {self.bill_amount}"
        return f"{self.utility_type} - {self.billing_month}/{self.billing_year} - LKR {self.bill_amount}"
    
    # Properties for backward compatibility
    def get_utility_type(self):
        """Get utility type from account or fallback to old field"""
        if self.account:
            return self.account.utility_type
        return self.utility_type or 'unknown'
    
    def get_account_number(self):
        """Get account number from account or fallback to old field"""
        if self.account:
            return self.account.account_number
        return self.account_number or 'N/A'


class BudgetForecast(models.Model):
    """6-month and 1-year budget forecasts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(UtilityAccount, on_delete=models.CASCADE, null=True, blank=True)
    
    forecast_type = models.CharField(max_length=20, choices=[
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
    ])
    
    start_month = models.IntegerField()
    start_year = models.IntegerField()
    
    # Store forecasts for each month
    month_1_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_2_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_3_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_4_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_5_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_6_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_7_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    month_8_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    month_9_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    month_10_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    month_11_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    month_12_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    
    total_forecast = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.account:
            return f"{self.account.account_name} - {self.forecast_type} Forecast"
        return f"Overall - {self.forecast_type} Forecast"
    
    def get_monthly_forecasts(self):
        """Return list of monthly forecast amounts"""
        months = 12 if self.forecast_type == '1_year' else 6
        return [
            getattr(self, f'month_{i}_amount') 
            for i in range(1, months + 1)
        ]


class Budget(models.Model):
    """Monthly budget (kept for backward compatibility)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    electricity_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mobile_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Budget {self.month}/{self.year} - LKR {self.total_budget}"
