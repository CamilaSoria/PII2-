from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bookings'

def ready(self):
        # Con esto Django activa el receptor de señales apenas prende el servidor
        import apps.bookings.signals

