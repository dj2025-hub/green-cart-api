#!/usr/bin/env python
"""
Script pour créer des données de test pour GreenCart MVP
Usage: python create_test_data.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Producer
from products.models import Category, Product
from decimal import Decimal

User = get_user_model()

def create_test_data():
    """Crée des données de test pour le parcours consommateur."""
    
    print("🌱 Création des données de test GreenCart...")
    
    # 1. Créer des utilisateurs de test
    print("\n👥 Création des utilisateurs...")
    
    # Consommateur de test
    consumer, created = User.objects.get_or_create(
        email='consumer@test.com',
        defaults={
            'username': 'consumer_marie',
            'first_name': 'Marie',
            'last_name': 'Dupont',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123456',
        }
    )
    if created:
        consumer.set_password('testpass123')
        consumer.save()
        print(f"✅ Consommateur créé: {consumer.email}")
    else:
        print(f"ℹ️  Consommateur existe déjà: {consumer.email}")
    
    # Producteurs de test
    producers_data = [
        {
            'email': 'ferme.bio@test.com',
            'first_name': 'Jean',
            'last_name': 'Martin',
            'business_name': 'Ferme Bio Martin',
            'description': 'Ferme biologique familiale depuis 3 générations',
            'region': 'Île-de-France',
        },
        {
            'email': 'maraicher.local@test.com',
            'first_name': 'Sophie',
            'last_name': 'Bernard',
            'business_name': 'Maraîchage Local Sophie',
            'description': 'Légumes frais cultivés localement sans pesticides',
            'region': 'Île-de-France',
        }
    ]
    
    created_producers = []
    for producer_data in producers_data:
        username = f"producer_{producer_data['first_name'].lower()}"
        user, created = User.objects.get_or_create(
            email=producer_data['email'],
            defaults={
                'username': username,
                'first_name': producer_data['first_name'],
                'last_name': producer_data['last_name'],
                'user_type': 'PRODUCER',
                'phone_number': '+237677123456',
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Producteur créé: {user.email}")
        else:
            print(f"ℹ️  Producteur existe déjà: {user.email}")
        
        # Créer le profil producteur
        producer, created = Producer.objects.get_or_create(
            user=user,
            defaults={
                'business_name': producer_data['business_name'],
                'description': producer_data['description'],
                'region': producer_data['region'],
                'is_verified': True,
            }
        )
        if created:
            print(f"✅ Profil producteur créé: {producer.business_name}")
        else:
            print(f"ℹ️  Profil producteur existe déjà: {producer.business_name}")
        
        created_producers.append(producer)
    
    # 2. Créer des catégories
    print("\n📦 Création des catégories...")
    categories_data = [
        {'name': 'Légumes', 'description': 'Légumes frais de saison'},
        {'name': 'Fruits', 'description': 'Fruits locaux et de saison'},
        {'name': 'Produits laitiers', 'description': 'Lait, fromages, yaourts artisanaux'},
        {'name': 'Viandes', 'description': 'Viandes locales et élevage responsable'},
        {'name': 'Pain et céréales', 'description': 'Pain artisanal et céréales anciennes'},
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"✅ Catégorie créée: {category.name}")
        else:
            print(f"ℹ️  Catégorie existe déjà: {category.name}")
        created_categories.append(category)
    
    # 3. Créer des produits
    print("\n🥬 Création des produits...")
    products_data = [
        # Ferme Bio Martin
        {
            'producer': created_producers[0],
            'category': created_categories[0],  # Légumes
            'name': 'Tomates cerises bio',
            'description': 'Tomates cerises biologiques, cultivées sous serre',
            'price': Decimal('4.50'),
            'quantity_available': 50,
            'unit': 'kg',
            'is_organic': True,
            'is_local': True,
        },
        {
            'producer': created_producers[0],
            'category': created_categories[0],
            'name': 'Courgettes bio',
            'description': 'Courgettes fraîches biologiques',
            'price': Decimal('3.20'),
            'quantity_available': 30,
            'unit': 'kg',
            'is_organic': True,
            'is_local': True,
        },
        {
            'producer': created_producers[0],
            'category': created_categories[1],  # Fruits
            'name': 'Pommes Golden bio',
            'description': 'Pommes Golden biologiques, récoltées à maturité',
            'price': Decimal('5.80'),
            'quantity_available': 100,
            'unit': 'kg',
            'is_organic': True,
            'is_local': True,
        },
        
        # Maraîchage Local Sophie
        {
            'producer': created_producers[1],
            'category': created_categories[0],  # Légumes
            'name': 'Salade mesclun',
            'description': 'Mélange de jeunes pousses de salade',
            'price': Decimal('2.80'),
            'quantity_available': 25,
            'unit': 'barquette',
            'is_organic': False,
            'is_local': True,
        },
        {
            'producer': created_producers[1],
            'category': created_categories[0],
            'name': 'Radis roses',
            'description': 'Radis roses croquants et savoureux',
            'price': Decimal('1.50'),
            'quantity_available': 40,
            'unit': 'botte',
            'is_organic': False,
            'is_local': True,
        },
        {
            'producer': created_producers[1],
            'category': created_categories[1],  # Fruits
            'name': 'Fraises de saison',
            'description': 'Fraises fraîches cultivées localement',
            'price': Decimal('8.90'),
            'quantity_available': 20,
            'unit': 'barquette',
            'is_organic': False,
            'is_local': True,
        },
    ]
    
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            producer=product_data['producer'],
            defaults=product_data
        )
        if created:
            print(f"✅ Produit créé: {product.name} - {product.producer.business_name}")
        else:
            print(f"ℹ️  Produit existe déjà: {product.name}")
    
    print(f"\n🎉 Données de test créées avec succès!")
    print(f"📧 Compte consommateur: consumer@test.com / testpass123")
    print(f"📧 Producteur 1: ferme.bio@test.com / testpass123")
    print(f"📧 Producteur 2: maraicher.local@test.com / testpass123")
    print(f"\n🚀 Vous pouvez maintenant tester l'API sur:")
    print(f"   - API Root: http://127.0.0.1:8000/api/")
    print(f"   - Swagger UI: http://127.0.0.1:8000/api/docs/")
    print(f"   - Admin: http://127.0.0.1:8000/admin/")


if __name__ == '__main__':
    create_test_data()