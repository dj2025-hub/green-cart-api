"""
API views for the accounts app.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes

from .models import User, Producer
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserListSerializer,
    ChangePasswordSerializer,
    UserStatsSerializer,
    ProducerSerializer
)


@extend_schema_view(
    list=extend_schema(
        tags=['Authentication'],
        summary="Liste des utilisateurs",
        description="Récupère la liste paginée de tous les utilisateurs avec filtres et recherche",
        parameters=[
            OpenApiParameter('user_type', OpenApiTypes.STR, description='Filtrer par type d\'utilisateur (CONSUMER/PRODUCER)'),
            OpenApiParameter('is_verified', OpenApiTypes.BOOL, description='Filtrer par statut de vérification'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par email, nom, prénom'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Authentication'],
        summary="Détail d'un utilisateur",
        description="Récupère les détails d'un utilisateur spécifique"
    ),
    create=extend_schema(
        tags=['Authentication'],
        summary="Créer un utilisateur",
        description="Crée un nouvel utilisateur (admin uniquement)"
    ),
    update=extend_schema(
        tags=['Authentication'],
        summary="Modifier un utilisateur",
        description="Modifie complètement un utilisateur existant"
    ),
    partial_update=extend_schema(
        tags=['Authentication'],
        summary="Modifier partiellement un utilisateur",
        description="Modifie partiellement un utilisateur existant"
    ),
    destroy=extend_schema(
        tags=['Authentication'],
        summary="Supprimer un utilisateur",
        description="Supprime un utilisateur (admin uniquement)"
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_verified', 'is_active', 'is_staff', 'user_type']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_login', 'email']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return UserProfileSerializer
        return UserProfileSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return User.objects.all()
        else:
            # Regular users can only see active users
            return User.objects.filter(is_active=True)

    def get_object(self):
        """Allow users to access their own profile with 'me' parameter."""
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()

    @extend_schema(
        tags=['Authentication'],
        summary="Mon profil utilisateur",
        description="Récupère ou modifie le profil de l'utilisateur connecté",
        methods=['GET', 'PUT', 'PATCH'],
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's profile."""
        user = request.user

        if request.method == 'GET':
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserProfileSerializer(
                user,
                data=request.data,
                partial=partial
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        tags=['Authentication'],
        summary="Changer mot de passe",
        description="Change le mot de passe de l'utilisateur connecté",
        request=ChangePasswordSerializer,
        responses={
            200: {"description": "Mot de passe changé avec succès"},
            400: {"description": "Erreurs de validation"}
        }
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully.'
            })
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        tags=['Authentication'],
        summary="Vérifier un utilisateur",
        description="Marque un utilisateur comme vérifié (admin uniquement)",
        responses={
            200: {"description": "Utilisateur vérifié avec succès"},
            403: {"description": "Permission refusée"}
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def verify(self, request, pk=None):
        """Verify a user (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()
        user.is_verified = True
        user.save()

        return Response({
            'message': f'User {user.email} has been verified.'
        })

    @extend_schema(
        tags=['Authentication'],
        summary="Statistiques utilisateurs",
        description="Récupère les statistiques générales des utilisateurs (admin uniquement)",
        responses={
            200: UserStatsSerializer,
            403: {"description": "Permission refusée"}
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """Get user statistics (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Calculate stats
        total_users = User.objects.count()
        verified_users = User.objects.filter(is_verified=True).count()
        active_users = User.objects.filter(is_active=True).count()

        # Users created this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = User.objects.filter(
            date_joined__gte=start_of_month
        ).count()

        stats_data = {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'new_users_this_month': new_users_this_month
        }

        serializer = UserStatsSerializer(stats_data)
        return Response(serializer.data)


@extend_schema(
    tags=['Authentication'],
    summary="Inscription utilisateur",
    description="Crée un nouveau compte utilisateur (consommateur ou producteur)",
    request=UserRegistrationSerializer,
    responses={
        201: {
            "description": "Inscription réussie",
            "examples": {
                "application/json": {
                    "message": "User created successfully.",
                    "user": {"email": "user@example.com", "first_name": "John"},
                    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
                }
            }
        },
        400: {"description": "Erreurs de validation"}
    },
    examples=[
        OpenApiExample(
            "Inscription consommateur",
            value={
                "email": "consumer@example.com",
                "password": "motdepasse123",
                "password_confirm": "motdepasse123",
                "first_name": "Marie",
                "last_name": "Dupont",
                "user_type": "CONSUMER",
                "phone_number": "+237677123456"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user."""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Create token for the new user
        token, created = Token.objects.get_or_create(user=user)

        # Return user data with token
        user_serializer = UserProfileSerializer(user)

        return Response({
            'message': 'User created successfully.',
            'user': user_serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    tags=['Authentication'],
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur et retourne son token d'API",
    request=UserLoginSerializer,
    responses={
        200: {
            "description": "Connexion réussie",
            "examples": {
                "application/json": {
                    "message": "Login successful.",
                    "user": {"email": "user@example.com", "first_name": "John"},
                    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
                }
            }
        },
        400: {"description": "Email ou mot de passe incorrect"}
    },
    examples=[
        OpenApiExample(
            "Connexion",
            value={
                "email": "consumer@test.com",
                "password": "testpass123"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user and return token."""
    serializer = UserLoginSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        # Login user (for session-based auth if needed)
        login(request, user)

        # Return user data with token
        user_serializer = UserProfileSerializer(user)

        return Response({
            'message': 'Login successful.',
            'user': user_serializer.data,
            'token': token.key
        })

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    tags=['Authentication'],
    summary="Déconnexion utilisateur",
    description="Déconnecte l'utilisateur en supprimant son token",
    request=None,
    responses={200: {"description": "Déconnexion réussie"}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user by deleting token."""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful.'
        })
    except Token.DoesNotExist:
        return Response({
            'message': 'User was not logged in.'
        })


@extend_schema(
    tags=['Authentication'],
    summary="Informations API Auth",
    description="Récupère les informations générales sur l'API d'authentification",
    responses={200: {"description": "Informations API avec endpoints disponibles"}}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint."""
    return Response({
        'message': 'Django Boilerplate API',
        'version': '1.0.0',
        'endpoints': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'profile': '/api/auth/users/me/',
            'users': '/api/auth/users/',
            'change_password': '/api/auth/users/change_password/',
        },
        'authentication': 'Token-based authentication',
        'documentation': 'Available at /api/docs/ (if configured)'
    })


@extend_schema(
    tags=['Authentication'],
    summary="Profil utilisateur",
    description="Récupère le profil de l'utilisateur connecté",
    responses={200: UserProfileSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user's profile."""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Producers'],
        summary="Liste des producteurs",
        description="Récupère la liste paginée des producteurs avec filtres et recherche",
        parameters=[
            OpenApiParameter('region', OpenApiTypes.STR, description='Filtrer par région'),
            OpenApiParameter('city', OpenApiTypes.STR, description='Filtrer par ville'),
            OpenApiParameter('is_verified', OpenApiTypes.BOOL, description='Filtrer par statut de vérification'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par nom d\'entreprise, région, ville'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Producers'],
        summary="Détail d'un producteur",
        description="Récupère les détails complets d'un producteur spécifique"
    ),
    create=extend_schema(
        tags=['Producers'],
        summary="Créer un profil producteur",
        description="Crée un nouveau profil producteur pour l'utilisateur connecté"
    ),
    update=extend_schema(
        tags=['Producers'],
        summary="Modifier un profil producteur",
        description="Modifie complètement le profil producteur"
    ),
    partial_update=extend_schema(
        tags=['Producers'],
        summary="Modifier partiellement un profil producteur",
        description="Modifie partiellement le profil producteur"
    ),
    destroy=extend_schema(
        tags=['Producers'],
        summary="Supprimer un profil producteur",
        description="Supprime le profil producteur (admin uniquement)"
    )
)
class ProducerViewSet(viewsets.ModelViewSet):
    """ViewSet for producer management."""
    
    queryset = Producer.objects.all()
    serializer_class = ProducerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region', 'city', 'is_verified']
    search_fields = ['business_name', 'user__first_name', 'user__last_name', 'region', 'city']
    ordering_fields = ['created_at', 'business_name', 'region']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Producer.objects.all()
        else:
            # Regular users can only see verified producers
            return Producer.objects.filter(is_verified=True)
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]