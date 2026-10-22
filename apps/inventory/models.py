from django.db import models, transaction  # <--- Importante para el bloqueo atómico
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.conf import settings  # Forma más segura de apuntar al usuario en Django
from apps.authentication.models import Usuario
from django.contrib.auth.models import User
from django.utils import timezone


# ==========================================
# ---        NÚCLEO DEL SISTEMA          ---
# ==========================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre



class Paquete(models.Model):
    DIFICULTAD_CHOICES = [
        ('baja', 'Baja 🟢'),
        ('media', 'Media 🟡'),
        ('alta', 'Alta 🔴'),
    ]

    # Estructura del Sprint 2 y Conexiones
    destino = models.ForeignKey('Destino', on_delete=models.PROTECT, related_name='paquetes_asociados')
    ruta = models.ForeignKey('Ruta', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ruta Incluida")
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, verbose_name="Categoría")
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(verbose_name="Descripción completa")
    duracion_dias = models.IntegerField(verbose_name="Duración (Días)")
    
    # Precios e Inventario General
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Base ($)")
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='media')
    cupos_totales = models.IntegerField(verbose_name="Cupos Totales")
    
    # Criterio 4: Publicación y despublicación de paquetes
    esta_activo = models.BooleanField(default=True, verbose_name="¿Publicado/Disponible para la venta?")
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=4.5, verbose_name="Calificación")
    
    # Criterio 1: Conecta con las joyas ocultas (POIs)
    pois = models.ManyToManyField('PuntoDeInteres', related_name='paquetes_incluidos', verbose_name="Joyas Ocultas Incluidas", blank=True)

    class Meta:
        verbose_name = "Paquete Turístico"
        verbose_name_plural = "Paquetes Turísticos"

    # 🧮 CRITERIO 3: Cálculo automático considerando Hotel, Temporada y Promociones
    # 🧮 CRITERIO 3: Cálculo automático considerando Hotel, Temporada y Promociones
    # 🧮 CRITERIO 3: Cálculo automático considerando Hotel, Temporada y Promociones
    @property
    def calcular_desglose(self):
        """
        Calcula el desglose neto real basado estrictamente en tus campos existentes.
        Aplica: Subtotal = Precio Base + (Precio Noche x Noches)
        Luego multiplica por el Factor de Temporada si aplica.
        """

        fecha_actual = timezone.now().date()
        base = self.precio_base
        
        # 🏨 Cálculo de noches reales: (Días - 1) ej: 4 días = 3 noches de hotel.
        noches = max(0, self.duracion_dias - 1)
        costo_hospedaje = 0
        
        # Usamos tu related_name 'habitaciones_inventario' del modelo InventarioHabitacion
        inventario_hotel = self.habitaciones_inventario.select_related('habitacion').first()
        if inventario_hotel:
            costo_hospedaje = inventario_hotel.habitacion.precio_por_noche * noches
            
        subtotal_neto = base + costo_hospedaje
        precio_acumulado = subtotal_neto
        
        # 🍂 Regla de Temporadas
        factor_temporada = 1.0
        recargo_temporada = 0
        temporada_actual = Temporada.objects.filter(
            fecha_inicio__lte=fecha_actual,
            fecha_fin__gte=fecha_actual
        ).first()
        
        if temporada_actual:
            factor_temporada = float(temporada_actual.factor_precio)
            precio_acumulado = float(subtotal_neto) * factor_temporada
            recargo_temporada = precio_acumulado - float(subtotal_neto)

        return {
            'base_paquete': base,
            'noches': noches,
            'costo_hospedaje': costo_hospedaje,
            'subtotal_neto': subtotal_neto,
            'factor_temporada': factor_temporada,
            'recargo_temporada': round(recargo_temporada, 2),
            'precio_final': round(precio_acumulado, 2)
        }

    @property
    def precio_final(self):
        """Mantiene la compatibilidad con tus formularios y listados"""
        return self.calcular_desglose['precio_final']

    def __str__(self):
        return f"{self.nombre} - Precio Calculado: ${self.precio_final}"
    # 🛡️ CRITERIO 5: Blindaje definitivo contra eliminación por reservas activas
    def delete(self, *args, **kwargs):
        # Buscamos de manera perezosa en el related_name que definimos en Reserva
        reservas_activas = self.reservas_asociadas.filter(estado_pago__in=['PENDIENTE', 'CONFIRMADA'])
        
        if reservas_activas.exists():
            raise ValidationError(
                f"No se puede eliminar el paquete '{self.nombre}' porque cuenta con "
                f"{reservas_activas.count()} reservas activas o pendientes de pago en este momento."
            )
        super().delete(*args, **kwargs)


