from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reserva

@receiver(post_save, sender=Reserva)
def devolver_cupo_por_cancelacion(sender, instance, created, **kwargs):
    """
    Señal tras bambalinas: Si una reserva existente cambia su estado a CANCELADA,
    devuelve automáticamente los pasajeros asignados al stock del Paquete.
    """
    # No actúa si la reserva se acaba de crear como cancelada de la nada
    if not created:
        # Si el estado_pago mutó a CANCELADA
        if instance.estado_pago == 'CANCELADA' and instance.paquete:
            paquete = instance.paquete
            # Sumamos de vuelta la cantidad de pasajeros que se habían bajado del viaje
            paquete.cupos_totales += instance.cantidad_pasajeros
            paquete.save()