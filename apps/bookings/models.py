from django.db import models
from django.conf import settings
# Importamos el nuevo modelo unificado del inventario
from apps.inventory.models import Paquete, Promocion


class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('PENDIENTE', 'Pendiente de Pago 🟡'),
        ('CONFIRMADA', 'Confirmada / Pagada 🟢'),
        ('CANCELADA', 'Cancelada 🔴'),
    ]

    METODOS_PAGO = [
        ('simulado', 'Simulador de Saldo Turista 💸'),
        ('transferencia', 'Transferencia Bancaria 🏦'),
        ('pasarela', 'Pasarela de Tarjetas (Stripe/PayPal) 💳'),
    ]

    id_reserva = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    
    # Apuntamos a Paquete de forma segura diferida por String
    paquete = models.ForeignKey('inventory.Paquete', on_delete=models.PROTECT, related_name='reservas_asociadas')
    
    # Soluciona el problema de inventarios: ¿Qué tipo de habitación reservó?
    inventario_habitacion = models.ForeignKey(
        'inventory.InventarioHabitacion', 
        on_delete=models.PROTECT, 
        related_name='reservas_asignadas',
        null=True, blank=True,
        verbose_name="Habitación Seleccionada"
    )
    
    cantidad_pasajeros = models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad de Pasajeros")
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_viaje = models.DateField(verbose_name="Fecha del Viaje")
    
    # Unificación monetaria estricta usando DecimalField
    precio_unitario_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario Base ($)", default=0.00)
    promocion_aplicada = models.ForeignKey(Promocion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cupón Aplicado")
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Total Final ($)")
    
    # Datos de pago consolidados
    estado_pago = models.CharField(max_length=15, choices=ESTADOS_RESERVA, default='PENDIENTE')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='simulado')
    codigo_transaccion = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Código/ID Único de Transacción")

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva #{self.id_reserva} - {self.usuario.email} [{self.estado_pago}]"

class Auditoria(models.Model):
    id_log = models.AutoField(primary_key=True)
    
    # Relación limpia y con related_name único para evitar choques
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='auditorias_reservas' 
    )
    
    tabla_afectada = models.CharField(max_length=100)
    accion_ejecutada = models.CharField(max_length=50)  # INSERT, UPDATE, DELETE, LOGIN, MODERACION
    valores_anteriores = models.JSONField(null=True, blank=True)
    valores_nuevos = models.JSONField(null=True, blank=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditoria'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        return f"[{self.accion_ejecutada}] en {self.tabla_afectada} - {self.fecha_evento}"

class Pago(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='pago_detalle')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    comprobante = models.FileField(upload_to='comprobantes_pagos/', null=True, blank=True, verbose_name="Recibo o Comprobante")

    def __str__(self):
        return f"Pago de Reserva #{self.reserva.id_reserva} - ${self.monto}"