# 📸 CRITERIO 2: Galería de imágenes múltiples para el Paquete Turístico
class ImagenPaquete(models.Model):
    paquete = models.ForeignKey(
        Paquete, 
        on_delete=models.CASCADE, 
        related_name='imagenes_galeria', 
        verbose_name="Paquete Asociado"
    )
    # 🆕 LE AGREGAMOS null=True y blank=True PARA EVITAR EL BLOQUEO DE LA TERMINAL
    imagen = models.ImageField(
        upload_to='paquetes_galeria/', 
        verbose_name="Foto de la Galería",
        null=True, blank=True  # 👈 ¡Agrégale esto temporalmente!
    )
    # Al quitarle el auto_now_add=True por ahora, Django no exigirá una fecha obligatoria en la migración
    fecha_subida = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Subida")

    class Meta:
        verbose_name = "Imagen de Paquete"
        verbose_name_plural = "Imágenes de Paquetes"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Foto para: {self.paquete.nombre} (ID: {self.id})"
    
class Temporada(models.Model):
    CLIMA_CHOICES = [
        ('soleado', '☀️ Soleado / Despejado'),
        ('lluvioso', '🌧️ Lluvioso / Monzón'),
        ('nevado', '❄️ Nevado / Invierno'),
        ('templado', '🍂 Templado / Nublado'),
    ]
    nombre = models.CharField(max_length=100, help_text="Ej: Alta Verano 2026, Baja Otoño")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    
    # T29: Condición climática asociada a la temporada
    condicion_climatica = models.CharField(max_length=100, choices=CLIMA_CHOICES, default='soleado', verbose_name="Condición Climática Esperada")
    
    # Porcentaje de ajuste de precio (Ej: 1.20 para aumentar 20% en temporada alta, 0.80 para rebajar)
    factor_precio = models.DecimalField(
            max_digits=4, 
            decimal_places=2, 
            default=1.00, 
            help_text="Multiplicador de precio. Ej: 1.25 aumenta un 25%, 0.80 descuenta un 20%."
        )

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"

    # T32: Validación de temporada única por período (Evitar solapamiento de fechas)
    
    def clean(self):
        # --- NUEVO CONTROL PARA EL CRITERIO 6 ---
        # Si la temporada ya existe (está siendo editada)
        if self.pk:
            instancia_original = Temporada.objects.get(pk=self.pk)
            # Si la temporada original ya empezó o ya terminó, congelamos sus datos críticos
            if instancia_original.fecha_inicio <= timezone.now().date():
                if (instancia_original.fecha_inicio != self.fecha_inicio or 
                    instancia_original.fecha_fin != self.fecha_fin or 
                    instancia_original.factor_precio != self.factor_precio):
                    raise ValidationError("🚨 No puedes modificar las fechas ni los precios de una temporada que ya está en curso o que ya finalizó.")

        # --- TU LÓGICA ACTUAL (IMPECABLE) ---
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
            
            coincidencias = Temporada.objects.filter(
                fecha_inicio__lte=self.fecha_fin,
                fecha_fin__gte=self.fecha_inicio
            )
            if self.pk:
                coincidencias = coincidencias.exclude(pk=self.pk)
            
            if coincidencias.exists():
                raise ValidationError("🚨 Ya existe una temporada registrada que se cruza con este rango de fechas.")
            
    def delete(self, *args, **kwargs):
        # Bloquea el borrado si la temporada ya empezó o ya pasó
        if self.fecha_inicio <= timezone.now().date():
            raise ValidationError("🚨 No se pueden eliminar temporadas activas o pasadas. Solo se permite eliminar temporadas futuras.")
        super().delete(*args, **kwargs)
        
    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio} a {self.fecha_fin})"
    
