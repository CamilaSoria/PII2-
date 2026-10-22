from django.db import models
# Importamos tu modelo de Paquete desde la app donde esté guardado
# AJUSTA ESTA IMPORTACIÓN a la ruta real de tu app de inventario/paquetes:
from apps.inventory.models import Paquete 

class LeadInformativo(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono de Contacto")
    
    # Conectamos directamente con tus paquetes reales
    paquete_interes = models.ForeignKey(
        Paquete, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Paquete de Interés"
    )
    
    # Campos extra necesarios para una cotización de viajes
    cantidad_personas = models.PositiveIntegerField(default=1, verbose_name="Número de Viajeros")
    fecha_viaje_tentativa = models.DateField(verbose_name="Fecha Tentativa de Viaje")
    
    # Control interno
    fecha_registro = models.DateTimeField(auto_now_add=True)
    atendido = models.BooleanField(default=False, verbose_name="¿Ya fue contactado?")

    class Meta:
        verbose_name = "Prospecto de Cliente"
        verbose_name_plural = "Prospectos de Clientes"

    def __str__(self):
        return f"{self.nombre} interesado en {self.paquete_interes}"