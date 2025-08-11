"""
Serializers for products management in GreenCart.
"""
from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, ProductImage
from accounts.serializers import ProducerSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_products_count(self, obj):
        """Count active products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image_data', 'image_format', 'alt_text', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    # Related fields
    producer = ProducerSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    
    # Additional computed fields
    formatted_price = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'producer', 'category', 'category_id',
            'name', 'description', 'price', 'unit', 'quantity_available',
            'expiry_date', 'harvest_date', 'image_data', 'image_format', 'images',
            'is_organic', 'is_local', 'is_active',
            'formatted_price', 'is_available', 'is_expiring_soon',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'producer', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expiring_soon(self, obj):
        """Check if product expires soon."""
        return obj.is_expiring_soon
    
    def validate_category_id(self, value):
        """Validate that category exists."""
        try:
            Category.objects.get(id=value)
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category does not exist.")
    
    def validate_expiry_date(self, value):
        """Validate expiry date is in the future."""
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value
    
    def validate_quantity_available(self, value):
        """Validate quantity is not negative."""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def create(self, validated_data):
        """Create product with producer from request user."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'producer_profile'):
            validated_data['producer'] = request.user.producer_profile
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product listings."""
    
    producer_name = serializers.CharField(source='producer.business_name', read_only=True)
    producer_region = serializers.CharField(source='producer.region', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    
    formatted_price = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'unit',
            'formatted_price', 'quantity_available', 'expiry_date',
            'image_data', 'image_format', 'is_organic', 'is_local', 'is_available',
            'is_expiring_soon', 'producer_name', 'producer_region',
            'category_name', 'category_icon', 'created_at'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expiring_soon(self, obj):
        """Check if product expires soon."""
        return obj.is_expiring_soon


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products (producer only)."""
    
    category_id = serializers.UUIDField()
    
    class Meta:
        model = Product
        fields = [
            'category_id', 'name', 'description', 'price', 'unit',
            'quantity_available', 'expiry_date', 'harvest_date',
            'image_data', 'image_format', 'is_organic', 'is_local', 'is_active'
        ]
    
    def validate_category_id(self, value):
        """Validate that category exists."""
        try:
            category = Category.objects.get(id=value)
            return category
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category does not exist.")
    
    def validate_expiry_date(self, value):
        """Validate expiry date is in the future."""
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value
    
    def validate_quantity_available(self, value):
        """Validate quantity is not negative."""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def create(self, validated_data):
        """Create product with producer from request user."""
        request = self.context.get('request')
        validated_data['category'] = validated_data.pop('category_id')
        
        if request and hasattr(request.user, 'producer_profile'):
            validated_data['producer'] = request.user.producer_profile
        
        return Product.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update product."""
        if 'category_id' in validated_data:
            validated_data['category'] = validated_data.pop('category_id')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance