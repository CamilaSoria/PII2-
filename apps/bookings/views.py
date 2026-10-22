import hmac
import hashlib
import json
import uuid  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Avg
from apps.inventory.models import Paquete  
from .models import Reserva, Auditoria, Pago  # 💳 Importamos el modelo Pago
from apps.bookings.models import Pago   

# Clave secreta criptográfica compartida con la pasarela simulada
SECRET_KEY_PASARELA = 'banco_secreto_super_seguro_2026' 

@login_required
@transaction.atomic  
def crear_reserva_transaccional(request, paquete_id):
    """
    Historia 1: El turista formaliza su viaje. 
    Nace como PENDIENTE y genera la orden de cobro en la tabla Pago.
    """
    paquete = get_object_or_404(Paquete, id=paquete_id, esta_activo=True)
    
    if request.method == 'POST':
        cantidad_pasajeros = int(request.POST.get('cantidad_pasajeros', 1))
        fecha_viaje = request.POST.get('fecha_viaje')
        
        try:
            paquete_db = Paquete.objects.select_for_update().get(id=paquete.id)
            
            if paquete_db.cupos_totales < cantidad_pasajeros:
                return HttpResponseBadRequest("Lo sentimos, no quedan suficientes cupos disponibles para este paquete.")
            
            # Descontamos preventivamente el cupo
            paquete_db.cupos_totales -= cantidad_pasajeros
            paquete_db.save()
            
            monto_total = paquete_db.precio_base * cantidad_pasajeros
            transaccion_inicial_id = f"TXN-PEND-{uuid.uuid4().hex[:10].upper()}"

            # 🛠️ AJUSTE: La reserva nace PENDIENTE hasta que el webhook verifique el pago
            reserva = Reserva.objects.create(
                usuario=request.user,
                paquete=paquete_db,
                cantidad_pasajeros=cantidad_pasajeros,
                fecha_viaje=fecha_viaje,
                monto_total=monto_total,
                estado_pago='PENDIENTE',  
                codigo_transaccion=transaccion_inicial_id
            )

            # 💳 Generamos la orden de Pago en estado PENDIENTE
            Pago.objects.create(
                reserva=reserva,
                monto=monto_total,
            )

            # Sistema de Auditoría
            Auditoria.objects.create(
                usuario=request.user,
                tabla_afectada='reservas',
                accion_ejecutada='INSERT',
                valores_nuevos={
                    'id_reserva': reserva.id_reserva,
                    'paquete': paquete_db.nombre,
                    'monto_total': float(monto_total),
                    'estado_inicial': 'PENDIENTE'
                },
                direccion_ip=request.META.get('REMOTE_ADDR')
            )

            messages.warning(request, f"⏳ Reserva registrada. Esperando confirmación de pago por el banco...")
            return redirect('bookings:checkout_pago', reserva_id=reserva.id_reserva)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('inventory:lista_paquetes')
            
    return HttpResponseBadRequest("Método no permitido.")


