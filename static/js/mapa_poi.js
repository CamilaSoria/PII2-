// apps/gestion/static/js/mapa_poi.js

document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 [Mapas POI] Script corporativo optimizado para estructuración de rutas.");

    // =========================================================================
    // 1. MAPA PARA EL MODAL DEL TURISTA (Si existe en este entorno)
    // =========================================================================
    const modalTurista = document.getElementById('modalCrearPOI');
    if (modalTurista) {
        let mapaTurista = null;
        let marcadorTurista = null;

        modalTurista.addEventListener('shown.bs.modal', function () {
            const contenedor = document.getElementById('mapaCrear');
            if (contenedor && !mapaTurista) {
                mapaTurista = L.map('mapaCrear').setView([-16.5000, -68.1193], 13);
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(mapaTurista);

                mapaTurista.on('click', function (e) {
                    modalTurista.querySelector('input[name="latitud"]').value = e.latlng.lat.toFixed(6);
                    modalTurista.querySelector('input[name="longitud"]').value = e.latlng.lng.toFixed(6);
                    if (marcadorTurista) {
                        marcadorTurista.setLatLng(e.latlng);
                    } else {
                        marcadorTurista = L.marker(e.latlng, { draggable: true }).addTo(mapaTurista);
                    }
                });
            } else if (mapaTurista) {
                mapaTurista.invalidateSize();
            }
        });
    }

    // =========================================================================
    // 2. MAPA PARA EL MODAL DEL AGENTE DE VENTAS (Buscador Integrado Oficial)
    // =========================================================================
    const modalAgente = document.getElementById('modalCrearPoiAgente');
    if (modalAgente) {
        let mapaAgente = null;
        let marcadorAgente = null;

        modalAgente.addEventListener('shown.bs.modal', function () {
            const contenedor = document.getElementById('mapaCrearAgente');
            
            if (contenedor && !mapaAgente) {
                // Instanciamos el mapa base
                mapaAgente = L.map('mapaCrearAgente').setView([-16.5000, -68.1193], 13);

                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(mapaAgente);

                // Caja de control oficial de Leaflet para el Buscador Integrado
                const buscadorControl = L.control({ position: 'topleft' });
                
                buscadorControl.onAdd = function () {
                    const div = L.DomUtil.create('div', 'leaflet-bar custom-search-box');
                    div.innerHTML = `
                        <div class="input-group input-group-sm shadow-sm" style="width: 240px; padding: 4px; background: white; border-radius: 6px;">
                            <input type="text" id="inputBuscarAgente" class="form-control border-1" placeholder="Buscar coordenadas globales...">
                            <button class="btn btn-dark btn-sm fw-bold" type="button" id="btnBuscarAgente">Ir</button>
                        </div>
                    `;
                    L.DomEvent.disableClickPropagation(div);
                    return div;
                };
                buscadorControl.addTo(mapaAgente);

                // Acción de geocodificación mediante Nominatim API
                document.getElementById('btnBuscarAgente').onclick = function() {
                    const textoBusqueda = document.getElementById('inputBuscarAgente').value.trim();
                    if (!textoBusqueda) return;

                    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(textoBusqueda)}&limit=1`)
                        .then(response => response.json())
                        .then(data => {
                            if (data && data.length > 0) {
                                const lat = parseFloat(data[0].lat);
                                const lon = parseFloat(data[0].lon);

                                mapaAgente.setView([lat, lon], 15);

                                if (marcadorAgente) {
                                    marcadorAgente.setLatLng([lat, lon]);
                                } else {
                                    marcadorAgente = L.marker([lat, lon], { draggable: true }).addTo(mapaAgente);
                                }

                                // Guardamos las coordenadas limpias en el formulario automático de Django
                                modalAgente.querySelector('#id_latitud').value = lat.toFixed(6);
                                modalAgente.querySelector('#id_longitud').value = lon.toFixed(6);
                            }
                        })
                        .catch(err => console.error("Error en geocodificador:", err));
                };

                // Evento click directo en el plano del mapa
                mapaAgente.on('click', function (e) {
                    const lat = e.latlng.lat.toFixed(6);
                    const lon = e.latlng.lng.toFixed(6);
                    
                    modalAgente.querySelector('#id_latitud').value = lat;
                    modalAgente.querySelector('#id_longitud').value = lon;

                    if (marcadorAgente) {
                        marcadorAgente.setLatLng(e.latlng);
                    } else {
                        marcadorAgente = L.marker(e.latlng, { draggable: true }).addTo(mapaAgente);
                    }
                });
            }
            
            // Garantía de renderizado completo mediante hilos asíncronos cortos
            setTimeout(function() {
                if (mapaAgente) {
                    mapaAgente.invalidateSize();
                }
            }, 150);
        });
    }

    // =========================================================================
    // 3. MAPA PARA LOS MODALES DE "EDITAR POI"
    // =========================================================================
    document.addEventListener('click', function (event) {
        const botonEditar = event.target.closest('[data-bs-target^="#modalEditarPoi"], [data-bs-target^="#modalEditarPOI"]');
        if (!botonEditar) return;
        const targetId = botonEditar.getAttribute('data-bs-target').replace('#', '');
        const modalEditar = document.getElementById(targetId);
        if (!modalEditar) return;
        const divMapa = modalEditar.querySelector('[id^="mapaEditar"]');
        if (!divMapa) return;

        modalEditar.addEventListener('shown.bs.modal', function () {
            if (!divMapa.classList.contains('leaflet-container')) {
                const latInicial = parseFloat(divMapa.getAttribute('data-lat')) || -16.5000;
                const lonInicial = parseFloat(divMapa.getAttribute('data-lon')) || -70.6483;
                const mapaEditar = L.map(divMapa.id).setView([latInicial, lonInicial], 14);
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}').addTo(mapaEditar);
                let marcadorEditar = L.marker([latInicial, lonInicial], { draggable: true }).addTo(mapaEditar);
                
                mapaEditar.on('click', function(e) {
                    marcadorEditar.setLatLng(e.latlng);
                    modalEditar.querySelector('#id_latitud').value = e.latlng.lat.toFixed(6);
                    modalEditar.querySelector('#id_longitud').value = e.latlng.lng.toFixed(6);
                });
            }
        }, { once: true });
    });
});

// =========================================================================
    // 4. MAPA PARA LA VISTA DE EDICIÓN COMPLETA (ADMIN/AGENTE - Con Buscador Oficial)
    // =========================================================================
    const divMapaEdicionDirecta = document.querySelector('[id^="mapaEditar_"]');
    
    if (divMapaEdicionDirecta) {
        console.log("📍 [Mapas POI] Inicializando mapa de edición directa con buscador...");

        // Coordenadas iniciales guardadas en el POI
        const latInicial = parseFloat(divMapaEdicionDirecta.getAttribute('data-lat')) || -16.5000;
        const lonInicial = parseFloat(divMapaEdicionDirecta.getAttribute('data-lon')) || -70.6483;

        // Instanciamos el mapa directo
        const mapaEdicionDirecta = L.map(divMapaEdicionDirecta.id).setView([latInicial, lonInicial], 15);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapaEdicionDirecta);

        // Ponemos el marcador original
        let marcadorEdicionDirecta = L.marker([latInicial, lonInicial], { 
            draggable: true 
        }).addTo(mapaEdicionDirecta);

        // 🔍 INYECTAMOS EL BUSCADOR AL MAPA DE EDICIÓN
        const buscadorControlEdicion = L.control({ position: 'topleft' });
        
        buscadorControlEdicion.onAdd = function () {
            const div = L.DomUtil.create('div', 'leaflet-bar custom-search-box');
            div.innerHTML = `
                <div class="input-group input-group-sm shadow-sm" style="width: 240px; padding: 4px; background: white; border-radius: 6px;">
                    <input type="text" id="inputBuscarEdicion" class="form-control border-1" placeholder="Buscar nueva ubicación...">
                    <button class="btn btn-warning btn-sm fw-bold text-dark" type="button" id="btnBuscarEdicion">Ir</button>
                </div>
            `;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        buscadorControlEdicion.addTo(mapaEdicionDirecta);

        // Lógica de búsqueda con la API de Nominatim
        document.getElementById('btnBuscarEdicion').onclick = function() {
            const textoBusqueda = document.getElementById('inputBuscarEdicion').value.trim();
            if (!textoBusqueda) return;

            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(textoBusqueda)}&limit=1`)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const lat = parseFloat(data[0].lat);
                        const lon = parseFloat(data[0].lon);

                        // Centramos el mapa en el nuevo destino encontrado
                        mapaEdicionDirecta.setView([lat, lon], 15);
                        marcadorEdicionDirecta.setLatLng([lat, lon]);

                        // Volcamos los nuevos datos directamente en los inputs de Django
                        document.getElementById('id_latitud').value = lat.toFixed(6);
                        document.getElementById('id_longitud').value = lon.toFixed(6);
                    } else {
                        alert("No se encontraron resultados para esa ubicación.");
                    }
                })
                .catch(err => console.error("Error en buscador de edición:", err));
        };

        // Evento al hacer clic en el mapa
        mapaEdicionDirecta.on('click', function (e) {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            
            marcadorEdicionDirecta.setLatLng(e.latlng);
            document.getElementById('id_latitud').value = lat;
            document.getElementById('id_longitud').value = lon;
        });

        // Evento al arrastrar el marcador
        marcadorEdicionDirecta.on('dragend', function (e) {
            const posicion = marcadorEdicionDirecta.getLatLng();
            document.getElementById('id_latitud').value = posicion.lat.toFixed(6);
            document.getElementById('id_longitud').value = posicion.lng.toFixed(6);
        });

        // Refresco de tamaño
        setTimeout(function () {
            mapaEdicionDirecta.invalidateSize();
        }, 200);
    }
