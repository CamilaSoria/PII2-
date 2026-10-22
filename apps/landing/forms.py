from django import forms
from .models import LeadInformativo
from apps.inventory.models import Paquete

class FormularioLanding(forms.ModelForm):
    class Meta:
        model = LeadInformativo
        # Los campos que el usuario completará en la Landing Page
        fields = [
            'nombre', 
            'apellido', 
            'email', 
            'telefono', 
            'paquete_interes', 
            'cantidad_personas', 
            'fecha_viaje_tentativa'
        ]
        
        # Le metemos un widget de tipo "date" para que salga el calendario nativo del navegador
        widgets = {
            'fecha_viaje_tentativa': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos para que en la landing solo aparezcan los paquetes que están disponibles/activos
        self.fields['paquete_interes'].queryset = Paquete.objects.filter(esta_activo=True)
        
        # Truco de ingeniería: Le inyectamos clases de Tailwind CSS a cada input automáticamente
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = (
                'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 '
                'focus:ring-blue-500 focus:border-transparent outline-none transition'
            )