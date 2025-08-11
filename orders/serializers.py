"""
Serializers for orders management in GreenCart.
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from .models import Order, OrderItem, OrderStatusHistory
from products.serializers import ProductListSerializer
from accounts.serializers import ProducerSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    
    product = ProductListSerializer(read_only=True)
    producer = ProducerSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'producer', 'quantity',
            'unit_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for OrderStatusHistory model."""
    
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'order', 'old_status', 'new_status',
            'old_status_display', 'new_status_display',
            'changed_by', 'changed_by_name', 'reason', 'changed_at'
        ]
        read_only_fields = ['id', 'changed_at']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    producers_involved = ProducerSerializer(many=True, read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'consumer', 'status', 'status_display',
            'total_amount', 'total_items', 'delivery_address', 'delivery_city',
            'delivery_postal_code', 'delivery_date', 'order_date',
            'confirmed_at', 'shipped_at', 'delivered_at', 'notes',
            'consumer_notes', 'items', 'status_history', 'producers_involved',
            'can_be_cancelled', 'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'consumer', 'total_amount', 'total_items',
            'order_date', 'confirmed_at', 'shipped_at', 'delivered_at',
            'created_at', 'updated_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for order listings."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    producers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'total_amount', 'total_items', 'producers_count',
            'order_date', 'delivery_date', 'consumer_notes'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_producers_count(self, obj):
        """Count number of producers involved in this order."""
        return obj.producers_involved.count()


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating orders from cart."""
    
    delivery_address = serializers.CharField(max_length=500)
    delivery_city = serializers.CharField(max_length=100)
    delivery_postal_code = serializers.CharField(max_length=10)
    delivery_date = serializers.DateField(required=False, allow_null=True)
    consumer_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_delivery_date(self, value):
        """Validate delivery date is in the future."""
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value
    
    def validate(self, attrs):
        """Validate that cart has items."""
        request = self.context.get('request')
        
        try:
            cart = request.user.cart
            if not cart.items.exists():
                raise serializers.ValidationError("Cart is empty.")
            
            # Check that all items are still available
            for item in cart.items.all():
                if not item.is_available():
                    raise serializers.ValidationError(
                        f"Product '{item.product.name}' is no longer available in requested quantity."
                    )
        except AttributeError:
            raise serializers.ValidationError("Cart not found.")
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Create order from cart."""
        request = self.context.get('request')
        cart = request.user.cart
        
        # Calculate total amount
        total_amount = cart.total_amount
        
        # Create order
        order = Order.objects.create(
            consumer=request.user,
            total_amount=total_amount,
            delivery_address=validated_data['delivery_address'],
            delivery_city=validated_data['delivery_city'],
            delivery_postal_code=validated_data['delivery_postal_code'],
            delivery_date=validated_data.get('delivery_date'),
            consumer_notes=validated_data.get('consumer_notes', ''),
            status='PENDING'
        )
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                producer=cart_item.product.producer,
                quantity=cart_item.quantity,
                unit_price=cart_item.price_at_time
            )
            
            # Reduce product stock
            cart_item.product.reduce_stock(cart_item.quantity)
        
        # Clear cart
        cart.clear()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status='PENDING',
            changed_by=request.user,
            reason='Order created'
        )
        
        return order


class UpdateOrderStatusSerializer(serializers.Serializer):
    """Serializer for updating order status (producers only)."""
    
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate status transition."""
        order = self.context.get('order')
        new_status = attrs['status']
        current_status = order.status
        
        # Define valid status transitions
        valid_transitions = {
            'PENDING': ['CONFIRMED', 'CANCELLED'],
            'CONFIRMED': ['SHIPPED', 'CANCELLED'],
            'SHIPPED': ['DELIVERED'],
            'CANCELLED': [],  # Cannot change from cancelled
            'DELIVERED': []   # Cannot change from delivered
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {new_status}."
            )
        
        return attrs
    
    @transaction.atomic
    def save(self):
        """Update order status."""
        order = self.context.get('order')
        request = self.context.get('request')
        
        old_status = order.status
        new_status = self.validated_data['status']
        reason = self.validated_data.get('reason', '')
        
        # Update order status
        order.status = new_status
        
        # Update timestamp fields
        now = timezone.now()
        if new_status == 'CONFIRMED':
            order.confirmed_at = now
        elif new_status == 'SHIPPED':
            order.shipped_at = now
        elif new_status == 'DELIVERED':
            order.delivered_at = now
        
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            reason=reason
        )
        
        return order


class CancelOrderSerializer(serializers.Serializer):
    """Serializer for cancelling orders."""
    
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate that order can be cancelled."""
        order = self.context.get('order')
        
        if not order.can_be_cancelled:
            raise serializers.ValidationError("This order cannot be cancelled.")
        
        return attrs
    
    @transaction.atomic
    def save(self):
        """Cancel the order."""
        order = self.context.get('order')
        request = self.context.get('request')
        reason = self.validated_data.get('reason', 'Cancelled by customer')
        
        # Cancel the order (this will restore stock)
        if order.cancel():
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status='PENDING' if order.status == 'CANCELLED' else order.status,
                new_status='CANCELLED',
                changed_by=request.user,
                reason=reason
            )
        
        return order