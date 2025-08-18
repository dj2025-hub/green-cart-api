from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Product

User = get_user_model()


class Comment(models.Model):
    """
    Modèle pour les commentaires et notes des produits.
    Met automatiquement à jour le rating moyen du produit.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Produit'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_comments',
        verbose_name='Utilisateur'
    )
    comment = models.TextField(
        verbose_name='Commentaire',
        help_text='Votre avis sur le produit'
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[
            MinValueValidator(0.0, message='La note doit être au moins 0.0'),
            MaxValueValidator(5.0, message='La note ne peut pas dépasser 5.0')
        ],
        verbose_name='Note',
        help_text='Note entre 0.0 et 5.0'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière modification'
    )

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        unique_together = ['product', 'user']  # Un seul commentaire par utilisateur par produit
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'rating']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'Commentaire de {self.user.email} sur {self.product.name} - Note: {self.rating}'

    def clean(self):
        """Validation personnalisée."""
        from django.core.exceptions import ValidationError
        
        if self.rating < 0.0 or self.rating > 5.0:
            raise ValidationError('La note doit être comprise entre 0.0 et 5.0')
        
        if not self.comment.strip():
            raise ValidationError('Le commentaire ne peut pas être vide')

    def save(self, *args, **kwargs):
        """Sauvegarde avec validation et mise à jour du rating du produit."""
        self.clean()
        super().save(*args, **kwargs)


@receiver([post_save, post_delete], sender=Comment)
def update_product_rating(sender, instance, **kwargs):
    """
    Signal pour mettre à jour automatiquement le rating moyen du produit
    quand un commentaire est créé, modifié ou supprimé.
    """
    product = instance.product
    
    # Calculer le nouveau rating moyen
    avg_rating = Comment.objects.filter(product=product).aggregate(
        avg_rating=Avg('rating')
    )['avg_rating']
    
    # Mettre à jour le rating du produit
    if avg_rating is not None:
        product.rating = round(avg_rating, 1)
    else:
        product.rating = 0.0
    
    product.save(update_fields=['rating'])


class CommentReport(models.Model):
    """
    Modèle pour signaler des commentaires inappropriés.
    """
    REPORT_REASONS = [
        ('inappropriate', 'Contenu inapproprié'),
        ('spam', 'Spam'),
        ('offensive', 'Contenu offensant'),
        ('fake', 'Fausse information'),
        ('other', 'Autre raison'),
    ]
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Commentaire signalé'
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reports',
        verbose_name='Utilisateur signalant'
    )
    reason = models.CharField(
        max_length=20,
        choices=REPORT_REASONS,
        verbose_name='Raison du signalement'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description du problème'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de signalement'
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name='Résolu'
    )

    class Meta:
        verbose_name = 'Signalement de commentaire'
        verbose_name_plural = 'Signalements de commentaires'
        unique_together = ['comment', 'reporter']  # Un seul signalement par utilisateur par commentaire
        ordering = ['-created_at']

    def __str__(self):
        return f'Signalement de {self.reporter.email} sur {self.comment}'
