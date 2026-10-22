from django import forms
from django.contrib.auth import get_user_model
from apps.inventory.models import Paquete, PuntoDeInteres, Destino, ImagenDestino, Ruta, ParadaRuta, ImagenRuta, Hotel, TipoHabitacion, ServicioHotel, InventarioHabitacion
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.forms.widgets import FileInput

Usuario = get_user_model()

class AdminEditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PaqueteForm(forms.ModelForm):
    class Meta:
        model = Paquete
        fields = [
            'destino', 'ruta', 'nombre', 'descripcion', 
            'categoria', 'duracion_dias', 'precio_base', 
            'dificultad', 'cupos_totales', 'esta_activo' # 🪓 Eliminamos 'pois' de aquí
        ]
        

# 🧙‍♂️ Truco pro: Creamos un widget personalizado que hereda de FileInput
class MultiFileInput(forms.FileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        # Le inyectamos el atributo de forma forzada saltándonos su validación molesta
        self.attrs.update({'multiple': True})


class PuntoDeInteresForm(forms.ModelForm):
    # 🎯 Ahora sí, usamos nuestro widget modificado sin que rompa el server ni el HTML
    imagenes_multiples = forms.ImageField(
        widget=MultiFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        label="Subir Múltiples Imágenes / Fotos de la Cámara"
    )

    class Meta:
        model = PuntoDeInteres
        # ❌ Eliminamos 'referencia_ubicacion' de esta lista para el Agente
        fields = [
            'nombre', 
            'descripcion', 
            'categoria', 
            'latitud', 
            'longitud'
        ]
        # 🛠️ Quitamos el widget redundante y dejamos los necesarios limpios
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Mirador Principal'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe el atractivo...'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }


class MultiFileInput(forms.FileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({'multiple': True})

class DestinoForm(forms.ModelForm):
    imagenes_multiples = forms.ImageField(
        widget=MultiFileInput(attrs={
            'class': 'form-control text-secondary small',
            'accept': 'image/*'
        }),
        required=False,
        label="Subir Múltiples Imágenes para la Galería"
    )

    class Meta:
        model = Destino
        fields = ['nombre', 'descripcion', 'ubicacion', 'tipo', 'clima', 'esta_activo', 'latitud', 'longitud']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Islas Galápagos'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Breve descripción...'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad, Región o País'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'clima': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Templado'}),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        

class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['destino', 'nombre', 'descripcion', 'duracion_estimada', 'origen_logistico', 'destino_logistico', 'horario_salida', 'horario_retorno', 'esta_activa']
        widgets = {
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duracion_estimada': forms.NumberInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'}),
            'origen_logistico': forms.TextInput(attrs={'class': 'form-control'}),
            'destino_logistico': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_salida': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_retorno': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        horario_salida = cleaned_data.get('horario_salida')
        horario_retorno = cleaned_data.get('horario_retorno')

        # 🛡️ VALIDACIÓN 1: Evitar basura en las horas
        if horario_salida and horario_retorno:
            if horario_retorno <= horario_salida:
                # Si la ruta no está explícitamente marcada como nocturna en la descripción, alertamos
                raise ValidationError({
                    'horario_retorno': "La hora de retorno no puede ser anterior o igual a la hora de salida."
                })
        return cleaned_data

