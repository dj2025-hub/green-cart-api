"""
Stripe webhook handlers for payments app.
"""
import json
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import stripe

from .models import Payment, Refund, WebhookEvent
from .stripe_client import StripeClient, convert_from_stripe_amount
from orders.models import Order

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handler class for processing Stripe webhook events.
    """
    
    def __init__(self, event):
        self.event = event
        self.event_type = event['type']
        self.data = event['data']['object']
    
    def handle(self):
        """
        Route webhook event to appropriate handler method.
        """
        handler_map = {
            'payment_intent.succeeded': self.handle_payment_succeeded,
            'payment_intent.payment_failed': self.handle_payment_failed,
            'payment_intent.canceled': self.handle_payment_canceled,
            'payment_intent.processing': self.handle_payment_processing,
            'payment_intent.requires_action': self.handle_payment_requires_action,
            'charge.dispute.created': self.handle_dispute_created,
            'refund.created': self.handle_refund_created,
            'refund.updated': self.handle_refund_updated,
            'invoice.payment_succeeded': self.handle_invoice_payment_succeeded,
            'invoice.payment_failed': self.handle_invoice_payment_failed,
        }
        
        handler = handler_map.get(self.event_type)
        if handler:
            try:
                return handler()
            except Exception as e:
                logger.error(f"Error handling webhook {self.event_type}: {e}")
                raise
        else:
            logger.info(f"Unhandled webhook event type: {self.event_type}")
            return True  # Return True for unhandled but valid events
    
    def handle_payment_succeeded(self):
        """Handle successful payment."""
        payment_intent_id = self.data['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Update payment status
            payment.mark_as_succeeded()
            
            # Update payment details from Stripe
            if 'charges' in self.data and self.data['charges']['data']:
                charge = self.data['charges']['data'][0]
                
                # Update payment method
                if 'payment_method_details' in charge:
                    payment_method_type = charge['payment_method_details']['type']
                    payment.payment_method = payment_method_type.upper()
                
                # Update fees
                if 'balance_transaction' in charge:
                    # Note: balance_transaction might need to be retrieved separately
                    pass
            
            payment.save()
            
            # Update order status
            if payment.order.status == 'PENDING':
                payment.order.confirm()
            
            logger.info(f"Payment succeeded: {payment_intent_id}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return False
    
    def handle_payment_failed(self):
        """Handle failed payment."""
        payment_intent_id = self.data['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Get failure reason
            failure_reason = ''
            if 'last_payment_error' in self.data and self.data['last_payment_error']:
                failure_reason = self.data['last_payment_error'].get('message', '')
            
            # Update payment status
            payment.mark_as_failed(failure_reason)
            
            logger.info(f"Payment failed: {payment_intent_id} - {failure_reason}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return False
    
    def handle_payment_canceled(self):
        """Handle canceled payment."""
        payment_intent_id = self.data['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Update payment status
            payment.status = 'CANCELLED'
            payment.save()
            
            logger.info(f"Payment canceled: {payment_intent_id}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return False
    
    def handle_payment_processing(self):
        """Handle payment in processing state."""
        payment_intent_id = self.data['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Update payment status
            payment.status = 'PROCESSING'
            payment.save()
            
            logger.info(f"Payment processing: {payment_intent_id}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return False
    
    def handle_payment_requires_action(self):
        """Handle payment that requires additional action."""
        payment_intent_id = self.data['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            
            # Keep status as pending but log the requirement
            logger.info(f"Payment requires action: {payment_intent_id}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return False
    
    def handle_dispute_created(self):
        """Handle dispute creation."""
        charge_id = self.data['charge']
        dispute_id = self.data['id']
        
        # Log dispute for manual review
        logger.warning(f"Dispute created: {dispute_id} for charge: {charge_id}")
        
        # You might want to send notifications to admins here
        # or create a Dispute model to track disputes
        
        return True
    
    def handle_refund_created(self):
        """Handle refund creation."""
        refund_id = self.data['id']
        payment_intent_id = self.data.get('payment_intent')
        
        try:
            # Find the refund in our database
            refund = Refund.objects.get(stripe_refund_id=refund_id)
            
            # Update refund status based on Stripe status
            stripe_status = self.data['status']
            if stripe_status == 'succeeded':
                refund.mark_as_succeeded()
            elif stripe_status == 'failed':
                failure_reason = self.data.get('failure_reason', '')
                refund.mark_as_failed(failure_reason)
            
            logger.info(f"Refund created: {refund_id}")
            return True
            
        except Refund.DoesNotExist:
            logger.warning(f"Refund not found: {refund_id}")
            return False
    
    def handle_refund_updated(self):
        """Handle refund update."""
        refund_id = self.data['id']
        
        try:
            refund = Refund.objects.get(stripe_refund_id=refund_id)
            
            # Update refund status
            stripe_status = self.data['status']
            if stripe_status == 'succeeded' and refund.status != 'SUCCEEDED':
                refund.mark_as_succeeded()
            elif stripe_status == 'failed' and refund.status != 'FAILED':
                failure_reason = self.data.get('failure_reason', '')
                refund.mark_as_failed(failure_reason)
            
            logger.info(f"Refund updated: {refund_id}")
            return True
            
        except Refund.DoesNotExist:
            logger.warning(f"Refund not found: {refund_id}")
            return False
    
    def handle_invoice_payment_succeeded(self):
        """Handle successful invoice payment (for subscriptions if implemented)."""
        invoice_id = self.data['id']
        logger.info(f"Invoice payment succeeded: {invoice_id}")
        return True
    
    def handle_invoice_payment_failed(self):
        """Handle failed invoice payment (for subscriptions if implemented)."""
        invoice_id = self.data['id']
        logger.info(f"Invoice payment failed: {invoice_id}")
        return True


@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.error("Missing Stripe signature header")
        return Response(
            {'error': 'Missing signature'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Construct and verify webhook event
        event = StripeClient.construct_webhook_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Create webhook event record
        webhook_event = WebhookEvent.objects.create(
            stripe_event_id=event['id'],
            event_type=event['type'],
            data=event,
            status='RECEIVED'
        )
        
        # Process the event
        handler = WebhookHandler(event)
        success = handler.handle()
        
        if success:
            webhook_event.mark_as_processed()
            logger.info(f"Successfully processed webhook: {event['type']} - {event['id']}")
            return Response({'status': 'success'})
        else:
            webhook_event.mark_as_failed('Handler returned False')
            logger.error(f"Handler failed for webhook: {event['type']} - {event['id']}")
            return Response(
                {'error': 'Handler failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValueError as e:
        logger.error(f"Invalid payload in webhook: {e}")
        return Response(
            {'error': 'Invalid payload'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature in webhook: {e}")
        return Response(
            {'error': 'Invalid signature'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        
        # Try to mark webhook as failed if we have the event
        try:
            if 'webhook_event' in locals():
                webhook_event.mark_as_failed(str(e))
        except:
            pass
        
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_test(request):
    """
    Test endpoint to verify webhook URL is accessible.
    """
    return Response({
        'message': 'Webhook endpoint is accessible',
        'timestamp': timezone.now().isoformat()
    })
