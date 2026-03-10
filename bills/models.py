from django.db import models
from django.contrib.auth.models import User

class UtilityAccount(models.Model):
    """Multiple utility accounts per user"""
    UTILITY_TYPES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('mobile', 'Mobile'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPES)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=200, help_text="e.g., Head Office, Restaurant, Pool")
    provider = models.CharField(max_length=100, blank=True, help_text="For mobile: Dialog, Mobitel, etc.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['utility_type', 'account_name']
        unique_together = ['user', 'utility_type', 'account_number']
    
    def __str__(self):
        return f"{self.account_name} - {self.get_utility_type_display()} ({self.account_number})"
    
    def get_bill_count(self):
        return self.bills.count()
    
    def get_total_amount(self):
        from django.db.models import Sum
        return self.bills.aggregate(total=Sum('bill_amount'))['total'] or 0

class Bill(models.Model):
    UTILITY_CHOICES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('mobile', 'Mobile'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Multi-account support
    account = models.ForeignKey(
        UtilityAccount, 
        on_delete=models.CASCADE, 
        related_name='bills',
        null=True,
        blank=True
    )
    # Email notification for this bill (OPTIONAL)
    notification_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional: Email for payment reminder"
    )
    
    # Backward compatibility
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

class Budget(models.Model):
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
    
