from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logged-in/', views.logged_in, name='logged_in'),
    path('logout/', views.logout, name='logout'),
    path('login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('api/scan-qr/', views.scan_qr, name='scan_qr'),
    path('api/orders/', views.create_order, name='create_order'),
    path('api/stripe-session/', views.create_stripe_session, name='create_stripe_session'),
    path('success/', views.success, name='success'),
    path('payments/stripe-success/', views.stripe_success, name='stripe_success'),
    path('payments/stripe-cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('payment-error/', views.payment_error, name='payment_error'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
]
