from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # 1. Si entran a /catalogo/ (vacío), va a la lista completa
    path('', views.lista_paquetes, name='lista_paquetes'),
    
    # 2. Si entran a /catalogo/1/ (un número entero), va al detalle del paquete
    path('<int:pk>/', views.detalle_paquete, name='detalle_paquete'),
    
    
    path('paquete/<int:paquete_id>/comprar/', views.procesar_compra_simulada, name='procesar_compra_simulada'),
    
    path('explorar/', views.explorar_paquetes, name='explorar_paquetes'),
    path('comparar/agregar/<int:paquete_id>/', views.agregar_a_comparacion, name='agregar_a_comparacion'),
    path('comparar/limpiar/', views.limpiar_comparacion, name='limpiar_comparacion'),

]