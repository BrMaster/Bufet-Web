from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logged-in/', views.logged_in, name='logged_in'),
    path('logout/', views.logout, name='logout'),
    path('login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('api/scan-qr/', views.scan_qr, name='scan_qr'),
    path('success/', views.success, name='success'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
]
