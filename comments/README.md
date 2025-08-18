# 📝 API Commentaires - GreenCart

## 🌟 Vue d'ensemble

L'API Commentaires permet aux utilisateurs de laisser des avis et des notes sur les produits, avec un système de gestion automatique des ratings des produits. Chaque commentaire met automatiquement à jour la note moyenne du produit associé.

## 🏗️ Architecture

### Modèles

- **Comment** : Commentaires et notes des utilisateurs sur les produits
- **CommentReport** : Signalements de commentaires inappropriés

### Fonctionnalités

- ✅ CRUD complet sur les commentaires
- ✅ Validation des notes (0.0 à 5.0)
- ✅ Mise à jour automatique du rating des produits
- ✅ Système de signalement de commentaires
- ✅ Filtrage et recherche avancés
- ✅ Gestion des permissions utilisateur
- ✅ Documentation Swagger complète

## 📡 Endpoints API

### 🔍 Commentaires

#### Lister tous les commentaires
```
GET /api/comments/comments/
```

**Paramètres de requête :**
- `product_id` : Filtrer par ID du produit
- `user_id` : Filtrer par ID de l'utilisateur
- `min_rating` : Note minimale (0.0 à 5.0)
- `max_rating` : Note maximale (0.0 à 5.0)
- `search` : Recherche dans le texte
- `ordering` : Tri (created_at, rating, updated_at)

**Exemple :**
```bash
GET /api/comments/comments/?product_id=1&min_rating=4.0&ordering=-rating
```

#### Récupérer un commentaire
```
GET /api/comments/comments/{id}/
```

#### Créer un commentaire
```
POST /api/comments/comments/
```

**Corps de la requête :**
```json
{
    "product": 1,
    "comment": "Excellent produit, très frais et de bonne qualité !",
    "rating": 4.5
}
```

**Validation :**
- Rating : 0.0 ≤ note ≤ 5.0
- Commentaire : minimum 10 caractères
- Un seul commentaire par utilisateur par produit

#### Modifier un commentaire
```
PATCH /api/comments/comments/{id}/
```

**Corps de la requête :**
```json
{
    "comment": "Commentaire modifié",
    "rating": 4.0
}
```

**Permissions :** Seulement ses propres commentaires ou admin

#### Supprimer un commentaire
```
DELETE /api/comments/comments/{id}/
```

**Permissions :** Seulement ses propres commentaires ou admin

### 🎯 Actions spéciales

#### Commentaires d'un produit
```
GET /api/comments/comments/product/{product_id}/
```

#### Mes commentaires
```
GET /api/comments/comments/my-comments/
```

**Authentification requise**

#### Statistiques des commentaires
```
GET /api/comments/comments/stats/
```

**Paramètres :**
- `product_id` : Statistiques pour un produit spécifique
- `user_id` : Statistiques pour un utilisateur spécifique

**Réponse :**
```json
{
    "total_comments": 25,
    "average_rating": 4.2,
    "rating_distribution": {
        "5": 10,
        "4": 8,
        "3": 5,
        "2": 1,
        "1": 1
    },
    "recent_comments": [...]
}
```

#### Commentaires populaires
```
GET /api/comments/comments/popular/
```

**Paramètres :**
- `limit` : Nombre de commentaires (max 50)

### 🚨 Signalements

#### Créer un signalement
```
POST /api/comments/reports/
```

**Corps de la requête :**
```json
{
    "comment": 1,
    "reason": "inappropriate",
    "description": "Ce commentaire contient du contenu inapproprié"
}
```

**Raisons disponibles :**
- `inappropriate` : Contenu inapproprié
- `spam` : Spam
- `offensive` : Contenu offensant
- `fake` : Fausse information
- `other` : Autre raison

#### Marquer comme résolu (Admin)
```
PATCH /api/comments/reports/{id}/resolve/
```

## 🔐 Authentification

### Permissions

