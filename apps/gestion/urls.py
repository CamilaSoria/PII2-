from django.urls import path
from . import views

app_name = 'gestion'  # Esto es obligatorio si usas namespace

urlpatterns = [
    # Ejemplo: /gestion/usuarios/
    path('usuarios/', views.UsuariosListView.as_view(), name='lista_usuarios'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar_usuario'),
    path('usuarios/<int:pk>/estado/', views.AlternarEstadoUsuarioView.as_view(), name='alternar_estado_usuario'),
    path('moderacion/', views.bandeja_moderacion, name='bandeja_moderacion'),
    
    
# 📋 Listado principal de paquetes (Usa la CBV PaqueteListView)
    path('paquetes/', views.PaqueteListView.as_view(), name='lista_paquetes'),
    
    # ✨ Crear un nuevo paquete (Usa la CBV PaqueteCreateView)
    path('paquetes/crear/', views.PaqueteCreateView.as_view(), name='crear_paquete'),
    
    # 🔄 Editar un paquete existente (Usa la CBV PaqueteUpdateView con <int:pk>)
    path('paquetes/<int:pk>/editar/', views.PaqueteUpdateView.as_view(), name='editar_paquete'),
    
    # 🗑️ Eliminar paquete (Usa la CBV PaqueteDeleteView con <int:pk>)
    path('paquetes/<int:pk>/eliminar/', views.PaqueteDeleteView.as_view(), name='eliminar_paquete'),
    
    # 📸 Paths para las acciones AJAX de la galería (Se quedan con funciones directas @require_POST)
    path('paquetes/<int:paquete_id>/foto/<int:foto_id>/portada/', views.asignar_portada_paquete, name='asignar_portada_paquete'),
    path('paquetes/foto/<int:foto_id>/eliminar/', views.eliminar_foto_paquete, name='eliminar_foto_paquete'),
    
    
    path('pois/', views.administrar_pois, name='administrar_pois'),
    path('pois/editar/<int:poi_id>/', views.editar_poi, name='editar_poi'),
    path('pois/eliminar/<int:poi_id>/', views.eliminar_poi, name='eliminar_poi'),
    
    # 📸 CORRECCIÓN: Rutas Multimedia con sus respectivos parámetros dinámicos
    path('pois/eliminar-foto/<int:foto_id>/', views.eliminar_foto_galeria, name='eliminar_foto_galeria'),
    path('pois/<int:poi_id>/asignar-portada/<int:foto_id>/', views.asignar_portada_poi, name='asignar_portada_poi'),
    path('pois/<int:poi_id>/alternar-estado/', views.alternar_estado_poi, name='alternar_estado_poi'),
    
    # Destinos
    path('destinos/', views.DestinoListView.as_view(), name='destino_list'),
    path('destinos/nuevo/', views.DestinoCreateView.as_view(), name='destino_create'),
    path('destinos/<int:pk>/editar/', views.DestinoUpdateView.as_view(), name='destino_update'),
    path('destinos/<int:pk>/eliminar/', views.DestinoDeleteView.as_view(), name='destino_delete'),
    path('destinos/foto/<int:foto_id>/eliminar/', views.eliminar_foto_destino, name='eliminar_foto_destino'),
    path('destinos/<int:destino_id>/foto/<int:foto_id>/portada/', views.reordenar_portada_destino, name='asignar_portada_destino'),

    # 🗺️ HU13: GESTIÓN DE RUTAS TURÍSTICAS (NUEVA)
    path('rutas/', views.RutaListView.as_view(), name='ruta_list'),
    path('rutas/nueva/', views.RutaCreateView.as_view(), name='ruta_create'),
    path('rutas/<int:pk>/editar/', views.RutaUpdateView.as_view(), name='ruta_edit'),
    path('rutas/<int:pk>/eliminar/', views.RutaDeleteView.as_view(), name='ruta_delete'),
    
    # 🏨 HU14: GESTIÓN DE HOTELES (NUEVA)
    path('hoteles/', views.HotelListView.as_view(), name='hotel_list'),
    path('hoteles/nuevo/', views.HotelCreateView.as_view(), name='hotel_create'),
    path('hoteles/<int:pk>/editar/', views.HotelUpdateView.as_view(), name='hotel_update'),
    path('hoteles/<int:pk>/eliminar/', views.HotelDeleteView.as_view(), name='hotel_delete'),
    path('hoteles/foto/<int:foto_id>/eliminar/', views.eliminar_foto_hotel, name='eliminar_foto_hotel'),
    path('hoteles/<int:hotel_id>/foto/<int:foto_id>/portada/', views.asignar_portada_hotel, name='asignar_portada_hotel'),
    path('hoteles/servicios/nuevo/', views.ServicioHotelCreateView.as_view(), name='servicio_create'),
    path('hoteles/servicios/', views.ServicioHotelListView.as_view(), name='servicio_list'),
    path('hoteles/servicios/nuevo/', views.ServicioHotelCreateView.as_view(), name='servicio_create'),
    path('hoteles/servicios/<int:pk>/editar/', views.ServicioHotelUpdateView.as_view(), name='servicio_update'),
    path('hoteles/servicios/<int:pk>/eliminar/', views.ServicioHotelDeleteView.as_view(), name='servicio_delete'),
    
    path('dashboard/temporadas/', views.gestion_temporadas, name='gestion_temporadas'),
    path('dashboard/temporadas/editar/<int:pk>/', views.gestion_temporadas, name='editar_temporada'),
    path('dashboard/temporadas/eliminar/<int:pk>/', views.eliminar_temporada, name='eliminar_temporada'),
]