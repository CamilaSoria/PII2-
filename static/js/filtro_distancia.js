// static/js/filtro_distancia.js

document.addEventListener("DOMContentLoaded", function() {
    const userLatInput = document.getElementById('userLat');
    const userLngInput = document.getElementById('userLng');

    // Comprobamos si el navegador soporta Geolocalización
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Si el usuario acepta el GPS, inyectamos las coordenadas reales
                if (userLatInput && userLngInput) {
                    userLatInput.value = position.coords.latitude;
                    userLngInput.value = position.coords.longitude;
                    console.log("📌 [GPS Éxito] Coordenadas cargadas en el formulario: ", position.coords.latitude, position.coords.longitude);
                }
            }, 
            function(error) {
                // Si el usuario rechaza o hay un error, dejamos los valores por defecto que Django maneja en el backend
                console.warn("⚠️ [GPS Advertencia] No se pudo obtener la ubicación real. Usando respaldo de la agencia.", error.message);
            },
            {
                enableHighAccuracy: true, // Solicita la mayor precisión posible (GPS en vez de solo redes)
                timeout: 5000,            // Espera máximo 5 segundos
                maximumAge: 60000         // Acepta una ubicación guardada hace máximo 1 minuto
            }
        );
    } else {
        console.error("❌ El navegador no soporta geolocalización.");
    }
});