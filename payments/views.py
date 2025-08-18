"""
API views for payments app.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
import stripe
import logging

from .models import Payment, Refund, WebhookEvent
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, PaymentIntentResponseSerializer,
    RefundSerializer, RefundCreateSerializer, WebhookEventSerializer,
    PaymentStatsSerializer
)
from .stripe_client import StripeClient, convert_to_stripe_amount, convert_from_stripe_amount
from orders.models import Order

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=['Payments'],
        summary="Liste des paiements",
        description="Récupère la liste paginée des paiements avec filtres et recherche",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrer par statut'),
            OpenApiParameter('payment_method', OpenApiTypes.STR, description='Filtrer par méthode de paiement'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par ID Stripe, email utilisateur'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Payments'],
        summary="Détail d'un paiement",
        description="Récupère les détails d'un paiement spécifique"
    ),
    create=extend_schema(
        tags=['Payments'],
        summary="Créer un paiement",
        description="Crée un nouveau paiement pour une commande",
        request=PaymentCreateSerializer,
        responses={201: PaymentIntentResponseSerializer}
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for payment management."""
    
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'currency']
    search_fields = ['stripe_payment_intent_id', 'user__email', 'order__order_number']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Payment.objects.all()
        else:
            # Regular users can only see their own payments
            return Payment.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new payment intent."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        return_url = serializer.validated_data.get('return_url')
        
        try:
            # Get the order
            order = Order.objects.get(id=order_id, consumer=request.user)
            
            # Convert amount to Stripe format (cents)
            stripe_amount = convert_to_stripe_amount(order.total_amount)
            
            # Create payment intent
            payment_intent = StripeClient.create_payment_intent(
                amount=stripe_amount,
                currency=settings.STRIPE_CURRENCY,
                metadata={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'user_id': str(request.user.id),
                    'user_email': request.user.email,
                }
            )
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                stripe_payment_intent_id=payment_intent.id,
                stripe_client_secret=payment_intent.client_secret,
                amount=order.total_amount,
                currency=settings.STRIPE_CURRENCY,
                status='PENDING'
            )
            
            # Return response for frontend
            response_data = {
                'payment_id': payment.id,
                'client_secret': payment_intent.client_secret,
                'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                'amount': order.total_amount,
                'currency': settings.STRIPE_CURRENCY
            }
            
            response_serializer = PaymentIntentResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            return Response(
                {'error': 'Payment processing error'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Payments'],
        summary="Confirmer un paiement",
        description="Confirme un paiement côté serveur après confirmation client",
        responses={200: PaymentSerializer}
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a payment on server side."""
        payment = self.get_object()
        
        # Check if user owns this payment
        if payment.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Retrieve payment intent from Stripe
            payment_intent = StripeClient.retrieve_payment_intent(
                payment.stripe_payment_intent_id
            )
            
            # Update payment status based on Stripe status
            if payment_intent.status == 'succeeded':
                payment.mark_as_succeeded()
                # Update order status
                payment.order.confirm()
            elif payment_intent.status == 'canceled':
                payment.status = 'CANCELLED'
                payment.save()
            elif payment_intent.status in ['requires_payment_method', 'requires_confirmation']:
                payment.status = 'FAILED'
                payment.failure_reason = 'Payment requires additional action'
                payment.save()
            
            serializer = PaymentSerializer(payment)
            return Response(serializer.data)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {e}")
            return Response(
                {'error': 'Payment confirmation error'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Payments'],
        summary="Annuler un paiement",
        description="Annule un paiement en attente",
        responses={200: PaymentSerializer}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending payment."""
        payment = self.get_object()
        
        # Check if user owns this payment
        if payment.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not payment.is_pending:
            return Response(
                {'error': 'Payment cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Cancel payment intent in Stripe
            StripeClient.cancel_payment_intent(payment.stripe_payment_intent_id)
            
            # Update payment status
            payment.status = 'CANCELLED'
            payment.save()
            
            serializer = PaymentSerializer(payment)
            return Response(serializer.data)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling payment: {e}")
            return Response(
                {'error': 'Payment cancellation error'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Payments'],
        summary="Statistiques des paiements",
        description="Récupère les statistiques des paiements (admin uniquement)",
        responses={200: PaymentStatsSerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """Get payment statistics (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate stats
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='SUCCEEDED').count()
        failed_payments = Payment.objects.filter(status='FAILED').count()
        pending_payments = Payment.objects.filter(status__in=['PENDING', 'PROCESSING']).count()
        
        total_amount = Payment.objects.filter(status='SUCCEEDED').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_refunded = Refund.objects.filter(status='SUCCEEDED').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        stats_data = {
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'pending_payments': pending_payments,
            'total_amount': total_amount,
            'total_refunded': total_refunded,
            'success_rate': round(success_rate, 2)
        }
        
        serializer = PaymentStatsSerializer(stats_data)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Payments'],
        summary="Liste des remboursements",
        description="Récupère la liste paginée des remboursements"
    ),
    retrieve=extend_schema(
        tags=['Payments'],
        summary="Détail d'un remboursement",
        description="Récupère les détails d'un remboursement spécifique"
    ),
    create=extend_schema(
        tags=['Payments'],
        summary="Créer un remboursement",
        description="Crée un nouveau remboursement pour un paiement",
        request=RefundCreateSerializer,
        responses={201: RefundSerializer}
    )
)
class RefundViewSet(viewsets.ModelViewSet):
    """ViewSet for refund management."""
    
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'reason']
    search_fields = ['stripe_refund_id', 'payment__stripe_payment_intent_id']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Refund.objects.all()
        else:
            # Regular users can only see refunds for their payments
            return Refund.objects.filter(payment__user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new refund."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_id = serializer.validated_data['payment_id']
        amount = serializer.validated_data.get('amount')
        reason = serializer.validated_data['reason']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # Determine refund amount
            refund_amount = amount or payment.amount
            
            # Convert amount to Stripe format
            stripe_amount = convert_to_stripe_amount(refund_amount)
            
            # Create refund in Stripe
            stripe_refund = StripeClient.create_refund(
                payment_intent_id=payment.stripe_payment_intent_id,
                amount=stripe_amount,
                reason=reason.lower() if reason in ['duplicate', 'fraudulent', 'requested_by_customer'] else None,
                metadata={
                    'payment_id': str(payment.id),
                    'order_id': str(payment.order.id),
                    'user_id': str(payment.user.id),
                    'description': description
                }
            )
            
            # Create refund record
            refund = Refund.objects.create(
                payment=payment,
                stripe_refund_id=stripe_refund.id,
                amount=refund_amount,
                currency=payment.currency,
                reason=reason,
                description=description,
                status='PENDING'
            )
            
            serializer = RefundSerializer(refund)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            return Response(
                {'error': 'Refund processing error'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating refund: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    tags=['Payments'],
    summary="Informations de configuration Stripe",
    description="Récupère les informations publiques de configuration Stripe",
    responses={200: {
        'type': 'object',
        'properties': {
            'publishable_key': {'type': 'string'},
            'currency': {'type': 'string'},
            'country': {'type': 'string'}
        }
    }}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def stripe_config(request):
    """Get Stripe public configuration."""
    return Response({
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'currency': settings.STRIPE_CURRENCY,
        'country': 'FR'  # Can be made configurable
    })
