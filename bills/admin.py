from django.contrib import admin
from .models import Bill, Budget, UtilityAccount

@admin.register(UtilityAccount)
class UtilityAccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'utility_type', 'account_number', 'user', 'is_active', 'get_bill_count']
    list_filter = ['utility_type', 'is_active', 'user']
    search_fields = ['account_name', 'account_number']
    
    def get_bill_count(self, obj):
        return obj.get_bill_count()
    get_bill_count.short_description = 'Bills'

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['get_account_info', 'billing_month', 'billing_year', 'bill_amount', 'is_paid', 'is_anomaly']
    list_filter = ['is_paid', 'is_anomaly', 'billing_year']
    search_fields = ['account__account_name', 'account_number']
    
    def get_account_info(self, obj):
        if obj.account:
            return f"{obj.account.account_name} ({obj.account.utility_type})"
        return f"{obj.utility_type} - {obj.account_number}"
    get_account_info.short_description = 'Account'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'total_budget', 'user', 'created_at']
    list_filter = ['year', 'user']
