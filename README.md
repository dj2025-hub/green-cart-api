# 🌱 GreenCart API

API REST pour une plateforme de circuit court connectant producteurs locaux et consommateurs écoresponsables.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/Django%20REST-3.16+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Fonctionnalités MVP](#-fonctionnalités-mvp)
- [Installation rapide](#-installation-rapide)
- [API Endpoints](#-api-endpoints)
- [Structure du projet](#-structure-du-projet)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Développement](#-développement)
- [Tests](#-tests)
- [Déploiement](#-déploiement)
- [Contribution](#-contribution)

## 🌱 Vue d'ensemble

GreenCart est une plateforme de circuit court qui révolutionne la façon dont les producteurs locaux et les consommateurs écoresponsables interagissent. Notre API REST facilite les échanges directs, réduisant les intermédiaires et favorisant une économie locale durable.

**Mission** : Connecter les producteurs locaux aux consommateurs soucieux de l'environnement pour créer un écosystème alimentaire plus durable et transparent.

## ✨ Fonctionnalités MVP

### 🔐 Système d'authentification
- Inscription/connexion pour consommateurs et producteurs
- Authentification par token JWT
- Gestion des profils utilisateur
- Système de rôles (consommateur/producteur)

### 🥕 Gestion des produits (Producteurs)
- Créer un produit (nom, description, prix, quantité, DLC, catégorie)
- Modifier et supprimer ses produits
- Gestion des stocks en temps réel
- Upload de photos produits

### 🛒 Catalogue et commandes (Consommateurs)
- Catalogue avec filtres (catégorie, région, DLC)
- Détail produit avec informations producteur
- Panier d'achat dynamique
- Gestion des quantités et suppression
- Commandes simplifiées (sans paiement en ligne)

### 📦 Gestion des commandes (Producteurs)
- Visualisation des commandes reçues
- Acceptation/refus des commandes
- Suivi des statuts (en attente, confirmée, expédiée, livrée)
- Notifications en temps réel

### 🏗️ Architecture technique
- **Backend** : Django 5.2+ avec Python 3.13+
- **API** : Django REST Framework 3.16+
- **Base de données** : PostgreSQL
- **Authentification** : Token-based avec DRF
- **Cache** : Redis pour les performances
- **Fichiers** : Upload et gestion des médias

## 🔧 Prérequis

- **Python 3.13+**
- **Git**
- **PostgreSQL** (recommandé pour la production)
- **Redis** (pour le cache et les sessions)

## 🚀 Installation rapide

### 1. Cloner le projet

```bash
git clone https://github.com/dj2025-hub/green-cart-api.git
cd green-cart-api
```

### 2. Configurer l'environnement

```bash
# Créer l'environnement virtuel
python3.13 -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements-dev.txt
```

### 3. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Créer une base de données PostgreSQL

# Éditer .env avec vos configurations pour la base de donnée
 DB_NAME=
 DB_USER=
 DB_PASSWORD=
 DB_HOST=

# Générer une nouvelle clé secrète (optionnel)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Créer la base de données
python manage.py makemigrations
python manage.py migrate

# Créer un super utilisateur
python manage.py createsuperuser

# Créer des données de test (optionnel)
python create_test_data.py
```

### 4. Lancer le serveur

```bash
python manage.py runserver
```

🎉 **GreenCart API est prête !**
- **API** : http://127.0.0.1:8000/api/
- **Admin** : http://127.0.0.1:8000/admin/
- **Documentation API** : http://127.0.0.1:8000/api/docs/ (prochainement)

## 📡 API Endpoints

### Authentification
```
POST /api/auth/register/          # Inscription utilisateur
POST /api/auth/login/             # Connexion
POST /api/auth/logout/            # Déconnexion
GET  /api/auth/profile/           # Profil utilisateur
PUT  /api/auth/profile/           # Mise à jour profil
```

### Produits
```
GET    /api/products/             # Catalogue public avec filtres
GET    /api/products/{id}/        # Détail produit
POST   /api/products/             # Créer produit (producteur)
PUT    /api/products/{id}/        # Modifier produit (producteur)
DELETE /api/products/{id}/        # Supprimer produit (producteur)
GET    /api/producer/products/    # Mes produits (producteur)
```

### Catégories
```
GET /api/categories/              # Liste des catégories
```

### Panier
```
GET    /api/cart/                 # Mon panier
POST   /api/cart/items/           # Ajouter au panier
PUT    /api/cart/items/{id}/      # Modifier quantité
DELETE /api/cart/items/{id}/      # Supprimer du panier
DELETE /api/cart/clear/           # Vider le panier
```

### Commandes
```
POST /api/orders/                 # Passer commande depuis le panier
GET  /api/orders/                 # Mes commandes (consommateur)
GET  /api/orders/{id}/            # Détail commande
PUT  /api/orders/{id}/cancel/     # Annuler commande (consommateur)

# Pour les producteurs
GET /api/producer/orders/         # Commandes reçues
PUT /api/producer/orders/{id}/    # Changer statut commande
```

### Régions
```
GET /api/regions/                 # Liste des régions françaises
```

## 📁 Structure du projet

```
greencart-api/
├── 📁 core/                    # Configuration principale
│   ├── 📁 settings/           # Settings modulaires
│   │   ├── base.py           # Configuration de base
│   │   ├── development.py    # Développement
│   │   ├── production.py     # Production
│   │   └── testing.py        # Tests
│   ├── urls.py               # URLs principales
│   ├── wsgi.py               # Configuration WSGI
│   └── asgi.py               # Configuration ASGI
├── 📁 accounts/               # Gestion des utilisateurs et authentification
├── 📁 api/                    # API REST et endpoints génériques
├── 📁 products/               # Gestion des produits
├── 📁 orders/                 # Gestion des commandes
├── 📁 cart/                   # Gestion du panier
├── 📁 static/                 # Fichiers statiques
├── 📁 media/                  # Fichiers média (photos produits)
├── 📁 templates/              # Templates HTML (optionnel)
├── 📄 requirements.txt        # Dépendances production
├── 📄 requirements-dev.txt    # Dépendances développement
├── 📄 .env.example           # Exemple de configuration
├── 📄 manage.py              # Script de gestion Django
└── 📄 README.md              # Cette documentation
```

## ⚙️ Configuration

### Variables d'environnement

Copiez `.env.example` vers `.env` et configurez selon vos besoins :

```env
# Configuration de base
SECRET_KEY=votre-clé-secrète-ici
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/greencart

# CORS pour le frontend React
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# API Settings
DRF_PAGE_SIZE=20

# Cache Redis
REDIS_URL=redis://127.0.0.1:6379/1
CACHE_BACKEND=django_redis.cache.RedisCache

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app

# Logging
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO

# Sécurité (production)
SESSION_COOKIE_SECURE=False  # True en production HTTPS
CSRF_COOKIE_SECURE=False     # True en production HTTPS
```

### Environnements de configuration

```bash
# Développement (par défaut)
python manage.py runserver

# Production
DJANGO_SETTINGS_MODULE=core.settings.production python manage.py runserver

# Tests
DJANGO_SETTINGS_MODULE=core.settings.testing python manage.py test
```

## 📖 Utilisation

### Créer une nouvelle app Django

```bash
# Créer l'app
python manage.py startapp nom_app

# Ajouter dans core/settings/base.py
LOCAL_APPS = [
    'accounts',
    'api',
    'nom_app',  # ← Ajouter ici
]
```

### Authentification API

```python
# Obtenir un token d'authentification
POST /api/auth/login/
{
    "email": "user@example.com",
    "password": "motdepasse"
}

# Réponse
{
    "token": "your-auth-token",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "user_type": "CONSUMER"
    }
}

# Utiliser le token dans les requêtes
headers: {
    "Authorization": "your-auth-token"
}
```

### Filtres disponibles

```
# Produits par catégorie
GET /api/products/?category=legumes

# Produits par région du producteur
GET /api/products/?region=ile-de-france

# Produits exprirant bientôt
GET /api/products/?expires_in_days=3

# Recherche par nom
GET /api/products/?search=tomate

# Combinaisons
GET /api/products/?category=fruits&region=bretagne&search=pomme
```

### Base de données

```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Réinitialiser la base de données
python manage.py flush
```

## 👨‍💻 Développement

### Debug

Le **Django Debug Toolbar** est automatiquement activé en développement :
- Accédez à http://127.0.0.1:8000/__debug__/
- Consultez les panneaux de debug sur vos pages

### Shell Django amélioré

```bash
# Shell avec toutes les apps chargées
python manage.py shell_plus

# Avec affichage des requêtes SQL
python manage.py shell_plus --print-sql
```

## 🚀 Déploiement

### Avec Docker

```bash
# Construire l'image
docker build -t mon-projet .

# Lancer avec docker-compose
docker-compose up -d
```

### Production manuelle

```bash
# Variables d'environnement de production
export DJANGO_SETTINGS_MODULE=core.settings.production
export SECRET_KEY=votre-vraie-clé-secrète
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Lancer avec Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Variables de production importantes

```env
DEBUG=False
SECRET_KEY=une-vraie-clé-secrète-complexe
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://user:password@localhost:5432/production_db
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.votre-provider.com
SENTRY_DSN=https://votre-dsn@sentry.io/project-id
```

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Avec pytest (recommandé)
pytest

# Avec couverture de code
pytest --cov=.

# Tests spécifiques
pytest apps/accounts/tests/
```

### Écrire des tests

```python
# Dans votre app/tests.py
import pytest
from django.test import TestCase
from rest_framework.test import APITestCase

class MonModelTestCase(TestCase):
    def test_creation(self):
        # Votre test ici
        pass

@pytest.mark.django_db
class TestMonAPI(APITestCase):
    def test_api_endpoint(self):
        # Test d'API ici
        pass
```

## 🎯 Règles métier GreenCart

### Gestion des stocks
- **Décrémentation automatique** : La quantité disponible est décrémenté automatiquement lors d'une commande confirmée
- **Contrôle des stocks** : Empêcher les commandes si quantité insuffisante
- **Réincrémentation** : Si une commande est annulée, remettre les quantités en stock

### Système de commandes
- Une **commande peut contenir des produits de plusieurs producteurs**
- Chaque **producteur gère ses propres items** dans la commande
- Le **statut global** de la commande dépend du statut de tous les items
- **Statuts possibles** : PENDING, CONFIRMED, CANCELLED, SHIPPED, DELIVERED

### Filtres et recherche
- **Par catégorie** : fruits, légumes, produits laitiers, etc.
- **Par région** : région du producteur pour favoriser la proximité
- **Par DLC** : produits périssant dans X jours pour éviter le gaspillage
- **Disponibilité** : uniquement les produits en stock

### Authentification et autorisations
- **Consommateurs** : peuvent naviguer, acheter, gérer leur panier et commandes
- **Producteurs** : peuvent gérer leurs produits, voir et traiter leurs commandes
- **Token-based** : Authentification sécurisée pour l'API REST

## 🚀 Prochaines étapes après MVP

### Phase 2 - Améliorations
- [ ] **Intégration paiement** (Stripe/PayPal)
- [ ] **Système de notifications** (email, SMS)
- [ ] **Géolocalisation avancée** avec calcul de distances
- [ ] **Reviews et ratings** des produits et producteurs

### Phase 3 - Fonctionnalités avancées
- [ ] **Tableau de bord analytics** pour les producteurs
- [ ] **Système de livraison** avec tracking
- [ ] **Programme de fidélité**
- [ ] **Application mobile** (React Native)

### Phase 4 - Scalabilité
- [ ] **Microservices architecture**
- [ ] **Cache Redis avancé**
- [ ] **CDN pour les images**
- [ ] **API GraphQL**

## 📚 Ressources utiles

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Python Decouple](https://github.com/henriquebastos/python-decouple)

### Commandes utiles

```bash
# Informations sur le projet
python manage.py check
python manage.py showmigrations
python manage.py dbshell

# Gestion des utilisateurs
python manage.py changepassword username
python manage.py createsuperuser

# Cache
python manage.py clear_cache
```

## 🤝 Contribution

1. **Fork** le projet
2. **Créez** votre branche (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add: Amazing Feature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrez** une Pull Request

### Standards de code

- Utilisez **Black** pour le formatage
- Suivez **PEP 8**
- Ajoutez des **tests** pour les nouvelles fonctionnalités
- Documentez votre code

## 🐛 Problèmes courants

### Erreur de base de données
```bash
# Réinitialiser les migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### Erreur de clé secrète
```bash
# Générer une nouvelle clé
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Debug Toolbar ne s'affiche pas
```bash
# Vérifier INTERNAL_IPS dans settings/development.py
# Vérifier que DEBUG=True
# Redémarrer le serveur
```

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Équipe GreenCart

**Développeur Backend** - [@dj2025-hub](https://github.com/dj2025-hub)

---

⭐ **Rejoignez la révolution du circuit court avec GreenCart !**

## 🔗 Liens utiles

- [Signaler un bug](https://github.com/camcoder337/greencart-api/issues)
- [Demander une fonctionnalité](https://github.com/camcoder337/greencart-api/issues)
- [Documentation API](https://github.com/camcoder337/greencart-api/wiki)

## 🌍 Mission

GreenCart s'engage à créer un écosystème alimentaire plus durable en connectant directement producteurs locaux et consommateurs écoresponsables. Ensemble, réduisons l'empreinte carbone de notre alimentation !

---

*Made with 🌱 for a sustainable future*