from django.contrib import admin
from .models import Reserva, Pago  # 🛠️ Aseguramos la importación de ambos modelos

class ReservaAdmin(admin.ModelAdmin):
    # Columnas principales en la lista (Historia 2: Ver estado de pago actualizado)
    list_display = ['id_reserva', 'usuario', 'paquete', 'estado_pago', 'fecha_viaje']
    
    # 🕵️ Filtrar reservas por Estado de pago y Fecha de viaje (Historia 5)
    list_filter = ['estado_pago', 'fecha_viaje']
    
    # 🔍 Buscador inteligente por username, email o el nombre del paquete comprado (Historia 5)
    search_fields = ['usuario__username', 'usuario__email', 'paquete__nombre']
    
    # ⚡ Edición rápida en línea del estado (Historia 4: Confirmar, Cancelar o dejar en Pendiente)
    list_editable = ['estado_pago']
    
    # Ordenar las reservas de las más recientes a las más antiguas
    ordering = ['-fecha_viaje']


# 💳 Nueva sección para que el agente gestione los Pagos Individuales (Historia 3)
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    # Usamos métodos para traer la información desde la Reserva asociada
    list_display = ['id', 'reserva', 'monto', 'get_metodo_pago', 'get_estado_pago', 'fecha_pago']
    list_filter = ['reserva__metodo_pago', 'reserva__estado_pago', 'fecha_pago']
    
    # Quita 'list_editable' por ahora, ya que 'estado' no es un campo directo de Pago.
    # Si quieres editar el estado, se hace desde la Reserva.
    
    def get_metodo_pago(self, obj):
        return obj.reserva.get_metodo_pago_display()
    get_metodo_pago.short_description = 'Método de Pago'

    def get_estado_pago(self, obj):
        return obj.reserva.get_estado_pago_display()
    get_estado_pago.short_description = 'Estado de Reserva'

# Registramos ambos modelos con sus configuraciones empresariales limpias
admin.site.register(Reserva, ReservaAdmin)