# Formset para las Paradas Intermedias (Aparecerán 3 filas para llenar POIs de golpe)
ParadaRutaFormSet = inlineformset_factory(
    Ruta, ParadaRuta,
    fields=['poi', 'orden', 'hora_llegada_estimada', 'tiempo_permanencia'],
    extra=0,  # Te pinta 3 bloques vacíos por defecto
    can_delete=True,
    widgets={
        'poi': forms.Select(attrs={'class': 'form-select'}),
        'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        'hora_llegada_estimada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        'tiempo_permanencia': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)

# Formset para las Imágenes de la Ruta
ImagenRutaFormSet = inlineformset_factory(
    Ruta, ImagenRuta,
    fields=['imagen_url', 'imagen_archivo'],
    extra=0,
    can_delete=True,
    widgets={
        'imagen_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'http://...'}),
        'imagen_archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
    }
)

class BaseParadaRutaFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return  # Si ya hay errores individuales, no seguimos

        ordenes = []
        pois = []

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            
            orden = form.cleaned_data.get('orden')
            poi = form.cleaned_data.get('poi')

            # 🛡️ VALIDACIÓN 2: Evitar órdenes duplicados (Ej: dos paradas con número 2)
            if orden in ordenes:
                raise ValidationError(f"No puedes asignar el número de parada '{orden}' a más de un punto de interés.")
            if orden:
                ordenes.append(orden)

            # 🛡️ VALIDACIÓN 3: Evitar el mismo POI dos veces en la misma ruta
            if poi in pois:
                raise ValidationError(f"El Punto de Interés '{poi.nombre}' ya ha sido agregado a esta ruta.")
            if poi:
                pois.append(poi)

# 1. Creamos un Select personalizado que guarde las coordenadas en las opciones
# En apps/gestion/forms.py
class POISelectConCoordenadas(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        
        if value:
            try:
                # 💡 Extrayemos el ID real si viene envuelto en un ModelChoiceIteratorValue
                poi_id = value.value if hasattr(value, 'value') else value
                
                # Ahora sí, el QuerySet recibirá el número limpio
                poi = PuntoDeInteres.objects.get(pk=poi_id)
                
                if poi.latitud and poi.longitud:
                    option['attrs']['data-lat'] = str(poi.latitud)
                    option['attrs']['data-lon'] = str(poi.longitud)
            except (PuntoDeInteres.DoesNotExist, ValueError, TypeError):
                # Protegemos por si viene un valor vacío o inválido (como el "---------")
                pass
        return option
# 2. Se lo aplicamos al FormSet de las paradas
class BaseParadaRutaFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        ordenes = []
        pois = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            orden = form.cleaned_data.get('orden')
            poi = form.cleaned_data.get('poi')
            
            if orden in ordenes:
                raise forms.ValidationError(f"No puedes asignar el número de parada '{orden}' a más de un punto.")
            if orden:
                ordenes.append(orden)
                
            if poi in pois:
                raise forms.ValidationError(f"El Punto de Interés '{poi.nombre}' ya está en esta ruta.")
            if poi:
                pois.append(poi)

ParadaRutaFormSet = forms.inlineformset_factory(
    Ruta, ParadaRuta,
    formset=BaseParadaRutaFormSet,
    fields=['poi', 'orden', 'hora_llegada_estimada', 'tiempo_permanencia'],
    extra=0,
    can_delete=True,
    widgets={
        # Aquí es donde se usa el selector corregido 👇
        'poi': POISelectConCoordenadas(attrs={'class': 'form-select select-poi-mapa'}), 
        'orden': forms.NumberInput(attrs={'class': 'form-control parada-orden', 'min': 1}),
        'hora_llegada_estimada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        'tiempo_permanencia': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)



#======================================================================================================= HOTELES 

# 1. Creamos el widget múltiple real que Django sí soporta sin quejarse

#======================================================================================================= HOTELES 

# 🟢 Reutilizamos la misma lógica limpia que usas en POIs y Destinos
class MultiFileInputHoteles(forms.FileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        # Usamos el booleano True idéntico a tus otros formularios funcionales
        self.attrs.update({'multiple': True})

class HotelForm(forms.ModelForm):
    # Usamos FileField con el método de limpieza manual para que no interfiera con el JS
    imagenes_multiples = forms.FileField(
        widget=MultiFileInputHoteles(attrs={
            'class': 'form-control text-secondary small',
            'accept': 'image/*'
        }),
        required=False,
        label="Galería de Fotos (Selecciona múltiples archivos)"
    )

    servicios = forms.ModelMultipleChoiceField(
        queryset=ServicioHotel.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Comodidades / Servicios Incluidos"
    )

    class Meta:
        model = Hotel
        # 🟢 Agregamos 'latitud' y 'longitud' justo después de la dirección
        fields = [
            'destino', 'nombre', 'direccion', 'latitud', 'longitud', 
            'descripcion', 'calificacion_estrellas', 'servicios', 'esta_activo'
        ]
        
        widgets = {
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Grand Hotel Central'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_direccion', 'placeholder': 'Ej. Av. Marítima 452 o haz clic en el mapa'}),
            
            # 🟢 Nuevos campos controlados con ID único para que tu JS los capture fácil y readonly para que no tipeen cualquiera
            'latitud': forms.TextInput(attrs={'class': 'form-control text-secondary bg-light font-monospace small', 'id': 'id_latitud', 'readonly': 'readonly', 'placeholder': 'Haz clic en el mapa...'}),
            'longitud': forms.TextInput(attrs={'class': 'form-control text-secondary bg-light font-monospace small', 'id': 'id_longitud', 'readonly': 'readonly', 'placeholder': 'Haz clic en el mapa...'}),
            
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Breve descripción...'}),
            'calificacion_estrellas': forms.Select(choices=[(i, f"{i} Estrella{'s' if i>1 else ''}") for i in range(1, 6)], attrs={'class': 'form-select'}),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    # Interceptamos la validación para que no choque con la bolsa virtual del JS
    def clean_imagenes_multiples(self):
        return self.files.getlist('imagenes_multiples')
    
# Formset dinámico de habitaciones
TipoHabitacionFormSet = inlineformset_factory(
    Hotel, TipoHabitacion,
    fields=['nombre', 'capacidad_personas', 'precio_por_noche'],
    extra=0,
    can_delete=True,
    widgets={
        'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Suite Matrimonial'}),
        'capacidad_personas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Ej. 2'}),
        'precio_por_noche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
    }
)
   
