from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from products.models import Product, Category
from .models import Comment, CommentReport

User = get_user_model()


class CommentModelTest(TestCase):
    """Tests pour le modèle Comment."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='CONSUMER'
        )
        
        self.category = Category.objects.create(
            name='Légumes',
            description='Légumes frais'
        )
        
        self.product = Product.objects.create(
            name='Tomates',
            description='Tomates fraîches du jardin',
            price=Decimal('2.50'),
            quantity=100,
            category=self.category,
            producer=self.user,
            rating=Decimal('0.0')
        )
    
    def test_comment_creation(self):
        """Test de création d'un commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Excellent produit, très frais !',
            rating=Decimal('4.5')
        )
        
        self.assertEqual(comment.product, self.product)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.rating, Decimal('4.5'))
        self.assertIn('Excellent produit', comment.comment)
    
    def test_comment_str_representation(self):
        """Test de la représentation string du commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Très bon produit',
            rating=Decimal('4.0')
        )
        
        expected = f'Commentaire de {self.user.email} sur {self.product.name} - Note: 4.0'
        self.assertEqual(str(comment), expected)
    
    def test_rating_validation(self):
        """Test de validation du rating."""
        # Rating trop bas
        with self.assertRaises(Exception):
            Comment.objects.create(
                product=self.product,
                user=self.user,
                comment='Test',
                rating=Decimal('-1.0')
            )
        
        # Rating trop haut
        with self.assertRaises(Exception):
            Comment.objects.create(
                product=self.product,
                user=self.user,
                comment='Test',
                rating=Decimal('6.0')
            )
    
    def test_unique_together_constraint(self):
        """Test de la contrainte unique_together."""
        Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Premier commentaire',
            rating=Decimal('4.0')
        )
        
        # Deuxième commentaire du même utilisateur sur le même produit
        with self.assertRaises(Exception):
            Comment.objects.create(
                product=self.product,
                user=self.user,
                comment='Deuxième commentaire',
                rating=Decimal('3.0')
            )


class CommentRatingUpdateTest(TestCase):
    """Tests pour la mise à jour automatique du rating des produits."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            user_type='CONSUMER'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            user_type='CONSUMER'
        )
        
        self.category = Category.objects.create(
            name='Fruits',
            description='Fruits frais'
        )
        
        self.product = Product.objects.create(
            name='Pommes',
            description='Pommes bio',
            price=Decimal('3.00'),
            quantity=50,
            category=self.category,
            producer=self.user1,
            rating=Decimal('0.0')
        )
    
    def test_product_rating_update_on_comment_create(self):
        """Test de mise à jour du rating du produit lors de la création d'un commentaire."""
        # Créer un commentaire avec note 4.0
        Comment.objects.create(
            product=self.product,
            user=self.user1,
            comment='Très bon produit',
            rating=Decimal('4.0')
        )
        
        # Vérifier que le rating du produit a été mis à jour
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal('4.0'))
    
    def test_product_rating_update_on_multiple_comments(self):
        """Test de mise à jour du rating avec plusieurs commentaires."""
        # Premier commentaire : 4.0
        Comment.objects.create(
            product=self.product,
            user=self.user1,
            comment='Bon produit',
            rating=Decimal('4.0')
        )
        
        # Deuxième commentaire : 5.0
        Comment.objects.create(
            product=self.product,
            user=self.user2,
            comment='Excellent produit',
            rating=Decimal('5.0')
        )
        
        # Vérifier que le rating moyen est correct (4.5)
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal('4.5'))
    
    def test_product_rating_update_on_comment_update(self):
        """Test de mise à jour du rating lors de la modification d'un commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user1,
            comment='Produit moyen',
            rating=Decimal('3.0')
        )
        
        # Modifier la note
        comment.rating = Decimal('5.0')
        comment.save()
        
        # Vérifier que le rating du produit a été mis à jour
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal('5.0'))
    
    def test_product_rating_update_on_comment_delete(self):
        """Test de mise à jour du rating lors de la suppression d'un commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user1,
            comment='Bon produit',
            rating=Decimal('4.0')
        )
        
        # Supprimer le commentaire
        comment.delete()
        
        # Vérifier que le rating du produit est revenu à 0.0
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal('0.0'))


