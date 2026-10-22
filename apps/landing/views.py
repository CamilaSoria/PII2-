from django.shortcuts import render, redirect
from .forms import FormularioLanding  # El formulario con Tailwind que creamos
from apps.inventory.models import Paquete  # Apuntando correctamente a tu app core

def landing_page(request):
    if request.method == 'POST':
        form = FormularioLanding(request.POST)
        if form.is_valid():
            form.save()  # Guarda el LeadInformativo directamente en la BD
            return redirect('gracias')  # Redirige a la página de éxito (crearemos esta URL luego)
    else:
        form = FormularioLanding()
    
    # Traemos los paquetes activos de tu BD. 
    # Usamos .prefetch_related('pois') para que traiga las joyas ocultas eficientemente sin saturar la BD
    paquetes = Paquete.objects.filter(esta_activo=True).prefetch_related('pois')[:3] 
    
    context = {
        'form': form,
        'paquetes': paquetes
    }
    
    return render(request, 'landing/index.html', context)

def pagina_gracias(request):
    """Vista simple para mostrar un mensaje de éxito tras enviar el formulario"""
    return render(request, 'landing/gracias.html')