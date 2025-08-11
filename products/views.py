"""
API views for products management in GreenCart.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes

from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductCreateUpdateSerializer,
    ProductImageSerializer
)


@extend_schema_view(
    list=extend_schema(
        tags=['Categories'],
        summary="Liste des catégories",
        description="Récupère toutes les catégories de produits disponibles",
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par nom ou description'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tri par: name, -name'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Categories'],
        summary="Détail d'une catégorie",
        description="Récupère les détails d'une catégorie spécifique"
    )
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for product categories (read-only)."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


@extend_schema_view(
    list=extend_schema(
        tags=['Products'],
        summary="Liste des produits",
        description="Récupère la liste paginée des produits avec filtres avancés",
        parameters=[
            OpenApiParameter('category', OpenApiTypes.UUID, description='Filtrer par catégorie (UUID)'),
            OpenApiParameter('producer', OpenApiTypes.UUID, description='Filtrer par producteur (UUID)'),
            OpenApiParameter('is_organic', OpenApiTypes.BOOL, description='Produits biologiques uniquement'),
            OpenApiParameter('is_local', OpenApiTypes.BOOL, description='Produits locaux uniquement'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par nom, description, producteur'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tri: price, -price, name, -name, created_at, -created_at'),
            OpenApiParameter('region', OpenApiTypes.STR, description='Filtrer par région du producteur'),
            OpenApiParameter('expires_in_days', OpenApiTypes.INT, description='Produits expirant dans X jours'),
            OpenApiParameter('available_only', OpenApiTypes.BOOL, description='Produits en stock uniquement'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Products'],
        summary="Détail d'un produit",
        description="Récupère les détails complets d'un produit"
    ),
    create=extend_schema(
        tags=['Products'],
        summary="Créer un produit",
        description="Crée un nouveau produit (producteur authentifié uniquement)"
    ),
    update=extend_schema(
        tags=['Products'],
        summary="Modifier un produit",
        description="Modifie complètement un produit existant"
    ),
    partial_update=extend_schema(
        tags=['Products'],
        summary="Modifier partiellement un produit",
        description="Modifie partiellement un produit existant"
    ),
    destroy=extend_schema(
        tags=['Products'],
        summary="Supprimer un produit",
        description="Supprime un produit (producteur propriétaire uniquement)"
    )
)
class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for products management."""
    
    queryset = Product.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'producer', 'is_organic', 'is_local']
    search_fields = ['name', 'description', 'producer__business_name']
    ordering_fields = ['created_at', 'price', 'name', 'expiry_date']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on action and user."""
        user = self.request.user
        
        # Base queryset - only active products for public
        if self.action in ['list', 'retrieve']:
            queryset = Product.objects.filter(is_active=True)
        else:
            queryset = Product.objects.all()
        
        # Apply additional filters
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(producer__region__icontains=region)
        
        expires_in_days = self.request.query_params.get('expires_in_days')
        if expires_in_days:
            try:
                days = int(expires_in_days)
                expire_date = timezone.now().date() + timedelta(days=days)
                queryset = queryset.filter(
                    expiry_date__isnull=False,
                    expiry_date__lte=expire_date
                )
            except ValueError:
                pass
        
        available_only = self.request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(quantity_available__gt=0)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create product with producer from current user."""
        if hasattr(self.request.user, 'producer_profile'):
            serializer.save(producer=self.request.user.producer_profile)
        else:
            return Response(
                {'error': 'Only producers can create products.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def perform_update(self, serializer):
        """Update product - only producer owner can update."""
        if (hasattr(self.request.user, 'producer_profile') and 
            self.get_object().producer == self.request.user.producer_profile):
            serializer.save()
        else:
            return Response(
                {'error': 'You can only update your own products.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def perform_destroy(self, instance):
        """Delete product - only producer owner can delete."""
        if (hasattr(self.request.user, 'producer_profile') and 
            instance.producer == self.request.user.producer_profile):
            instance.delete()
        else:
            return Response(
                {'error': 'You can only delete your own products.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @extend_schema(
        tags=['Products'],
        summary="Mes produits",
        description="Récupère tous les produits du producteur connecté",
        responses={200: ProductSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_products(self, request):
        """Get products of the current producer."""
        if not hasattr(request.user, 'producer_profile'):
            return Response(
                {'error': 'Only producers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        products = Product.objects.filter(producer=request.user.producer_profile)
        page = self.paginate_queryset(products)
        
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Products'],
        summary="Produits en vedette",
        description="Récupère les produits mis en avant (bio, locaux, ou qui expirent bientôt)",
        responses={200: ProductSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products (organic, local, or expiring soon)."""
        featured_products = self.get_queryset().filter(
            models.Q(is_organic=True) | 
            models.Q(is_local=True) |
            models.Q(expiry_date__lte=timezone.now().date() + timedelta(days=3))
        )[:10]
        
        serializer = ProductListSerializer(featured_products, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Products'],
        summary="Produits par région",
        description="Récupère les statistiques de produits groupés par région de producteur",
        responses={200: OpenApiExample("Statistiques par région", value=[{"producer__region": "Île-de-France", "product_count": 10}])}
    )
    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Get products grouped by producer region."""
        from django.db.models import Count
        
        regions = Product.objects.filter(is_active=True).values(
            'producer__region'
        ).annotate(
            product_count=Count('id')
        ).order_by('-product_count')
        
        return Response(regions)


@extend_schema_view(
    list=extend_schema(
        tags=['Products'],
        summary="Liste des images produits",
        description="Récupère toutes les images des produits du producteur connecté"
    ),
    retrieve=extend_schema(
        tags=['Products'],
        summary="Détail d'une image",
        description="Récupère une image spécifique"
    ),
    create=extend_schema(
        tags=['Products'],
        summary="Ajouter une image",
        description="Ajoute une image à un produit (stockée en base64 en BDD)",
        request=ProductImageSerializer
    ),
    update=extend_schema(
        tags=['Products'],
        summary="Modifier une image",
        description="Modifie une image existante"
    ),
    partial_update=extend_schema(
        tags=['Products'],
        summary="Modifier partiellement une image",
        description="Modifie partiellement une image existante"
    ),
    destroy=extend_schema(
        tags=['Products'],
        summary="Supprimer une image",
        description="Supprime une image produit"
    )
)
class ProductImageViewSet(viewsets.ModelViewSet):
    """ViewSet for product images (producer only)."""
    
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter images based on product ownership."""
        user = self.request.user
        
        if hasattr(user, 'producer_profile'):
            return ProductImage.objects.filter(
                product__producer=user.producer_profile
            )
        
        return ProductImage.objects.none()
    
    def perform_create(self, serializer):
        """Create image only if user owns the product."""
        product = serializer.validated_data['product']
        
        if (hasattr(self.request.user, 'producer_profile') and 
            product.producer == self.request.user.producer_profile):
            serializer.save()
        else:
            return Response(
                {'error': 'You can only add images to your own products.'},
                status=status.HTTP_403_FORBIDDEN
            )