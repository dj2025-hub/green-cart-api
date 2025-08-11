"""
Models for products management in GreenCart.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
from accounts.models import Producer


class Category(models.Model):
    """
    Product categories (fruits, vegetables, dairy, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        'Nom de la catégorie',
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        'Slug',
        max_length=100,
        unique=True,
        blank=True
    )
    description = models.TextField(
        'Description',
        blank=True,
        help_text='Description de la catégorie de produits'
    )
    
    # Emoji ou icône pour l'interface
    icon = models.CharField(
        'Icône',
        max_length=10,
        blank=True,
        help_text='Emoji ou classe d\'icône pour l\'affichage'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Products offered by producers.
    """
    
    # Choix pour les unités de mesure
    UNIT_CHOICES = [
        ('kg', 'Kilogramme'),
        ('g', 'Gramme'),
        ('piece', 'Pièce'),
        ('litre', 'Litre'),
        ('ml', 'Millilitre'),
        ('bunch', 'Bouquet'),
        ('box', 'Boîte'),
        ('bag', 'Sac'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    producer = models.ForeignKey(
        Producer,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Producteur'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Catégorie'
    )
    
    name = models.CharField(
        'Nom du produit',
        max_length=200,
        help_text='Nom du produit (ex: Tomates cerises bio)'
    )
    
    description = models.TextField(
        'Description',
        help_text='Description détaillée du produit, méthodes de culture, etc.'
    )
    
    price = models.DecimalField(
        'Prix',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Prix unitaire en euros'
    )
    
    unit = models.CharField(
        'Unité',
        max_length=10,
        choices=UNIT_CHOICES,
        default='kg',
        help_text='Unité de vente du produit'
    )
    
    quantity_available = models.PositiveIntegerField(
        'Quantité disponible',
        default=0,
        help_text='Quantité actuellement en stock'
    )
    
    expiry_date = models.DateField(
        'Date limite de consommation',
        null=True,
        blank=True,
        help_text='DLC du produit (optionnel pour les produits non périssables)'
    )
    
    # Image principale du produit stockée en base64
    image_data = models.TextField(
        'Photo du produit (Base64)',
        blank=True,
        help_text='Photo principale encodée en base64'
    )
    
    image_format = models.CharField(
        'Format image',
        max_length=10,
        blank=True,
        choices=[
            ('JPEG', 'JPEG'),
            ('PNG', 'PNG'),
            ('WEBP', 'WEBP'),
        ],
        help_text='Format de l\'image principale'
    )
    
    # Champs pour les caractéristiques spéciales
    is_organic = models.BooleanField(
        'Produit bio',
        default=False,
        help_text='Produit issu de l\'agriculture biologique'
    )
    
    is_local = models.BooleanField(
        'Produit local',
        default=True,
        help_text='Produit cultivé localement (moins de 50km)'
    )
    
    harvest_date = models.DateField(
        'Date de récolte',
        null=True,
        blank=True,
        help_text='Date de récolte du produit'
    )
    
    is_active = models.BooleanField(
        'Actif',
        default=True,
        help_text='Le produit est-il disponible à la vente ?'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['producer', 'is_active']),
            models.Index(fields=['is_active', 'expiry_date']),
            models.Index(fields=['is_organic']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.producer.business_name}"
    
    @property
    def is_available(self):
        """Vérifie si le produit est disponible."""
        return self.is_active and self.quantity_available > 0
    
    @property
    def is_expiring_soon(self, days=3):
        """Vérifie si le produit expire dans les X jours."""
        if not self.expiry_date:
            return False
        return (self.expiry_date - timezone.now().date()).days <= days
    
    @property
    def formatted_price(self):
        """Retourne le prix formaté avec l'unité."""
        return f"{self.price}€ / {self.get_unit_display().lower()}"
    
    def reduce_stock(self, quantity):
        """Réduit le stock du produit."""
        if self.quantity_available >= quantity:
            self.quantity_available -= quantity
            self.save(update_fields=['quantity_available'])
            return True
        return False
    
    def increase_stock(self, quantity):
        """Augmente le stock du produit."""
        self.quantity_available += quantity
        self.save(update_fields=['quantity_available'])


class ProductImage(models.Model):
    """
    Additional images for products.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Produit'
    )
    
    image_data = models.TextField(
        'Données image (Base64)',
        default='',
        blank=True,
        help_text='Image encodée en base64 pour stockage en BDD'
    )
    
    image_format = models.CharField(
        'Format image',
        max_length=10,
        default='JPEG',
        blank=True,
        choices=[
            ('JPEG', 'JPEG'),
            ('PNG', 'PNG'),
            ('WEBP', 'WEBP'),
        ],
        help_text='Format de l\'image'
    )
    
    alt_text = models.CharField(
        'Texte alternatif',
        max_length=200,
        blank=True,
        help_text='Description de l\'image pour l\'accessibilité'
    )
    
    order = models.PositiveIntegerField(
        'Ordre',
        default=0,
        help_text='Ordre d\'affichage de l\'image'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Image produit'
        verbose_name_plural = 'Images produits'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image de {self.product.name}"