from django.urls import path
from . import views
urlpatterns = [
    path('accounts/<int:account_id>/edit/', views.edit_account, name='edit_account'),
    path('accounts/<int:account_id>/delete/', views.delete_account, name='delete_account'),
    path('bills/<int:bill_id>/edit/', views.edit_bill, name='edit_bill'),
    path('bills/<int:bill_id>/delete/', views.delete_bill, name='delete_bill'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bills/add/', views.add_bill, name='add_bill'),
    path('bills/', views.bill_list, name='bill_list'),
    path('predict/', views.predict_bill, name='predict_bill'),
    path('budget/', views.generate_budget, name='generate_budget'),
    path('accounts/', views.manage_accounts, name='manage_accounts'),
    path('accounts/add/', views.add_account, name='add_account'),
    path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<int:account_id>/bulk-import/', views.bulk_import_bills, name='bulk_import_bills'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/reset/<int:user_id>/', views.reset_password, name='reset_password'),
    path('predict/download-pdf/', views.download_prediction_pdf, name='download_prediction_pdf'),
    path('forecast/', views.forecast_six_months, name='forecast_six_months'),



]
