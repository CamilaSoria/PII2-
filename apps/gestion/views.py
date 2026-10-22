from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import AdminEditarUsuarioForm
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from apps.inventory.models import PuntoDeInteres, Paquete, ImagenPOI, Destino, Ruta, Hotel, ImagenHotel, InventarioHabitacion, ServicioHotel, Temporada, ImagenPaquete
from .forms import PaqueteForm, PuntoDeInteresForm, DestinoForm, ImagenDestino
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# Asegúrate de importar tu modelo ImagenPOI aquí
from django.db.models.deletion import ProtectedError  # 👈 IMPORTANTE: Importa esto arriba
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from .forms import RutaForm, ParadaRutaFormSet, ImagenRutaFormSet,  HotelForm, TipoHabitacionFormSet, HospedajeFormSet
from django.utils import timezone


@staff_member_required
@require_POST
def eliminar_foto_galeria(request, foto_id):
    """ Borra una foto específica de la galería satélite """
    foto = get_object_or_404(ImagenPOI, id=foto_id)
    poi_id = foto.poi.id
    foto.delete()
    return JsonResponse({'success': True, 'message': 'Foto eliminada correctamente.'})

@staff_member_required
@require_POST
def asignar_portada_poi(request, poi_id, foto_id):
    """ Toma una foto de la galería satélite y la clona en el campo principal del POI """
    poi = get_object_or_404(PuntoDeInteres, id=poi_id)
    foto = get_object_or_404(ImagenPOI, id=foto_id, poi=poi)
    
    # Actualizamos el campo base del POI con el archivo físico de la foto satélite
    poi.imagen_archivo = foto.imagen
    poi.save()
    
    return JsonResponse({'success': True, 'message': 'Nueva portada asignada con éxito.'})

# --- CRUD DE PUNTOS DE INTERÉS (POIs) ---

Usuario = get_user_model()

class UsuariosListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Usuario
    context_object_name = 'usuarios'
    
    # Si usas AJAX dinámico en tiempo real, es mejor quitar o ampliar el paginado 
    # para que la búsqueda responda sobre la base completa.
    paginate_by = 100 

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_queryset(self):
        queryset = Usuario.objects.all().order_by('-id')
        buscar_texto = self.request.GET.get('search', '').strip()

        if buscar_texto:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar_texto) | 
                Q(email__icontains=buscar_texto)
            )
        return queryset

    def render_to_response(self, context, **response_kwargs):
        """
        🎯 Interceptamos la respuesta de Django.
        Si la cabecera indica que viene de nuestro JavaScript (Fetch),
        devolvemos ÚNICAMENTE las filas parciales.
        """
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.template_name = 'gestion/admin/partials/usuarios_table_rows.html'
        else:
            self.template_name = 'gestion/admin/usuarios_list.html'
            
        return super().render_to_response(context, **response_kwargs)
# --- 2. VISTA PARA EDITAR DATOS Y ROLES ---
class UsuarioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Usuario
    form_class = AdminEditarUsuarioForm
    template_name = 'gestion/admin/usuario_form.html'
    success_url = reverse_lazy('gestion:lista_usuarios')

    def test_func(self):
        return self.request.user.is_superuser  # Solo el mero jefe edita roles

    def form_valid(self, form):
        messages.success(self.request, f"Usuario {form.instance.email} actualizado con éxito.")
        return super().form_valid(form)


# --- 3. VISTA RÁPIDA PARA BANEAR / ACTIVAR ---
class AlternarEstadoUsuarioView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        
        # Evitar que el admin se banee a sí mismo
        if usuario == request.user:
            messages.error(request, "No puedes desactivar tu propia cuenta.")
            return redirect('gestion:lista_usuarios')

        # Switch lógico de estado
        usuario.is_active = not usuario.is_active
        usuario.save()

        estado = "activado" if usuario.is_active else "desactivado / baneado"
        messages.success(request, f"El usuario {usuario.email} ha sido {estado}.")
        return redirect('gestion:lista_usuarios')


