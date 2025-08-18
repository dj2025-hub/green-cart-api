from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from .models import Comment, CommentReport
from products.serializers import ProductSerializer

User = get_user_model()


class UserCommentSerializer(serializers.ModelSerializer):
    """Sérialiseur pour afficher les informations utilisateur dans les commentaires."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'user_type']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 'user_type']


class CommentSerializer(serializers.ModelSerializer):
    """Sérialiseur principal pour les commentaires."""
    
    user = UserCommentSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'product', 'product_name', 'user', 'user_id',
            'comment', 'rating', 'created_at', 'updated_at',
            'can_edit', 'can_delete'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'product_name']
        validators = [
            UniqueTogetherValidator(
                queryset=Comment.objects.all(),
                fields=['product', 'user_id'],
                message='Vous avez déjà commenté ce produit.'
            )
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_can_edit(self, obj) -> bool:
        """Vérifier si l'utilisateur peut modifier le commentaire."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user == obj.user or request.user.is_staff
        return False
    
    @extend_schema_field(serializers.BooleanField)
    def get_can_delete(self, obj) -> bool:
        """Vérifier si l'utilisateur peut supprimer le commentaire."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user == obj.user or request.user.is_staff
        return False
    
    def validate_rating(self, value):
        """Validation personnalisée pour le rating."""
        if value < 0.0 or value > 5.0:
            raise serializers.ValidationError(
                'La note doit être comprise entre 0.0 et 5.0'
            )
        return value
    
    def validate_comment(self, value):
        """Validation personnalisée pour le commentaire."""
        if not value.strip():
            raise serializers.ValidationError(
                'Le commentaire ne peut pas être vide'
            )
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Le commentaire doit contenir au moins 10 caractères'
            )
        return value.strip()
    
    def create(self, validated_data):
        """Créer un commentaire en s'assurant que l'utilisateur est connecté."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            validated_data['user_id'] = request.user.id
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création de commentaires."""
    
    class Meta:
        model = Comment
        fields = ['product', 'comment', 'rating']
    
    def validate_rating(self, value):
        """Validation personnalisée pour le rating."""
        if value < 0.0 or value > 5.0:
            raise serializers.ValidationError(
                'La note doit être comprise entre 0.0 et 5.0'
            )
        return value
    
    def validate_comment(self, value):
        """Validation personnalisée pour le commentaire."""
        if not value.strip():
            raise serializers.ValidationError(
                'Le commentaire ne peut pas être vide'
            )
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Le commentaire doit contenir au moins 10 caractères'
            )
        return value.strip()
    
    def create(self, validated_data):
        """Créer un commentaire avec l'utilisateur connecté."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                'Vous devez être connecté pour commenter'
            )
        
        validated_data['user'] = request.user
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour de commentaires."""
    
    class Meta:
        model = Comment
        fields = ['comment', 'rating']
    
    def validate_rating(self, value):
        """Validation personnalisée pour le rating."""
        if value < 0.0 or value > 5.0:
            raise serializers.ValidationError(
                'La note doit être comprise entre 0.0 et 5.0'
            )
        return value
    
    def validate_comment(self, value):
        """Validation personnalisée pour le commentaire."""
        if not value.strip():
            raise serializers.ValidationError(
                'Le commentaire ne peut pas être vide'
            )
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Le commentaire doit contenir au moins 10 caractères'
            )
        return value.strip()
    
    def update(self, instance, validated_data):
        """Mettre à jour le commentaire."""
        # Vérifier que l'utilisateur peut modifier ce commentaire
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user != instance.user and not request.user.is_staff:
                raise serializers.ValidationError(
                    'Vous ne pouvez modifier que vos propres commentaires'
                )
        
        return super().update(instance, validated_data)


class CommentListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour lister les commentaires."""
    
    user = UserCommentSerializer(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'product_id', 'product_name', 'user',
            'comment', 'rating', 'created_at'
        ]


class CommentReportSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les signalements de commentaires."""
    
    reporter = UserCommentSerializer(read_only=True)
    comment_text = serializers.CharField(source='comment.comment', read_only=True)
    product_name = serializers.CharField(source='comment.product.name', read_only=True)
    
    class Meta:
        model = CommentReport
        fields = [
            'id', 'comment', 'comment_text', 'product_name',
            'reporter', 'reason', 'description', 'created_at', 'is_resolved'
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'is_resolved']
    
    def create(self, validated_data):
        """Créer un signalement avec l'utilisateur connecté."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                'Vous devez être connecté pour signaler un commentaire'
            )
        
        validated_data['reporter'] = request.user
        return super().create(validated_data)


class CommentStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des commentaires."""
    
    total_comments = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=1)
    rating_distribution = serializers.DictField()
    recent_comments = serializers.ListField()