@csrf_exempt  # Eximimos esta ruta del token CSRF interno
@transaction.atomic
def webhook_pagos(request):
    """
    Historia 2: Recibe la notificación asíncrona del banco de forma criptográfica segura.
    Sincroniza la tabla Pago y confirma la Reserva.
    """
    if request.method == 'POST':
        firma_recibida = request.headers.get('X-Signature')
        payload = request.body  # Cuerpo en bytes crudos

        if not firma_recibida:
            return JsonResponse({'error': 'Falta la firma de seguridad'}, status=400)

        # Generamos firma local para corroborar que provenga del banco legítimo
        firma_calculada = hmac.new(
            key=SECRET_KEY_PASARELA.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

        # Comparación inmune a ataques de tiempo (Timing Attacks)
        if hmac.compare_digest(firma_recibida, firma_calculada):
            try:
                datos = json.loads(payload)
                # Ojo: Tu webhook buscaba reserva_id, usamos el campo relacional id_reserva
                reserva_id = datos.get('reserva_id')
                estado_transaccion = datos.get('estado')

                # Buscamos el registro de Pago usando el id_reserva relacional
                pago = Pago.objects.select_for_update().get(reserva__id_reserva=reserva_id, estado='PENDIENTE')
                
                if estado_transaccion == 'aprobado':
                    # 1. Actualizamos el estado del Pago individual
                    pago.estado = 'COMPLETADO'
                    pago.transaccion_id = datos.get('transaccion_id')
                    pago.save()

                    # 2. ⚡ ACTUALIZACIÓN EN CADENA: Confirmamos la Reserva asociada
                    reserva = pago.reserva
                    reserva.estado_pago = 'CONFIRMADA'
                    reserva.transaccion_pago_id = datos.get('transaccion_id')
                    reserva.save()

                    return JsonResponse({'status': 'Webhook procesado. Pago y reserva confirmados con éxito ✅'})
                else:
                    pago.estado = 'FALLIDO'
                    pago.save()
                    return JsonResponse({'status': 'Pago rechazado registrado ❌'})
                
            except Pago.DoesNotExist:
                return JsonResponse({'error': 'Orden de pago pendiente no encontrada'}, status=200)
        else:
            return JsonResponse({'error': '¡ALERTA DE SEGURIDAD! Firma inválida ❌'}, status=403)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@transaction.atomic 
def cancelar_reserva_turista(request, reserva_id):
    """
    Historia 3: El turista cancela autónomamente.
    Devuelve los cupos de manera directa y segura.
    """
    reserva = get_object_or_404(Reserva, id_reserva=reserva_id, usuario=request.user)
    
    if reserva.estado_pago.upper() in ['CONFIRMADA', 'PENDIENTE']:
        reserva.estado_pago = 'CANCELADA'
        reserva.save()
        
        # Si tenía un Pago asociado pendiente o completado, lo cancelamos de igual manera
        Pago.objects.filter(reserva=reserva).update(estado='FALLIDO')
        
        if reserva.paquete:
            paquete_db = Paquete.objects.select_for_update().get(id=reserva.paquete.id)
            paquete_db.cupos_totales += reserva.cantidad_pasajeros
            paquete_db.save()
            
        messages.success(request, "❌ Tu reserva ha sido cancelada y el cupo fue liberado correctamente.")
    else:
        messages.error(request, "⚠️ No se puede cancelar una reserva que ya está en curso o completada.")
        
    return redirect('authentication:perfil')

@login_required
def checkout_pago(request, reserva_id):
    """
    Historia 1: Pantalla de Caja/Checkout para el Turista.
    Muestra el resumen de compra y prepara el terreno para la simulación del pago.
    """
    # 🛠️ CORREGIDO: Buscamos por tu PK real 'id_reserva'
    reserva = get_object_or_404(Reserva, id_reserva=reserva_id, usuario=request.user)
    
    # Intentamos traer el pago pendiente que creamos en 'crear_reserva_transaccional'
    # Si por alguna razón no existía, lo creamos de respaldo de forma segura
    pago, created = Pago.objects.get_or_create(
        reserva=reserva,
        defaults={
            'monto': reserva.monto_total, # 🛠️ CORREGIDO: Usamos el monto ya calculado en la reserva
            'metodo': 'PASARELA',
            'estado': 'PENDIENTE'
        }
    )

    # Renderizamos la plantilla de checkout pasándole el token para el simulador
    return render(request, 'bookings/checkout.html', {
        'reserva': reserva, 
        'pago': pago,
        'secret_key_pasarela': SECRET_KEY_PASARELA # La pasaremos para usarla en el simulador frontend si hace falta
    })
    

@staff_member_required # 🔒 Solo staff/analistas
def reporte_ventas(request):
    """
    Filtra y agrega las ventas del sistema desde la app de bookings.
    """
    # El resto del motor se queda exactamente igual y seguro contra mayúsculas:
    pagos = Pago.objects.filter(
        estado__iexact='completado'
    ).select_related('reserva__usuario')
    
    paquetes = Paquete.objects.all()

    # --- CAPTURA DE FILTROS ---
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    paquete_id = request.GET.get('paquete')
    metodo_pago = request.GET.get('metodo')

    if fecha_inicio:
        pagos = pagos.filter(fecha_pago__date__gte=fecha_inicio)
    if fecha_fin:
        pagos = pagos.filter(fecha_pago__date__lte=fecha_fin)
    if paquete_id:
        pagos = pagos.filter(reserva__habitacion_inventario__paquete_id=paquete_id)
    if metodo_pago:
        pagos = pagos.filter(metodo=metodo_pago)

    # --- MOTOR DE AGREGACIÓN ORM ---
    kpis = pagos.aggregate(
        total_ingresos=Sum('monto'),
        total_ventas_cant=Count('id'),
        ticket_promedio=Avg('monto')
    )

    # Control de nulos por si no hay registros que sumen
    if kpis['total_ingresos'] is None:
        kpis['total_ingresos'] = 0
    if kpis['ticket_promedio'] is None:
        kpis['ticket_promedio'] = 0

    metodos_choices = getattr(Pago, 'METODO_CHOICES', [])

    # 🛠️ AJUSTE DE RUTA HTML: Asegúrate de que la plantilla esté en la carpeta correcta
    # Lo ideal es que se guarde en templates/bookings/reporte_ventas.html
    return render(request, 'bookings/reporte_ventas.html', {
        'pagos': pagos,
        'paquetes': paquetes,
        'kpis': kpis,
        'filtros': request.GET,
        'metodos': metodos_choices
    })