- **Lecture** : Publique (pas d'authentification requise)
- **Création** : Utilisateur authentifié
- **Modification** : Propriétaire du commentaire ou admin
- **Suppression** : Propriétaire du commentaire ou admin
- **Signalements** : Utilisateur authentifié

### Headers requis

```http
Authorization: Token your_token_here
Content-Type: application/json
```

## 📊 Gestion automatique des ratings

### Mise à jour automatique

Le rating des produits est automatiquement mis à jour :

1. **Création** : Calcul de la nouvelle moyenne
2. **Modification** : Recalcul de la moyenne
3. **Suppression** : Recalcul de la moyenne

### Formule de calcul

```
rating_moyen = Σ(ratings_commentaires) / nombre_commentaires
```

## 🎨 Interface d'administration

### Commentaires

- Liste avec filtres avancés
- Affichage des étoiles pour les notes
- Liens vers les produits et utilisateurs
- Recherche par texte, utilisateur, produit

### Signalements

- Gestion des signalements
- Actions en lot (marquer comme résolu)
- Couleurs par type de raison
- Liens vers les commentaires signalés

## 🧪 Tests

### Exécution des tests

```bash
# Tests de l'application comments
python manage.py test comments

# Tests spécifiques
python manage.py test comments.tests.CommentModelTest
python manage.py test comments.tests.CommentAPITest
```

### Couverture des tests

- ✅ Modèles et validation
- ✅ Mise à jour automatique des ratings
- ✅ API CRUD complète
- ✅ Gestion des permissions
- ✅ Signalements
- ✅ Filtrage et recherche

## 🚀 Utilisation

### Exemple complet

```python
import requests

# Configuration
BASE_URL = 'http://127.0.0.1:8000/api'
TOKEN = 'your_auth_token'

headers = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

# 1. Créer un commentaire
comment_data = {
    'product': 1,
    'comment': 'Excellent produit bio, très frais !',
    'rating': 5.0
}

response = requests.post(
    f'{BASE_URL}/comments/comments/',
    json=comment_data,
    headers=headers
)

if response.status_code == 201:
    comment = response.json()
    print(f'Commentaire créé avec ID: {comment["id"]}')

# 2. Lister les commentaires d'un produit
response = requests.get(
    f'{BASE_URL}/comments/comments/product/1/'
)

if response.status_code == 200:
    comments = response.json()
    print(f'Nombre de commentaires: {len(comments)}')

# 3. Obtenir les statistiques
response = requests.get(
    f'{BASE_URL}/comments/comments/stats/?product_id=1'
)

if response.status_code == 200:
    stats = response.json()
    print(f'Note moyenne: {stats["average_rating"]}')
```

## 🔧 Configuration

### Variables d'environnement

```env
# Aucune configuration spécifique requise
# L'application utilise les paramètres Django par défaut
```

### Base de données

- **Tables créées automatiquement** via les migrations
- **Index optimisés** pour les requêtes fréquentes
- **Contraintes d'intégrité** pour éviter les doublons

## 🐛 Dépannage

### Problèmes courants

#### Erreur de validation du rating
```
"rating": ["La note doit être comprise entre 0.0 et 5.0"]
```
**Solution :** Vérifier que la note est entre 0.0 et 5.0

#### Commentaire dupliqué
```
"non_field_errors": ["Vous avez déjà commenté ce produit."]
```
**Solution :** Un seul commentaire par utilisateur par produit

#### Permission refusée
```
"error": "Vous ne pouvez modifier que vos propres commentaires."
```
**Solution :** Vérifier l'authentification et les permissions

### Logs et debugging

```python
# Activer les logs SQL dans settings/development.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
}
```

## 📚 Ressources

### Documentation

- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Models](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [DRF Spectacular](https://drf-spectacular.readthedocs.io/)

### Exemples de code

- Tests complets dans `comments/tests.py`
- Sérialiseurs avec validation dans `comments/serializers.py`
- Vues avec gestion des permissions dans `comments/views.py`

---

## 🌱 Développé avec amour pour GreenCart

L'API Commentaires est conçue pour offrir une expérience utilisateur exceptionnelle tout en maintenant la qualité et l'intégrité des données. Chaque commentaire contribue à la réputation des produits et aide les autres utilisateurs à faire des choix éclairés.
