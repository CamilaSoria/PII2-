document.addEventListener('DOMContentLoaded', function() {
    // Django por defecto genera los IDs como 'id_nombre_del_campo'
    const salidaInput = document.getElementById('id_horario_salida');
    const retornoInput = document.getElementById('id_horario_retorno');
    const duracionInput = document.getElementById('id_duracion_estimada');

    // Bloqueamos el input desde el cliente para que el usuario sepa que es automático
    if (duracionInput) {
        duracionInput.readOnly = true;
        duracionInput.placeholder = "Se calcula automáticamente...";
    }

    function calcularMinutos() {
        if (salidaInput && retornoInput && duracionInput && salidaInput.value && retornoInput.value) {
            // Split a las horas y minutos (ej: "08:30" -> [8, 30])
            const [h1, m1] = salidaInput.value.split(':').map(Number);
            const [h2, m2] = retornoInput.value.split(':').map(Number);
            
            let minutosSalida = h1 * 60 + m1;
            let minutosRetorno = h2 * 60 + m2;
            
            let diferencia = minutosRetorno - minutosSalida;
            
            // Si la hora de retorno es menor, significa que terminó al día siguiente
            if (diferencia < 0) {
                diferencia += 24 * 60; 
            }
            
            duracionInput.value = diferencia;
        }
    }

    // Escuchamos cuando el usuario cambie cualquiera de las dos horas
    if (salidaInput && retornoInput) {
        salidaInput.addEventListener('change', calcularMinutos);
        retornoInput.addEventListener('change', calcularMinutos);
    }
});