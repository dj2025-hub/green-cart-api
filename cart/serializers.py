"""
Serializers for cart management in GreenCart.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Cart, CartItem
from products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem model."""
    
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    price_changed = serializers.BooleanField(read_only=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'cart', 'product', 'product_id', 'quantity',
            'price_at_time', 'total_price', 'price_changed',
            'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'cart', 'price_at_time', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_available(self, obj):
        """Check if product is still available in requested quantity."""
        return obj.is_available()
    
    def validate_product_id(self, value):
        """Validate that product exists and is active."""
        from products.models import Product
        
        try:
            product = Product.objects.get(id=value, is_active=True)
            return product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist or is not active.")
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value
    
    def validate(self, attrs):
        """Validate that there's enough stock."""
        if 'product_id' in attrs and 'quantity' in attrs:
            product = attrs['product_id']
            quantity = attrs['quantity']
            
            if product.quantity_available < quantity:
                raise serializers.ValidationError(
                    f"Not enough stock. Only {product.quantity_available} available."
                )
        
        return attrs


class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating cart items."""
    
    product_id = serializers.UUIDField()
    
    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity']
    
    def validate_product_id(self, value):
        """Validate that product exists and is active."""
        from products.models import Product
        
        try:
            product = Product.objects.get(id=value, is_active=True)
            return product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist or is not active.")
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value
    
    def validate(self, attrs):
        """Validate that there's enough stock."""
        product = attrs['product_id']
        quantity = attrs['quantity']
        
        if product.quantity_available < quantity:
            raise serializers.ValidationError(
                f"Not enough stock. Only {product.quantity_available} available."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create cart item."""
        request = self.context.get('request')
        cart, created = Cart.objects.get_or_create(consumer=request.user)
        
        product = validated_data['product_id']
        quantity = validated_data['quantity']
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'price_at_time': product.price
            }
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart model."""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'consumer', 'items', 'total_items',
            'total_amount', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'consumer', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart."""
    
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        """Validate that product exists and is active."""
        from products.models import Product
        
        try:
            product = Product.objects.get(id=value, is_active=True)
            return product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist or is not active.")
    
    def validate(self, attrs):
        """Validate that there's enough stock."""
        product = attrs['product_id']
        quantity = attrs['quantity']
        
        if product.quantity_available < quantity:
            raise serializers.ValidationError({
                'quantity': f"Not enough stock. Only {product.quantity_available} available."
            })
        
        return attrs
    
    def save(self):
        """Add item to cart."""
        request = self.context.get('request')
        cart, created = Cart.objects.get_or_create(consumer=request.user)
        
        product = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        
        return cart.add_product(product, quantity)


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity."""
    
    quantity = serializers.IntegerField(min_value=0)
    
    def validate(self, attrs):
        """Validate that there's enough stock."""
        cart_item = self.context.get('cart_item')
        quantity = attrs['quantity']
        
        if quantity > 0 and cart_item.product.quantity_available < quantity:
            raise serializers.ValidationError({
                'quantity': f"Not enough stock. Only {cart_item.product.quantity_available} available."
            })
        
        return attrs
    
    def save(self):
        """Update cart item quantity."""
        cart_item = self.context.get('cart_item')
        quantity = self.validated_data['quantity']
        
        if quantity == 0:
            cart_item.delete()
            return None
        else:
            cart_item.quantity = quantity
            cart_item.save()
            return cart_item