from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
# Manejo de tokens con límite de tiempo
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.contrib import messages  # <-- ¡ASEGÚRATE DE TENER ESTE IMPORT ARRIBA!
from .forms import TuristaPOIForm, PuntoDeInteres  

#Importaciones de modelos desde juera
from apps.inventory.models import Paquete, CompraPaquete

# Formularios y Modelos locales
from .forms import RegistroTuristaForm, EditarPerfilForm
from django.utils import timezone  # <-- ¡OBLIGATORIO para manejar fechas!
from datetime import timedelta     # <-- ¡OBLIGATORIO para sumar los 15 minutos!
from .models import Usuario


# Importamos el modelo de Reserva real desde la app de bookings
from apps.bookings.models import Reserva 
from django.db.models import Q
from apps.inventory.models import PuntoDeInteres
import math

from django.http import JsonResponse
# Inicializamos el firmador temporal seguro (Usa este para registro y activación)
signer = TimestampSigner()



def login_usuario(request):
    mensaje_error = None
    
    if request.method == 'POST':
        email_ingresado = request.POST.get('email')
        password_ingresado = request.POST.get('password')
        
        try:
            usuario = Usuario.objects.get(email=email_ingresado)
            
            # 1. VERIFICAR SI ESTÁ BLOQUEADO ACTUALMENTE
            if usuario.bloqueado_hasta and timezone.now() < usuario.bloqueado_hasta:
                tiempo_restante = usuario.bloqueado_hasta - timezone.now()
                minutos = int(tiempo_restante.total_seconds() // 60) + 1
                mensaje_error = f"Tu cuenta está bloqueada. Intenta de nuevo en {minutos} minutos."
                return render(request, 'authentication/login.html', {'error': mensaje_error})
                
        except Usuario.DoesNotExist:
            usuario = None

        # 2. INTENTAR AUTENTICAR
        user_autenticado = authenticate(request, email=email_ingresado, password=password_ingresado)
        
        if user_autenticado is not None:
            # Si el usuario está inactivo (no verificado por correo)
            if not user_autenticado.is_active:
                mensaje_error = "Tu cuenta aún no está activa. Revisa tu correo de verificación."
                return render(request, 'authentication/login.html', {'error': mensaje_error})

            # ¡Éxito real! Reseteamos todo
            user_autenticado.intentos_fallidos = 0
            user_autenticado.bloqueado_hasta = None
            user_autenticado.save()
            
            # Iniciamos la sesión
            auth_login(request, user_autenticado)
            
            # 🔀 ¡AQUÍ ESTÁ LA MAGIA DE LA REDIRECCIÓN INTELIGENTE!
            if user_autenticado.is_superuser or user_autenticado.is_staff:
                # Si es Admin, Agente o Moderador, se va al nuevo panel de gestión
                return redirect('gestion:lista_usuarios')
            else:
                # Si es un turista común, se va a su dashboard clásico
                return redirect('authentication:dashboard')
        else:
            # 3. EL INGRESO FALLÓ
            if usuario:
                usuario.intentos_fallidos += 1
                
                if usuario.intentos_fallidos >= 3:
                    usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                    mensaje_error = "Has fallado 3 veces. Tu acceso ha sido bloqueado por 15 minutos."
                else:
                    intentos_restantes = 3 - usuario.intentos_fallidos
                    mensaje_error = f"Contraseña incorrecta. Te quedan {intentos_restantes} intentos."
                
                usuario.save()
            else:
                mensaje_error = "Credenciales inválidas."
                
    return render(request, 'authentication/login.html', {'error': mensaje_error})

@login_required 
def dashboard(request):
    # 🛠️ OPTIMIZADO: Filtramos los activos y precargamos las imágenes para evitar lentitud
    paquetes_inventario = Paquete.objects.filter(esta_activo=True).prefetch_related('imagenes_galeria').order_by('-id')[:4]
    
    # Se los pasamos a la plantilla en el contexto
    return render(request, 'authentication/dashboard.html', {
        'usuario': request.user,
        'paquetes': paquetes_inventario  # <-- Mantiene vivo tu {% for p in paquetes %}
    })

def registro_turista(request):
    if request.method == 'POST':
        form = RegistroTuristaForm(request.POST)
        if form.is_valid():
            # 1. Guardamos el usuario desactivado
            usuario = form.save(commit=False)
            usuario.is_active = False  # Bloqueado hasta que verifique
            usuario.save()
            
            # --- NUEVA LÓGICA DE TOKEN ENLAZADO ---
            # Generamos el token seguro basado en su email
            token = signer.sign(usuario.email)
            
            # Construimos la URL usando el namespace 'authentication' de forma dinámica
            ruta_activacion = reverse('authentication:activar_cuenta', kwargs={'token': token})
            enlace_activacion = request.build_absolute_uri(ruta_activacion)
            # --------------------------------------
            
            # 2. Envío del email de verificación real
            asunto = 'Verifica tu cuenta - Proyecto Integrador'
            
            # Ajustado para usar usuario.nombre (ya que no manejas campo username)
            mensaje = (
                f'Hola {usuario.nombre},\n\n'  
                f'Por favor verifica tu cuenta haciendo clic en el siguiente enlace:\n'
                f'{enlace_activacion}\n\n'
                f'Si no solicitaste este registro, puedes ignorar este correo.'
            )
            
            email_desde = settings.DEFAULT_FROM_EMAIL
            email_para = [usuario.email]
            
            try:
                # Pon esto justo antes del send_mail para saltarte cualquier problema de backend
                send_mail(asunto, mensaje, email_desde, email_para, fail_silently=False)
            except Exception:
                # Fallback por si el servidor de correo no está configurado en desarrollo
                pass

            # 3. Redirección obligatoria según tu Criterio de Aceptación
            return redirect('authentication:verificacion_pendiente') 
    else:
        form = RegistroTuristaForm()
    
    return render(request, 'authentication/registro.html', {'form': form})


def verificacion_pendiente(request):
    # Vista simple que renderiza la plantilla de "Revisa tu correo"
    return render(request, 'authentication/verificacion_pendiente.html')


@login_required
def perfil_turista(request):
    usuario = request.user
    
    if request.method == 'POST':
        # CAMBIO AQUÍ: Se añade request.FILES para recibir la imagen del formulario
        form = EditarPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            # Corregido: Se añade el namespace para evitar NoReverseMatch
            return redirect('authentication:perfil')
    else:
        form = EditarPerfilForm(instance=usuario)

    # --- CONSULTA REAL A LA BASE DE DATOS (Historias 2 y 3) ---
    # 1. Traemos las reservas del usuario actual que estén PENDIENTES o CONFIRMADAS
    reservas_reales = Reserva.objects.filter(
        usuario=usuario, 
        estado_pago__in=['PENDIENTE', 'CONFIRMADA']
    ).order_by('-fecha_viaje')
    
    # 2. Traemos las reservas que ya fueron CANCELADAS
    reservas_historicas = Reserva.objects.filter(
        usuario=usuario, 
        estado_pago='CANCELADA'
    ).order_by('-fecha_viaje')

    # Enviamos las variables al HTML perfectamente coordinadas
    return render(request, 'authentication/perfil.html', {
        'form': form,
        'usuario': usuario,
        'reservas_reales': reservas_reales,      
        'reservas_historicas': reservas_historicas  
    })

def activar_cuenta(request, token):
    try:
        # Intentamos descifrar el email del token con una vida máxima de 24 horas (86400 segundos)
        email_usuario = signer.unsign(token, max_age=86400)
        usuario = Usuario.objects.get(email=email_usuario)
        
        # ESCENARIO 1: Enlace Válido
        if not usuario.is_active:
            usuario.is_active = True
            usuario.save()
        
        # Iniciamos sesión automáticamente para mejorar la experiencia (UX)
        auth_login(request, usuario)
        
        # Redirigimos al Dashboard del Turista
        return redirect('authentication:dashboard') 

    except SignatureExpired:
        # ESCENARIO 2: El enlace expiró (> 24 horas)
        return render(request, 'authentication/enlace_expirado.html', {'token_viejo': token})
        
    except (BadSignature, Usuario.DoesNotExist):
        # ESCENARIO 3: El token fue alterado o es inválido
        return render(request, 'authentication/enlace_invalido.html')
    
# Agrega esto al final de tu views.py

def reenviar_enlace(request):
    if request.method == 'POST':
        token_viejo = request.POST.get('token_viejo')
        
        try:
            # Extraemos el email del token viejo ignorando que ya expiró
            email_usuario = signer.unsign(token_viejo)
            usuario = Usuario.objects.get(email=email_usuario)
            
            # Si el usuario ya está activo, no tiene sentido reenviar nada
            if usuario.is_active:
                return redirect('authentication:login')
                
            # Generamos un NUEVO token con tiempo limpio
            nuevo_token = signer.sign(usuario.email)
            ruta_activacion = reverse('authentication:activar_cuenta', kwargs={'token': nuevo_token})
            enlace_activacion = request.build_absolute_uri(ruta_activacion)
            
            # --- GUARDAR EN EL ARCHIVO DE EMERGENCIA ---
            with open("ENLACE_MÁGICO.txt", "w", encoding="utf-8") as f:
                f.write(f"NUEVO Enlace para el usuario {usuario.email}:\n")
                f.write(enlace_activacion)
            # --------------------------------------------
            
            # Enviamos el correo de nuevo
            asunto = 'Nuevo enlace de verificación - Proyecto Integrador'
            mensaje = (
                f'Hola {usuario.nombre},\n\n'
                f'Tu enlace anterior expiro. Aqui tienes tu nuevo enlace de activación valido por 24 horas:\n'
                f'{enlace_activacion}\n\n'
            )
            
            try:
                send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [usuario.email], fail_silently=False)
            except Exception:
                pass
                
            # Lo mandamos de vuelta a la pantalla de espera
            return redirect('authentication:verificacion_pendiente')
            
        except (BadSignature, Usuario.DoesNotExist):
            # Si el token viejo está corrupto o alterado, lo mandamos a error
            return render(request, 'authentication/enlace_invalido.html')
            
    return redirect('authentication:login')

