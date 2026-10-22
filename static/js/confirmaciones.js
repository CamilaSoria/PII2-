/**
 * Lógica de confirmaciones interactivas para el Perfil del Turista
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Capturar todos los enlaces de cancelación autónoma
    const botonesCancelar = document.querySelectorAll('.btn-confirmar-cancelacion');
    
    botonesCancelar.forEach(boton => {
        boton.addEventListener('click', function(event) {
            // Mensaje de advertencia nativo del navegador
            const mensaje = "¿Estás completamente seguro de que deseas cancelar esta reserva?\n\n" +
                            "Esta acción liberará tu cupo en el paquete turístico de forma inmediata y no se puede deshacer.";
            
            // Si el usuario presiona "Cancelar" en la ventana emergente...
            if (!confirm(mensaje)) {
                event.preventDefault(); // ...detenemos la redirección a la vista de Django
                console.log("Cancelación abortada por el usuario.");
            } else {
                console.log("Cancelación confirmada. Redirigiendo a la ruta de Django...");
            }
        });
    });

    // 2. [Opcional] Auto-cerrar alertas de éxito/error de Bootstrap después de 5 segundos
    const alertas = document.querySelectorAll('.alert');
    alertas.forEach(alerta => {
        setTimeout(() => {
            // Usamos el método nativo de Bootstrap 5 si está disponible
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alerta);
                bsAlert.close();
            }
        }, 5000);
    });

});