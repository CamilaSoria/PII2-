from django.core.management.base import BaseCommand
from apps.core_intelligence.utils import entrenar_motor_tfidf

class Command(BaseCommand):
    help = 'Calcula y actualiza los vectores TF-IDF de todos los Puntos de Interés aprobados.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando el entrenamiento del Core Inteligente (TF-IDF)...'))
        
        # Disparamos la función matemática que escribimos en la Tarea 5.2
        resultado = entrenar_motor_tfidf()
        
        # Mostramos el resultado final en la terminal en un bonito color verde de éxito
        self.stdout.write(self.style.SUCCESS(resultado))