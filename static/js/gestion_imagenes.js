document.addEventListener('DOMContentLoaded', function() {
    const contenedor = document.getElementById('contenedor-imagenes');
    const btnAdd = document.getElementById('btn-add-imagen');
    const totalFormsInput = document.getElementById('id_imagenes_galeria-TOTAL_FORMS');
    const templateHTML = document.getElementById('imagen-template').innerHTML;

    // ➕ AÑADIR NUEVA FOTO
    if (btnAdd) {
        btnAdd.addEventListener('click', function() {
            let formIdx = parseInt(totalFormsInput.value);
            
            // Reemplazamos el prefijo de Django por el índice correcto
            let nuevaFilaHTML = templateHTML.replace(/__prefix__/g, formIdx);
            
            // Insertamos antes del template oculto
            document.getElementById('imagen-template').insertAdjacentHTML('beforebegin', nuevaFilaHTML);
            
            // Sumamos 1 al contador oficial de Django
            totalFormsInput.value = formIdx + 1;
        });
    }

    // ❌ QUITAR FOTO
    if (contenedor) {
        contenedor.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-remove-imagen') || e.target.closest('.btn-remove-imagen')) {
                const boton = e.target.classList.contains('btn-remove-imagen') ? e.target : e.target.closest('.btn-remove-imagen');
                const fila = boton.closest('.fila-imagen');
                
                const checkboxDelete = fila.querySelector('input[type="checkbox"][name$="-DELETE"]');
                
                if (checkboxDelete) {
                    // Si ya existía en BD, se marca para borrar y se oculta
                    checkboxDelete.checked = true;
                    fila.classList.add('d-none');
                } else {
                    // Si era nueva en el DOM, se elimina directamente
                    fila.remove();
                }
            }
        });
    }
});