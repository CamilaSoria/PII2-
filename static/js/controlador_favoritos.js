// static/js/controlador_favoritos.js

document.addEventListener("DOMContentLoaded", function() {
    const contenedorPrincipal = document.getElementById('contenedor-favoritos');

    if (contenedorPrincipal) {
        contenedorPrincipal.addEventListener('click', function(e) {
            // Verificamos si el clic fue en un botón de favoritos
            const boton = e.target.closest('.btn-fav-toggle');
            if (!boton) return;

            const poiId = boton.getAttribute('data-poi-id');
            
            // Le damos 150ms de espera para que favoritos.js (el script global) 
            // termine la petición AJAX y cambie las clases del botón
            setTimeout(() => {
                const btnActualizado = document.getElementById(`btn-fav-${poiId}`);
                
                // Si favoritos.js le quitó la clase 'btn-danger', significa que ya no es favorito
                if (btnActualizado && btnActualizado.classList.contains('btn-outline-danger')) {
                    const contenedorTarjeta = document.getElementById(`tarjeta-fav-container-${poiId}`);
                    
                    if (contenedorTarjeta) {
                        // Aplicamos la animación fluida de desvanecimiento
                        contenedorTarjeta.style.transition = "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
                        contenedorTarjeta.style.opacity = "0";
                        contenedorTarjeta.style.transform = "scale(0.85) translateY(10px)";
                        
                        // Esperamos a que la animación termine para remover el elemento del DOM
                        setTimeout(() => {
                            contenedorTarjeta.remove();
                            
                            // Si ya no quedan más tarjetas, recargamos la página para mostrar el estado vacío 💔
                            const tarjetasRestantes = document.querySelectorAll('#contenedor-favoritos > div');
                            if (tarjetasRestantes.length === 0) {
                                window.location.reload();
                            }
                        }, 400);
                    }
                }
            }, 150);
        });
    }
});