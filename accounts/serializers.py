"""
Serializers for the accounts app API.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_field
from .models import User, Producer


class ProducerSerializer(serializers.ModelSerializer):
    """Serializer for Producer model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = Producer
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'business_name', 'description', 'siret',
            'address', 'city', 'postal_code', 'region',
            'full_address', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    # Optional producer data for producer registration
    producer_data = ProducerSerializer(required=False, write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'user_type',
            'producer_data'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        """Validate password confirmation and strength."""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })

        # Validate producer data if user type is PRODUCER
        if attrs.get('user_type') == 'PRODUCER':
            if not attrs.get('producer_data'):
                raise serializers.ValidationError({
                    'producer_data': 'Producer information is required for producer accounts.'
                })

        return attrs

    def create(self, validated_data):
        """Create a new user."""
        password = validated_data.pop('password')
        producer_data = validated_data.pop('producer_data', None)
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create producer profile if needed
        if user.user_type == 'PRODUCER' and producer_data:
            Producer.objects.create(user=user, **producer_data)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Try to authenticate with email
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include email and password.',
                code='authorization'
            )


def validate_phone_number(value):
    """Validate phone number format for Cameroon."""
    if value:
        # Remove spaces and check format
        cleaned_number = value.replace(' ', '')

        # Check if it matches Cameroon format
        import re
        pattern = r'^(\+237|237)?[2368]\d{7,8}$'
        if not re.match(pattern, cleaned_number):
            raise serializers.ValidationError(
                "Phone number must be in Cameroon format. Example: +237677123456"
            )
    return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (read/update)."""

    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj) -> str:
        return obj.full_name
    
    full_name = serializers.SerializerMethodField()
    
    @extend_schema_field(serializers.URLField)
    def get_avatar_url(self, obj) -> str:
        return obj.avatar_url
    
    avatar_url = serializers.SerializerMethodField()
    producer_profile = ProducerSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'user_type', 'avatar', 'avatar_url', 'full_name',
            'is_verified', 'date_joined', 'last_login', 'producer_profile'
        )
        read_only_fields = (
            'id', 'email', 'user_type', 'is_verified', 'date_joined', 'last_login'
        )


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list (minimal data)."""

    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj) -> str:
        return obj.full_name
    
    full_name = serializers.SerializerMethodField()
    
    @extend_schema_field(serializers.URLField)
    def get_avatar_url(self, obj) -> str:
        return obj.avatar_url
    
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'avatar_url',
            'is_verified', 'date_joined'
        )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate the old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate password confirmation and strength."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })

        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })

        return attrs

    def save(self):
        """Change the user's password."""
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics."""

    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
