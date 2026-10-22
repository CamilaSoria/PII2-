// apps/gestion/static/gestion/js/preview_images.js

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.querySelector('input[type="file"][multiple]');
    const previewContainer = document.getElementById('preview-container');
    const placeholder = document.getElementById('preview-placeholder');

    if (fileInput && previewContainer) {
        // 🛍️ Nuestra "bolsa virtual" para acumular los archivos seleccionados
        let archivosAcumulados = [];
        // 👑 Registra cuál archivo fue seleccionado explícitamente como portada
        let archivoPortada = null;

        fileInput.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                // Quitamos el texto de "ninguna imagen" o placeholder anterior
                if (placeholder && (previewContainer.contains(placeholder) || previewContainer.innerHTML.includes('📸'))) {
                    previewContainer.innerHTML = '';
                }

                // Agregamos los nuevos archivos al acumulador global
                Array.from(this.files).forEach(file => {
                    if (file.type.startsWith('image/')) {
                        // Evitamos duplicados exactos por nombre y tamaño si vuelven a abrir el selector
                        if (!archivosAcumulados.some(f => f.name === file.name && f.size === file.size)) {
                            archivosAcumulados.push(file);
                            
                            // Si es el primer archivo absoluto de la bolsa, lo marcamos como portada inicial
                            if (!archivoPortada) {
                                archivoPortada = file;
                            }
                            
                            renderizarMiniatura(file);
                        }
                    }
                });

                // Sincronizamos los archivos de la bolsa con el input real de Django
                actualizarInputDjango();
            }
        });

        // 🖼️ Función encargada de construir visualmente la miniatura
        function renderizarMiniatura(file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                // Crear el contenedor de la miniatura
                const imgWrapper = document.createElement('div');
                imgWrapper.className = 'position-relative d-inline-block m-2 card-previsualizacion';
                imgWrapper.style.width = '100px';
                imgWrapper.style.height = '80px';
                imgWrapper.style.cursor = 'pointer';
                // Guardamos una referencia al nombre en el DOM para poder reordenar visualmente después
                imgWrapper.setAttribute('data-filename', file.name);

                // La imagen previsualizada
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = `img-thumbnail shadow-sm w-100 h-100 ${archivoPortada === file ? 'border-warning border-3' : ''}`;
                img.style.objectFit = 'cover';
                img.title = "Haz clic aquí para marcarla como Portada principal";

                // 👑 Badge flotante indicador de Portada
                const badgePortada = document.createElement('span');
                badgePortada.className = `position-absolute badge bg-warning text-dark fw-bold p-1 m-1 top-0 start-0 small ${archivoPortada === file ? '' : 'd-none'}`;
                badgePortada.style.fontSize = '10px';
                badgePortada.innerHTML = 'Portada';

                // ❌ Botón para eliminar esta foto específica antes de guardar
                const btnDelete = document.createElement('button');
                btnDelete.innerHTML = '×';
                btnDelete.type = 'button';
                btnDelete.className = 'btn btn-danger btn-sm p-0 position-absolute rounded-circle';
                btnDelete.style.top = '-8px';
                btnDelete.style.right = '-8px';
                btnDelete.style.width = '22px';
                btnDelete.style.height = '22px';
                btnDelete.style.lineHeight = '16px';
                btnDelete.style.zIndex = '10';

                // 👑 INTERACCIÓN 1: Seleccionar como Portada al hacer clic en la foto o el contenedor
                img.addEventListener('click', function(event) {
                    event.stopPropagation(); // Evitamos interferencias
                    archivoPortada = file;
                    
                    // Actualizamos las clases visuales de todas las miniaturas en la carga actual
                    previewContainer.querySelectorAll('.card-previsualizacion').forEach(wrapper => {
                        const esEsta = wrapper.getAttribute('data-filename') === file.name;
                        const wrapperImg = wrapper.querySelector('img');
                        const wrapperBadge = wrapper.querySelector('.badge');
                        
                        if (esEsta) {
                            wrapperImg.classList.add('border-warning', 'border-3');
                            wrapperBadge.classList.remove('d-none');
                        } else {
                            wrapperImg.classList.remove('border-warning', 'border-3');
                            wrapperBadge.classList.add('d-none');
                        }
                    });

                    // Sincronizamos la lista empujando esta foto al inicio
                    actualizarInputDjango();
                });

                // ❌ INTERACCIÓN 2: Quitar la foto si el usuario se arrepiente
                btnDelete.addEventListener('click', function(event) {
                    event.stopPropagation(); // Evitamos gatillar el clic de la portada
                    
                    // La eliminamos del arreglo virtual
                    archivosAcumulados = archivosAcumulados.filter(f => f !== file);
                    // Quitamos su miniatura del HTML
                    imgWrapper.remove();
                    
                    // Si eliminamos la que era portada, reasignamos la nueva portada a la primera que quede libre
                    if (archivoPortada === file) {
                        archivoPortada = archivosAcumulados.length > 0 ? archivosAcumulados[0] : null;
                        
                        if (archivoPortada) {
                            // Buscamos la miniatura sobreviviente en el HTML y le encendemos la corona
                            const nuevaPortadaWrapper = previewContainer.querySelector(`[data-filename="${archivoPortada.name}"]`);
                            if (nuevaPortadaWrapper) {
                                nuevaPortadaWrapper.querySelector('img').classList.add('border-warning', 'border-3');
                                nuevaPortadaWrapper.querySelector('.badge').classList.remove('d-none');
                            }
                        }
                    }
                    
                    // Sincronizamos con el input
                    actualizarInputDjango();
                });
                
                imgWrapper.appendChild(img);
                imgWrapper.appendChild(badgePortada);
                imgWrapper.appendChild(btnDelete);
                previewContainer.appendChild(imgWrapper);
            };
            reader.readAsDataURL(file);
        }

        // 🧙‍♂️ Función mágica mejorada: Reordena y empaqueta para Django
        function actualizarInputDjango() {
            const dataTransfer = new DataTransfer();
            
            // Si el usuario eligió una portada, la obligamos a ir en la posición 0 del envío
            if (archivoPortada && archivosAcumulados.includes(archivoPortada)) {
                dataTransfer.items.add(archivoPortada);
            }
            
            // Metemos el resto de las imágenes secundarias a la cola
            archivosAcumulados.forEach(file => {
                if (file !== archivoPortada) {
                    dataTransfer.items.add(file);
                }
            });

            // Sobrescribimos la carga del input real
            fileInput.files = dataTransfer.files;

            // Si la bolsa se queda vacía, volvemos a poner el aviso descriptivo
            if (archivosAcumulados.length === 0 && placeholder) {
                previewContainer.innerHTML = '';
                previewContainer.appendChild(placeholder);
            }
        }
    }
});