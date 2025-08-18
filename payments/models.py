"""
Models for payment processing with Stripe integration.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from orders.models import Order


class Payment(models.Model):
    """
    Payment record for orders processed through Stripe.
    """
    
    # Payment status choices
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours de traitement'),
        ('SUCCEEDED', 'Réussi'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
        ('REFUNDED', 'Remboursé'),
        ('PARTIALLY_REFUNDED', 'Partiellement remboursé'),
    ]
    
    # Payment method choices
    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Carte bancaire'),
        ('SEPA_DEBIT', 'Prélèvement SEPA'),
        ('BANCONTACT', 'Bancontact'),
        ('IDEAL', 'iDEAL'),
        ('SOFORT', 'Sofort'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Commande'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Utilisateur'
    )
    
    # Stripe identifiers
    stripe_payment_intent_id = models.CharField(
        'Stripe Payment Intent ID',
        max_length=255,
        unique=True,
        help_text='ID du PaymentIntent Stripe'
    )
    
    stripe_client_secret = models.CharField(
        'Stripe Client Secret',
        max_length=255,
        blank=True,
        help_text='Client secret pour confirmer le paiement côté client'
    )
    
    # Payment details
    amount = models.DecimalField(
        'Montant',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Montant du paiement en euros'
    )
    
    currency = models.CharField(
        'Devise',
        max_length=3,
        default='EUR',
        help_text='Code devise ISO (EUR, USD, etc.)'
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Statut actuel du paiement'
    )
    
    payment_method = models.CharField(
        'Méthode de paiement',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        help_text='Méthode de paiement utilisée'
    )
    
    # Stripe metadata
    stripe_fee = models.DecimalField(
        'Frais Stripe',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Frais prélevés par Stripe'
    )
    
    net_amount = models.DecimalField(
        'Montant net',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Montant net après déduction des frais'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        'Traité le',
        null=True,
        blank=True,
        help_text='Date et heure de traitement du paiement'
    )
    
    # Additional fields
    failure_reason = models.TextField(
        'Raison de l\'échec',
        blank=True,
        help_text='Raison de l\'échec du paiement si applicable'
    )
    
    metadata = models.JSONField(
        'Métadonnées',
        default=dict,
        blank=True,
        help_text='Métadonnées additionnelles du paiement'
    )
    
    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Paiement {self.amount}€ - Commande {self.order.order_number}"
    
    @property
    def is_successful(self):
        """Vérifie si le paiement a réussi."""
        return self.status == 'SUCCEEDED'
    
    @property
    def is_pending(self):
        """Vérifie si le paiement est en attente."""
        return self.status in ['PENDING', 'PROCESSING']
    
    @property
    def can_be_refunded(self):
        """Vérifie si le paiement peut être remboursé."""
        return self.status == 'SUCCEEDED'
    
    def mark_as_succeeded(self):
        """Marque le paiement comme réussi."""
        self.status = 'SUCCEEDED'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, reason=''):
        """Marque le paiement comme échoué."""
        self.status = 'FAILED'
        self.failure_reason = reason
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'failure_reason', 'processed_at'])


class Refund(models.Model):
    """
    Refund record for payments.
    """
    
    # Refund status choices
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('SUCCEEDED', 'Réussi'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
    ]
    
    # Refund reason choices
    REASON_CHOICES = [
        ('REQUESTED_BY_CUSTOMER', 'Demandé par le client'),
        ('DUPLICATE', 'Paiement en double'),
        ('FRAUDULENT', 'Frauduleux'),
        ('SUBSCRIPTION_CANCELED', 'Abonnement annulé'),
        ('PRODUCT_UNACCEPTABLE', 'Produit non acceptable'),
        ('PRODUCT_NOT_RECEIVED', 'Produit non reçu'),
        ('UNRECOGNIZED', 'Non reconnu'),
        ('CREDIT_NOT_PROCESSED', 'Crédit non traité'),
        ('GENERAL', 'Raison générale'),
        ('INCORRECT_ACCOUNT_DETAILS', 'Détails de compte incorrects'),
        ('INSUFFICIENT_FUNDS', 'Fonds insuffisants'),
        ('PRODUCT_NOT_RECEIVED', 'Produit non reçu'),
        ('PRODUCT_UNACCEPTABLE', 'Produit non acceptable'),
        ('SUBSCRIPTION_CANCELED', 'Abonnement annulé'),
        ('UNRECOGNIZED', 'Non reconnu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='Paiement'
    )
    
    # Stripe identifiers
    stripe_refund_id = models.CharField(
        'Stripe Refund ID',
        max_length=255,
        unique=True,
        help_text='ID du remboursement Stripe'
    )
    
    # Refund details
    amount = models.DecimalField(
        'Montant remboursé',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Montant du remboursement en euros'
    )
    
    currency = models.CharField(
        'Devise',
        max_length=3,
        default='EUR',
        help_text='Code devise ISO (EUR, USD, etc.)'
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Statut actuel du remboursement'
    )
    
    reason = models.CharField(
        'Raison',
        max_length=50,
        choices=REASON_CHOICES,
        default='REQUESTED_BY_CUSTOMER',
        help_text='Raison du remboursement'
    )
    
    description = models.TextField(
        'Description',
        blank=True,
        help_text='Description détaillée du remboursement'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        'Traité le',
        null=True,
        blank=True,
        help_text='Date et heure de traitement du remboursement'
    )
    
    # Additional fields
    failure_reason = models.TextField(
        'Raison de l\'échec',
        blank=True,
        help_text='Raison de l\'échec du remboursement si applicable'
    )
    
    metadata = models.JSONField(
        'Métadonnées',
        default=dict,
        blank=True,
        help_text='Métadonnées additionnelles du remboursement'
    )
    
    class Meta:
        verbose_name = 'Remboursement'
        verbose_name_plural = 'Remboursements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_refund_id']),
            models.Index(fields=['payment', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Remboursement {self.amount}€ - Paiement {self.payment.id}"
    
    @property
    def is_successful(self):
        """Vérifie si le remboursement a réussi."""
        return self.status == 'SUCCEEDED'
    
    def mark_as_succeeded(self):
        """Marque le remboursement comme réussi."""
        self.status = 'SUCCEEDED'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, reason=''):
        """Marque le remboursement comme échoué."""
        self.status = 'FAILED'
        self.failure_reason = reason
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'failure_reason', 'processed_at'])


class WebhookEvent(models.Model):
    """
    Record of Stripe webhook events for audit and debugging.
    """
    
    # Event status choices
    STATUS_CHOICES = [
        ('RECEIVED', 'Reçu'),
        ('PROCESSED', 'Traité'),
        ('FAILED', 'Échoué'),
        ('IGNORED', 'Ignoré'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Stripe webhook data
    stripe_event_id = models.CharField(
        'Stripe Event ID',
        max_length=255,
        unique=True,
        help_text='ID unique de l\'événement Stripe'
    )
    
    event_type = models.CharField(
        'Type d\'événement',
        max_length=100,
        help_text='Type d\'événement Stripe (ex: payment_intent.succeeded)'
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='RECEIVED',
        help_text='Statut de traitement de l\'événement'
    )
    
    # Event data
    data = models.JSONField(
        'Données',
        help_text='Données complètes de l\'événement Stripe'
    )
    
    # Processing info
    processed_at = models.DateTimeField(
        'Traité le',
        null=True,
        blank=True,
        help_text='Date et heure de traitement de l\'événement'
    )
    
    error_message = models.TextField(
        'Message d\'erreur',
        blank=True,
        help_text='Message d\'erreur si le traitement a échoué'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Événement Webhook'
        verbose_name_plural = 'Événements Webhook'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.event_type} - {self.stripe_event_id}"
    
    def mark_as_processed(self):
        """Marque l'événement comme traité."""
        self.status = 'PROCESSED'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, error_message=''):
        """Marque l'événement comme échoué."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
