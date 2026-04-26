from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/', views.book_ticket, name='book'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('cancel/<int:id>/', views.cancel_booking, name='cancel_booking'),
    path('pnr/', views.pnr_status, name='pnr'),
]