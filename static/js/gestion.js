// static/js/gestion.js

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const tableBody = document.getElementById('usuarios-table-body');
    let debounceTimer;

    if (searchInput && tableBody) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            // ⏱️ DEBOUNCE: Espera 300ms desde que el usuario deja de escribir antes de consultar
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                
                // Hacemos la petición asíncrona a la misma URL de Django pasándole el parámetro ?search=
                fetch(`?search=${encodeURIComponent(query)}`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest' // Le avisa a Django que es una petición AJAX
                    }
                })
                .then(response => {
                    if (!response.ok) throw new Error('Error en la respuesta del servidor');
                    return response.text();
                })
                .then(html => {
                    // Reemplazamos el cuerpo de la tabla dinámicamente con las nuevas filas procesadas
                    tableBody.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error al filtrar dinámicamente:', error);
                });

            }, 300); 
        });
    }
});