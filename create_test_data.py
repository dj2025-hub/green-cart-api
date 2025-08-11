#!/usr/bin/env python
"""
Script pour créer des données de test avec des tableaux manuels incluant les données initiales pour GreenCart MVP
Usage: python create_test_data.py
"""
import os
import sys
import django
from random import choice, randint
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Producer
from products.models import Category, Product

User = get_user_model()

def create_test_data():
    """Crée des données de test avec des tableaux manuels incluant les données initiales."""

    print("🌱 Création des données de test GreenCart (version avec données initiales)...")

    # 1. Créer des utilisateurs de test
    print("\n👥 Création des utilisateurs...")

    # Consommateurs de test (inclut les données initiales)
    consumers_data = [
        # Données initiales
        {
            'email': 'consumer@test.com',
            'username': 'consumer_marie',
            'first_name': 'Marie',
            'last_name': 'Dupont',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123456',
        },
        # Données supplémentaires
        {
            'email': 'pierre.lefevre@test.com',
            'username': 'pierre_l',
            'first_name': 'Pierre',
            'last_name': 'Lefèvre',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123401',
        },
        {
            'email': 'sophie.martin@test.com',
            'username': 'sophie_m',
            'first_name': 'Sophie',
            'last_name': 'Martin',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123402',
        },
        {
            'email': 'lucas.roux@test.com',
            'username': 'lucas_r',
            'first_name': 'Lucas',
            'last_name': 'Roux',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123403',
        },
        {
            'email': 'emma.fournier@test.com',
            'username': 'emma_f',
            'first_name': 'Emma',
            'last_name': 'Fournier',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123404',
        },
        {
            'email': 'julien.bernard@test.com',
            'username': 'julien_b',
            'first_name': 'Julien',
            'last_name': 'Bernard',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123405',
        },
        {
            'email': 'claire.durand@test.com',
            'username': 'claire_d',
            'first_name': 'Claire',
            'last_name': 'Durand',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123406',
        },
        {
            'email': 'antoine.leroy@test.com',
            'username': 'antoine_l',
            'first_name': 'Antoine',
            'last_name': 'Leroy',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123407',
        },
        {
            'email': 'amelie.girard@test.com',
            'username': 'amelie_g',
            'first_name': 'Amélie',
            'last_name': 'Girard',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123408',
        },
        {
            'email': 'thomas.moreau@test.com',
            'username': 'thomas_m',
            'first_name': 'Thomas',
            'last_name': 'Moreau',
            'user_type': 'CONSUMER',
            'phone_number': '+237677123409',
        },
    ]

    created_consumers = []
    for consumer_data in consumers_data:
        consumer, created = User.objects.get_or_create(
            email=consumer_data['email'],
            defaults=consumer_data
        )
        if created:
            consumer.set_password('testpass123')
            consumer.save()
            print(f"✅ Consommateur créé: {consumer.email}")
        else:
            print(f"ℹ️  Consommateur existe déjà: {consumer.email}")
        created_consumers.append(consumer)

    # Producteurs de test (inclut les données initiales)
    producers_data = [
        # Données initiales
        {
            'email': 'ferme.bio@test.com',
            'first_name': 'Jean',
            'last_name': 'Martin',
            'business_name': 'Ferme Bio Martin',
            'description': 'Ferme biologique familiale depuis 3 générations',
            'region': 'Île-de-France',
            'phone_number': '+237677123456',
        },
        {
            'email': 'maraicher.local@test.com',
            'first_name': 'Sophie',
            'last_name': 'Bernard',
            'business_name': 'Maraîchage Local Sophie',
            'description': 'Légumes frais cultivés localement sans pesticides',
            'region': 'Île-de-France',
            'phone_number': '+237677123456',
        },
        # Données supplémentaires
        {
            'email': 'verger.dupre@test.com',
            'first_name': 'Claire',
            'last_name': 'Dupré',
            'business_name': 'Verger du Soleil',
            'description': 'Fruits juteux cultivés avec soin en Provence',
            'region': 'Provence-Alpes-Côte d’Azur',
            'phone_number': '+237677123501',
        },
        {
            'email': 'fromagerie.lebreton@test.com',
            'first_name': 'Anne',
            'last_name': 'Lebreton',
            'business_name': 'Fromagerie Lebreton',
            'description': 'Fromages artisanaux bretons au lait cru',
            'region': 'Bretagne',
            'phone_number': '+237677123502',
        },
        {
            'email': 'boulangerie.roussel@test.com',
            'first_name': 'Marc',
            'last_name': 'Roussel',
            'business_name': 'Boulangerie du Terroir',
            'description': 'Pains et farines au levain naturel en Nouvelle-Aquitaine',
            'region': 'Nouvelle-Aquitaine',
            'phone_number': '+237677123503',
        },
        {
            'email': 'ferme.charpentier@test.com',
            'first_name': 'Elise',
            'last_name': 'Charpentier',
            'business_name': 'Ferme des Volcans',
            'description': 'Viandes et charcuteries bio d’Auvergne',
            'region': 'Auvergne-Rhône-Alpes',
            'phone_number': '+237677123504',
        },
        {
            'email': 'maraicher.laurent@test.com',
            'first_name': 'François',
            'last_name': 'Laurent',
            'business_name': 'Maraîchage Laurent',
            'description': 'Légumes frais et locaux en Occitanie',
            'region': 'Occitanie',
            'phone_number': '+237677123505',
        },
        {
            'email': 'cidrerie.dubois@test.com',
            'first_name': 'Camille',
            'last_name': 'Dubois',
            'business_name': 'Cidrerie Normande',
            'description': 'Cidres et jus de pomme artisanaux de Normandie',
            'region': 'Normandie',
            'phone_number': '+237677123506',
        },
        {
            'email': 'apiculture.morin@test.com',
            'first_name': 'Nathalie',
            'last_name': 'Morin',
            'business_name': 'Miel des Vosges',
            'description': 'Miels et produits apicoles du Grand Est',
            'region': 'Grand Est',
            'phone_number': '+237677123507',
        },
        {
            'email': 'ferme.vincent@test.com',
            'first_name': 'Paul',
            'last_name': 'Vincent',
            'business_name': 'Ferme des Hauts',
            'description': 'Produits laitiers et œufs bio des Hauts-de-France',
            'region': 'Hauts-de-France',
            'phone_number': '+237677123508',
        },
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
                'phone_number': producer_data['phone_number'],
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Producteur créé: {user.email} ({producer_data['region']})")
        else:
            print(f"ℹ️  Producteur existe déjà: {user.email}")

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
        {'name': 'Épicerie', 'description': 'Miel, confitures, huiles locales'},
        {'name': 'Boissons', 'description': 'Jus de fruits, cidres, bières artisanales'},
        {'name': 'Œufs', 'description': 'Œufs frais de poules élevées en plein air'},
        {'name': 'Herbes et aromates', 'description': 'Herbes fraîches et épices locales'},
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
    product_templates = [
        {'category': 'Légumes', 'name': 'Tomates', 'description': 'Tomates bio', 'price': Decimal('4.50'), 'quantity_available': 50, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Légumes', 'name': 'Courgettes', 'description': 'Courgettes bio', 'price': Decimal('3.20'), 'quantity_available': 30, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Légumes', 'name': 'Carottes', 'description': 'Carottes bio', 'price': Decimal('2.90'), 'quantity_available': 60, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Légumes', 'name': 'Salade', 'description': 'Mesclun frais', 'price': Decimal('2.80'), 'quantity_available': 25, 'unit': 'unit', 'is_organic': False, 'is_local': True},
        {'category': 'Légumes', 'name': 'Radis', 'description': 'Radis croquants', 'price': Decimal('1.50'), 'quantity_available': 40, 'unit': 'unit', 'is_organic': False, 'is_local': True},
        {'category': 'Légumes', 'name': 'Poireaux', 'description': 'Poireaux frais', 'price': Decimal('3.50'), 'quantity_available': 35, 'unit': 'kg', 'is_organic': False, 'is_local': True},
        {'category': 'Fruits', 'name': 'Pommes', 'description': 'Pommes bio', 'price': Decimal('5.80'), 'quantity_available': 100, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Fruits', 'name': 'Fraises', 'description': 'Fraises locales', 'price': Decimal('8.90'), 'quantity_available': 20, 'unit': 'unit', 'is_organic': False, 'is_local': True},
        {'category': 'Fruits', 'name': 'Abricots', 'description': 'Abricots bio', 'price': Decimal('6.20'), 'quantity_available': 40, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Fruits', 'name': 'Pêches', 'description': 'Pêches bio', 'price': Decimal('5.50'), 'quantity_available': 50, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Produits laitiers', 'name': 'Fromage', 'description': 'Chèvre frais', 'price': Decimal('7.50'), 'quantity_available': 20, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Produits laitiers', 'name': 'Yaourt', 'description': 'Yaourt bio', 'price': Decimal('3.80'), 'quantity_available': 50, 'unit': 'pack', 'is_organic': True, 'is_local': True},
        {'category': 'Produits laitiers', 'name': 'Beurre', 'description': 'Beurre salé', 'price': Decimal('4.90'), 'quantity_available': 30, 'unit': 'unit', 'is_organic': False, 'is_local': True},
        {'category': 'Viandes', 'name': 'Saucisson', 'description': 'Saucisson bio', 'price': Decimal('12.50'), 'quantity_available': 15, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Viandes', 'name': 'Bœuf', 'description': 'Côte de bœuf', 'price': Decimal('25.00'), 'quantity_available': 10, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Pain et céréales', 'name': 'Pain', 'description': 'Pain au levain', 'price': Decimal('4.00'), 'quantity_available': 25, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Pain et céréales', 'name': 'Farine', 'description': 'Farine bio', 'price': Decimal('6.50'), 'quantity_available': 40, 'unit': 'kg', 'is_organic': True, 'is_local': True},
        {'category': 'Épicerie', 'name': 'Miel', 'description': 'Miel bio', 'price': Decimal('9.80'), 'quantity_available': 20, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Boissons', 'name': 'Jus', 'description': 'Jus de pomme', 'price': Decimal('4.00'), 'quantity_available': 30, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Œufs', 'name': 'Œufs', 'description': 'Œufs bio', 'price': Decimal('3.50'), 'quantity_available': 50, 'unit': 'unit', 'is_organic': True, 'is_local': True},
        {'category': 'Herbes et aromates', 'name': 'Basilic', 'description': 'Basilic frais', 'price': Decimal('2.00'), 'quantity_available': 30, 'unit': 'unit', 'is_organic': True, 'is_local': True},
    ]

    created_products = []
    for producer in created_producers:
        num_products = randint(4, 8)  # 4 à 8 produits par producteur
        for _ in range(num_products):
            template = choice(product_templates)
            category = next(c for c in created_categories if c.name == template['category'])
            # Truncate name to fit max_length=10
            base_name = template['name']
            truncated_name = base_name[:10]
            product_data = {
                'producer': producer,
                'category': category,
                'name': truncated_name,
                'description': f"{template['description']} par {producer.business_name}"[:50],  # Limit description length
                'price': template['price'],
                'quantity_available': randint(10, 100),
                'unit': template['unit'],
                'is_organic': template['is_organic'],
                'is_local': template['is_local'],
            }
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                producer=product_data['producer'],
                defaults=product_data
            )
            if created:
                print(f"✅ Produit créé: {product.name} - {product.producer.business_name}")
            else:
                print(f"ℹ️  Produit existe déjà: {product.name}")
            created_products.append(product)

    print(f"\n🎉 Données de test créées avec succès!")
    print(f"📧 Comptes consommateurs ({len(created_consumers)}):")
    for consumer in created_consumers[:5]:  # Afficher seulement les 5 premiers
        print(f"   - {consumer.email} / testpass123")
    print(f"📧 Comptes producteurs ({len(created_producers)}):")
    for producer in created_producers[:5]:
        print(f"   - {producer.user.email} / testpass123 ({producer.region})")
    print(f"🥬 Produits créés: {len(created_products)}")
    print(f"\n🚀 Vous pouvez maintenant tester l'API sur:")
    print(f"   - API Root: http://127.0.0.1:8000/api/")
    print(f"   - Swagger UI: http://127.0.0.1:8000/api/docs/")
    print(f"   - Admin: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    create_test_data()