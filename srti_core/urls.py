"""
URL configuration for srti_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin estándar
    path('admin/', admin.site.urls),
    
    # 2. Rutas de autenticación
    path('auth/', include(('apps.authentication.urls', 'authentication'), namespace='authentication')),

    # 3. Ruta única para el catálogo e inventario (Módulos 2, 4, 5 y 8)
    # Dejamos 'catalogo/' como puerta de entrada principal para el inventario
    path('catalogo/', include('apps.inventory.urls', namespace='inventory')),
    
    # 4. Ruta maestra para las reservas y pagos (Módulos 6 and 7)
    path('reservas/', include('apps.bookings.urls', namespace='bookings')),

    # 5. Reportes y Dashboard (Corregido: apuntando a su propia app de reportes si existe)
    # NOTA: Si no tienes una app 'dashboard', apunta a la app encargada de las analíticas.
    path('dashboard/', include('apps.bookings.urls', namespace='dashboard')), 
    
    # 6. Gestión (Hoteles y Destinos - Módulo actual)
    path('gestion/', include('apps.gestion.urls', namespace='gestion')),
    
    # 7. Landing Page Principal (Raíz)
    path('', include('apps.landing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)