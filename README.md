# Plataforma web de turismo

**Proyecto Integrador Intermedio II · Hito 3 – Evaluación continua**

| | |
|---|---|
| **Proyecto** | Plataforma web de gestión y reserva de paquetes turísticos (`srti_core`) |
| **Estudiante** | [NOMBRE COMPLETO DEL ESTUDIANTE] |
| **Docente** | Lic. Patricia Fernández Quisbert |

## Descripción del sistema

Aplicación web desarrollada con **Django** que permite a los turistas explorar un catálogo de destinos, rutas y paquetes turísticos,
reservar y pagar en línea, y compartir "joyas ocultas" (lugares poco conocidos). El personal de la agencia administra el catálogo,
modera los aportes de los turistas y gestiona usuarios desde un panel restringido. Incluye un recomendador basado en TF-IDF.

## Funcionalidades principales

- **Autenticación:** registro con verificación por correo, recuperación de contraseña y perfil.
- **Catálogo:** destinos, rutas con mapa interactivo, paquetes con itinerario, hoteles y comparador.
- **Joyas ocultas:** propuestas de turistas, moderación, favoritos y filtro por distancia.
- **Reservas y pagos:** control de cupos, cancelación, checkout y confirmación por webhook firmado (HMAC-SHA256).
- **Panel de gestión:** administración del catálogo y usuarios, accesible solo para el personal.
- **Recomendador:** vectorización TF-IDF de las joyas aprobadas (comando `entrenar_ia`).

## Tecnologías

Python · Django · SQLite · HTML, CSS y JavaScript · Bootstrap · Leaflet · pytest · Git y GitHub.

## Puesta en marcha

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                # edita los valores
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Pruebas

```bash
pytest
```

## Estructura

| Carpeta | Responsabilidad |
|---|---|
| `apps/authentication` | Usuarios, roles, registro, recuperación de contraseña, perfil |
| `apps/inventory` | Destinos, rutas, paquetes, hoteles, joyas ocultas |
| `apps/bookings` | Reservas, checkout, webhook de pagos, reporte de ventas |
| `apps/gestion` | Panel del personal (solo `is_staff`) |
| `apps/landing` | Página principal y captación de leads |
| `apps/core_intelligence` | Recomendador TF-IDF |

## Estado del avance

Funcionalidades completas, parciales y pendientes: ver el informe del Hito 3.

## Seguridad

Los secretos viven en `.env` (excluido de git). Con `DJANGO_DEBUG=False` el proyecto exige `DJANGO_SECRET_KEY`,
`PAYMENT_WEBHOOK_SECRET` y `DJANGO_ALLOWED_HOSTS`.