class CommentAPITest(APITestCase):
    """Tests pour l'API des commentaires."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            user_type='CONSUMER'
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            user_type='CONSUMER',
            is_staff=True
        )
        
        self.category = Category.objects.create(
            name='Légumes',
            description='Légumes frais'
        )
        
        self.product = Product.objects.create(
            name='Carottes',
            description='Carottes bio',
            price=Decimal('1.50'),
            quantity=200,
            category=self.category,
            producer=self.user,
            rating=Decimal('0.0')
        )
        
        self.comment_data = {
            'product': self.product.id,
            'comment': 'Excellent produit, très frais et de bonne qualité !',
            'rating': 4.5
        }
    
    def test_create_comment_authenticated(self):
        """Test de création de commentaire par un utilisateur authentifié."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            reverse('api:comment-list'),
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        
        comment = Comment.objects.first()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.product, self.product)
        self.assertEqual(comment.rating, Decimal('4.5'))
    
    def test_create_comment_unauthenticated(self):
        """Test de création de commentaire sans authentification."""
        response = self.client.post(
            reverse('api:comment-list'),
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Comment.objects.count(), 0)
    
    def test_create_duplicate_comment(self):
        """Test de création d'un commentaire dupliqué."""
        # Créer le premier commentaire
        Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Premier commentaire',
            rating=Decimal('4.0')
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Essayer de créer un deuxième commentaire
        response = self.client.post(
            reverse('api:comment-list'),
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 1)
    
    def test_list_comments(self):
        """Test de liste des commentaires."""
        # Créer quelques commentaires
        Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Commentaire 1',
            rating=Decimal('4.0')
        )
        
        Comment.objects.create(
            product=self.product,
            user=self.admin_user,
            comment='Commentaire 2',
            rating=Decimal('5.0')
        )
        
        response = self.client.get(reverse('api:comment-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_filter_comments_by_product(self):
        """Test de filtrage des commentaires par produit."""
        # Créer un commentaire
        Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Test commentaire',
            rating=Decimal('4.0')
        )
        
        response = self.client.get(
            reverse('api:comment-list'),
            {'product': self.product.id}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_update_own_comment(self):
        """Test de mise à jour de son propre commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Commentaire original',
            rating=Decimal('3.0')
        )
        
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'comment': 'Commentaire modifié',
            'rating': 4.0
        }
        
        response = self.client.patch(
            reverse('api:comment-detail', args=[comment.id]),
            update_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        comment.refresh_from_db()
        self.assertEqual(comment.comment, 'Commentaire modifié')
        self.assertEqual(comment.rating, Decimal('4.0'))
    
    def test_update_other_user_comment(self):
        """Test de mise à jour du commentaire d'un autre utilisateur."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Commentaire original',
            rating=Decimal('3.0')
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        update_data = {
            'comment': 'Commentaire modifié par admin',
            'rating': 5.0
        }
        
        response = self.client.patch(
            reverse('api:comment-detail', args=[comment.id]),
            update_data
        )
        
        # L'admin peut modifier n'importe quel commentaire
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_own_comment(self):
        """Test de suppression de son propre commentaire."""
        comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Commentaire à supprimer',
            rating=Decimal('3.0')
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(
            reverse('api:comment-detail', args=[comment.id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)


class CommentReportTest(APITestCase):
    """Tests pour les signalements de commentaires."""
    
    def setUp(self):
        """Créer les données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            user_type='CONSUMER'
        )
        
        self.category = Category.objects.create(
            name='Fruits',
            description='Fruits frais'
        )
        
        self.product = Product.objects.create(
            name='Bananes',
            description='Bananes bio',
            price=Decimal('2.00'),
            quantity=150,
            category=self.category,
            producer=self.user,
            rating=Decimal('0.0')
        )
        
        self.comment = Comment.objects.create(
            product=self.product,
            user=self.user,
            comment='Commentaire test',
            rating=Decimal('4.0')
        )
        
        self.report_data = {
            'comment': self.comment.id,
            'reason': 'inappropriate',
            'description': 'Ce commentaire contient du contenu inapproprié'
        }
    
    def test_create_report_authenticated(self):
        """Test de création d'un signalement par un utilisateur authentifié."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            reverse('api:commentreport-list'),
            self.report_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CommentReport.objects.count(), 1)
    
    def test_create_duplicate_report(self):
        """Test de création d'un signalement dupliqué."""
        # Créer le premier signalement
        CommentReport.objects.create(
            comment=self.comment,
            reporter=self.user,
            reason='inappropriate',
            description='Premier signalement'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Essayer de créer un deuxième signalement
        response = self.client.post(
            reverse('api:commentreport-list'),
            self.report_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CommentReport.objects.count(), 1)
