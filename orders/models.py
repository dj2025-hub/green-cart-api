"""
Models for orders management in GreenCart.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from products.models import Product
from accounts.models import Producer


class Order(models.Model):
    """
    Customer orders containing products from potentially multiple producers.
    """
    
    # Statuts des commandes
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmée'),
        ('CANCELLED', 'Annulée'),
        ('SHIPPED', 'Expédiée'),
        ('DELIVERED', 'Livrée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Numéro de commande lisible
    order_number = models.CharField(
        'Numéro de commande',
        max_length=20,
        unique=True,
        blank=True,
        help_text='Numéro de commande généré automatiquement'
    )
    
    consumer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Consommateur'
    )
    
    # Informations de livraison (copiées du profil utilisateur au moment de la commande)
    delivery_address = models.TextField(
        'Adresse de livraison',
        help_text='Adresse complète de livraison'
    )
    
    delivery_city = models.CharField(
        'Ville de livraison',
        max_length=100
    )
    
    delivery_postal_code = models.CharField(
        'Code postal de livraison',
        max_length=10
    )
    
    # Montant total de la commande
    total_amount = models.DecimalField(
        'Montant total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Montant total de la commande en euros'
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Statut actuel de la commande'
    )
    
    # Dates importantes
    order_date = models.DateTimeField(
        'Date de commande',
        default=timezone.now,
        help_text='Date et heure de passage de la commande'
    )
    
    delivery_date = models.DateField(
        'Date de livraison souhaitée',
        null=True,
        blank=True,
        help_text='Date de livraison souhaitée par le consommateur'
    )
    
    confirmed_at = models.DateTimeField(
        'Confirmée le',
        null=True,
        blank=True,
        help_text='Date de confirmation de la commande'
    )
    
    shipped_at = models.DateTimeField(
        'Expédiée le',
        null=True,
        blank=True,
        help_text='Date d\'expédition de la commande'
    )
    
    delivered_at = models.DateTimeField(
        'Livrée le',
        null=True,
        blank=True,
        help_text='Date de livraison effective'
    )
    
    # Notes et commentaires
    notes = models.TextField(
        'Notes',
        blank=True,
        help_text='Notes ou instructions spéciales pour la commande'
    )
    
    consumer_notes = models.TextField(
        'Notes du consommateur',
        blank=True,
        help_text='Notes laissées par le consommateur'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['consumer', '-order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['order_date']),
        ]
    
    def __str__(self):
        return f"Commande {self.order_number or self.id} - {self.consumer.email}"
    
    def save(self, *args, **kwargs):
        # Générer un numéro de commande si pas présent
        if not self.order_number:
            # Format: GC2024001 (GreenCart + année + numéro séquentiel)
            year = timezone.now().year
            last_order = Order.objects.filter(
                order_number__startswith=f'GC{year}'
            ).order_by('-order_number').first()
            
            if last_order and last_order.order_number:
                last_num = int(last_order.order_number[-3:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.order_number = f'GC{year}{new_num:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Retourne le nombre total d'articles dans la commande."""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def producers_involved(self):
        """Retourne la liste des producteurs impliqués dans cette commande."""
        return Producer.objects.filter(
            id__in=self.items.values_list('producer_id', flat=True).distinct()
        )
    
    @property
    def can_be_cancelled(self):
        """Vérifie si la commande peut être annulée."""
        return self.status in ['PENDING', 'CONFIRMED']
    
    @property
    def is_completed(self):
        """Vérifie si la commande est terminée."""
        return self.status in ['DELIVERED', 'CANCELLED']
    
    def cancel(self):
        """Annule la commande et remet les stocks."""
        if self.can_be_cancelled:
            # Remettre les stocks
            for item in self.items.all():
                item.product.increase_stock(item.quantity)
            
            self.status = 'CANCELLED'
            self.save(update_fields=['status'])
            return True
        return False
    
    def confirm(self):
        """Confirme la commande."""
        if self.status == 'PENDING':
            self.status = 'CONFIRMED'
            self.confirmed_at = timezone.now()
            self.save(update_fields=['status', 'confirmed_at'])
            return True
        return False


class OrderItem(models.Model):
    """
    Individual item in an order.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Commande'
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Produit'
    )
    
    # Producteur pour faciliter les requêtes
    producer = models.ForeignKey(
        Producer,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Producteur'
    )
    
    quantity = models.PositiveIntegerField(
        'Quantité',
        validators=[MinValueValidator(1)],
        help_text='Quantité commandée'
    )
    
    # Prix unitaire au moment de la commande
    unit_price = models.DecimalField(
        'Prix unitaire',
        max_digits=10,
        decimal_places=2,
        help_text='Prix unitaire au moment de la commande'
    )
    
    # Prix total pour cette ligne
    total_price = models.DecimalField(
        'Prix total',
        max_digits=10,
        decimal_places=2,
        help_text='Prix total pour cette ligne (quantité × prix unitaire)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Commande {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement le prix total
        self.total_price = self.quantity * self.unit_price
        
        # Copier le producteur depuis le produit si pas défini
        if not self.producer_id:
            self.producer = self.product.producer
        
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    History of status changes for orders.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Commande'
    )
    
    old_status = models.CharField(
        'Ancien statut',
        max_length=20,
        choices=Order.STATUS_CHOICES,
        blank=True
    )
    
    new_status = models.CharField(
        'Nouveau statut',
        max_length=20,
        choices=Order.STATUS_CHOICES
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='status_changes',
        verbose_name='Modifié par'
    )
    
    reason = models.TextField(
        'Raison du changement',
        blank=True,
        help_text='Raison ou commentaire sur le changement de statut'
    )
    
    changed_at = models.DateTimeField(
        'Modifié le',
        default=timezone.now
    )
    
    class Meta:
        verbose_name = 'Historique des statuts'
        verbose_name_plural = 'Historiques des statuts'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"