"""
Configuration Swagger alternative pour éviter les problèmes de schéma.
"""

# Configuration minimale pour Swagger UI
SPECTACULAR_SETTINGS = {
    'TITLE': 'GreenCart API',
    'DESCRIPTION': 'API REST pour une plateforme de circuit court connectant producteurs locaux et consommateurs écoresponsables',
    'VERSION': '1.0.0',
    
    # Désactiver complètement la génération de schéma
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_SCHEMA': False,
    'GENERATE_SCHEMA': False,
    
    # Configuration Swagger UI simple
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'tryItOutEnabled': True,
        'docExpansion': 'none',
    },
    
    # Permissions
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    
    # Tags de base
    'TAGS': [
        {'name': 'Authentication', 'description': 'Gestion des utilisateurs et authentification'},
        {'name': 'Products', 'description': 'Gestion des produits et catégories'},
        {'name': 'Categories', 'description': 'Gestion des catégories de produits'},
        {'name': 'Cart', 'description': 'Gestion du panier d\'achat'},
        {'name': 'Orders', 'description': 'Gestion des commandes'},
        {'name': 'Producers', 'description': 'Gestion des producteurs'},
        {'name': 'Comments', 'description': 'Gestion des commentaires et évaluations des produits'},
    ],
    
    # Informations de contact
    'CONTACT': {
        'name': 'Équipe GreenCart',
        'email': 'contact@greencart.com',
    },
    
    # Licence
    'LICENSE': {
        'name': 'MIT License',
    },
}
