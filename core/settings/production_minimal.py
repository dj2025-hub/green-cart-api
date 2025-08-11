"""
Settings pour l'environnement de production - VERSION MINIMALISTE.
"""
from .base import *
from decouple import config

# Override middleware to add WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.middleware.SwaggerCSRFExemptMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# DEBUG CONFIGURATION
# ==============================================================================
DEBUG = False

# ==============================================================================
# HOST CONFIGURATION
# ==============================================================================
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='gc-api-3yjt.onrender.com,.onrender.com,localhost,127.0.0.1,*',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
DATABASES = {
    'default': config(
        'DATABASE_URL', 
        default='sqlite:///db.sqlite3',
        cast=db_url
    )
}

# ==============================================================================
# SECURITY SETTINGS - MINIMAL
# ==============================================================================
SECURE_SSL_REDIRECT = False  # Render handles this
SESSION_COOKIE_SECURE = False  # Render handles this
CSRF_COOKIE_SECURE = False  # Render handles this

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://*.onrender.com,http://localhost:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# DISABLE LOGGING TO AVOID ERRORS
# ==============================================================================
LOGGING_CONFIG = None

# ==============================================================================
# CSRF CONFIGURATION - DISABLE FOR API ONLY DEPLOYMENT
# ==============================================================================
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = False
USE_TZ = True

# ==============================================================================
# SWAGGER UI CONFIGURATION
# ==============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'GreenCart API',
    'DESCRIPTION': 'API REST pour une plateforme de circuit court connectant producteurs locaux et consommateurs écoresponsables',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'requestSnippetsEnabled': True,
        'tryItOutEnabled': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch', 'head', 'options'],
        'docExpansion': 'none',
        'operationsSorter': 'alpha',
        'tagsSorter': 'alpha',
    },
    'SERVERS': [
        {'url': 'https://gc-api-3yjt.onrender.com/api', 'description': 'Production server'},
        {'url': 'http://localhost:8000/api', 'description': 'Development server'},
    ],
}

# ==============================================================================
# STATIC FILES
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True