# =====================================================================
# VISTAS PARA RESTABLECER CONTRASEÑA (OLVIDÓ SU CONTRASEÑA)
# =====================================================================

def solicitar_restablecimiento(request):
    if request.method == 'POST':
        email_ingresado = request.POST.get('email')
        mensaje_exito = "Si el correo electrónico coincide con una cuenta registrada, recibiras un enlace para restablecer tu contraseña en unos minutos."
        
        try:
            usuario = Usuario.objects.get(email=email_ingresado)
            
            # GENERAR EL TOKEN (Válido por 1 hora)
            token = signer.sign(usuario.email)
            
            # CORREGIDO: Construcción dinámica usando reverse con namespace
            ruta_restablecer = reverse('authentication:restablecer_password_confirmar', kwargs={'token': token})
            enlace = request.build_absolute_uri(ruta_restablecer)
            
            # --- NUESTRO RESPALDO DE EMERGENCIA LOCAL ---
            with open("ENLACE_MÁGICO.txt", "w", encoding="utf-8") as f:
                f.write(f"Enlace de restablecimiento para {usuario.email}:\n")
                f.write(enlace)
            # --------------------------------------------
            
            # Enviar el correo real / simulación por consola
            send_mail(
                'Restablecer Contrasena - Proyecto Integrador',
                f'Haz clic aquí para restablecer tu contrasena: {enlace}',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
        except Usuario.DoesNotExist:
            # Pasamos de largo silenciosamente por seguridad
            pass
            
        # Ambos caminos terminan en la misma pantalla
        return render(request, 'authentication/solicitud_enviada.html', {'mensaje': mensaje_exito})
        
    return render(request, 'authentication/solicitar_restablecimiento.html')


def restablecer_password_confirmar(request, token):
    try:
        # Validamos que no haya pasado más de 1 hora (3600 segundos)
        email_usuario = signer.unsign(token, max_age=3600)
        usuario = Usuario.objects.get(email=email_usuario)
        
    except (SignatureExpired, BadSignature, Usuario.DoesNotExist):
        # Si expiró o alteraron el token, mandamos a error
        return render(request, 'authentication/enlace_password_expirado.html')

    # Si el token es válido y el usuario envía el nuevo password
    if request.method == 'POST':
        nuevo_password = request.POST.get('password')
        nuevo_password_confirm = request.POST.get('password_confirm')
        
        if nuevo_password == nuevo_password_confirm:
            usuario.set_password(nuevo_password)
            
            # LOGICA EXTRA PRO: Liberamos el bloqueo por fuerza bruta de inmediato
            # Esto soluciona tu caso: si estaba bloqueado, aquí lo perdonamos porque ya usó su correo.
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            usuario.save()
            
            # --- NUEVO: Mandamos el aviso de éxito al Login ---
            messages.success(request, '¡Tu contraseña se ha actualizado correctamente! Ya puedes iniciar sesión sin bloqueos.')
            
            # Redirección con namespace a tu login personalizado
            return redirect('authentication:login')  
        else:
            return render(request, 'authentication/restablecer_password_nuevo.html', {
                'error': 'Las contraseñas no coinciden.'
            })
            
    return render(request, 'authentication/restablecer_password_nuevo.html')

@login_required
def mis_joyas_ocultas(request):
    mis_puntos = PuntoDeInteres.objects.filter(proponente=request.user)
    return render(request, 'authentication/mis_joyas_ocultas.html', {'mis_puntos': mis_puntos})

@login_required # <-- Solo turistas logueados entran aquí
def crear_joya_oculta(request):
    if request.method == 'POST':
        print("📸 [Logs Foto] Empezando revisión de imágenes...")
        print(f"🔗 URL copiada por el usuario: {request.POST.get('imagen_url')}")
        print(f"📂 Archivos detectados en la petición: {request.FILES.keys()}")
        # Capturamos los datos directos del formulario del modal
        imagen_url = request.POST.get('imagen_url')
        nombre = request.POST.get('nombre')
        categoria = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion')
        referencia_ubicacion = request.POST.get('referencia_ubicacion')
        latitud = request.POST.get('latitud') or None
        longitud = request.POST.get('longitud') or None

        # CAPTURA DEL ARCHIVO: Buscamos si viene un archivo en la petición
        imagen_archivo = request.FILES.get('imagen_archivo')

        # Creamos el registro en la base de datos
        PuntoDeInteres.objects.create(
            proponente=request.user,
            imagen_url=imagen_url,
            imagen_archivo=imagen_archivo,  # <--- Agregamos el archivo aquí
            nombre=nombre,
            categoria=categoria,
            descripcion=descripcion,
            referencia_ubicacion=referencia_ubicacion,
            latitud=latitud,
            longitud=longitud
            # 'estado' no se pone porque por defecto se guarda como 'PENDIENTE'
        )
        # Al terminar, redirigimos de vuelta a su tablero para que vea el nuevo punto "En revisión"
        return redirect('authentication:mis_joyas_ocultas')
        
    return redirect('authentication:mis_joyas_ocultas')


@login_required
def editar_joya_oculta(request, poi_id):
    # Buscamos el POI asegurándonos de que pertenezca al turista logueado (por seguridad)
    poi = get_object_or_404(PuntoDeInteres, id=poi_id, proponente=request.user)
    
    if request.method == 'POST':
        poi.imagen_url = request.POST.get('imagen_url', '')
        
        # CAPTURA DEL ARCHIVO EN EDICIÓN: Usamos .get() que es más seguro y no da error si viene vacío
        if 'imagen_archivo' in request.FILES:
            poi.imagen_archivo = request.FILES['imagen_archivo']
            
        poi.nombre = request.POST.get('nombre')
        poi.categoria = request.POST.get('categoria', 'Naturaleza')
        poi.descripcion = request.POST.get('descripcion')
        poi.referencia_ubicacion = request.POST.get('referencia_ubicacion')
        poi.latitud = request.POST.get('latitud') or None
        poi.longitud = request.POST.get('longitud') or None
        
        # ¡LA CLAVE DEL FLUJO!: Vuelve a estar pendiente para que el moderador lo revise de nuevo
        poi.estado = 'PENDIENTE' 
        poi.save()
        
        return redirect('authentication:mis_joyas_ocultas')
        
    return redirect('authentication:mis_joyas_ocultas')


def feed_joyas_ocultas(request):
    # 1. Traemos solo lo que ya pasó por el filtro del moderador
    pois = PuntoDeInteres.objects.filter(estado='APROBADO')

    # 2. Capturamos los parámetros de búsqueda del HTML (GET)
    buscar_texto = request.GET.get('search', '')
    filtrar_categoria = request.GET.get('categoria', '')
    filtrar_ubicacion = request.GET.get('ubicacion', '')

    # 3. Aplicamos los filtros si el usuario interactúa con la barra
    if buscar_texto:
        pois = pois.filter(Q(nombre__icontains=buscar_texto) | Q(descripcion__icontains=buscar_texto))
    
    if filtrar_categoria:
        pois = pois.filter(categoria=filtrar_categoria) 
        
    if filtrar_ubicacion:
        pois = pois.filter(referencia_ubicacion__icontains=filtrar_ubicacion)

    # 4. Obtenemos listas limpias para llenar los selectores del buscador (sin repetir)
    categorias = ["Aventura", "Gastronomía", "Cultural", "Naturaleza", "Mirador"] 

    context = {
        'pois': pois,
        'categorias': categorias,
        'buscar_texto': buscar_texto,
        'categoria_seleccionada': filtrar_categoria,
        'ubicacion_seleccionada': filtrar_ubicacion,
    }
    
    return render(request, 'authentication/feed_joyas.html', context)


def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Fórmula de Haversine para calcular la distancia en kilómetros entre dos coordenadas
    """
    # Si falta alguna coordenada, retornamos infinito para que no rompa el filtro
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
        
    rad = math.pi / 180
    dlat = (lat2 - lat1) * rad
    dlon = (lon2 - lon1) * rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1*rad) * math.cos(lat2*rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia_km = 6371 * c # 6371 es el radio de la Tierra en kilómetros
    return distancia_km

def feed_joyas_ocultas(request):
    # 1. Base inicial: Solo lo aprobado
    pois_queryset = PuntoDeInteres.objects.filter(estado='APROBADO')

    # 2. Captura de parámetros
    buscar_texto = request.GET.get('search', '')
    filtrar_categoria = request.GET.get('categoria', '')
    distancia_max = request.GET.get('distancia', '')
    orden_seleccionado = request.GET.get('orden', '-fecha_propuesta')

    # Coordenadas que vienen del JavaScript (GPS)
    # Si fallan, ponemos unas por defecto (Ej: coordenadas del centro de La Ceja)
    try:
        user_lat = float(request.GET.get('user_lat'))
        user_lng = float(request.GET.get('user_lng'))
    except (TypeError, ValueError):
        # 📌 COORDENADAS POR DEFECTO (Cámbialas por las de tu plaza local si quieres)
        user_lat = -16.5000 
        user_lng = -68.1500

    # 3. Aplicar Filtros estándar (Texto y Categoría)
    if buscar_texto:
        pois_queryset = pois_queryset.filter(Q(nombre__icontains=buscar_texto) | Q(descripcion__icontains=buscar_texto))
    
    if filtrar_categoria:
        pois_queryset = pois_queryset.filter(categoria=filtrar_categoria)

    # 4. ORDENAR BASE DE DATOS TRADICIONAL (Si no es por cercanía)
    if orden_seleccionado != 'cercania':
        pois_queryset = pois_queryset.order_by(orden_seleccionado)

    # 5. 🆕 CONVERTIR A LISTA PARA EL CÁLCULO DE KILÓMETROS IN SITU
    pois_filtrados = []
    for poi in pois_queryset:
        # Calculamos los km reales desde el usuario hasta el POI
        poi.distancia_usuario = calcular_distancia(user_lat, user_lng, poi.latitud, poi.longitud)
        
        # Si el usuario eligió un rango (ej: 5km) y el POI está más lejos, lo descartamos
        if distancia_max:
            if poi.distancia_usuario <= float(distancia_max):
                pois_filtrados.append(poi)
        else:
            # Si no hay filtro de distancia, pasan todos
            pois_filtrados.append(poi)

    # 6. ORDENAMIENTO EXTRA: Si el usuario quiere ver los más cercanos primero
    if distancia_max and orden_seleccionado == 'cercania':
        pois_filtrados.sort(key=lambda x: x.distancia_usuario)

    context = {
        'pois': pois_filtrados,
        'buscar_texto': buscar_texto,
        'categoria_seleccionada': filtrar_categoria,
        'distancia_seleccionada': distancia_max,
        'orden_seleccionado': orden_seleccionado,
        'user_lat': user_lat,
        'user_lng': user_lng,
    }
    return render(request, 'authentication/feed_joyas.html', context)

@login_required
def modificar_favorito_joya(request, poi_id):
    """
    Vista AJAX: Agrega o quita un POI de los favoritos del usuario autenticado
    """
    if request.method == "POST":
        poi = get_object_or_404(PuntoDeInteres, id=poi_id, estado='APROBADO')
        usuario = request.user
        
        if usuario in poi.usuarios_favoritos.all():
            # Si ya era favorito, lo quitamos (Unlove 💔)
            poi.usuarios_favoritos.remove(usuario)
            guardado = False
            mensaje = "Removido de tus favoritos"
        else:
            # Si no era favorito, lo agregamos (Love ❤️)
            poi.usuarios_favoritos.add(usuario)
            guardado = True
            mensaje = "¡Guardado en tus favoritos!"
            
        # Devolvemos la respuesta en formato JSON
        return JsonResponse({
            "status": "success",
            "guardado": guardado,
            "mensaje": mensaje,
            "total_favoritos": poi.usuarios_favoritos.count()
        })
        
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=400)

@login_required
def mis_joyas_favoritas(request):
    """
    Muestra el listado de todos los POIs que el turista actual ha guardado
    """
    # Filtramos los POIs donde el usuario actual esté en la relación ManyToMany
    favoritos = PuntoDeInteres.objects.filter(usuarios_favoritos=request.user, estado='APROBADO').order_by('-fecha_propuesta')
    
    context = {
        'favoritos': favoritos,
        'user_lat': request.GET.get('user_lat'), # Mantenemos soporte por si heredamos ubicación
        'user_lng': request.GET.get('user_lng'),
    }
    return render(request, 'authentication/mis_favoritos.html', context)

@login_required
def eliminar_poi_turista(request, poi_id):
    """
    Permite al turista eliminar una propuesta de POI propia 
    siempre y cuando no esté aprobada públicamente.
    """
    # Nos aseguramos de que el POI sea del usuario actual y NO esté aprobado
    poi = get_object_or_404(PuntoDeInteres, id=poi_id, proponente=request.user)
    
    if poi.estado in ['PENDIENTE', 'CAMBIOS', 'RECHAZADO']:
        nombre_poi = poi.nombre
        poi.delete()
        messages.success(request, f"🗑️ La propuesta '{nombre_poi}' ha sido eliminada correctamente.")
    else:
        messages.error(request, "🚫 No puedes eliminar un punto de interés que ya ha sido aprobado y es público.")
        
    return redirect('authentication:mis_joyas_ocultas') # Te redirige a su panel de control

@login_required
def historial_compras(request):
    """
    T28: Muestra al turista logueado el desglose de sus comprobantes de compra
    """
    mis_compras = CompraPaquete.objects.filter(turista=request.user).order_by('-fecha_compra')
    compras_lista = list(mis_compras)
    return render(request, 'authentication/historial_compras.html', {'compras': compras_lista})

