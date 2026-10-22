// static/js/favoritos.js

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.btn-fav-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const poiId = this.getAttribute('data-poi-id');
            const btn = document.getElementById(`btn-fav-${poiId}`);
            const contador = document.getElementById(`contador-fav-${poiId}`);
            
            // 🚨 CAMBIO CLAVE: Leemos la URL exacta que generó Django
            const url = this.getAttribute('data-url'); 
            
            // Buscamos el token CSRF obligatorio de Django
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Enviamos la petición
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                // Validación de seguridad por si acaso
                if (!response.ok) {
                    throw new Error(`Error en el servidor: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    if (contador) {
                        contador.textContent = data.total_favoritos;
                    }
                    
                    if (data.guardado) {
                        btn.classList.remove('btn-outline-danger');
                        btn.classList.add('btn-danger');
                        btn.innerHTML = '❤️ Guardado';
                    } else {
                        btn.classList.remove('btn-danger');
                        btn.classList.add('btn-outline-danger');
                        btn.innerHTML = '❤️ Guardar Lugar';
                    }
                }
            })
            .catch(error => console.error('Error al procesar el favorito:', error));
        });
    });
});