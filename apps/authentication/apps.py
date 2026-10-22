from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'

    def ready(self):
        # Esto le dice a Django que cargue tus funciones @receiver al arrancar
        import apps.authentication.models