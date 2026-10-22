# apps/gestion/apps.py
from django.apps import AppConfig

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # ¡AQUÍ! Debe decir 'apps.gestion' para que Django la encuentre en esa subcarpeta
    name = 'apps.gestion'