from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Bills
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/add/', views.add_bill, name='add_bill'),
    path('bills/edit/<int:bill_id>/', views.edit_bill, name='edit_bill'),
    path('bills/delete/<int:bill_id>/', views.delete_bill, name='delete_bill'),
    path('bills/toggle/<int:bill_id>/', views.toggle_bill_payment, name='toggle_bill_payment'),
    
    # Prediction
    path('predict/', views.predict_bill, name='predict_bill'),
    path('predict/download/', views.download_prediction_pdf, name='download_prediction_pdf'),
    
    # Budget
    path('budget/', views.generate_budget, name='generate_budget'),
    
    # Accounts
    path('accounts/', views.manage_accounts, name='manage_accounts'),
    path('accounts/add/', views.add_account, name='add_account'),
    path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<int:account_id>/edit/', views.edit_account, name='edit_account'),
    path('accounts/<int:account_id>/delete/', views.delete_account, name='delete_account'),
    path('accounts/<int:account_id>/bulk-import/', views.bulk_import_bills, name='bulk_import_bills'),
    
    # User Management (Admin only)
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/reset-password/', views.reset_password, name='reset_password'),
]
