// static/js/eliminar_poi.js

document.addEventListener("DOMContentLoaded", function() {
    const formulariosEliminar = document.querySelectorAll('form[action*="eliminar"]');
    
    formulariosEliminar.forEach(form => {
        form.addEventListener('submit', function() {
            const botonSubmit = this.querySelector('.btn-confirmar-eliminar');
            if (botonSubmit) {
                // Deshabilitamos el botón y mostramos feedback de carga tradicional
                botonSubmit.disabled = true;
                botonSubmit.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Eliminando...`;
            }
        });
    });
});