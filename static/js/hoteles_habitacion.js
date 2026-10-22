document.addEventListener("DOMContentLoaded", function () {
    // ==========================================
    // 1. MANEJO DINÁMICO DEL FORMSET DE HABITACIONES
    // ==========================================
    const contenedor = document.getElementById("contenedor-habitaciones");
    const plantilla = document.getElementById("plantilla-habitacion");
    const totalForms = document.getElementById("id_tipos_habitacion-TOTAL_FORMS");
    const btnAgregar = document.getElementById("btn-agregar-habitacion");

    if (btnAgregar && contenedor && plantilla) {
btnAgregar.addEventListener("click", function() {
        let formIdx = parseInt(totalForms.value);
        let clon = plantilla.cloneNode(true);
        
        clon.id = "";
        clon.classList.remove("d-none");
        
        // 🟢 Buscamos los data-name y los transformamos en nombres procesables por Django
        clon.querySelectorAll("[data-name]").forEach(input => {
            let nombreReal = input.getAttribute("data-name").replace(/__prefix__/g, formIdx);
            input.setAttribute("name", nombreReal);
            input.removeAttribute("data-name"); // Limpiamos el atributo temporal
        });

        // Botón remover para las nuevas filas
        clon.querySelector(".btn-remover").addEventListener("click", function() {
            clon.remove();
            reindexarFormsets();
        });

        contenedor.appendChild(clon);
        totalForms.value = formIdx + 1;
    });
    }

    // Botón remover para filas EXISTENTES (Base de Datos)
    document.querySelectorAll(".btn-remover-existente").forEach(btn => {
        btn.addEventListener("click", function() {
            let fila = btn.closest(".item-habitacion");
            let checkboxDelete = fila.querySelector("input[type='checkbox'][name$='DELETE']");
            if (checkboxDelete) {
                checkboxDelete.checked = true;
                fila.classList.add("bg-danger-subtle", "opacity-50");
                btn.disabled = true;
            }
        });
    });

    // 🌟 CORRECCIÓN MAESTRA: Reordena los IDs para que Django reciba un arreglo limpio correlativo
    function reindexarFormsets() {
        let filas = contenedor.querySelectorAll(".item-habitacion:not(#plantilla-habitacion)");
        totalForms.value = filas.length;
        
        filas.forEach((fila, index) => {
            fila.querySelectorAll("input, select, textarea").forEach(input => {
                if (input.name) {
                    // Reemplaza el número de índice antiguo por el nuevo correlativo del DOM
                    input.name = input.name.replace(/tipos_habitacion-\d+-/, `tipos_habitacion-${index}-`);
                }
                if (input.id) {
                    input.id = input.id.replace(/id_tipos_habitacion-\d+-/, `id_tipos_habitacion-${index}-`);
                }
            });
        });
    }

    // ==========================================
    // 2. MAPA DE HOTELES CON COORDENADAS REALES Y BUSCADOR
    // ==========================================
    const divMapa = document.getElementById('mapaDestinoAgente');
    if (divMapa) {
        const latGuardada = parseFloat(divMapa.getAttribute('data-lat'));
        const lonGuardada = parseFloat(divMapa.getAttribute('data-lon'));
        
        const latInicial = !isNaN(latGuardada) && latGuardada !== 0 ? latGuardada : -33.4569;
        const lonInicial = !isNaN(lonGuardada) && lonGuardada !== 0 ? lonGuardada : -70.6483;

        const mapa = L.map('mapaDestinoAgente').setView([latInicial, lonInicial], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapa);
        
        let marcador = L.marker([latInicial, lonInicial], { draggable: true }).addTo(mapa);

        // Si es una creación totalmente limpia, limpiamos campos de Django para validar obligatoriedad
        if (isNaN(latGuardada)) {
            actualizarInputsCoordenadas('', '');
        }

        function actualizarInputsCoordenadas(lat, lon) {
            const inputLat = document.getElementById('id_latitud');
            const inputLon = document.getElementById('id_longitud');
            if (inputLat) inputLat.value = lat !== '' ? parseFloat(lat).toFixed(6) : '';
            if (inputLon) inputLon.value = lon !== '' ? parseFloat(lon).toFixed(6) : '';
        }

        // Eventos de interacción con el mapa
        mapa.on('click', function(e) {
            marcador.setLatLng(e.latlng);
            actualizarInputsCoordenadas(e.latlng.lat, e.latlng.lng);
        });

        marcador.on('dragend', function() {
            const posicion = marcador.getLatLng();
            actualizarInputsCoordenadas(posicion.lat, posicion.lng);
        });

        // 🔍 INYECTAMOS EL BUSCADOR OFICIAL NOMINATIM
        const buscadorControl = L.control({ position: 'topleft' });
        buscadorControl.onAdd = function () {
            const div = L.DomUtil.create('div', 'leaflet-bar custom-search-box');
            div.innerHTML = `
                <div class="input-group input-group-sm shadow-sm" style="width: 240px; padding: 4px; background: white; border-radius: 6px;">
                    <input type="text" id="inputBuscarHotel" class="form-control border-0 bg-transparent" placeholder="Buscar dirección...">
                    <button class="btn btn-primary btn-sm fw-bold" type="button" id="btnBuscarHotel">Ir</button>
                </div>
            `;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        buscadorControl.addTo(mapa);

        // Ejecución de búsqueda
        document.body.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'btnBuscarHotel') {
                e.preventDefault();
                const texto = document.getElementById('inputBuscarHotel').value.trim();
                if (!texto) return;

                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(texto)}&limit=1`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.length > 0) {
                            const newLat = parseFloat(data[0].lat);
                            const newLon = parseFloat(data[0].lon);
                            mapa.setView([newLat, newLon], 15);
                            marcador.setLatLng([newLat, newLon]);
                            actualizarInputsCoordenadas(newLat, newLon);
                        } else {
                            alert("Ubicación no encontrada.");
                        }
                    });
            }
        });

        setTimeout(() => { mapa.invalidateSize(); }, 300);
    }
});

// 3. ELIMINAR FOTOS MEDIANTE FETCH ASÍNCRONO (Mismo comportamiento global)
function eliminarFotoServidor(fotoId, boton) {
    if (confirm("¿Seguro que deseas quitar esta imagen de la galería del hotel?")) {
        fetch(`/gestion/hoteles/foto/${fotoId}/eliminar/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                boton.closest(".col").remove();
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    // 🗑️ ELIMINACIÓN ASÍNCRONA DE FOTOS (HOTEL)
    document.addEventListener("click", function (e) {
        const botonBorrar = e.target.closest(".btn-borrar-foto-hotel");
        if (botonBorrar) {
            e.preventDefault();
            const fotoId = botonBorrar.getAttribute("data-id");
            const urlAccion = botonBorrar.getAttribute("data-url");
            
            if (confirm("¿Estás seguro de que deseas eliminar esta imagen de la galería del hotel?")) {
                fetch(urlAccion, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "success") {
                        const wrapper = document.getElementById(`foto-wrapper-${fotoId}`);
                        if (wrapper) {
                            wrapper.style.transition = "all 0.3s ease";
                            wrapper.style.opacity = "0";
                            wrapper.style.transform = "scale(0.7)";
                            setTimeout(() => wrapper.remove(), 300);
                        }
                    } else {
                        alert("Error: " + data.message);
                    }
                })
                .catch(error => console.error("Error en la petición:", error));
            }
        }
    });

    // 👑 ASIGNACIÓN DE PORTADA ASÍNCRONA (HOTEL)
    document.addEventListener("click", function (e) {
        const botonPortada = e.target.closest(".btn-hacer-portada-hotel");
        if (botonPortada) {
            e.preventDefault();
            const urlAccion = botonPortada.getAttribute("data-url");

            fetch(urlAccion, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "success") {
                        // Recargamos la sección de forma limpia para pintar la nueva corona dorada y los bordes
                        window.location.reload();
                    } else {
                        alert("Error: " + data.message);
                    }
                })
                .catch(error => console.error("Error en la petición:", error));
        }
    });
});