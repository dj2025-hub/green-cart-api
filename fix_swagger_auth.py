#!/usr/bin/env python
"""
Script pour corriger la configuration Swagger et ajouter l'authentification
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def create_tokens_for_test_users():
    """Crée des tokens pour les utilisateurs de test."""
    User = get_user_model()
    
    # Créer des tokens pour tous les utilisateurs sans token
    users = User.objects.filter(auth_token__isnull=True)
    
    for user in users:
        token, created = Token.objects.get_or_create(user=user)
        if created:
            print(f"✅ Token créé pour {user.email}: {token.key}")
        else:
            print(f"ℹ️  Token existe déjà pour {user.email}: {token.key}")

if __name__ == '__main__':
    create_tokens_for_test_users()