class ItinerarioDia(models.Model):
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='itinerarios')
    dia_numero = models.IntegerField(verbose_name="Número de Día")
    titulo = models.CharField(max_length=200, verbose_name="Título del día")
    descripcion = models.TextField(verbose_name="¿Qué se hará este día?")

    class Meta:
        ordering = ['dia_numero']
        verbose_name = "Día de Itinerario"
        verbose_name_plural = "Días de Itinerario"

    def __str__(self):
        return f"Día {self.dia_numero}: {self.titulo} ({self.paquete.nombre})"


# ==========================================
# ---      HOTELES E INVENTARIO          ---
# ==========================================

# T22: Gestión dinámica de servicios
class ServicioHotel(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej: Piscina, Wi-Fi Gratis, Spa, Desayuno")
    icono = models.CharField(max_length=50, blank=True, null=True, help_text="Código de icono (FontAwesome, Lucide, etc.)")

    class Meta:
        verbose_name = "Servicio de Hotel"
        verbose_name_plural = "Servicios de Hoteles"

    def __str__(self):
        return self.nombre


class Hotel(models.Model):
    destino = models.ForeignKey('Destino', on_delete=models.CASCADE, related_name='hoteles', verbose_name="Destino")
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    
    # 🟢 NUEVOS CAMPOS PARA EL MAPA (Déjalos con null/blank para que no chille la BD)
    latitud = models.FloatField(blank=True, null=True, verbose_name="Latitud")
    longitud = models.FloatField(blank=True, null=True, verbose_name="Longitud")
    
    descripcion = models.TextField(verbose_name="Descripción del Hotel", blank=True)
    calificacion_estrellas = models.IntegerField(default=3, verbose_name="Estrellas (1-5)")
    servicios = models.ManyToManyField(ServicioHotel, related_name='hoteles', verbose_name="Servicios/Amenities")
    esta_activo = models.BooleanField(default=True, verbose_name="¿Disponible?")

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hoteles"

    def __str__(self):
        return f"{self.nombre} ({self.destino.nombre})"
    
# T21: Modelo para soportar imágenes múltiples del hotel
class ImagenHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='imagenes')
    imagen_url = models.URLField(blank=True, null=True, help_text="Enlace de imagen externa")
    imagen_archivo = models.ImageField(upload_to='hoteles/', blank=True, null=True, help_text="Archivo de imagen local")
    es_principal = models.BooleanField(default=False, verbose_name="¿Es la foto de portada?")

    class Meta:
        verbose_name = "Imagen de Hotel"
        verbose_name_plural = "Imágenes de Hoteles"


# T20: Tipos de Habitación y Precios propios del Hotel (Desacoplado del paquete)
class TipoHabitacion(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='tipos_habitacion')
    nombre = models.CharField(max_length=100, help_text="Ej: Doble Ejecutiva, Suite Presidencial")
    capacidad_personas = models.PositiveIntegerField(default=2)
    
    # T20: Precio por noche base
    precio_por_noche = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio por Noche ($)")

    class Meta:
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitaciones"

    def __str__(self):
        return f"{self.hotel.nombre} - {self.nombre} (${self.precio_por_noche}/noche)"


# TU MODELO AJUSTADO: El inventario que une el hotel, la habitación y el paquete comercial
class InventarioHabitacion(models.Model):
    paquete = models.ForeignKey('Paquete', on_delete=models.CASCADE, related_name='habitaciones_inventario')
    habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE, related_name='inventarios')
    
    cupo_total = models.IntegerField(verbose_name="Cupos Totales para este Paquete")
    cupo_disponible = models.IntegerField(verbose_name="Cupos Disponibles")

    class Meta:
        verbose_name = "Inventario de Habitación"
        verbose_name_plural = "Inventario de Habitaciones"

    def __str__(self):
        return f"Paquete: {self.paquete.nombre} -> {self.habitacion.hotel.nombre} ({self.habitacion.nombre})"