// =========================================================================
    // 5. MAPA PARA LA GESTIÓN DE DESTINOS (Crear y Editar con Buscador Oficial)
    // =========================================================================
    const divMapaDestino = document.getElementById('mapaDestinoAgente');
    
    if (divMapaDestino) {
        console.log("📍 [Mapas] Inicializando mapa de destinos con buscador integrado...");

        // Coordenadas guardadas u origen por defecto
        const latGuardada = parseFloat(divMapaDestino.getAttribute('data-lat'));
        const lonGuardada = parseFloat(divMapaDestino.getAttribute('data-lon'));
        
        const latInicial = !isNaN(latGuardada) && latGuardada !== 0 ? latGuardada : -33.4569;
        const lonInicial = !isNaN(lonGuardada) && lonGuardada !== 0 ? lonGuardada : -70.6483;

        // Instanciamos el mapa en su contenedor específico
        const mapaDestino = L.map(divMapaDestino.id).setView([latInicial, lonInicial], 13);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapaDestino);

        // Colocamos el marcador arrastrable
        let marcadorDestino = L.marker([latInicial, lonInicial], { 
            draggable: true 
        }).addTo(mapaDestino);

        // Si es una creación totalmente limpia, dejamos los inputs vacíos en el arranque
        if (isNaN(latGuardada)) {
            document.getElementById('id_latitud').value = '';
            document.getElementById('id_longitud').value = '';
        }

        // 🔍 INYECTAMOS EL BUSCADOR AL MAPA DE DESTINOS
        const buscadorControlDestino = L.control({ position: 'topleft' });
        
        buscadorControlDestino.onAdd = function () {
            const div = L.DomUtil.create('div', 'leaflet-bar custom-search-box');
            div.innerHTML = `
                <div class="input-group input-group-sm shadow-sm" style="width: 240px; padding: 4px; background: white; border-radius: 6px;">
                    <input type="text" id="inputBuscarDestino" class="form-control border-1" placeholder="Buscar ciudad, país...">
                    <button class="btn btn-warning btn-sm fw-bold text-dark" type="button" id="btnBuscarDestino">Ir</button>
                </div>
            `;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        buscadorControlDestino.addTo(mapaDestino);

        // Lógica de búsqueda con la API de Nominatim
        document.getElementById('btnBuscarDestino').onclick = function(e) {
            e.preventDefault();
            const textoBusqueda = document.getElementById('inputBuscarDestino').value.trim();
            if (!textoBusqueda) return;

            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(textoBusqueda)}&limit=1`)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const lat = parseFloat(data[0].lat);
                        const lon = parseFloat(data[0].lon);

                        mapaDestino.setView([lat, lon], 13);
                        marcadorDestino.setLatLng([lat, lon]);

                        document.getElementById('id_latitud').value = lat.toFixed(6);
                        document.getElementById('id_longitud').value = lon.toFixed(6);
                    } else {
                        alert("No se encontraron resultados para esa ubicación.");
                    }
                })
                .catch(err => console.error("Error en buscador de destinos:", err));
        };

        // Evento al hacer clic directo en cualquier punto del mapa
        mapaDestino.on('click', function (e) {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            
            marcadorDestino.setLatLng(e.latlng);
            document.getElementById('id_latitud').value = lat;
            document.getElementById('id_longitud').value = lon;
        });

        // Evento al arrastrar el pin/marcador
        marcadorDestino.on('dragend', function () {
            const posicion = marcadorDestino.getLatLng();
            document.getElementById('id_latitud').value = posicion.lat.toFixed(6);
            document.getElementById('id_longitud').value = posicion.lng.toFixed(6);
        });

        // Refresco nativo de tamaño por si se renderiza asíncronamente
        setTimeout(function () {
            mapaDestino.invalidateSize();
        }, 250);
    }

// =========================================================================
    // 6. MAPA DE PREVISUALIZACIÓN DE RUTA TURÍSTICA (Edición Dinámica en Vivo)
    // =========================================================================
    const divMapaRuta = document.getElementById('mapaVistaRuta');
    
    if (divMapaRuta) {
        console.log("🗺️ [Mapas POI] Inicializando trazador interactivo de trayectos para la edición de rutas.");
        
        // Coordenadas base por defecto (las mismas de tu script: Santiago de Chile o zona de cobertura)
        const mapaRuta = L.map('mapaVistaRuta').setView([-16.5000, -68.1193], 12);
        
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapaRuta);

        // Capa para la línea del recorrido
        let capaLineas = L.polyline([], {
            color: '#0d6efd', // Azul corporativo
            weight: 5,
            opacity: 0.8,
            dashArray: '8, 12' // Línea segmentada estética que simula un trayecto vial
        }).addTo(mapaRuta);

        // Grupo contenedor para limpiar y añadir marcadores de paradas fácilmente
        let grupoMarcadores = L.featureGroup().addTo(mapaRuta);

        // 🔄 Función principal: Recorre los elementos del DOM y redibuja la ruta en el mapa
        function redibujarTrayectoRuta() {
            if (!grupoMarcadores || !capaLineas) return;
            
            grupoMarcadores.clearLayers();
            let coordenadas = [];

            const filasParadas = document.querySelectorAll('.fila-parada:not(.d-none):not(#parada-template .fila-parada)');
            console.log(`🧐 [Mapa RT] Analizando ${filasParadas.length} filas activas...`);
            
            filasParadas.forEach((fila, index) => {
                const selectPoi = fila.querySelector('select.select-poi-mapa') || fila.querySelector('select');
                const inputOrden = fila.querySelector('.parada-orden');
                
                if (selectPoi && selectPoi.value) {
                    const idSeleccionado = selectPoi.value;
                    let opcionSeleccionada = selectPoi.options[selectPoi.selectedIndex];
                    
                    if (opcionSeleccionada) {
                        let latRaw = opcionSeleccionada.getAttribute('data-lat');
                        let lonRaw = opcionSeleccionada.getAttribute('data-lon');

                        // 🚀 EL PARCHE MAESTRO: Si el clonador rompió los atributos data-, los rescatamos del template original
                        if (!latRaw || latRaw === "null" || latRaw === "undefined") {
                            console.log(`⚠️ [Plan B] Fila N°${index + 1} perdió sus atributos. Rescatando coordenadas para POI ID: ${idSeleccionado}...`);
                            
                            // Buscamos en CUALQUIER otro select de la página que SÍ tenga la opción con datos válidos
                            const opcionConDatos = document.querySelector(`select option[value="${idSeleccionado}"][data-lat]:not([data-lat="null"])`);
                            
                            if (opcionConDatos) {
                                latRaw = opcionConDatos.getAttribute('data-lat');
                                lonRaw = opcionConDatos.getAttribute('data-lon');
                                console.log(`✅ [Plan B Éxito] Coordenadas recuperadas: Lat: ${latRaw} | Lon: ${lonRaw}`);
                            }
                        }
                        
                        const lat = parseFloat(latRaw);
                        const lon = parseFloat(lonRaw);

                        if (!isNaN(lat) && !isNaN(lon)) {
                            coordenadas.push([lat, lon]);
                            
                            L.marker([lat, lon])
                                .addTo(grupoMarcadores)
                                .bindPopup(`<b>Parada N° ${inputOrden ? (inputOrden.value || '?') : '?'}:</b> ${opcionSeleccionada.text}`);
                        }
                    }
                }
            });

            // Trazamos la línea y refrescamos el tamaño de Leaflet por si acaso
            if (coordenadas.length > 0) {
                capaLineas.setLatLngs(coordenadas);
                mapaRuta.fitBounds(grupoMarcadores.getBounds(), { padding: [40, 40] });
                
                // Forzamos el refresco del mapa para evitar congelamientos en modales/vistas dinámicas
                setTimeout(() => { mapaRuta.invalidateSize(); }, 50);
                console.log(`🚀 [Mapa RT] Trayecto dibujado en vivo con ${coordenadas.length} puntos.`);
            } else {
                capaLineas.setLatLngs([]);
            }
        }
        
       // 1. Escucha global nativa para cambios (Funciona para el input de orden)
        document.addEventListener('change', function(e) {
            if (e.target && (e.target.classList.contains('select-poi-mapa') || e.target.name.includes('-poi') || e.target.classList.contains('parada-orden'))) {
                console.log("🎯 [Rutas RT] Cambio nativo detectado. Redibujando...");
                redibujarTrayectoRuta();
            }
        });

        // 2. 🚀 EL ARREGLO MAESTRO: Escuchar eventos de librerías dinámicas (Select2 / JQuery)
        // Si tu script de paradas usa Select2, este bloque atrapará el cambio al instante
        if (typeof jQuery !== 'undefined') {
            // Escuchamos el evento 'select2:select' en cualquier selector de paradas
            jQuery(document).on('change select2:select', 'select[name$="-poi"]', function() {
                console.log("🔌 [Rutas RT] Cambio detectado mediante intermediario de UI. Redibujando mapa...");
                // Le damos un mini delay de 50ms para que la librería termine de actualizar el DOM
                setTimeout(redibujarTrayectoRuta, 50);
            });
        }

        // 3. Escucha global para el botón de eliminar ❌ (Este ya sabemos que funciona de 10)
        document.addEventListener('click', function(e) {
            if (e.target && (e.target.classList.contains('btn-remove-parada') || e.target.closest('.btn-remove-parada'))) {
                console.log("❌ [Rutas RT] Parada eliminada. Recalculando mapa...");
                setTimeout(redibujarTrayectoRuta, 150);
            }
        });

        // 4. Observador de mutaciones (Conserva este bloque igual)
        const contenedorParadas = document.getElementById('contenedor-paradas');
        if (contenedorParadas) {
            const observadorDOM = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length > 0) {
                        redibujarTrayectoRuta();
                    }
                });
            });
            observadorDOM.observe(contenedorParadas, { childList: true });
        }

        setTimeout(redibujarTrayectoRuta, 500);
    }

// =========================================================================
    // 7. MAPA PARA LA GESTIÓN DE HOTELES (Crear y Editar con Buscador - HU14)
    // =========================================================================
const divMapaHotel = document.getElementById('mapaHotelAgente');
    
    if (divMapaHotel) {
        console.log("🏨 [Mapas] Inicializando mapa de hoteles con buscador para la HU14...");

        const latGuardada = parseFloat(divMapaHotel.getAttribute('data-lat'));
        const lonGuardada = parseFloat(divMapaHotel.getAttribute('data-lon'));
        
        const latInicial = !isNaN(latGuardada) && latGuardada !== 0 ? latGuardada : -33.4569;
        const lonInicial = !isNaN(lonGuardada) && lonGuardada !== 0 ? lonGuardada : -70.6483;

        // 🔴 Se instancia usando el ID único 'mapaHotelAgente'
        const mapaHotel = L.map(divMapaHotel.id).setView([latInicial, lonInicial], 14);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapaHotel);

        let marcadorHotel = L.marker([latInicial, lonInicial], { 
            draggable: true 
        }).addTo(mapaHotel);

        // ... El resto del buscador interno e inputs se queda exactamente igual ...

        // Si es una creación desde cero, dejamos los campos vacíos en el arranque para validar
        if (isNaN(latGuardada)) {
            if(document.getElementById('id_latitud')) document.getElementById('id_latitud').value = '';
            if(document.getElementById('id_longitud')) document.getElementById('id_longitud').value = '';
        }

        // 🔍 INYECTAMOS EL BUSCADOR AL MAPA DE HOTELES
        const buscadorControlHotel = L.control({ position: 'topleft' });
        
        buscadorControlHotel.onAdd = function () {
            const div = L.DomUtil.create('div', 'leaflet-bar custom-search-box');
            div.innerHTML = `
                <div class="input-group input-group-sm shadow-sm" style="width: 250px; padding: 4px; background: white; border-radius: 6px;">
                    <input type="text" id="inputBuscarHotel" class="form-control border-1" placeholder="Buscar dirección, calle o zona...">
                    <button class="btn btn-primary btn-sm fw-bold" type="button" id="btnBuscarHotel">Buscar</button>
                </div>
            `;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        buscadorControlHotel.addTo(mapaHotel);

        // Función para actualizar de golpe los campos invisibles de Django (Lat/Lon)
        function actualizarCoordenadasHotel(lat, lon) {
            const inputLat = document.getElementById('id_latitud');
            const inputLon = document.getElementById('id_longitud');
            if (inputLat) inputLat.value = parseFloat(lat).toFixed(6);
            if (inputLon) inputLon.value = parseFloat(lon).toFixed(6);
            console.log(`📌 [HU14] Campos actualizados -> Lat: ${lat} | Lon: ${lon}`);
        }

        // Lógica del botón de búsqueda del mapa (Conexión API Nominatim OpenStreetMap)
        document.getElementById('btnBuscarHotel').onclick = function(e) {
            e.preventDefault();
            const textoBusqueda = document.getElementById('inputBuscarHotel').value.trim();
            if (!textoBusqueda) return;

            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(textoBusqueda)}&limit=1`)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const lat = parseFloat(data[0].lat);
                        const lon = parseFloat(data[0].lon);

                        mapaHotel.setView([lat, lon], 15);
                        marcadorHotel.setLatLng([lat, lon]);
                        
                        // Guardamos la info para que viaje en el POST
                        actualizarCoordenadasHotel(lat, lon);
                    } else {
                        alert("No pudimos encontrar coordenadas exactas para esa dirección.");
                    }
                })
                .catch(err => console.error("Error en el buscador del mapa de hoteles:", err));
        };

        // Evento 1: Clic directo en cualquier parte de la cuadrícula del mapa
        mapaHotel.on('click', function (e) {
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;
            
            marcadorHotel.setLatLng(e.latlng);
            actualizarCoordenadasHotel(lat, lon);
        });

        // Evento 2: Cuando el usuario arrastra manualmente el pin por la calle
        marcadorHotel.on('dragend', function () {
            const posicion = marcadorHotel.getLatLng();
            actualizarCoordenadasHotel(posicion.lat, posicion.lng);
        });

        // Forzar el redibujado de Leaflet (evita parches grises o mapas cortados)
        setTimeout(function () {
            mapaHotel.invalidateSize();
        }, 300);
    }