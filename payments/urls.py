"""
URL configuration for payments app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, RefundViewSet, stripe_config
from .webhooks import stripe_webhook, webhook_test

# Create router for viewsets
router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'refunds', RefundViewSet)

app_name = 'payments'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Configuration endpoints
    path('config/', stripe_config, name='stripe-config'),
    
    # Webhook endpoints
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    path('webhooks/test/', webhook_test, name='webhook-test'),
]
