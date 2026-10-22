from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('gracias/', views.pagina_gracias, name='gracias'),  # <-- La URL del redireccionamiento
]