@staff_member_required # <-- Seguridad: Solo empleados/admin de la agencia pueden entrar
def bandeja_moderacion(request):
    if request.method == 'POST':
        poi_id = request.POST.get('poi_id')
        nuevo_estado = request.POST.get('estado')
        feedback = request.POST.get('motivo_moderacion', '')

        # Buscamos el POI que se está moderando
        poi = get_object_or_404(PuntoDeInteres, id=poi_id)
        poi.estado = nuevo_estado
        poi.motivo_moderacion = feedback
        poi.save()

        return redirect('gestion:bandeja_moderacion')

    # Si es GET, traemos SOLO los que están 'PENDIENTE' o requieren 'CAMBIOS' (los que necesitan atención)
    # Ordenados por el más antiguo primero para atenderlos en orden de llegada
    pendientes = PuntoDeInteres.objects.filter(estado__in=['PENDIENTE']).order_by('fecha_propuesta')
    
    return render(request, 'gestion/moderador/bandeja_moderacion.html', {'pendientes': pendientes})

def administrar_paquetes(request):
    """
    Lista todos los paquetes y procesa la creación de uno nuevo mapeando los POIs automáticamente
    """
    paquetes = Paquete.objects.all().order_by('-id')
    
    if request.method == 'POST':
        # 📸 Agregamos request.FILES para soportar la subida de imágenes de la galería
        form = PaqueteForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardamos el paquete sin comprometer la base de datos todavía (commit=False)
            paquete = form.save(commit=False)
            paquete.save() # Guarda los campos directos primero
            
            # 🪄 AUTOMATIZACIÓN SPRINT 3: Si el paquete incluye una ruta, hereda sus POIs de forma nativa
            if paquete.ruta:
                pois_de_la_ruta = paquete.ruta.paradas.all()
                paquete.pois.set(pois_de_la_ruta) # Sincroniza la relación ManyToMany en segundo plano
            
            messages.success(request, "🎉 ¡Paquete turístico creado con éxito con sus paradas dinámicas!")
            return redirect('gestion:administrar_paquetes')
    else:
        form = PaqueteForm()
        
    return render(request, 'gestion/ventas/administrar_paquetes.html', {'paquetes': paquetes, 'form': form})


def editar_paquete(request, paquete_id):
    paquete = get_object_or_404(Paquete, id=paquete_id)
    tiene_reservas = False # Cambiar a True para testear el bloqueo ante el profesor
    
    if request.method == 'POST':
        if tiene_reservas:
            paquete.esta_activo = 'esta_activo' in request.POST
            paquete.save()
            messages.warning(request, "⚠️ El paquete tiene reservas activas. Solo se modificó su disponibilidad para proteger el historial de pagos.")
            return redirect('gestion:administrar_paquetes')
            
        # 📸 Corregido: Agregamos request.FILES para no perder imágenes al editar
        form = PaqueteForm(request.POST, request.FILES, instance=paquete)
        if form.is_valid():
            paquete = form.save()
            
            # 🪄 Re-sincronizamos los POIs por si el administrador cambió de ruta en la edición
            if paquete.ruta:
                paquete.pois.set(paquete.ruta.paradas.all())
            else:
                paquete.pois.clear()
                
            messages.success(request, "✏️ ¡Paquete actualizado correctamente!")
            return redirect('gestion:administrar_paquetes')
    else:
        form = PaqueteForm(instance=paquete)
        
    return render(request, 'gestion/editar_paquete.html', {'form': form, 'paquete': paquete, 'tiene_reservas': tiene_reservas})

def eliminar_paquete(request, paquete_id):
    if request.method == 'POST':
        paquete = get_object_or_404(Paquete, id=paquete_id)
        nombre = paquete.nombre
        paquete.delete()
        messages.success(request, f"🗑️ El paquete '{nombre}' fue eliminado del catálogo.")
    return redirect('gestion:administrar_paquetes')

@staff_member_required
def administrar_pois(request):
    pois = PuntoDeInteres.objects.all().order_by('-id')
    
    if request.method == 'POST':
        form = PuntoDeInteresForm(request.POST, request.FILES)
        if form.is_valid():
            poi = form.save(commit=False)
            poi.proponente = request.user
            
            # 🎯 Criterio 4: POIs creados por el Staff/Admin se aprueban de inmediato
            poi.estado = 'APROBADO' 
            
            # Capturamos la lista completa de archivos multimedia
            archivos = request.FILES.getlist('imagenes_multiples')
            if archivos:
                # Guardamos la primera como portada principal en el modelo base
                poi.imagen_archivo = archivos[0]
                
            poi.save() # Guardamos primero el POI para generar su ID
            
            # 📸 GUARDADO EN LA GALERÍA MÚLTIPLE (Modelo Satélite)
            if archivos:
                for archivo in archivos:
                    ImagenPOI.objects.create(poi=poi, imagen=archivo)
            
            # 🎯 Criterio 6: Confirmación explícita corregida para el Admin
            messages.success(request, f"🎉 POI '{poi.nombre}' creado y publicado con éxito. Ya está disponible para la venta y armado de rutas.")
            return redirect('gestion:administrar_pois')
    else:
        form = PuntoDeInteresForm()
        
    return render(request, 'gestion/ventas/administrar_pois.html', {'pois': pois, 'form': form})


