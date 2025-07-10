from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather, name='home'),  # Add this line for the base URL
    path('weather/', views.weather, name='weather'),
    path('details/', views.details_view, name='details'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('globe/', views.globe, name='globe'),
    path('travel/', views.travel_view, name='travel'),
]
