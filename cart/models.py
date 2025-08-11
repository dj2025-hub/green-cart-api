"""
Models for shopping cart management in GreenCart.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from products.models import Product


class Cart(models.Model):
    """
    Shopping cart for consumers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    consumer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Consommateur'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Panier'
        verbose_name_plural = 'Paniers'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Panier de {self.consumer.email}"
    
    @property
    def total_items(self):
        """Retourne le nombre total d'articles dans le panier."""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def total_amount(self):
        """Calcule le montant total du panier."""
        total = 0
        for item in self.items.all():
            total += item.total_price
        return total
    
    @property
    def items_count(self):
        """Retourne le nombre de types d'articles différents."""
        return self.items.count()
    
    def clear(self):
        """Vide le panier."""
        self.items.all().delete()
    
    def add_product(self, product, quantity=1):
        """
        Ajoute un produit au panier ou met à jour la quantité.
        """
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={
                'quantity': quantity,
                'price_at_time': product.price
            }
        )
        
        if not created:
            # Si l'article existe déjà, on met à jour la quantité
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    def remove_product(self, product):
        """Retire un produit du panier."""
        try:
            cart_item = self.items.get(product=product)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def update_quantity(self, product, quantity):
        """Met à jour la quantité d'un produit dans le panier."""
        try:
            cart_item = self.items.get(product=product)
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return True
        except CartItem.DoesNotExist:
            return False


class CartItem(models.Model):
    """
    Individual item in a shopping cart.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Panier'
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Produit'
    )
    
    quantity = models.PositiveIntegerField(
        'Quantité',
        validators=[MinValueValidator(1)],
        help_text='Quantité de ce produit dans le panier'
    )
    
    # Prix au moment de l'ajout (pour éviter les changements de prix)
    price_at_time = models.DecimalField(
        'Prix au moment de l\'ajout',
        max_digits=10,
        decimal_places=2,
        help_text='Prix unitaire du produit quand il a été ajouté au panier'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Article du panier'
        verbose_name_plural = 'Articles du panier'
        ordering = ['created_at']
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} dans le panier de {self.cart.consumer.email}"
    
    @property
    def total_price(self):
        """Calcule le prix total pour cette ligne d'article."""
        return self.quantity * self.price_at_time
    
    @property
    def price_changed(self):
        """Vérifie si le prix du produit a changé depuis l'ajout au panier."""
        return self.price_at_time != self.product.price
    
    def update_price(self):
        """Met à jour le prix avec le prix actuel du produit."""
        self.price_at_time = self.product.price
        self.save(update_fields=['price_at_time'])
    
    def is_available(self):
        """Vérifie si le produit est toujours disponible en quantité suffisante."""
        return (
            self.product.is_active and 
            self.product.quantity_available >= self.quantity
        )