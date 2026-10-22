from django.apps import AppConfig

class LandingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Cambia esto: de 'landing' a 'apps.landing'
    name = 'apps.landing'