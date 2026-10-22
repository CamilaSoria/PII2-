document.addEventListener("DOMContentLoaded", function () {
    const inputImagenes = document.querySelector('input[name="imagenes_multiples"]');
    const contenedorPreview = document.getElementById("previsualizacion-galeria");

    if (inputImagenes && contenedorPreview) {
        inputImagenes.addEventListener("change", function (event) {
            // Limpiamos los previews temporales anteriores
            const elementosTemporales = contenedorPreview.querySelectorAll('.img-temporal');
            elementosTemporales.forEach(el => el.remove());

            const archivos = event.target.files;
            
            Array.from(archivos).forEach(archivo => {
                if (archivo.type.startsWith("image/")) {
                    const lector = new FileReader();
                    
                    lector.onload = function (e) {
                        const divCol = document.createElement("div");
                        divCol.classList.add("col", "position-relative", "img-temporal"); // Cambiado a col para adaptarse a tu grid de Bootstrap
                        
                        divCol.innerHTML = `
                            <img src="${e.target.result}" class="img-thumbnail rounded w-100" style="height: 80px; object-fit: cover;">
                            <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-dark" style="z-index: 2;">Nuevo</span>
                        `;
                        contenedorPreview.appendChild(divCol);
                    };
                    
                    lector.readAsDataURL(archivo);
                }
            });
        });
    }
});