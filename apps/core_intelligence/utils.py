import math
import re
import json
from apps.inventory.models import PuntoInteres

# Lista básica de palabras vacías (Stopwords) en español para limpiar las descripciones de La Paz
STOPWORDS = set([
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'a', 'al', 
    'en', 'y', 'o', 'no', 'si', 'su', 'sus', 'para', 'con', 'por', 'es', 'son', 
    'un', 'con', 'para', 'este', 'esta', 'estos', 'estas', 'que', 'como', 'muy'
])

def limpiar_texto(texto):
    """Convierte a minúsculas, elimina tildes, caracteres especiales y limpia el texto."""
    if not texto:
        return []
    texto = texto.lower()
    # Reemplazos básicos de tildes
    texto = re.sub(r'[áàäâ]', 'a', texto)
    texto = re.sub(r'[éèëê]', 'e', texto)
    texto = re.sub(r'[íìïî]', 'i', texto)
    texto = re.sub(r'[óòöô]', 'o', texto)
    texto = re.sub(r'[úùüû]', 'u', texto)
    # Dejar solo letras y espacios
    palabras = re.findall(r'[a-zñ]+', texto)
    # Filtrar stopwords
    return [p for p in palabras if p not in STOPWORDS and len(p) > 2]

def calcular_tf(tokens):
    """Calcula la frecuencia de término (TF) normalizada para un texto."""
    tf = {}
    if not tokens:
        return tf
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    
    # Normalizamos dividiendo entre el total de palabras del texto
    total = len(tokens)
    for token in tf:
        tf[token] = tf[token] / total
    return tf


def entrenar_motor_tfidf():
    """Calcula el vector TF-IDF de todos los POIs APROBADOS y los guarda en la Base de Datos."""
    # 1. Traer solo los POIs que ya pasaron por el flujo de moderación y están APROBADOS
    pois = PuntoInteres.objects.filter(estado='APROBADO')
    total_documentos = pois.count()
    
    if total_documentos == 0:
        return "No hay suficientes POIs aprobados para entrenar el motor."

    # 2. Tokenizar todos los documentos y contar en cuántos aparece cada palabra (para el IDF)
    documentos_tokens = {}
    conteo_documentos_con_termino = {}
    
    for poi in pois:
        # Combinamos el nombre, la categoría y la descripción para darle contexto semántico rico a la IA
        texto_completo = f"{poi.nombre} {poi.categoria} {poi.descripcion}"
        tokens = limpiar_texto(texto_completo)
        documentos_tokens[poi.id] = tokens
        
        # Guardar términos únicos de este POI para el conteo global
        for termino in set(tokens):
            conteo_documentos_con_termino[termino] = conteo_documentos_con_termino.get(termino, 0) + 1

    # 3. Calcular el IDF global de cada palabra
    idf = {}
    for termino, conteo in conteo_documentos_con_termino.items():
        # Fórmula matemática logarítmica estándar de IDF
        idf[termino] = math.log10(total_documentos / conteo)

    # 4. Calcular el vector final TF-IDF para cada POI y guardarlo en su JSONField
    for poi in pois:
        tokens = documentos_tokens[poi.id]
        tf = calcular_tf(tokens)
        
        vector_poi = {}
        for termino, tf_valor in tf.items():
            vector_poi[termino] = tf_valor * idf[termino]
            
        # Serializamos y guardamos el diccionario matemático en el campo nativo JSON de la fila
        poi.vector_tfidf = vector_poi
        poi.save()
        
    return f"Éxito: Se entrenó y vectorizó el contenido semántico de {total_documentos} POIs."