# ==========================================
# ---            RESERVAS                ---
# ==========================================

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('CONFIRMADA', 'Confirmada ✅'),  # 🛠️ Ajustado a MAYÚSCULAS
        ('CANCELADA', 'Cancelada ❌'),    # 🛠️ Ajustado a MAYÚSCULAS por consistencia
    ]
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    habitacion_inventario = models.ForeignKey(InventarioHabitacion, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Compra")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='CONFIRMADA')

    def __str__(self):
        identificador = getattr(self.usuario, 'email', getattr(self.usuario, 'username', str(self.usuario.id)))
        return f"Reserva #{self.id} - {identificador} - Estado: {self.estado}"


# ==========================================
# ---        LOGÍSTICA Y GUÍAS           ---
# ==========================================

class GuiaTuristico(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre Completo")
    idiomas = models.CharField(max_length=200, help_text="Ej: Español, Inglés, Francés")
    especialidad = models.CharField(max_length=100, help_text="Ej: Trekking, Alta Montaña, Histórico")
    esta_disponible = models.BooleanField(default=True, verbose_name="¿Está Activo/Disponible?")

    class Meta:
        verbose_name = "Guía Turístico"
        verbose_name_plural = "Guías Turísticos"

    def __str__(self):
        return f"{self.nombre} ({self.especialidad}) - Idiomas: {self.idiomas}"


class AsignacionLogistica(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='asignacion_guia', verbose_name="Reserva Confirmada")
    guia = models.ForeignKey(GuiaTuristico, on_delete=models.CASCADE, verbose_name="Guía Asignado")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    notas_operaciones = models.TextField(blank=True, null=True, verbose_name="Notas de Operaciones")

    class Meta:
        verbose_name = "Asignación de Guía"
        verbose_name_plural = "Logística: Asignaciones de Guías"

    def clean(self):
        # 1. Validar que el guía esté activo en el sistema
        if not self.guia.esta_disponible:
            raise ValidationError(f"⚠️ El guía {self.guia.nombre} no está disponible para operaciones actualmente.")
        
        # 2. Validar que la reserva esté realmente confirmada
        if self.reserva.estado != 'CONFIRMADA':
            raise ValidationError("🛑 No se puede asignar un guía a una reserva que no esté en estado 'Confirmada'.")
            
        # 3. Validar doble asignación para la misma fecha (Concurrencia logística)
        # 🛠️ ALERTA OPERATIVA: Comparar con 'reserva__fecha' busca colisiones en el SEGUNDO exacto en que se compró la reserva.
        # Si se requiere por itinerario real, se debería mapear contra una 'fecha_viaje' del paquete. 
        # Dejamos la consulta optimizada excluyendo el registro actual.
        if self.reserva_id and self.guia_id:
            existe_cruce = AsignacionLogistica.objects.filter(
                guia=self.guia, 
                reserva__fecha=self.reserva.fecha
            ).exclude(id=self.id).exists()
            
            if existe_cruce:
                raise ValidationError(f"❌ Conflicto de Agenda: El guía {self.guia.nombre} ya tiene un grupo asignado para esa misma fecha/operación.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Fuerza la ejecución de clean() en la API y scripts de Django
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Guía {self.guia.nombre} -> Reserva #{self.reserva.id}"


# ==========================================
# ---      EDITORIAL Y COMUNIDAD         ---
# ==========================================

class PuntoDeInteres(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Revisión 🟡'),
        ('APROBADO', 'Aprobado (Público) 🟢'),
        ('RECHAZADO', 'Rechazado 🔴'),
        ('CAMBIOS', 'Requiere Cambios 🟠'),
    ]

    # 1. Datos de autoría y básicos
    proponente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Joya Oculta")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    
    # 2. Estructura de ubicación
    latitud = models.FloatField(verbose_name="Latitud", blank=True, null=True, help_text="Se captura automáticamente desde el mapa")
    longitud = models.FloatField(verbose_name="Longitud", blank=True, null=True, help_text="Se captura automáticamente desde el mapa")
    referencia_ubicacion = models.CharField(max_length=250, blank=True, null=True, verbose_name="¿Cómo llegar o dónde queda?")

    # 3. Flujo de moderación y fechas
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado Editorial")
    motivo_moderacion = models.TextField(blank=True, null=True, verbose_name="Feedback del Moderador")
    fecha_propuesta = models.DateTimeField(auto_now_add=True)

    # =========================================================================
    # 📌 ¡AQUÍ DEBES PONER CADA CAMBIO NUEVO QUE VENGA EN EL FUTURO!
    # =========================================================================
    CATEGORIAS_CHOICES = [
        ('Aventura', 'Aventura 🧗‍♂️'),
        ('Gastronomía', 'Gastronomía 🍲'),
        ('Cultural', 'Cultural 🏛️'),
        ('Naturaleza', 'Naturaleza 🌲'),
        ('Mirador', 'Mirador 📸'),
    ]
    categoria = models.CharField(
        max_length=50, 
        choices=CATEGORIAS_CHOICES, 
        default='Naturaleza', 
        verbose_name="Categoría"
    )
    
    # Ponlo justo debajo de tu campo 'categoria'
    imagen_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name="Enlace de la foto (URL)",
        help_text="Pega el link de una foto de internet (Ej: de Unsplash o Google Images)"
    )
    
    # 🆕 NUEVO: Campo para recibir archivos reales (fotos guardadas o de la cámara)
    imagen_archivo = models.ImageField(
        upload_to='joyas_fotos/', 
        blank=True, 
        null=True, 
        verbose_name="Archivo de imagen o Foto de Cámara"
    )

    # (Este lo dejo listo para la tarea T16/T17 de selección de POIs, no te preocupes todavía por él)
    usuarios_que_lo_visitan = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="pois_seleccionados", 
        blank=True,
        verbose_name="Turistas que planean ir"
    )
    
    # Ponlo al final de tus otros campos
    usuarios_favoritos = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="joyas_guardadas", 
        blank=True,
        verbose_name="Usuarios que guardaron esta joya"
    )
    
    # =========================================================================

    # 4. Configuraciones y Métodos (SIEMPRE AL FINAL DEL ARCHIVO)
    class Meta:
        verbose_name = "Joya Oculta (POI)"
        verbose_name_plural = "Joyas Ocultas (POIs)"
        ordering = ['-fecha_propuesta']

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

