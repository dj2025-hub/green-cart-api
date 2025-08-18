"""
Stripe client configuration and utilities for GreenCart payments.
"""
import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

# Configure Stripe with secret key
if not settings.STRIPE_SECRET_KEY:
    raise ImproperlyConfigured(
        "STRIPE_SECRET_KEY must be set in environment variables"
    )

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeClient:
    """
    Wrapper class for Stripe API operations.
    """
    
    @staticmethod
    def create_payment_intent(amount, currency='EUR', metadata=None):
        """
        Create a Stripe PaymentIntent.
        
        Args:
            amount (int): Amount in cents (e.g., 2000 for 20.00 EUR)
            currency (str): Currency code (default: EUR)
            metadata (dict): Additional metadata for the payment
            
        Returns:
            stripe.PaymentIntent: Created PaymentIntent object
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            logger.info(f"Created PaymentIntent: {payment_intent.id}")
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            raise
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Retrieve a Stripe PaymentIntent.
        
        Args:
            payment_intent_id (str): PaymentIntent ID
            
        Returns:
            stripe.PaymentIntent: Retrieved PaymentIntent object
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Retrieved PaymentIntent: {payment_intent_id}")
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving PaymentIntent {payment_intent_id}: {e}")
            raise
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id, payment_method=None):
        """
        Confirm a Stripe PaymentIntent.
        
        Args:
            payment_intent_id (str): PaymentIntent ID
            payment_method (str): Payment method ID (optional)
            
        Returns:
            stripe.PaymentIntent: Confirmed PaymentIntent object
        """
        try:
            confirm_params = {}
            if payment_method:
                confirm_params['payment_method'] = payment_method
            
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_params
            )
            logger.info(f"Confirmed PaymentIntent: {payment_intent_id}")
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming PaymentIntent {payment_intent_id}: {e}")
            raise
    
    @staticmethod
    def cancel_payment_intent(payment_intent_id):
        """
        Cancel a Stripe PaymentIntent.
        
        Args:
            payment_intent_id (str): PaymentIntent ID
            
        Returns:
            stripe.PaymentIntent: Cancelled PaymentIntent object
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Cancelled PaymentIntent: {payment_intent_id}")
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling PaymentIntent {payment_intent_id}: {e}")
            raise
    
    @staticmethod
    def create_refund(payment_intent_id, amount=None, reason=None, metadata=None):
        """
        Create a refund for a PaymentIntent.
        
        Args:
            payment_intent_id (str): PaymentIntent ID
            amount (int): Amount to refund in cents (optional, defaults to full amount)
            reason (str): Reason for refund
            metadata (dict): Additional metadata
            
        Returns:
            stripe.Refund: Created Refund object
        """
        try:
            refund_params = {
                'payment_intent': payment_intent_id,
                'metadata': metadata or {}
            }
            
            if amount:
                refund_params['amount'] = amount
            
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            logger.info(f"Created refund: {refund.id} for PaymentIntent: {payment_intent_id}")
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund for {payment_intent_id}: {e}")
            raise
    
    @staticmethod
    def retrieve_refund(refund_id):
        """
        Retrieve a Stripe Refund.
        
        Args:
            refund_id (str): Refund ID
            
        Returns:
            stripe.Refund: Retrieved Refund object
        """
        try:
            refund = stripe.Refund.retrieve(refund_id)
            logger.info(f"Retrieved refund: {refund_id}")
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving refund {refund_id}: {e}")
            raise
    
    @staticmethod
    def construct_webhook_event(payload, signature, webhook_secret=None):
        """
        Construct and verify a Stripe webhook event.
        
        Args:
            payload (bytes): Raw request body
            signature (str): Stripe signature header
            webhook_secret (str): Webhook secret (optional, uses settings default)
            
        Returns:
            stripe.Event: Constructed webhook event
        """
        webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET
        
        if not webhook_secret:
            raise ImproperlyConfigured(
                "STRIPE_WEBHOOK_SECRET must be set to verify webhooks"
            )
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            logger.info(f"Constructed webhook event: {event['type']} - {event['id']}")
            return event
        except ValueError as e:
            logger.error(f"Invalid payload in webhook: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in webhook: {e}")
            raise
    
    @staticmethod
    def list_payment_methods(customer_id, type='card'):
        """
        List payment methods for a customer.
        
        Args:
            customer_id (str): Stripe customer ID
            type (str): Payment method type (default: card)
            
        Returns:
            stripe.ListObject: List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type=type
            )
            logger.info(f"Listed payment methods for customer: {customer_id}")
            return payment_methods
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error listing payment methods for {customer_id}: {e}")
            raise
    
    @staticmethod
    def create_customer(email, name=None, metadata=None):
        """
        Create a Stripe customer.
        
        Args:
            email (str): Customer email
            name (str): Customer name (optional)
            metadata (dict): Additional metadata
            
        Returns:
            stripe.Customer: Created Customer object
        """
        try:
            customer_params = {
                'email': email,
                'metadata': metadata or {}
            }
            
            if name:
                customer_params['name'] = name
            
            customer = stripe.Customer.create(**customer_params)
            logger.info(f"Created customer: {customer.id} for email: {email}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer for {email}: {e}")
            raise
    
    @staticmethod
    def retrieve_customer(customer_id):
        """
        Retrieve a Stripe customer.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            stripe.Customer: Retrieved Customer object
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            logger.info(f"Retrieved customer: {customer_id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving customer {customer_id}: {e}")
            raise


def convert_to_stripe_amount(amount, currency='EUR'):
    """
    Convert decimal amount to Stripe amount (cents).
    
    Args:
        amount (Decimal): Amount in major currency unit
        currency (str): Currency code
        
    Returns:
        int: Amount in minor currency unit (cents)
    """
    # Most currencies use 2 decimal places, but some exceptions exist
    zero_decimal_currencies = [
        'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 
        'MGA', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 
        'XOF', 'XPF'
    ]
    
    if currency.upper() in zero_decimal_currencies:
        return int(amount)
    else:
        return int(amount * 100)


def convert_from_stripe_amount(amount, currency='EUR'):
    """
    Convert Stripe amount (cents) to decimal amount.
    
    Args:
        amount (int): Amount in minor currency unit (cents)
        currency (str): Currency code
        
    Returns:
        Decimal: Amount in major currency unit
    """
    from decimal import Decimal
    
    zero_decimal_currencies = [
        'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 
        'MGA', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 
        'XOF', 'XPF'
    ]
    
    if currency.upper() in zero_decimal_currencies:
        return Decimal(str(amount))
    else:
        return Decimal(str(amount)) / 100
