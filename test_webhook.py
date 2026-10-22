import hmac
import hashlib
import json
import urllib.request

# 1. Configura el ID real de la reserva que quieres pagar en tu base de datos
ID_DE_TU_RESERVA_REAL = 10  # <-- ¡Cambia este número por el que tengas en el sistema!

payload_dict = {
    "reserva_id": ID_DE_TU_RESERVA_REAL, 
    "estado": "aprobado",
    "transaccion_id": "TXN-99887766"
}
payload_bytes = json.dumps(payload_dict).encode('utf-8')

# 2. El banco firma el mensaje con la MISMA clave secreta
SECRET_KEY = 'banco_secreto_super_seguro_2026'
firma = hmac.new(key=SECRET_KEY.encode('utf-8'), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()

# 3. 🛠️ URL CORREGIDA: Apuntando directamente a tu servidor local de Django
url = 'http://127.0.0.1:8000/reservas/webhook-pagos/'

print("🚀 Iniciando simulación de Servidor Bancario...")
print(f"📦 Enviando Payload: {payload_dict}")
print(f"🔒 Firma Digital Generada (X-Signature): {firma}\n")

req = urllib.request.Request(
    url, 
    data=payload_bytes, 
    headers={
        'X-Signature': firma, 
        'Content-Type': 'application/json'
    }
)

try:
    respuesta = urllib.request.urlopen(req)
    print("✅ Respuesta del servidor Django:", respuesta.read().decode('utf-8'))
except Exception as e:
    print("❌ Error al golpear el Webhook:", e)