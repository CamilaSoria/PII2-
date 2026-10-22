from django import forms
from .models import Paquete

class PaqueteForm(forms.ModelForm):

    class Meta:
        model = Paquete
        # 🛠️ CORRECCIÓN CRÍTICA: Reemplaza 'precio' por 'precio_base'.
        # QUITA 'imagen_url' e 'imagen_archivo' de aquí, ya que se manejan en su propio formulario/inline de galería.
        fields = [
            'destino', 'ruta', 'nombre', 'descripcion', 
            'categoria', 'duracion_dias', 'precio_base', 
            'dificultad', 'cupos_totales', 'esta_activo', 'pois'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tu línea de inicialización para los POIs se queda exactamente igual:
        self.fields['pois'].widget.attrs.update({'class': 'form-select', 'size': '5'})