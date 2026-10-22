from django.contrib import admin
from .models import (
    Categoria, 
    Paquete, 
    ItinerarioDia, 
    Destino,       
    ImagenDestino, 
    Hotel, 
    TipoHabitacion,
    ServicioHotel, 
    ImagenHotel,   
    InventarioHabitacion, 
    Reserva, 
    PuntoDeInteres,
    CompraPaquete,
    Temporada,
    ImagenPaquete,
    Ruta,
    ParadaRuta
)

# ==========================================
# --- ACCIONES RÁPIDAS EN LOTE (ACTIONS) ---
# ==========================================

@admin.action(description='🟢 Aprobar POIs seleccionados')
def aprobar_pois(modeladmin, request, queryset):
    queryset.update(estado='APROBADO', motivo_moderacion='')
    modeladmin.message_user(request, f"Se han aprobado {queryset.count()} Puntos de Interés.")

@admin.action(description='🟢 Activar paquetes para la venta')
def activar_paquetes(modeladmin, request, queryset):
    queryset.update(esta_activo=True)

@admin.action(description='🔴 Desactivar paquetes (Pausar temporalmente)')
def desactivar_paquetes(modeladmin, request, queryset):
    queryset.update(esta_activo=False)


# ==========================================
# ---   CONFIGURACIÓN DE INLINES        ---
# ==========================================

class ItinerarioDiaInline(admin.TabularInline):
    model = ItinerarioDia
    extra = 1

class ImagenDestinoInline(admin.TabularInline):
    model = ImagenDestino
    extra = 1

class ImagenHotelInline(admin.TabularInline):
    model = ImagenHotel
    extra = 1

class TipoHabitacionInline(admin.TabularInline):
    model = TipoHabitacion
    extra = 1

class InventarioHabitacionInline(admin.TabularInline):
    """Asociado a PaqueteAdmin para manejar el stock por paquete comercial"""
    model = InventarioHabitacion
    extra = 1
    
class ImagenPaqueteInline(admin.TabularInline):
    model = ImagenPaquete
    extra = 1

class ParadaRutaInline(admin.TabularInline):
    """
    Permite agregar, quitar y ordenar los POIs de la ruta 
    directamente desde la vista de creación de la Ruta.
    """
    model = ParadaRuta
    extra = 2  # Te muestra 2 espacios vacíos por defecto para añadir paradas rápidas

# ==========================================
# --- CONFIGURACIÓN DE MODELADMINS       ---
# ==========================================

@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'clima', 'tipo', 'esta_activo']
    list_filter = ['clima', 'tipo', 'esta_activo']
    search_fields = ['nombre']
    inlines = [ImagenDestinoInline]

@admin.register(PuntoDeInteres)
class PuntoDeInteresAdmin(admin.ModelAdmin):
    # 🛠️ CORRECCIÓN: Quitamos 'ubicacion' y ponemos tus campos reales de coordenadas y referencia
    list_display = ['nombre', 'proponente', 'categoria', 'estado', 'referencia_ubicacion', 'fecha_propuesta']
    list_filter = ['estado', 'categoria', 'fecha_propuesta']
    search_fields = ['nombre', 'proponente__email', 'referencia_ubicacion']
    
    # Organiza el formulario de edición en secciones limpias para el Admin
    fieldsets = (
        ('Información Básica', {
            'fields': ('proponente', 'nombre', 'descripcion', 'categoria')
        }),
        ('Multimedia', {
            'fields': ('imagen_url', 'imagen_archivo')
        }),
        ('Ubicación Geográfica', {
            'fields': ('latitud', 'longitud', 'referencia_ubicacion'),
            'description': 'Coordenadas del mapa y datos de referencia.'
        }),
        ('Moderación Editorial', {
            'fields': ('estado', 'motivo_moderacion')
        }),
    )

    # Acción en lote para aprobar rápido lo que envíen los turistas
    actions = ['aprobar_pois']

    @admin.action(description='🟢 Aprobar POIs seleccionados')
    def aprobar_pois(self, request, queryset):
        queryset.update(estado='APROBADO', motivo_moderacion='')

@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    # Usamos precio_base ya que 'precio' ya no existe en el modelo
    list_display = ['nombre', 'categoria', 'precio_base', 'duracion_dias', 'dificultad', 'esta_activo']
    list_filter = ['esta_activo', 'categoria', 'dificultad']
    search_fields = ['nombre', 'descripcion']
    actions = [activar_paquetes, desactivar_paquetes]
    inlines = [ItinerarioDiaInline, InventarioHabitacionInline, ImagenPaqueteInline]


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    # Usamos destino ya que 'ciudad' ya no existe en el modelo
    list_display = ['nombre', 'destino', 'calificacion_estrellas', 'esta_activo']
    list_filter = ['destino', 'calificacion_estrellas', 'esta_activo']
    search_fields = ['nombre']
    inlines = [ImagenHotelInline, TipoHabitacionInline]


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'habitacion_inventario', 'estado', 'fecha']
    list_filter = ['estado']
    list_editable = ['estado']


@admin.register(CompraPaquete)
class CompraPaqueteAdmin(admin.ModelAdmin):
    list_display = ('codigo_transaccion', 'turista', 'paquete', 'cantidad_cupos', 'total_pagado', 'metodo_pago', 'fecha_compra')
    list_filter = ('metodo_pago', 'fecha_compra', 'paquete')
    search_fields = ('codigo_transaccion', 'turista__email', 'paquete__nombre')
    readonly_fields = ('fecha_compra',)
    ordering = ('-fecha_compra',)


@admin.register(ServicioHotel)
class ServicioHotelAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'icono']


@admin.register(Temporada)
class TemporadaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha_inicio', 'fecha_fin', 'condicion_climatica', 'factor_precio']
    list_filter = ['fecha_inicio', 'fecha_fin']
    search_fields = ['nombre']


# ==========================================
# ---       CONFIGURACIÓN DE RUTA        ---
# ==========================================
@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    # Campos que se verán en la tabla principal de rutas
    list_display = ['nombre', 'destino', 'duracion_horas_minutos', 'esta_activa']
    list_filter = ['esta_activa', 'destino']
    search_fields = ['nombre', 'descripcion']
    
    # Inyectamos el inline para manejar los POIs dinámicamente
    inlines = [ParadaRutaInline]

    # Tip pro: Formatear la duración en minutos a algo más legible (Horas y Minutos)
    @admin.display(description="Duración Estimada")
    def duracion_horas_minutos(self, obj):
        horas = obj.duracion_estimada // 60
        minutos = obj.duracion_estimada % 60
        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos} min"

# ==========================================
# ---     REGISTRO DE MODELOS SIMPLE     ---
# ==========================================

# Solo registramos aquí los que NO llevan el decorador @admin.register arriba
admin.site.register(Categoria)