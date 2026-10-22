document.addEventListener('DOMContentLoaded', function() {
    const contenedor = document.getElementById('contenedor-paradas');
    const btnAdd = document.getElementById('btn-add-parada');
    const totalFormsInput = document.getElementById('id_detalles_paradas-TOTAL_FORMS');
    const templateHTML = document.getElementById('parada-template').innerHTML;

    // Función para recalcular el número de orden sugerido automáticamente
    function actualizarOrdenesAutomaticas() {
        let ordenCounter = 1;
        contenedor.querySelectorAll('.fila-parada:not(.d-none):not(#parada-template .fila-parada)').forEach(fila => {
            const inputOrden = fila.querySelector('.parada-orden');
            if (inputOrden && !inputOrden.value) {
                inputOrden.value = ordenCounter;
            }
            ordenCounter++;
        });
    }

    // ➕ AÑADIR NUEVA FILA
    if (btnAdd) {
        btnAdd.addEventListener('click', function() {
            let formIdx = parseInt(totalFormsInput.value);
        
            let nuevaFilaHTML = templateHTML.replace(/__prefix__/g, formIdx);

            document.getElementById('parada-template').insertAdjacentHTML('beforebegin', nuevaFilaHTML);

            totalFormsInput.value = formIdx + 1;
            
            actualizarOrdenesAutomaticas();
        });
    }

    // ❌ QUITAR O ELIMINAR FILA
    if (contenedor) {
        contenedor.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-remove-parada') || e.target.closest('.btn-remove-parada')) {
                const boton = e.target.classList.contains('btn-remove-parada') ? e.target : e.target.closest('.btn-remove-parada');
                const fila = boton.closest('.fila-parada');
                

                const checkboxDelete = fila.querySelector('input[type="checkbox"][name$="-DELETE"]');
                
                if (checkboxDelete) {

                    checkboxDelete.checked = true;
                    fila.classList.add('d-none');
                } else {
                    fila.remove();
                }
            }
        });
    }
});