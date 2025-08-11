"""
Configuration des URLs principales du projet.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render
import django


def home_view(request):
    """Vue d'accueil avec informations API GreenCart."""
    return JsonResponse({
        'message': 'Welcome to GreenCart API',
        'version': '1.0.0',
        'description': 'API REST pour une plateforme de circuit court',
        'endpoints': {
            'auth': '/api/auth/',
            'products': '/api/products/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'admin': '/admin/',
        },
        'debug': settings.DEBUG,
        'django_version': django.get_version(),
    })



urlpatterns = [
    path('', home_view, name='home'),  # Page d'accueil HTML
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),  # API principale
]

# Servir les fichiers statiques et média
# En production, WhiteNoise gère les static files automatiquement
# On ajoute les media files pour tous les environnements
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# En développement, aussi les static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Django Debug Toolbar (désactivé pour le MVP)
# if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