@staff_member_required
def editar_poi(request, poi_id):
    poi = get_object_or_404(PuntoDeInteres, id=poi_id)
    
    # 💾 Guardamos el estado que tenía el POI justo antes de procesar el formulario
    estado_previo = poi.estado 
    
    if request.method == 'POST':
        form = PuntoDeInteresForm(request.POST, request.FILES, instance=poi)
        if form.is_valid():
            poi = form.save(commit=False)
            
            # 🎯 REGLA DE NEGOCIO CORREGIDA: 
            # Si el usuario es de tipo staff (Admin/Moderador), conservamos su estado actual (por si lo aprobó arriba).
            # Si en el futuro abres esta vista a guías o turistas, a ellos sí se les fuerza a 'PENDIENTE'.
            if request.user.is_staff:
                poi.estado = estado_previo
            else:
                poi.estado = 'PENDIENTE'
            
            archivos = request.FILES.getlist('imagenes_multiples')
            if archivos:
                # Actualiza la imagen de portada con el archivo en la posición 0 (ordenado por JS)
                poi.imagen_archivo = archivos[0]
                
            poi.save()
            
            # 📸 Añadimos las nuevas imágenes seleccionadas a su galería secundaria
            if archivos:
                for archivo in archivos:
                    ImagenPOI.objects.create(poi=poi, imagen=archivo)
            
            # 🎯 Mensajes de confirmación diferenciados según el estado final
            if poi.estado == 'APROBADO':
                messages.success(request, f"✅ Atractivo '{poi.nombre}' actualizado y publicado con éxito inmediatamente.")
            else:
                messages.warning(request, f"✏️ Atractivo '{poi.nombre}' guardado. Se mantiene en estado 'Pendiente de Revisión'.")
                
            return redirect('gestion:administrar_pois')
    else:
        form = PuntoDeInteresForm(instance=poi)
        
    return render(request, 'gestion/ventas/editar_poi.html', {'form': form, 'poi': poi})

@staff_member_required
def eliminar_poi(request, poi_id):
    if request.method == 'POST':
        poi = get_object_or_404(PuntoDeInteres, id=poi_id)
        
        # 🎯 Buscamos en Paquete los que estén activos y contengan este POI específico
        paquetes_vinculados_activos = Paquete.objects.filter(
            esta_activo=True, 
            pois=poi
        ).distinct()
        
        if paquetes_vinculados_activos.exists():
            nombres_paquetes = ", ".join([p.nombre for p in paquetes_vinculados_activos])
            messages.error(request, f"🚫 No se puede eliminar el POI '{poi.nombre}' porque está vinculado a los siguientes paquetes turísticos activos: {nombres_paquetes}.")
            return redirect('gestion:administrar_pois')
            
        nombre = poi.nombre
        poi.delete()
        
        messages.success(request, f"🗑️ El Punto de Interés '{nombre}' ha sido eliminado exitosamente.")
    return redirect('gestion:administrar_pois')


@staff_member_required
@require_POST
def eliminar_foto_galeria(request, foto_id):
    """ Borra una foto específica de la galería satélite """
    foto = get_object_or_404(ImagenPOI, id=foto_id)
    poi_id = foto.poi.id
    foto.delete()
    return JsonResponse({'success': True, 'message': 'Foto eliminada correctamente.'})

@staff_member_required
@require_POST
def asignar_portada_poi(request, poi_id, foto_id):
    """ Toma una foto de la galería satélite y la clona en el campo principal del POI """
    poi = get_object_or_404(PuntoDeInteres, id=poi_id)
    foto = get_object_or_404(ImagenPOI, id=foto_id, poi=poi)
    
    # Actualizamos el campo base del POI con el archivo físico de la foto satélite
    poi.imagen_archivo = foto.imagen
    poi.save()
    
    return JsonResponse({'success': True, 'message': 'Nueva portada asignada con éxito.'})

