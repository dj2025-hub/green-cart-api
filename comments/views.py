from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiResponse

from .models import Comment, CommentReport
from .serializers import (
    CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer,
    CommentListSerializer, CommentReportSerializer, CommentStatsSerializer
)
from products.models import Product


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion complète des commentaires.
    
    Permet de créer, lire, mettre à jour et supprimer des commentaires
    avec gestion automatique du rating des produits.
    """
    
    queryset = Comment.objects.select_related('user', 'product').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'user', 'rating']
    search_fields = ['comment', 'user__email', 'product__name']
    ordering_fields = ['created_at', 'rating', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retourner le bon sérialiseur selon l'action."""
        if self.action == 'create':
            return CommentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CommentUpdateSerializer
        elif self.action == 'list':
            return CommentListSerializer
        return CommentSerializer
    
    def get_queryset(self):
        """Filtrer les commentaires selon le contexte."""
        queryset = super().get_queryset()
        
        # Filtrer par produit si spécifié
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filtrer par utilisateur si spécifié
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrer par note minimale
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        
        # Filtrer par note maximale
        max_rating = self.request.query_params.get('max_rating')
        if max_rating:
            try:
                queryset = queryset.filter(rating__lte=float(max_rating))
            except ValueError:
                pass
        
        return queryset
    
    @extend_schema(
        summary="Lister tous les commentaires",
        description="Récupérer la liste de tous les commentaires avec filtres et pagination",
        parameters=[
            OpenApiParameter(
                name='product_id',
                type=int,
                description='Filtrer par ID du produit'
            ),
            OpenApiParameter(
                name='user_id',
                type=int,
                description='Filtrer par ID de l\'utilisateur'
            ),
            OpenApiParameter(
                name='min_rating',
                type=float,
                description='Note minimale (0.0 à 5.0)'
            ),
            OpenApiParameter(
                name='max_rating',
                type=float,
                description='Note maximale (0.0 à 5.0)'
            ),
            OpenApiParameter(
                name='search',
                type=str,
                description='Rechercher dans le texte des commentaires'
            ),
            OpenApiParameter(
                name='ordering',
                type=str,
                description='Trier par: created_at, rating, updated_at (préfixer par - pour ordre décroissant)'
            ),
        ],
        responses={
            200: CommentListSerializer(many=True),
            400: OpenApiResponse(description="Paramètres de requête invalides")
        }
    )
    def list(self, request, *args, **kwargs):
        """Lister tous les commentaires avec filtres."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Récupérer un commentaire",
        description="Récupérer les détails d'un commentaire spécifique",
        responses={
            200: CommentSerializer,
            404: OpenApiResponse(description="Commentaire non trouvé")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Récupérer un commentaire spécifique."""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Créer un commentaire",
        description="Créer un nouveau commentaire sur un produit",
        request=CommentCreateSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description="Données invalides"),
            401: OpenApiResponse(description="Authentification requise")
        },
        examples=[
            OpenApiExample(
                'Exemple de commentaire',
                value={
                    'product': 1,
                    'comment': 'Excellent produit, très frais et de bonne qualité !',
                    'rating': 4.5
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        """Créer un nouveau commentaire."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier que l'utilisateur n'a pas déjà commenté ce produit
        product_id = serializer.validated_data['product'].id
        if Comment.objects.filter(product_id=product_id, user=request.user).exists():
            return Response(
                {'error': 'Vous avez déjà commenté ce produit.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = serializer.save()
        
        # Retourner le commentaire complet
        full_serializer = CommentSerializer(comment, context={'request': request})
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Mettre à jour un commentaire",
        description="Modifier un commentaire existant (seulement ses propres commentaires)",
        request=CommentUpdateSerializer,
        responses={
            200: CommentSerializer,
            400: OpenApiResponse(description="Données invalides"),
            403: OpenApiResponse(description="Permission refusée"),
            404: OpenApiResponse(description="Commentaire non trouvé")
        }
    )
    def update(self, request, *args, **kwargs):
        """Mettre à jour un commentaire."""
        comment = self.get_object()
        
        # Vérifier les permissions
        if request.user != comment.user and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres commentaires.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        
        # Retourner le commentaire complet
        full_serializer = CommentSerializer(comment, context={'request': request})
        return Response(full_serializer.data)
    
    @extend_schema(
        summary="Supprimer un commentaire",
        description="Supprimer un commentaire (seulement ses propres commentaires ou admin)",
        responses={
            204: OpenApiResponse(description="Commentaire supprimé"),
            403: OpenApiResponse(description="Permission refusée"),
            404: OpenApiResponse(description="Commentaire non trouvé")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Supprimer un commentaire."""
        comment = self.get_object()
        
        # Vérifier les permissions
        if request.user != comment.user and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez supprimer que vos propres commentaires.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="Commentaires d'un produit",
        description="Récupérer tous les commentaires d'un produit spécifique",
        parameters=[
            OpenApiParameter(
                name='product_id',
                type=int,
                required=True,
                description='ID du produit'
            ),
        ],
        responses={
            200: CommentListSerializer(many=True),
            404: OpenApiResponse(description="Produit non trouvé")
        }
    )
    @action(detail=False, methods=['get'], url_path='product/(?P<product_id>[^/.]+)')
    def product_comments(self, request, product_id=None):
        """Récupérer tous les commentaires d'un produit."""
        product = get_object_or_404(Product, id=product_id)
        comments = Comment.objects.filter(product=product).select_related('user')
        
        serializer = CommentListSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mes commentaires",
        description="Récupérer tous les commentaires de l'utilisateur connecté",
        responses={
            200: CommentListSerializer(many=True),
            401: OpenApiResponse(description="Authentification requise")
        }
    )
    @action(detail=False, methods=['get'], url_path='my-comments')
    def my_comments(self, request):
        """Récupérer les commentaires de l'utilisateur connecté."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        comments = Comment.objects.filter(user=request.user).select_related('product')
        serializer = CommentListSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Statistiques des commentaires",
        description="Récupérer les statistiques des commentaires (total, moyenne, distribution)",
        responses={
            200: CommentStatsSerializer,
            400: OpenApiResponse(description="Paramètres invalides")
        }
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Récupérer les statistiques des commentaires."""
        # Paramètres de filtrage
        product_id = request.query_params.get('product_id')
        user_id = request.query_params.get('user_id')
        
        queryset = Comment.objects.all()
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Calculs
        total_comments = queryset.count()
        average_rating = queryset.aggregate(avg=Avg('rating'))['avg'] or 0.0
        
        # Distribution des notes
        rating_distribution = {}
        for rating in range(6):  # 0.0 à 5.0
            count = queryset.filter(rating=rating).count()
            if count > 0:
                rating_distribution[str(rating)] = count
        
        # Commentaires récents
        recent_comments = queryset.order_by('-created_at')[:5]
        recent_serializer = CommentListSerializer(recent_comments, many=True, context={'request': request})
        
        stats_data = {
            'total_comments': total_comments,
            'average_rating': round(average_rating, 1),
            'rating_distribution': rating_distribution,
            'recent_comments': recent_serializer.data
        }
        
        serializer = CommentStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Commentaires populaires",
        description="Récupérer les commentaires les plus populaires (par note et nombre de réponses)",
        responses={
            200: CommentListSerializer(many=True),
            400: OpenApiResponse(description="Paramètres invalides")
        }
    )
    @action(detail=False, methods=['get'], url_path='popular')
    def popular_comments(self, request):
        """Récupérer les commentaires les plus populaires."""
        limit = min(int(request.query_params.get('limit', 10)), 50)  # Max 50
        
        # Commentaires avec les meilleures notes
        popular_comments = Comment.objects.filter(
            rating__gte=4.0
        ).select_related('user', 'product').order_by('-rating', '-created_at')[:limit]
        
        serializer = CommentListSerializer(popular_comments, many=True, context={'request': request})
        return Response(serializer.data)


class CommentReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des signalements de commentaires.
    """
    
    queryset = CommentReport.objects.select_related('comment', 'reporter').all()
    serializer_class = CommentReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['comment', 'reporter', 'reason', 'is_resolved']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les signalements selon les permissions."""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leurs propres signalements
        if not self.request.user.is_staff:
            queryset = queryset.filter(reporter=self.request.user)
        
        return queryset
    
    @extend_schema(
        summary="Créer un signalement",
        description="Signaler un commentaire inapproprié",
        request=CommentReportSerializer,
        responses={
            201: CommentReportSerializer,
            400: OpenApiResponse(description="Données invalides"),
            401: OpenApiResponse(description="Authentification requise")
        }
    )
    def create(self, request, *args, **kwargs):
        """Créer un signalement de commentaire."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier que l'utilisateur n'a pas déjà signalé ce commentaire
        comment_id = serializer.validated_data['comment'].id
        if CommentReport.objects.filter(comment_id=comment_id, reporter=request.user).exists():
            return Response(
                {'error': 'Vous avez déjà signalé ce commentaire.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Marquer comme résolu",
        description="Marquer un signalement comme résolu (admin seulement)",
        responses={
            200: CommentReportSerializer,
            403: OpenApiResponse(description="Permission refusée"),
            404: OpenApiResponse(description="Signalement non trouvé")
        }
    )
    @action(detail=True, methods=['patch'], url_path='resolve')
    def resolve_report(self, request, pk=None):
        """Marquer un signalement comme résolu."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission refusée. Admin seulement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = self.get_object()
        report.is_resolved = True
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