# Al final de tu archivo apps/inventory/models.py (o donde esté tu PuntoDeInteres)

class ImagenPOI(models.Model):
    # Conexión directa: Un POI tiene muchas imágenes. Si el POI se borra, sus fotos también.
    poi = models.ForeignKey(
        PuntoDeInteres, 
        on_delete=models.CASCADE, 
        related_name='imagenes_galeria', # 👈 Nombre clave para el ciclo en el HTML
        verbose_name="Punto de Interés"
    )
    # Aquí se guarda cada archivo de la tanda múltiple
    imagen = models.ImageField(
        upload_to='joyas_galeria/', 
        verbose_name="Foto de la Galería"
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagen de Galería"
        verbose_name_plural = "Imágenes de Galerías"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Foto para: {self.poi.nombre} (ID: {self.id})"
# ==========================================
# ---        LOGICA DE NEGOCIO           ---
# ==========================================

def procesar_reserva_segura(usuario, inventario_id):
    with transaction.atomic():
        inventario = InventarioHabitacion.objects.select_for_update().get(id=inventario_id)
        
        if inventario.cupo_disponible > 0:
            inventario.cupo_disponible -= 1
            inventario.save()
            
            reserva = Reserva.objects.create(
                usuario=usuario,
                habitacion_inventario=inventario,
                estado='CONFIRMADA'
            )
            return reserva
        else:
            raise ValidationError("¡Lo sentimos! Ya no quedan habitaciones disponibles para este paquete.")


@receiver(post_save, sender=Reserva)
def restituir_inventario_por_cancelacion(sender, instance, created, **kwargs):
    if not created and instance.estado == 'CANCELADA':
        with transaction.atomic():
            inventario = InventarioHabitacion.objects.select_for_update().get(id=instance.habitacion_inventario.id)
            if inventario.cupo_disponible < inventario.cupo_total:
                inventario.cupo_disponible += 1
                inventario.save()
                

class GuiaTuristico(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre Completo")
    idiomas = models.CharField(max_length=200, help_text="Ej: Español, Inglés, Francés")
    especialidad = models.CharField(max_length=100, help_text="Ej: Trekking, Alta Montaña, Histórico")
    esta_disponible = models.BooleanField(default=True, verbose_name="¿Está Activo/Disponible?")

    class Meta:
        verbose_name = "Guía Turístico"
        verbose_name_plural = "Guías Turísticos"

    def __str__(self):
        return f"{self.nombre} ({self.especialidad}) - Idiomas: {self.idiomas}"


class AsignacionLogistica(models.Model):
    # Nota: Usamos el objeto Reserva directamente en lugar del string 'Reserva' si está en el mismo archivo arriba.
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='asignacion_guia', verbose_name="Reserva Confirmada")
    guia = models.ForeignKey(GuiaTuristico, on_delete=models.CASCADE, verbose_name="Guía Asignado")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    notas_operaciones = models.TextField(blank=True, null=True, verbose_name="Notas de Operaciones")

    class Meta:
        verbose_name = "Asignación de Guía"
        verbose_name_plural = "Logística: Asignaciones de Guías"

    # --- VALIDACIÓN DE NEGOCIO EN EL MODELO ---
    def clean(self):
        # 🛠️ AJUSTE 1: Protección defensiva contra valores nulos antes de evaluar atributos
        if not self.guia_id or not self.reserva_id:
            return

        # 1. Validar que el guía esté activo en el sistema
        if not self.guia.esta_disponible:
            raise ValidationError(f"⚠️ El guía {self.guia.nombre} no está disponible para operaciones actualmente.")
        
        # 2. Validar que la reserva esté realmente confirmada
        # 🛠️ AJUSTE 2: Cambiado a upper() para tolerar tanto 'confirmada' como 'CONFIRMADA' según tu base de datos
        if self.reserva.estado.upper() != 'CONFIRMADA':
            raise ValidationError("🛑 No se puede asignar un guía a una reserva que no esté en estado 'Confirmada'.")
            
        # 3. Validar doble asignación para la misma fecha (Concurrencia logística)
        existe_cruce = AsignacionLogistica.objects.filter(
            guia=self.guia, 
            reserva__fecha=self.reserva.fecha
        ).exclude(id=self.id).exists()
        
        if existe_cruce:
            raise ValidationError(f"❌ Conflicto de Agenda: El guía {self.guia.nombre} ya tiene un grupo asignado en esa misma fecha.")

    def save(self, *args, **kwargs):
        self.full_clean() # Fuerza a Django a ejecutar el método clean() antes de guardar en la base de datos
        super().save(*args, **kwargs)

    def __str__(self):
        # Controlamos que no rompa si se visualiza un objeto mal creado o vacío
        reserva_id = self.reserva_id if self.reserva_id else "Sin ID"
        guia_nombre = self.guia.nombre if self.guia_id else "Sin Guía"
        return f"Guía {guia_nombre} -> Reserva #{reserva_id}"


# 🎟️ T29: MODELO DE PROMOCIONES Y DESCUENTOS
class Promocion(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código del Cupón (Ej: ADVENTURE20)")
    porcentaje_descuento = models.PositiveIntegerField(
        help_text="Porcentaje a restar, ej: 15 para 15% de descuento"
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Vencimiento")
    esta_activa = models.BooleanField(default=True, verbose_name="¿Cupón Activo?")

    class Meta:
        verbose_name = "Promoción / Cupón"
        verbose_name_plural = "Promociones / Cupones"

    @property
    def ha_vencido(self):
        return timezone.now() > self.fecha_fin

    def __str__(self):
        return f"{self.codigo} (-{self.porcentaje_descuento}%)"

# 💳 T26/T27/T28: MODELO DE COMPRA E HISTORIAL (El Simulador)
class CompraPaquete(models.Model):
    METODOS_PAGO = [
        ('simulado', 'Simulador de Saldo Turista 💸'),
        ('transferencia', 'Transferencia Bancaria (Validación Manual) 🏦'),
    ]
    
    turista = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compras')
    paquete = models.ForeignKey('Paquete', on_delete=models.PROTECT, related_name='reservas_hechas')
    promocion_aplicada = models.ForeignKey(Promocion, on_delete=models.SET_NULL, null=True, blank=True)
    
    cantidad_cupos = models.IntegerField(default=1)
    precio_unitario = models.FloatField(verbose_name="Precio Unitario")
    total_pagado = models.FloatField(verbose_name="Total Pagado")
    
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='simulado')
    codigo_transaccion = models.CharField(max_length=50, unique=True, help_text="Código único de comprobante")
    fecha_compra = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compra de Paquete"
        verbose_name_plural = "Compras de Paquetes"

    def __str__(self):
    #  ¡Listo! Con esto se arregla la vida
        return f"{self.turista.email} - {self.paquete.nombre} ({self.codigo_transaccion})"
    


# ==========================================
# ---        DESTINO                     ---
# ==========================================

class Destino(models.Model):
    TIPO_CHOICES = [
        ('urbano', 'Urbano 🏙️'),
        ('natural', 'Natural 🌲'),
        ('cultural', 'Cultural 🏛️'),
        ('gastronomico', 'Gastronómico 🍲'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre del Destino")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    ubicacion = models.CharField(max_length=250, blank=True, null=True, verbose_name="Ubicación General")
    
    # Manejo nativo de floats para el JS de mapas (Igual que en tus POIs)
    latitud = models.FloatField(verbose_name="Latitud", blank=True, null=True)
    longitud = models.FloatField(verbose_name="Longitud", blank=True, null=True)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='natural', verbose_name="Tipo de Destino")
    clima = models.CharField(max_length=100, verbose_name="Clima Predominante")
    esta_activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Destino Turístico"
        verbose_name_plural = "Destinos Turísticos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    # 🛡️ BLINDAJE DE SEGURIDAD (MÉTODO SOBREESCRITO)
    def delete(self, *args, **kwargs):
        # 1. Validar si tiene rutas activas vinculadas (ruta_set se genera automáticamente por el ForeignKey en Ruta)
        if hasattr(self, 'ruta_set') and self.ruta_set.filter(esta_activa=True).exists():
            raise ValidationError(
                f"No se puede eliminar el destino '{self.nombre}' porque está vinculado a una ruta activa."
            )
            
        # 2. Validar si está vinculado a algún paquete turístico (por si la relación es directa)
        if hasattr(self, 'paquete_set') and self.paquete_set.exists():
            raise ValidationError(
                f"No se puede eliminar el destino '{self.nombre}' porque forma parte de un paquete turístico."
            )

        # Si pasa las pruebas, borra normalmente (incluyendo sus ImagenDestino por su CASCADE)
        super().delete(*args, **kwargs)


class ImagenDestino(models.Model):
    destino = models.ForeignKey(
        Destino, 
        on_delete=models.CASCADE, 
        related_name='imagenes_galeria', # 👈 ¡Perfecto para el HTML que armamos!
        verbose_name="Destino Asociado"
    )
    imagen = models.ImageField(
        upload_to='destinos_galeria/', 
        verbose_name="Foto de la Galería"
    )
    fecha_subida = models.DateTimeField(auto_now_add=True) 

    class Meta:
        verbose_name = "Imagen de Destino"
        verbose_name_plural = "Imágenes de Destinos"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Foto para: {self.destino.nombre} (ID: {self.id})"
# ==========================================
# ---        RUTAS                       ---
# ==========================================
from django.core.exceptions import ValidationError

class Ruta(models.Model):
    # Relación existente
    destino = models.ForeignKey('Destino', on_delete=models.PROTECT, related_name='rutas', verbose_name="Destino Principal")
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Ruta")
    descripcion = models.TextField(verbose_name="Descripción del Recorrido", blank=True)
    duracion_estimada = models.PositiveIntegerField(verbose_name="Duración Total (Minutos)", help_text="Tiempo total estimado de la ruta", default=0) # 💡 editable=False hace que no se pueda modificar a mano en el admin
    
    # 🆕 NUEVOS CAMPOS PARA CUMPLIR EL CRITERIO 1 A RAJATABLA
    origen_logistico = models.CharField(max_length=200, verbose_name="Punto de Origen", default="Terminal Principal")
    destino_logistico = models.CharField(max_length=200, verbose_name="Punto de Destino Final", default="Punto Central")
    horario_salida = models.TimeField(verbose_name="Horario de Salida", null=True, blank=True)
    horario_retorno = models.TimeField(verbose_name="Horario de Retorno", null=True, blank=True)

    # Tu relación ManyToMany existente con through (T18)
    paradas = models.ManyToManyField(
        'PuntoDeInteres', 
        through='ParadaRuta', 
        related_name='rutas_que_lo_incluyen',
        verbose_name="Paradas de la Ruta"
    )
    
    esta_activa = models.BooleanField(default=True, verbose_name="¿Ruta Activa?")

    class Meta:
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"

    def __str__(self):
        return f"{self.nombre} ({self.origen_logistico} -> {self.destino_logistico})"

    def save(self, *args, **kwargs):
        # 🚀 CÁLCULO AUTOMÁTICO EN BACKEND
        if self.horario_salida and self.horario_retorno:
            # Convertimos las horas a minutos totales desde las 00:00
            minutos_salida = self.horario_salida.hour * 60 + self.horario_salida.minute
            minutos_retorno = self.horario_retorno.hour * 60 + self.horario_retorno.minute
            
            if minutos_retorno >= minutos_salida:
                self.duracion_estimada = minutos_retorno - minutos_salida
            else:
                # Caso especial: Rutas nocturnas que pasan de la medianoche
                self.duracion_estimada = (24 * 60 - minutos_salida) + minutos_retorno
        else:
            self.duracion_estimada = 0
            
        super().save(*args, **kwargs)
    
    # 🚨 CRITERIO 5: Interceptamos el borrado para proteger paquetes activos
    def delete(self, *args, **kwargs):
        # Buscamos en Paquete (atendiendo a que tu modelo Paquete tiene 'ruta = ForeignKey(...)')
        paquetes_activos = self.paquete_set.filter(esta_activo=True)
        if paquetes_activos.exists():
            nombres = ", ".join([p.nombre for p in paquetes_activos])
            raise ValidationError(
                f"No puedes eliminar esta ruta porque está vinculada a los paquetes activos: {nombres}."
            )
        super().delete(*args, **kwargs)


# Tu tabla intermedia se queda EXACTAMENTE IGUAL (T19, T17 intactos)
class ParadaRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='detalles_paradas')
    poi = models.ForeignKey('PuntoDeInteres', on_delete=models.CASCADE, verbose_name="Punto de Interés (Parada)")
    orden = models.PositiveIntegerField(
        verbose_name="Número de Parada", 
        help_text="Ej: 1 para la primera parada, 2 para la segunda, etc."
    )
    hora_llegada_estimada = models.TimeField(verbose_name="Hora de Llegada Estimada", blank=True, null=True)
    tiempo_permanencia = models.PositiveIntegerField(verbose_name="Tiempo de Estancia (Minutos)", default=30)

    class Meta:
        verbose_name = "Parada de Ruta"
        verbose_name_plural = "Paradas de la Ruta"
        unique_together = ('ruta', 'orden')
        ordering = ['orden']

    def __str__(self):
        return f"Parada {self.orden}: {self.poi.nombre} en {self.ruta.nombre}"


# 🆕 CRITERIO 3: Galería de imágenes múltiples para la Ruta (Igual que tus otros modelos)
class ImagenRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='imagenes_galeria')
    imagen_url = models.URLField(blank=True, null=True, help_text="Enlace de imagen externa")
    imagen_archivo = models.ImageField(upload_to='rutas/', blank=True, null=True, help_text="Archivo de imagen local")

    class Meta:
        verbose_name = "Imagen de Ruta"
        verbose_name_plural = "Galería de Imágenes de Rutas"