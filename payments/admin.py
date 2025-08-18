"""
Admin configuration for payments app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Payment, Refund, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    
    list_display = [
        'id', 'order_link', 'user_link', 'amount', 'currency', 
        'status', 'payment_method', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'currency', 'created_at'
    ]
    search_fields = [
        'stripe_payment_intent_id', 'user__email', 'order__order_number'
    ]
    readonly_fields = [
        'id', 'stripe_payment_intent_id', 'stripe_client_secret',
        'created_at', 'updated_at', 'processed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'order', 'user', 'status')
        }),
        ('Détails du paiement', {
            'fields': ('amount', 'currency', 'payment_method', 'net_amount', 'stripe_fee')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_client_secret')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
        ('Informations supplémentaires', {
            'fields': ('failure_reason', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        """Link to related order."""
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.pk])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Commande'
    
    def user_link(self, obj):
        """Link to related user."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'Utilisateur'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin interface for Refund model."""
    
    list_display = [
        'id', 'payment_link', 'amount', 'currency', 'status', 
        'reason', 'created_at'
    ]
    list_filter = [
        'status', 'reason', 'currency', 'created_at'
    ]
    search_fields = [
        'stripe_refund_id', 'payment__stripe_payment_intent_id',
        'payment__user__email'
    ]
    readonly_fields = [
        'id', 'stripe_refund_id', 'created_at', 'updated_at', 'processed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'payment', 'status', 'reason')
        }),
        ('Détails du remboursement', {
            'fields': ('amount', 'currency', 'description')
        }),
        ('Stripe', {
            'fields': ('stripe_refund_id',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
        ('Informations supplémentaires', {
            'fields': ('failure_reason', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_link(self, obj):
        """Link to related payment."""
        if obj.payment:
            url = reverse('admin:payments_payment_change', args=[obj.payment.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.payment.id)[:8])
        return '-'
    payment_link.short_description = 'Paiement'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin interface for WebhookEvent model."""
    
    list_display = [
        'stripe_event_id', 'event_type', 'status', 'created_at'
    ]
    list_filter = [
        'status', 'event_type', 'created_at'
    ]
    search_fields = [
        'stripe_event_id', 'event_type'
    ]
    readonly_fields = [
        'stripe_event_id', 'event_type', 'data', 'created_at', 
        'updated_at', 'processed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('stripe_event_id', 'event_type', 'status')
        }),
        ('Traitement', {
            'fields': ('processed_at', 'error_message')
        }),
        ('Données', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding webhook events manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but not editing webhook events."""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deleting old webhook events."""
        return True