# Formset dinámico sin filas vacías obligatorias (las crearemos dinámicamente con JS)
TipoHabitacionFormSet = inlineformset_factory(
    Hotel, TipoHabitacion,
    fields=['nombre', 'capacidad_personas', 'precio_por_noche'],
    extra=0,  # 👈 Ponemos 0 para que el usuario añada filas solo cuando las necesite
    can_delete=True,
    widgets={
        'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Suite Matrimonial'}),
        'capacidad_personas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Ej. 2'}),
        'precio_por_noche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
    }
)

class MultiFileInput(forms.FileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({'multiple': True})

class PaqueteForm(forms.ModelForm):
    # 🎯 Usamos exactamente tu widget modificado que ya demostró que no da error
    imagenes_multiples = forms.ImageField(
        widget=MultiFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        label="Subir Múltiples Imágenes para el Paquete"
    )

    class Meta:
        model = Paquete
        # Sigue fielmente tu descarte de 'pois' del formulario principal
        fields = [
            'destino', 'ruta', 'nombre', 'descripcion', 
            'categoria', 'duracion_dias', 'precio_base', 
            'dificultad', 'cupos_totales', 'esta_activo'
        ]
        widgets = {
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'ruta': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Aventura Amazónica Completa'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Detalles del paquete turístico...'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'dificultad': forms.Select(attrs={'class': 'form-select'}),
            'cupos_totales': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }
        
HospedajeFormSet = inlineformset_factory(
    Paquete, 
    InventarioHabitacion,
    # 🎯 Solo exponemos 'habitacion' y 'cupo_total' al Agente
    fields=['habitacion', 'cupo_total'],  
    extra=1,
    can_delete=True,
    widgets={
        'habitacion': forms.Select(attrs={'class': 'form-select'}),
        'cupo_total': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Ej. 10'}),
    }
)