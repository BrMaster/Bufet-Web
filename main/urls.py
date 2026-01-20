from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logged-in/', views.logged_in, name='logged_in'),
]
