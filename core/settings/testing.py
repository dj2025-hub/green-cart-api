"""
Settings pour l'environnement de test.
"""
from .base import *
import tempfile

# ==============================================================================
# DEBUG CONFIGURATION
# ==============================================================================

DEBUG = False

# ==============================================================================
# HOST CONFIGURATION
# ==============================================================================

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Utiliser une base de données en mémoire pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# ==============================================================================
# PASSWORD VALIDATION
# ==============================================================================

# Désactiver la validation des mots de passe pour accélérer les tests
AUTH_PASSWORD_VALIDATORS = []

# ==============================================================================
# CACHE CONFIGURATION
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ==============================================================================
# MEDIA FILES
# ==============================================================================

# Utiliser un dossier temporaire pour les fichiers média pendant les tests
MEDIA_ROOT = tempfile.mkdtemp()

# ==============================================================================
# STATIC FILES
# ==============================================================================

# Désactiver WhiteNoise pour les tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Désactiver la plupart des logs pendant les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# Désactiver les vérifications de sécurité pour les tests
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================

# Utiliser un mode synchrone pour Celery pendant les tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# ==============================================================================
# PERFORMANCE SETTINGS
# ==============================================================================

# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# ==============================================================================
# TEST SPECIFIC SETTINGS
# ==============================================================================

# Accélérer les hash de mots de passe pour les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactiver les signaux pour certains tests si nécessaire
# SILENCED_SYSTEM_CHECKS = ['django_extensions.W001']

# Configuration pour pytest-django
TESTING = True

# Désactiver le cache pour les tests
USE_CACHE = False

# Configuration pour les tests d'API
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework.authentication.SessionAuthentication',
]

# Désactiver la pagination pour simplifier les tests
REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'] = None