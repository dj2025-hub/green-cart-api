"""
Serializers for payments app.
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Payment, Refund, WebhookEvent
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    can_be_refunded = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'user', 'user_email',
            'stripe_payment_intent_id', 'amount', 'formatted_amount',
            'currency', 'status', 'payment_method', 'stripe_fee',
            'net_amount', 'created_at', 'updated_at', 'processed_at',
            'failure_reason', 'is_successful', 'is_pending', 'can_be_refunded'
        ]
        read_only_fields = [
            'id', 'stripe_payment_intent_id', 'stripe_fee', 'net_amount',
            'created_at', 'updated_at', 'processed_at', 'failure_reason'
        ]
    
    def get_formatted_amount(self, obj):
        """Return formatted amount with currency."""
        return f"{obj.amount} {obj.currency}"


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating a payment."""
    
    order_id = serializers.UUIDField()
    return_url = serializers.URLField(required=False)
    
    def validate_order_id(self, value):
        """Validate that order exists and belongs to user."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            order = Order.objects.get(id=value, consumer=request.user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found or access denied")
        
        # Check if order already has a payment
        if hasattr(order, 'payment'):
            raise serializers.ValidationError("Order already has a payment")
        
        # Check if order can be paid
        if order.status != 'PENDING':
            raise serializers.ValidationError("Order cannot be paid in current status")
        
        return value


class PaymentIntentResponseSerializer(serializers.Serializer):
    """Serializer for payment intent response."""
    
    payment_id = serializers.UUIDField()
    client_secret = serializers.CharField()
    publishable_key = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model."""
    
    payment_id = serializers.CharField(source='payment.id', read_only=True)
    order_number = serializers.CharField(source='payment.order.order_number', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    is_successful = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'payment_id', 'order_number',
            'stripe_refund_id', 'amount', 'formatted_amount',
            'currency', 'status', 'reason', 'description',
            'created_at', 'updated_at', 'processed_at',
            'failure_reason', 'is_successful'
        ]
        read_only_fields = [
            'id', 'stripe_refund_id', 'created_at', 'updated_at',
            'processed_at', 'failure_reason'
        ]
    
    def get_formatted_amount(self, obj):
        """Return formatted amount with currency."""
        return f"{obj.amount} {obj.currency}"


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for creating a refund."""
    
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Amount to refund. If not provided, full amount will be refunded."
    )
    reason = serializers.ChoiceField(
        choices=Refund.REASON_CHOICES,
        default='REQUESTED_BY_CUSTOMER'
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Optional description for the refund"
    )
    
    def validate_payment_id(self, value):
        """Validate that payment exists and can be refunded."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        try:
            payment = Payment.objects.get(id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found")
        
        # Check if user has permission to refund
        if not (request.user.is_staff or payment.user == request.user):
            raise serializers.ValidationError("Permission denied")
        
        # Check if payment can be refunded
        if not payment.can_be_refunded:
            raise serializers.ValidationError("Payment cannot be refunded")
        
        return value
    
    def validate_amount(self, value):
        """Validate refund amount."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Refund amount must be positive")
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        payment_id = attrs.get('payment_id')
        amount = attrs.get('amount')
        
        if payment_id and amount:
            try:
                payment = Payment.objects.get(id=payment_id)
                
                # Check if refund amount doesn't exceed payment amount
                total_refunded = sum(
                    refund.amount for refund in payment.refunds.filter(
                        status='SUCCEEDED'
                    )
                )
                
                if total_refunded + amount > payment.amount:
                    raise serializers.ValidationError({
                        'amount': 'Refund amount exceeds available amount'
                    })
                    
            except Payment.DoesNotExist:
                pass  # Will be caught by payment_id validation
        
        return attrs


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEvent model."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'stripe_event_id', 'event_type', 'status',
            'processed_at', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_event_id', 'event_type', 'data',
            'processed_at', 'error_message', 'created_at', 'updated_at'
        ]


class PaymentStatsSerializer(serializers.Serializer):
    """Serializer for payment statistics."""
    
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_refunded = serializers.DecimalField(max_digits=15, decimal_places=2)
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
