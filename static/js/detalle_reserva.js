document.addEventListener("DOMContentLoaded", function () {
    // Capturamos los elementos del formulario de reserva
    const inputPasajeros = document.getElementById("cantidad_pasajeros");
    const btnReservar = document.getElementById("btnReservar");
    const formReserva = document.getElementById("formReserva");

    // Buscamos el contenedor del precio final inyectado por Django
    const precioContenedor = document.getElementById("precio-final-dinamico");
    
    if (precioContenedor && inputPasajeros) {
        // Extraemos el valor numérico base del precio (removiendo el signo de pesos)
        const precioUnitario = parseFloat(precioContenedor.getAttribute("data-precio-base"));
        
        // Creamos un elemento visual para mostrar el total acumulado en vivo
        const infoTotal = document.createElement("div");
        infoTotal.style.marginTop = "15px";
        infoTotal.style.fontWeight = "bold";
        infoTotal.style.fontSize = "1.2rem";
        infoTotal.style.color = "#2b6cb0";
        infoTotal.innerHTML = `Total a Pagar: $${(precioUnitario * inputPasajeros.value).toFixed(2)}`;
        
        // Lo insertamos justo arriba del botón de enviar
        formReserva.insertBefore(infoTotal, btnReservar);

        // Escuchamos los cambios en el input numérico para actualizar el precio
        inputPasajeros.addEventListener("input", function () {
            const cantidad = parseInt(inputPasajeros.value) || 1;
            const nuevoTotal = precioUnitario * cantidad;
            infoTotal.innerHTML = `Total a Pagar: $${nuevoTotal.toFixed(2)}`;
        });
    }

    // Efecto visual de deshabilitar el botón al enviar para evitar doble cobro (Seguridad ACID)
    if (formReserva) {
        formReserva.addEventListener("submit", function () {
            btnReservar.disabled = true;
            btnReservar.innerText = "Procesando Reserva Segura...";
            btnReservar.style.backgroundColor = "#a0aec0";
        });
    }
});