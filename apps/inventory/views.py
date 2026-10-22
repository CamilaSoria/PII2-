from django.shortcuts import render, get_object_or_404, redirect
from .models import Paquete, Categoria
from django.contrib.auth.decorators import login_required
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Paquete, Promocion, CompraPaquete

def lista_paquetes(request):
    # El visitante solo ve lo que el agente tiene activo
    paquetes = Paquete.objects.filter(esta_activo=True)
    categorias = Categoria.objects.all()

    # --- CAPTURA DE FILTROS DESDE LA URL (Historia 1) ---
    cat_id = request.GET.get('categoria')
    duracion = request.GET.get('duracion')
    precio_max = request.GET.get('precio_max')
    dificultad = request.GET.get('dificultad')

    if cat_id:
        paquetes = paquetes.filter(categoria_id=cat_id)
    if duracion:
        paquetes = paquetes.filter(duracion_dias=duracion)
    if precio_max:
        paquetes = paquetes.filter(precio__lte=precio_max)
    if dificultad:
        paquetes = paquetes.filter(dificultad=dificultad)

    return render(request, 'inventory/lista.html', {
        'paquetes': paquetes,
        'categorias': categorias,
        # Devolvemos los filtros aplicados para mantenerlos en los inputs de la pantalla
        'filtros': request.GET 
    })

def detalle_paquete(request, pk):
    paquete = get_object_or_404(Paquete, pk=pk, esta_activo=True)
    # Gracias al related_name='itinerarios' traemos los días asociados automáticamente
    itinerario = paquete.itinerarios.all()
    return render(request, 'inventory/detalle.html', {
        'paquete': paquete,
        'itinerario': itinerario
    })


@login_required
def procesar_compra_simulada(request, paquete_id):
    paquete = get_object_or_404(Paquete, id=paquete_id, esta_activo=True)
    
    # Captura de datos segura
    cantidad = int(request.POST.get('cantidad_cupos') or request.GET.get('cantidad_cupos') or 1)
    codigo_cupon = (request.POST.get('codigo_promocion') or request.GET.get('codigo_promocion') or '').strip().upper()
    
    # 🎯 PRINT 1: Ver si la vista detecta el clic
    print(f"--- NUEVA PETICIÓN --- Método: {request.method} | Botón Confirmar en POST: {'confirmar_pago' in request.POST}")
    
    if paquete.cupos_totales < cantidad:
        messages.error(request, f"💔 ¡No quedan cupos suficientes!")
        return redirect('inventory:administrar_paquetes')

    subtotal = paquete.precio * cantidad
    descuento = 0
    promocion_valida = None

    # Cálculo del cupón
    if codigo_cupon:
        try:
            promo = Promocion.objects.get(codigo=codigo_cupon, esta_activa=True)
            if not promo.ha_vencido:
                promocion_valida = promo
                descuento = (subtotal * promo.porcentaje_descuento) / 100
            else:
                messages.warning(request, "⚠️ Este cupón ya ha vencido.")
        except Promocion.DoesNotExist:
            messages.error(request, "🚫 El código de promoción no es válido.")

    total_final = subtotal - descuento

    # Procesamiento del Pago Seguro
    if request.method == 'POST' and 'confirmar_pago' in request.POST:
        print("✅ ¡ENTRAMOS AL BLOQUE DE COMPRA!")
        try:
            codigo_ticket = f"TK-{uuid.uuid4().hex[:8].upper()}"
            
            # Intentamos guardar en la base de datos
            CompraPaquete.objects.create(
                turista=request.user,
                paquete=paquete,
                promocion_aplicada=promocion_valida,
                cantidad_cupos=cantidad,
                precio_unitario=paquete.precio,
                total_pagado=total_final,
                codigo_transaccion=codigo_ticket
            )
            print(f"💾 REGISTRO CREADO EXITOSAMENTE: {codigo_ticket}")
            
            # Descontar inventario
            paquete.cupos_totales -= cantidad
            if paquete.cupos_totales == 0:
                paquete.esta_activo = False
            paquete.save()

            messages.success(request, f"🎉 ¡Compra exitosa! Tu comprobante es el {codigo_ticket}.")
            print("🚀 EJECUTANDO REDIRECCIÓN AL HISTORIAL...")
            return redirect('authentication:historial_compras') # 👈 Redirección al éxito
            
        except Exception as e:
            # 🚨 Si la base de datos choca, atrapamos el error REAL de SQL aquí
            print(f"💥 EXCEPCIÓN EN BASE DE DATOS: {str(e)}")
            messages.error(request, f"💥 Error en Base de Datos: {str(e)}")
            # No redirigimos al limbo, dejamos que continúe abajo para renderizar el HTML con el error

    # 🎯 EL SALVAVIDAS: Este contexto se renderiza tanto en el GET como si el POST del botón verde falla
    context = {
        'paquete': paquete,
        'cantidad': cantidad,
        'subtotal': subtotal,
        'descuento': descuento,
        'total_final': total_final,
        'codigo_cupon': codigo_cupon,
    }
    return render(request, 'inventory/checkout_simulado.html', context)

def explorar_paquetes(request):
    """
    T25: Vista pública para que los turistas exploren paquetes activos,
    filtren por categoría y seleccionen cuáles quieren comparar.
    """
    # Solo mostramos paquetes con cupos y que estén activos
    paquetes = Paquete.objects.filter(esta_activo=True, cupos_totales__gt=0).order_by('-id')
    
    # Sistema de filtros rápido
    buscar = request.GET.get('buscar', '')
    categoria = request.GET.get('categoria', '')
    
    if buscar:
        paquetes = paquetes.filter(nombre__icontains=buscar)
    if categoria:
        paquetes = paquetes.filter(categoria=categoria)
        
    # Lógica de comparación basada en la sesión de Django (sin tocar base de datos)
    comparar_ids = request.session.get('comparar_paquetes', [])
    paquetes_a_comparar = Paquete.objects.filter(id__in=comparar_ids)

    context = {
        'paquetes': paquetes,
        'paquetes_a_comparar': paquetes_a_comparar,
        'buscar': buscar,
        'categoria': categoria,
    }
    return render(request, 'inventory/explorar_paquetes.html', context)

def agregar_a_comparacion(request, paquete_id):
    """Agrega un paquete a la lista temporal de comparación"""
    comparar_ids = request.session.get('comparar_paquetes', [])
    
    if paquete_id not in comparar_ids:
        if len(comparar_ids) >= 3: # Límite estético de 3 paquetes para la tabla
            messages.warning(request, "⚠️ Solo puedes comparar hasta 3 paquetes a la vez.")
        else:
            comparar_ids.append(paquete_id)
            request.session['comparar_paquetes'] = comparar_ids
            messages.success(request, "🔄 Paquete añadido a la tabla de comparación.")
            
    return redirect('inventory:explorar_paquetes')

def limpiar_comparacion(request):
    """Vacía la lista de comparación"""
    if 'comparar_paquetes' in request.session:
        del request.session['comparar_paquetes']
    messages.info(request, "🧹 Comparador limpio.")
    return redirect('inventory:explorar_paquetes')