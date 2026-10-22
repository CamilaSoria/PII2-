/**
 * apps/gestion/static/js/modal_galeria.js
 * Manejo dinámico del carrusel de fotos dentro del modal de destinos.
 */
document.addEventListener("DOMContentLoaded", function () {
    const modalGaleria = document.getElementById('modalGaleria');
    
    if (modalGaleria) {
        modalGaleria.addEventListener('show.bs.modal', function (event) {
            // El botón/badge que abrió el modal
            const boton = event.relatedTarget;
            
            // Extraer los atributos data-* del botón
            const nombreDestino = boton.getAttribute('data-nombre') || 'Destino';
            const rawFotos = boton.getAttribute('data-fotos');
            
            let arrayFotos = [];
            try {
                // Parseamos de forma segura protegiendo fallos de JSON
                arrayFotos = JSON.parse(rawFotos) || [];
            } catch (error) {
                console.error("Error al procesar el JSON de imágenes del destino:", error);
            }
            
            // 1. Actualizar el título del modal usando concatenación limpia
            const modalTitle = modalGaleria.querySelector('.modal-title');
            if (modalTitle) {
                modalTitle.innerHTML = '📸 Galería: <span class="text-warning">' + nombreDestino + '</span>';
            }
            
            // 2. Limpiar e Inyectar el carrusel de fotos dinámicamente
            const contenedor = document.getElementById('contenedorFotosModal');
            if (!contenedor) return;
            
            contenedor.innerHTML = ""; // Limpieza total
            
            if (arrayFotos.length === 0) {
                contenedor.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-muted"><p>No hay fotos disponibles.</p></div>';
                return;
            }
            
            // Construimos los elementos del carrusel
            arrayFotos.forEach((urlFoto, indice) => {
                const isActive = indice === 0 ? 'active' : '';
                const totalFotos = arrayFotos.length;
                const numeroActual = indice + 1;
                
                // Evitamos template literals conflictivos si usas procesadores o simplemente para máxima compatibilidad externa
                const itemHtml = 
                    '<div class="carousel-item ' + isActive + ' h-100">' +
                        '<img src="' + urlFoto + '" class="d-block w-100 h-100" style="object-fit: cover;" alt="Foto ' + numeroActual + '">' +
                        '<div class="carousel-caption d-none d-md-block bg-dark bg-opacity-50 rounded py-1 px-2 start-50 translate-middle-x" style="bottom: 15px; width: fit-content;">' +
                            '<small class="text-white">Imagen ' + numeroActual + ' de ' + totalFotos + '</small>' +
                        '</div>' +
                    '</div>';
                
                contenedor.insertAdjacentHTML('beforeend', itemHtml);
            });

            // 3. Forzar a Bootstrap 5 a reconocer que el carrusel tiene contenido nuevo y reinicie desde la foto 0
            const carruselElemento = document.getElementById('carruselDestino');
            if (carruselElemento && typeof bootstrap !== 'undefined' && bootstrap.Carousel) {
                let carruselInstancia = bootstrap.Carousel.getInstance(carruselElemento);
                if (!carruselInstancia) {
                    carruselInstancia = new bootstrap.Carousel(carruselElemento, {
                        interval: false, // Que no se mueva solo a menos que den click
                        ride: false
                    });
                }
                carruselInstancia.to(0); // Forzar ir a la primera imagen inyectada
            }
        });
    }
});