@staff_member_required
@require_POST
def alternar_estado_poi(request, poi_id):
    """ Permite al administrador aprobar o mandar a revisión un POI directamente """
    poi = get_object_or_404(PuntoDeInteres, id=poi_id)
    
    if poi.estado == 'APROBADO':
        poi.estado = 'PENDIENTE'
        nuevo_estado = 'PENDIENTE'
        mensaje = f"⚠️ El POI '{poi.nombre}' ha vuelto a estado Pendiente y ya no es visible para turistas."
    else:
        poi.estado = 'APROBADO'
        nuevo_estado = 'APROBADO'
        mensaje = f"✅ El POI '{poi.nombre}' ha sido aprobado y ya es visible en la plataforma."
        
    poi.save()
    return JsonResponse({
        'success': True, 
        'nuevo_estado': nuevo_estado,
        'message': mensaje
    })
    
#==========================================================================================================================DESTINO

class DestinoListView(ListView):
    model = Destino
    template_name = 'gestion/ventas/destino_lista.html'
    context_object_name = 'destinos'

class DestinoCreateView(CreateView):
    model = Destino
    form_class = DestinoForm
    template_name = 'gestion/ventas/destino_form.html'
    success_url = reverse_lazy('gestion:destino_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Extraer la ráfaga (el índice 0 ya viene ordenado como portada por tu JS)
        imagenes = self.request.FILES.getlist('imagenes_multiples')
        
        for img in imagenes:
            ImagenDestino.objects.create(
                destino=self.object,
                imagen=img
            )
        messages.success(self.request, f"Destino '{self.object.nombre}' publicado con éxito.")
        return response

class DestinoUpdateView(UpdateView):
    model = Destino
    form_class = DestinoForm
    template_name = 'gestion/ventas/destino_form.html'
    success_url = reverse_lazy('gestion:destino_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        imagenes = self.request.FILES.getlist('imagenes_multiples')
        
        if imagenes:
            for img in imagenes:
                ImagenDestino.objects.create(
                    destino=self.object,
                    imagen=img
                )
        messages.success(self.request, f"Cambios en '{self.object.nombre}' actualizados correctamente.")
        return response

class DestinoDeleteView(DeleteView):
    model = Destino
    template_name = 'gestion/ventas/destino_confirm_delete.html'
    success_url = reverse_lazy('gestion:destino_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # 1. Tu validación manual actual (Sigue funcionando excelente para filtrar los ACTIVOS)
        tiene_rutas_activas = self.object.rutas.filter(esta_activa=True).exists()
        tiene_paquetes_activos = self.object.paquetes_asociados.filter(esta_activo=True).exists()

        if tiene_rutas_activas or tiene_paquetes_activos:
            messages.error(
                request, 
                f"🚨 No se puede eliminar '{self.object.nombre}'. Está vinculado a rutas o paquetes turísticos activos."
            )
            return redirect('gestion:destino_list')
        
        # 2. 🛡️ EL ESCUDO TRY/EXCEPT: Por si la base de datos salta por registros inactivos protegidos
        try:
            self.object.delete()
            messages.success(request, "🗑️ El destino ha sido eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request, 
                f"⚠️ Error de integridad: No se puede eliminar '{self.object.nombre}' porque existen registros históricos (rutas/paquetes) vinculados que la base de datos protege."
            )
        
        return redirect(self.get_success_url())

@require_POST
def eliminar_foto_destino(request, foto_id):
    """Elimina una foto específica de la galería de destinos mediante AJAX"""
    foto = get_object_or_404(ImagenDestino, id=foto_id)
    foto.delete()
    return JsonResponse({'success': True, 'message': 'Imagen eliminada correctamente.'})

@require_POST
def reordenar_portada_destino(request, destino_id, foto_id):
    """
    Hace que la foto seleccionada sea la 'portada' alterando su fecha de subida,
    colocándola al principio de la cola debido al 'ordering = [-fecha_subida]'
    """
    destino = get_object_or_404(Destino, id=destino_id)
    foto_elegida = get_object_or_404(ImagenDestino, id=foto_id, destino=destino)
    
    from django.utils import timezone
    foto_elegida.fecha_subida = timezone.now()
    foto_elegida.save()
    
    return JsonResponse({'success': True, 'message': 'Nueva portada asignada con éxito.'})



#==========================================================================================================================RUTAS

class RutaListView(ListView):
    model = Ruta
    template_name = 'gestion/ventas/ruta_list.html'
    context_object_name = 'rutas'

class RutaCreateView(SuccessMessageMixin, CreateView):
    model = Ruta
    form_class = RutaForm
    template_name = 'gestion/ventas/ruta_form.html'
    success_url = reverse_lazy('gestion:ruta_list')
    success_message = "¡La ruta turística ha sido creada con éxito!" # Criterio 6

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['paradas'] = ParadaRutaFormSet(self.request.POST, instance=self.object)
            data['imagenes'] = ImagenRutaFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            data['paradas'] = ParadaRutaFormSet(instance=self.object)
            data['imagenes'] = ImagenRutaFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        paradas = context['paradas']
        imagenes = context['imagenes']
        if form.is_valid() and paradas.is_valid() and imagenes.is_valid():
            self.object = form.save()
            paradas.instance = self.object
            paradas.save()
            imagenes.instance = self.object
            imagenes.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RutaUpdateView(SuccessMessageMixin, UpdateView):
    model = Ruta
    form_class = RutaForm
    template_name = 'gestion/ventas/ruta_form.html'
    success_url = reverse_lazy('gestion:ruta_list')
    success_message = "¡La ruta turística fue modificada correctamente!" # Criterio 4 y 6

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['paradas'] = ParadaRutaFormSet(self.request.POST, instance=self.object)
            data['imagenes'] = ImagenRutaFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            data['paradas'] = ParadaRutaFormSet(instance=self.object)
            data['imagenes'] = ImagenRutaFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        paradas = context['paradas']
        imagenes = context['imagenes']
        if form.is_valid() and paradas.is_valid() and imagenes.is_valid():
            self.object = form.save()
            paradas.instance = self.object
            paradas.save()
            imagenes.instance = self.object
            imagenes.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RutaDeleteView(DeleteView):
    model = Ruta
    template_name = 'gestion/ventas/ruta_confirm_delete.html'
    success_url = reverse_lazy('gestion:ruta_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, "¡Ruta eliminada permanentemente!") # Criterio 6
            return redirect(self.success_url)
        except ValidationError as e:
            # Captura el error del Criterio 5 y manda el mensaje al HTML en vez de romper la app
            messages.error(request, e.message)
            return redirect('gestion:ruta_list')
    

#================================================================== HOTELES 

# 1. LISTADO DE HOTELES
class HotelListView(ListView):
    model = Hotel
    template_name = 'gestion/ventas/hotel_list.html'
    context_object_name = 'hoteles'

# 2. CREAR HOTEL
# 2. CREAR HOTEL (CORREGIDO)
import sys

class HotelCreateView(SuccessMessageMixin, CreateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'gestion/ventas/hotel_form.html'
    success_url = reverse_lazy('gestion:hotel_list')
    success_message = "Hotel creado exitosamente."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = TipoHabitacionFormSet(self.request.POST)
        else:
            data['formset'] = TipoHabitacionFormSet()
        return data

    def post(self, request, *args, **kwargs):
        # 🟢 EL PARCHE OBLIGATORIO DE DJANGO: Inicializamos el objeto vacío para evitar el AttributeError
        self.object = None  

        print("\n" + "="*60, file=sys.stderr)
        print("🚨 --- INICIO DE DEPURACIÓN DE DETECCIÓN MULTIMEDIA --- 🚨", file=sys.stderr)
        print(f"DATOS RECIBIDOS EN POST: {request.POST}", file=sys.stderr)
        print(f"ARCHIVOS RECIBIDOS EN FILES: {request.FILES}", file=sys.stderr)
        print(f"¿'imagenes_multiples' está en FILES?: {'imagenes_multiples' in request.FILES}", file=sys.stderr)
        
        lista_fotos = request.FILES.getlist('imagenes_multiples')
        print(f"Cantidad de fotos detectadas por getlist: {len(lista_fotos)}", file=sys.stderr)
        for idx, f in enumerate(lista_fotos):
            print(f" -> Foto [{idx}]: Nombre={f.name}, Tamaño={f.size} bytes", file=sys.stderr)

        form = self.get_form()
        formset = TipoHabitacionFormSet(self.request.POST)

        form_ok = form.is_valid()
        formset_ok = formset.is_valid()
        
        print(f"¿Formulario de Hotel es Válido?: {form_ok}", file=sys.stderr)
        if not form_ok:
            print(f"❌ ERRORES DEL HOTEL: {form.errors.as_json()}", file=sys.stderr)
            
        print(f"¿Formset de Habitaciones es Válido?: {formset_ok}", file=sys.stderr)
        if not formset_ok:
            print(f"❌ ERRORES DEL FORMSET: {formset.errors}", file=sys.stderr)
            
        print("="*60 + "\n", file=sys.stderr)

        if form_ok and formset_ok:
            return self.form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        self.object = form.save()
        formset.instance = self.object
        formset.save()
        
        imagenes = self.request.FILES.getlist('imagenes_multiples')
        for i, img in enumerate(imagenes):
            ImagenHotel.objects.create(
                hotel=self.object,
                imagen_archivo=img,
                es_principal=(i == 0)
            )
        return super().form_valid(form)

# 3. EDITAR HOTEL (CORREGIDO)
# 3. EDITAR HOTEL (SOLUCIÓN COMPLETA PARA PORTADAS)
class HotelUpdateView(SuccessMessageMixin, UpdateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'gestion/ventas/hotel_form.html'
    success_url = reverse_lazy('gestion:hotel_list')
    success_message = "El hotel y sus servicios fueron modificados correctamente."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = TipoHabitacionFormSet(self.request.POST, instance=self.object)
        else:
            data['formset'] = TipoHabitacionFormSet(instance=self.object)
        return data

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = TipoHabitacionFormSet(self.request.POST, instance=self.object)
        
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # 1. Guardamos los cambios de los campos de texto del hotel y habitaciones
        self.object = form.save()
        formset.save()
        
        # 2. Procesamos las NUEVAS imágenes que se subieron en este envío (si las hay)
        imagenes = self.request.FILES.getlist('imagenes_multiples')
        
        # Guardamos la referencia de si el hotel ya cuenta con alguna portada asignada previamente
        tiene_portada = self.object.imagenes.filter(es_principal=True).exists()
        
        for i, img in enumerate(imagenes):
            ImagenHotel.objects.create(
                hotel=self.object, 
                imagen_archivo=img,
                # 🛡️ Solo se marca como principal la primera foto si el hotel está completamente vacío de portadas
                es_principal=(not tiene_portada and i == 0) 
            )
            if not tiene_portada and i == 0:
                tiene_portada = True

        # 3. ¡EL PARCHE CLAVE! Re-verificamos la base de datos antes de terminar la petición 
        # para garantizar que la sesión conserve la bandera True en la imagen que coronó el JS.
        # Si por alguna razón el guardado del formulario reseteó los booleanos, esto lo reestablece:
        portada_actual = self.object.imagenes.filter(es_principal=True).first()
        if not portada_actual:
            # Si se quedó sin portada por el guardado, agarramos la primera que exista para que no quede vacía
            primera_foto = self.object.imagenes.first()
            if primera_foto:
                primera_foto.es_principal = True
                primera_foto.save()

        return super().form_valid(form)

# 4. ELIMINAR HOTEL (Con protección estricta del Criterio 5)
class HotelDeleteView(DeleteView):
    model = Hotel
    template_name = 'gestion/ventas/hotel_confirm_delete.html'
    success_url = reverse_lazy('gestion:hotel_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object_name()
        hotel = self.object

        # 🛡️ Control de paquetes comerciales activos del Sprint 2
        paquetes_activos = InventarioHabitacion.objects.filter(
            habitacion__hotel=hotel,
            paquete__esta_activo=True
        ).exists()

        if paquetes_activos:
            messages.error(
                request, 
                f"Acción denegada: El hotel '{hotel.nombre}' tiene habitaciones asignadas a paquetes turísticos que están activos."
            )
            return redirect('gestion:hotel_list')

        messages.success(request, f"El hotel '{hotel.nombre}' ha sido eliminado.") # Criterio 6
        return super().delete(request, *args, **kwargs)

# 5. ELIMINACIÓN ASÍNCRONA DE FOTOS DE LA GALERÍA (Mismo comportamiento que POIs)
def eliminar_foto_hotel(request, foto_id):
    if request.method == "POST" or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        foto = get_object_or_404(ImagenHotel, id=foto_id)
        foto.delete()
        return JsonResponse({"status": "success", "message": "Foto eliminada de la galería."})
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=400)

# En tu views.py de Hoteles:
def asignar_portada_hotel(request, hotel_id, foto_id):
    if request.method == "POST" or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        # Ponemos todas las fotos del hotel en False
        hotel.imagenes.update(es_principal=False)
        # Marcamos la elegida como principal
        foto = get_object_or_404(ImagenHotel, id=foto_id, hotel=hotel)
        foto.es_principal = True
        foto.save()
        return JsonResponse({"status": "success", "message": "Nueva foto de portada establecida."})
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=400)



#================================================================== SERVICIOS

    
# 1. LISTAR los servicios para ver qué limpiar
class ServicioHotelListView(ListView):
    model = ServicioHotel
    template_name = 'gestion/ventas/servicio_list.html'
    context_object_name = 'servicios'

# 2. CREAR un servicio
class ServicioHotelCreateView(SuccessMessageMixin, CreateView):
    model = ServicioHotel
    fields = ['nombre', 'icono']
    template_name = 'gestion/ventas/servicio_form.html'
    success_message = "¡El servicio '%(nombre)s' fue añadido con éxito!"
    success_url = reverse_lazy('gestion:servicio_list') # Te manda a la lista para que lo veas

# 3. EDITAR (Por si escribiste una cochinada)
class ServicioHotelUpdateView(SuccessMessageMixin, UpdateView):
    model = ServicioHotel
    fields = ['nombre', 'icono']
    template_name = 'gestion/ventas/servicio_form.html'
    success_message = "¡Servicio actualizado correctamente!"
    success_url = reverse_lazy('gestion:servicio_list')

# 4. ELIMINAR (Para borrar la cochinada para siempre)
class ServicioHotelDeleteView(DeleteView):
    model = ServicioHotel
    template_name = 'gestion/ventas/servicio_confirm_delete.html'
    success_url = reverse_lazy('gestion:servicio_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "El servicio fue eliminado del sistema.")
        return super().delete(request, *args, **kwargs)



#================================================================== temporadas

def gestion_temporadas(request, pk=None):
    hoy = timezone.now().date()
    temporadas = Temporada.objects.all().order_by('fecha_inicio')
    
    # Si viene un PK, estamos en modo EDICIÓN
    temporada_editar = None
    if pk:
        temporada_editar = get_object_or_404(Temporada, pk=pk)
        # Criterio 6: Si intenta editar una activa o pasada por URL, bloquear
        if temporada_editar.fecha_inicio <= hoy:
            messages.error(request, "🚨 No puedes editar una temporada en curso o pasada.")
            return redirect('gestion:gestion_temporadas')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        condicion_climatica = request.POST.get('condicion_climatica')
        factor_precio = request.POST.get('factor_precio')
        
        if temporada_editar:
            # Actualizar instancia existente
            temporada_editar.nombre = nombre
            temporada_editar.fecha_inicio = fecha_inicio
            temporada_editar.fecha_fin = fecha_fin
            temporada_editar.condicion_climatica = condicion_climatica
            temporada_editar.factor_precio = factor_precio
            obj_guardar = temporada_editar
        else:
            # Crear nueva instancia
            obj_guardar = Temporada(
                nombre=nombre, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                condicion_climatica=condicion_climatica, factor_precio=factor_precio
            )
        
        try:
            obj_guardar.full_clean()
            obj_guardar.save()
            messages.success(request, f"✨ ¡Éxito! La temporada '{nombre}' se guardó correctamente.")
            return redirect('gestion:gestion_temporadas')
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors: messages.error(request, f"❌ {error}")
            else:
                for error in e.messages: messages.error(request, f"❌ {error}")

    return render(request, 'gestion/ventas/gestion_temporadas.html', {
        'temporadas': temporadas,
        'hoy': hoy,
        'climas': Temporada.CLIMA_CHOICES,
        'temporada_editar': temporada_editar  # Pasa el objeto si se va a editar
    })

def eliminar_temporada(request, pk):
    temporada = get_object_or_404(Temporada, pk=pk)
    try:
        temporada.delete()
        messages.success(request, "🗑️ La temporada fue eliminada con éxito.")
    except ValidationError as e:
        messages.error(request, f"{e.message}")
    return redirect('gestion:gestion_temporadas')

#================================================================== PAQUETES

# 📋 1. VISTA DE LISTADO DE PAQUETES
class PaqueteListView(ListView):
    model = Paquete
    template_name = 'gestion/ventas/paquete_lista.html'
    context_object_name = 'paquetes'


# ✨ 2. VISTA DE CREACIÓN DE PAQUETE
class PaqueteCreateView(CreateView):
    model = Paquete
    form_class = PaqueteForm
    template_name = 'gestion/ventas/paquete_form.html'
    success_url = reverse_lazy('inventory:lista_paquetes')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['hospedaje_formset'] = HospedajeFormSet(self.request.POST)
        else:
            data['hospedaje_formset'] = HospedajeFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hospedaje_formset = context['hospedaje_formset']
        
        if hospedaje_formset.is_valid():
            # Guardamos el paquete base
            self.object = form.save()
            
            # Automatización: Heredar paradas (POIs) de la ruta elegida
            if self.object.ruta:
                self.object.pois.set(self.object.ruta.paradas.all())
            
            # Guardar el Formset de Hospedaje asignando cupos automáticos
            hospedajes = hospedaje_formset.save(commit=False)
            for hosp in hospedajes:
                hosp.paquete = self.object
                hosp.cupo_disponible = hosp.cupo_total  # El disponible arranca igual al total
                hosp.save()
            hospedaje_formset.save_m2m()
            
            # Guardar ráfaga de imágenes múltiples
            imagenes = self.request.FILES.getlist('imagenes_multiples')
            for img in imagenes:
                ImagenPaquete.objects.create(paquete=self.object, imagen=img)
                
            messages.success(self.request, f"🚀 Paquete '{self.object.nombre}' publicado con éxito con su ruta e inventario.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


# 🔄 3. VISTA DE EDICIÓN DE PAQUETE
class PaqueteUpdateView(UpdateView):
    model = Paquete
    form_class = PaqueteForm
    template_name = 'gestion/ventas/paquete_form.html'
    success_url = reverse_lazy('gestion:lista_paquetes')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['hospedaje_formset'] = HospedajeFormSet(self.request.POST, instance=self.object)
        else:
            data['hospedaje_formset'] = HospedajeFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        hospedaje_formset = context['hospedaje_formset']
        
        if hospedaje_formset.is_valid():
            self.object = form.save()
            
            # Sincronizar POIs por si la ruta cambió en la edición
            if self.object.ruta:
                self.object.pois.set(self.object.ruta.paradas.all())
                
            hospedaje_formset.save()
            
            # Guardar nuevas fotos si se añadieron en la edición
            imagenes = self.request.FILES.getlist('imagenes_multiples')
            for img in imagenes:
                ImagenPaquete.objects.create(paquete=self.object, imagen=img)
                
            messages.success(self.request, f"Cambios en el paquete '{self.object.nombre}' actualizados correctamente.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


# 🗑️ 4. VISTA DE ELIMINACIÓN DE PAQUETE (Protección contra reservas activas)
class PaqueteDeleteView(DeleteView):
    model = Paquete
    success_url = reverse_lazy('gestion:lista_paquetes')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Validación contra reservas vivas del Sprint 3 antes de borrar
        tiene_reservas_activas = self.object.reservas_asociadas.filter(
            estado_pago__in=['PENDIENTE', 'CONFIRMADA']
        ).exists()

        if tiene_reservas_activas:
            messages.error(
                request, 
                f"🚨 No se puede eliminar '{self.object.nombre}'. Cuenta con reservas activas o pendientes de pago en este momento."
            )
            return redirect('gestion:lista_paquetes')
        
        try:
            self.object.delete()
            messages.success(request, "🗑️ El paquete turístico y su galería se eliminaron correctamente.")
        except ProtectedError:
            messages.error(
                request, 
                f"⚠️ Error de integridad: No se puede borrar '{self.object.nombre}' por arrastre de registros históricos en la base de datos."
            )
        
        return redirect(self.get_success_url())


# 📸 5. ACCIÓN AJAX: ELIMINAR FOTO DE LA GALERÍA
@require_POST
def eliminar_foto_paquete(request, foto_id):
    foto = get_object_or_404(ImagenPaquete, id=foto_id)
    foto.delete()
    return JsonResponse({
        'success': True, 
        'message': '📸 Imagen del paquete eliminada correctamente.'
    })


# 👑 6. ACCIÓN AJAX: REORDENAR/ASIGNAR PORTADA
@require_POST
def asignar_portada_paquete(request, paquete_id, foto_id):
    paquete = get_object_or_404(Paquete, id=paquete_id)
    foto_elegida = get_object_or_404(ImagenPaquete, id=foto_id, paquete=paquete)
    
    # Mutamos la fecha para mandarla al principio de la fila por ordenamiento invertido
    foto_elegida.fecha_subida = timezone.now()
    foto_elegida.save()
    
    return JsonResponse({
        'success': True, 
        'message': '👑 Nueva portada del paquete asignada con éxito.'
    })