from django import forms
from .models import Usuario
from apps.inventory.models import PuntoDeInteres

class RegistroTuristaForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña segura'}), 
        label="Contraseña"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite tu contraseña'}), 
        label="Confirmar Contraseña"
    )
    
    PREFERENCIAS_CHOICES = [
        ('aventura', 'Montañismo y Aventura 🧗'),
        ('relax', 'Playas y Relajación 🏖️'),
        ('cultura', 'Museos y Cultura 🏛️'),
        ('gastronomia', 'Rutas Gastronómicas 🍜'),
    ]
    preferencias = forms.MultipleChoiceField(
        choices=PREFERENCIAS_CHOICES, 
        widget=forms.CheckboxSelectMultiple,
        label="¿Qué tipo de viaje prefieres?"
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email'] 
        error_messages = {
            'email': {
                'unique': "Este correo ya está en uso",
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bucle de Estilo Inteligente para Bootstrap 5
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "¡Las contraseñas no coinciden!")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        
        preferencias_seleccionadas = self.cleaned_data.get("preferencias", [])
        user.preferencias_json = {"intereses": preferencias_seleccionadas}
        
        if commit:
            user.save()
        return user
    

class EditarPerfilForm(forms.ModelForm):
    PREFERENCIAS_CHOICES = [
        ('aventura', 'Montañismo y Aventura 🧗'),
        ('relax', 'Playas y Relajación 🏖️'),
        ('cultura', 'Museos y Cultura 🏛️'),
        ('gastronomia', 'Rutas Gastronómicas 🍜'),
    ]
    preferencias = forms.MultipleChoiceField(
        choices=PREFERENCIAS_CHOICES, 
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Actualizar mis intereses de viaje"
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'pais_origen', 'foto_perfil']
        # CAMBIO AQUÍ: Forzamos la subida limpia para Bootstrap 5 sin textos de Django
        widgets = {
            'foto_perfil': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Bucle de Estilo Inteligente para Bootstrap 5
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        
        # 2. Cargar intereses previos en formato JSON
        if self.instance and self.instance.preferencias_json:
            intereses_previos = self.instance.preferencias_json.get('intereses', [])
            self.fields['preferencias'].initial = intereses_previos

    def save(self, commit=True):
        user = super().save(commit=False)
        user.preferencias_json = {"intereses": self.cleaned_data["preferencias"]}
        if commit:
            user.save()
        return user
    
class TuristaPOIForm(forms.ModelForm):
    class Meta:
        model = PuntoDeInteres
        # Al turista solo le pedimos estos 4 campos:
        fields = ['nombre','categoria','descripcion', 'referencia_ubicacion', 'latitud', 'longitud']
        widgets = {
            # Aquí ocultas la latitud y longitud en el HTML para que JS las llene con el mapa
            'latitud': forms.HiddenInput(),
            'longitud': forms.HiddenInput(),
        }
        

