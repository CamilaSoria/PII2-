from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # 🚀 Ruta para crear la reserva usando el ID del paquete directo
    path('reservar/<int:paquete_id>/', views.crear_reserva_transaccional, name='crear_reserva_transaccional'),
    
    # ❌ Ruta para la cancelación autónoma desde el perfil del turista
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva_turista, name='cancelar_reserva_turista'),
    
    path('webhook-pagos/', views.webhook_pagos, name='webhook_pagos'),
    
    path('checkout/<int:reserva_id>/', views.checkout_pago, name='checkout_pago'),
    
    path('reportes/', views.reporte_ventas, name='reporte_ventas'),
]