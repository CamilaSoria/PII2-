from django.urls import path
from django.contrib.auth.views import (
    LoginView, 
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView
)
from . import views

app_name = 'authentication'

urlpatterns = [
    # Usamos las vistas nativas de Django, solo le decimos qué HTML mostrar
    # Apuntamos directamente a tu nueva vista personalizada
    path('login/', views.login_usuario, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registro/', views.registro_turista, name='registro'),
    
    # --- RUTAS DE PERFIL Y RESERVAS SIMULADAS ---
    path('perfil/', views.perfil_turista, name='perfil'),
    
    # --- RUTAS DE RECUPERACIÓN DE CONTRASEÑA ---
    path('recuperar-password/', views.solicitar_restablecimiento, name='solicitar_restablecimiento'),
    path('restablecer/<str:token>/', views.restablecer_password_confirmar, name='restablecer_password_confirmar'), 
    # --- RUTAS DE CAMBIO DE CONTRASEÑA (INTERNA DESDE EL PERFIL) ---
    path('password-change/', 
        PasswordChangeView.as_view(template_name='authentication/password_change.html', success_url='/auth/perfil/'), 
        name='password_change'),
    
    path('verificacion-pendiente/', views.verificacion_pendiente, name='verificacion_pendiente'),
    
    path('activar/<str:token>/', views.activar_cuenta, name='activar_cuenta'),
    
    path('reenviar-enlace/', views.reenviar_enlace, name='reenviar_enlace'),
    
    # 1. Ruta para ver el tablero con el listado de joyas ocultas del turista
    path('mis-joyas-ocultas/', views.mis_joyas_ocultas, name='mis_joyas_ocultas'),
    
    # 2. Ruta de acción para procesar el formulario de creación del POI
    path('mis-joyas-ocultas/crear/', views.crear_joya_oculta, name='crear_joya_oculta'),
    
    path('mis-joyas-ocultas/editar/<int:poi_id>/', views.editar_joya_oculta, name='editar_joya_oculta'),
    
    path('explorar/', views.feed_joyas_ocultas, name='feed_joyas_ocultas'),
    
    path('joya/<int:poi_id>/favorito/', views.modificar_favorito_joya, name='modificar_favorito_joya'),
    
    path('mis-favoritos/', views.mis_joyas_favoritas, name='mis_joyas_favoritas'),
    
    path('mis-joyas/<int:poi_id>/eliminar/', views.eliminar_poi_turista, name='eliminar_poi_turista'),
    
    path('mis-compras/', views.historial_compras, name='historial_compras'),
]