// apps/gestion/static/gestion/js/editar_galeria.js

document.addEventListener('DOMContentLoaded', function () {
    
    // 🗑️ 1. ELIMINAR FOTO ANTIGUA
    const botonesBorrar = document.querySelectorAll('.btn-borrar-foto');
    botonesBorrar.forEach(boton => {
        boton.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Leemos la URL calculada por Django
            const urlDestino = this.getAttribute('data-url');
            const fotoId = this.getAttribute('data-id');
            
            // 🚨 LOG DE CONTROL: Veremos en la consola qué URL está leyendo
            console.log("Intentando borrar. URL detectada por JS:", urlDestino);
            
            if (!urlDestino) {
                alert("Error: El botón no tiene el atributo data-url configurado.");
                return;
            }

            if (!confirm('¿Estás seguro de que deseas eliminar permanentemente esta imagen de la galería?')) return;

            fetch(urlDestino, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Error en la respuesta del servidor (Status: ' + response.status + ')');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const contenedorFoto = document.getElementById(`foto-wrapper-${fotoId}`);
                    if (contenedorFoto) {
                        contenedorFoto.style.transition = 'all 0.3s ease';
                        contenedorFoto.style.opacity = '0';
                        contenedorFoto.style.transform = 'scale(0.7)';
                        setTimeout(() => { contenedorFoto.remove(); }, 300);
                    }
                } else {
                    alert('El servidor no autorizó el borrado de la imagen.');
                }
            })
            .catch(err => {
                console.error("Error AJAX:", err);
                alert('Hubo un problema al intentar eliminar.');
            });
        });
    });

    // 👑 2. ASIGNAR UNA FOTO EXISTENTE COMO PORTADA
    const botonesPortada = document.querySelectorAll('.btn-hacer-portada');
    botonesPortada.forEach(boton => {
        boton.addEventListener('click', function (e) {
            e.preventDefault();
            
            const urlDestino = this.getAttribute('data-url');
            
            // 🚨 LOG DE CONTROL: Veremos en la consola qué URL está leyendo
            console.log("Intentando cambiar portada. URL detectada por JS:", urlDestino);

            if (!urlDestino) {
                alert("Error: El botón no tiene el atributo data-url configurado.");
                return;
            }

            fetch(urlDestino, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Error en el servidor (Status: ' + response.status + ')');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('No se pudo asignar esta foto como portada.');
                }
            })
            .catch(err => console.error("Error AJAX:", err));
        });
    });

    // Función auxiliar para el Token CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 🟢 3. ALTERNAR ESTADO DE APROBACIÓN DEL POI (MODERACIÓN EN VIVO)
    const btnEstado = document.getElementById('btn-cambiar-estado');
    const badgeEstado = document.getElementById('badge-estado-poi');

    if (btnEstado && badgeEstado) {
        btnEstado.addEventListener('click', function (e) {
            e.preventDefault();
            const urlDestino = this.getAttribute('data-url');

            fetch(urlDestino, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Si el nuevo estado es APROBADO
                    if (data.nuevo_estado === 'APROBADO') {
                        badgeEstado.className = "badge p-2 rounded-pill bg-success text-white";
                        badgeEstado.innerText = "🟢 Publicado (Aprobado)";
                        
                        btnEstado.className = "btn btn-outline-danger px-3 shadow-sm fw-bold rounded-pill";
                        btnEstado.innerText = "🛑 Desactivar / Rechazar";
                    } 
                    // Si el nuevo estado regresó a PENDIENTE
                    else {
                        badgeEstado.className = "badge p-2 rounded-pill bg-danger text-white";
                        badgeEstado.innerText = "⏳ En Revisión (Pendiente)";
                        
                        btnEstado.className = "btn btn-success px-3 shadow-sm fw-bold rounded-pill";
                        btnEstado.innerText = "✅ Aprobar Ahora";
                    }
                    
                    // Opcional: Mostrar una pequeña alerta flotante o toast con el mensaje de Django
                    console.log(data.message);
                } else {
                    alert('No se pudo cambiar el estado del atractivo.');
                }
            })
            .catch(err => console.error("Error en la moderación AJAX:", err));
        });
    }
});