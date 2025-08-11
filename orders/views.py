"""
API views for orders management in GreenCart.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes, OpenApiResponse

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    CreateOrderSerializer,
    UpdateOrderStatusSerializer,
    CancelOrderSerializer,
    OrderStatusHistorySerializer
)


@extend_schema_view(
    list=extend_schema(
        tags=['Orders'],
        summary="Liste des commandes",
        description="Récupère la liste des commandes selon les permissions utilisateur",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrer par statut de commande'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Recherche par numéro de commande, email client'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Orders'],
        summary="Détail d'une commande",
        description="Récupère les détails complets d'une commande spécifique"
    ),
    create=extend_schema(
        tags=['Orders'],
        summary="Créer une commande",
        description="Crée une nouvelle commande à partir du panier"
    ),
    update=extend_schema(
        tags=['Orders'],
        summary="Modifier une commande",
        description="Modifie complètement une commande existante"
    ),
    partial_update=extend_schema(
        tags=['Orders'],
        summary="Modifier partiellement une commande",
        description="Modifie partiellement une commande existante"
    ),
    destroy=extend_schema(
        tags=['Orders'],
        summary="Supprimer une commande",
        description="Supprime une commande (admin uniquement)"
    )
)
class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for orders management."""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'consumer', 'order_date']
    search_fields = ['order_number', 'consumer__email', 'consumer__first_name', 'consumer__last_name']
    ordering_fields = ['order_date', 'total_amount', 'status']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """Filter queryset based on user type."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            # Staff can see all orders
            return Order.objects.all()
        elif hasattr(user, 'producer_profile'):
            # Producers can see orders containing their products
            return Order.objects.filter(
                items__producer=user.producer_profile
            ).distinct()
        else:
            # Consumers can only see their own orders
            return Order.objects.filter(consumer=user)
    
    def perform_create(self, serializer):
        """Create order from user's cart."""
        # The CreateOrderSerializer handles the order creation logic
        serializer.save()
    
    @extend_schema(
        tags=['Orders'],
        summary="Annuler une commande",
        description="Annule une commande (consommateur uniquement)",
        request=CancelOrderSerializer,
        responses={
            200: {"description": "Commande annulée avec succès"},
            403: {"description": "Permission refusée"},
            400: {"description": "Erreurs de validation"}
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order (consumer only)."""
        order = self.get_object()
        
        # Only the consumer can cancel their order
        if order.consumer != request.user:
            return Response(
                {'error': 'You can only cancel your own orders.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CancelOrderSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        
        if serializer.is_valid():
            cancelled_order = serializer.save()
            order_serializer = OrderSerializer(cancelled_order)
            return Response({
                'message': 'Order cancelled successfully.',
                'order': order_serializer.data
            })
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        tags=['Orders'],
        summary="Mettre à jour le statut",
        description="Met à jour le statut d'une commande (producteurs uniquement)",
        request=UpdateOrderStatusSerializer,
        responses={
            200: {"description": "Statut mis à jour avec succès"},
            403: {"description": "Permission refusée"},
            400: {"description": "Erreurs de validation"}
        }
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status (producers only)."""
        order = self.get_object()
        
        # Only producers involved in the order can update status
        if not hasattr(request.user, 'producer_profile'):
            return Response(
                {'error': 'Only producers can update order status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        producer = request.user.producer_profile
        if not order.items.filter(producer=producer).exists():
            return Response(
                {'error': 'You can only update status for orders containing your products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateOrderStatusSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        
        if serializer.is_valid():
            updated_order = serializer.save()
            order_serializer = OrderSerializer(updated_order)
            return Response({
                'message': 'Order status updated successfully.',
                'order': order_serializer.data
            })
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=['Orders'],
    summary="Mes commandes",
    description="Récupère toutes les commandes de l'utilisateur connecté (consommateur ou producteur)",
    responses={200: OrderListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_orders(request):
    """Get current user's orders."""
    user = request.user
    
    if hasattr(user, 'producer_profile'):
        # Producer - get orders containing their products
        orders = Order.objects.filter(
            items__producer=user.producer_profile
        ).distinct().order_by('-order_date')
    else:
        # Consumer - get their own orders
        orders = Order.objects.filter(consumer=user).order_by('-order_date')
    
    serializer = OrderListSerializer(orders, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get producer orders",
    description="Get orders containing products from the current producer",
    parameters=[
        OpenApiParameter(
            name='status',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Filter orders by status'
        )
    ],
    responses={
        200: OrderListSerializer(many=True),
        403: OpenApiResponse(description="Only producers can access this endpoint")
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def producer_orders(request):
    """Get orders for current producer."""
    if not hasattr(request.user, 'producer_profile'):
        return Response(
            {'error': 'Only producers can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    producer = request.user.producer_profile
    orders = Order.objects.filter(
        items__producer=producer
    ).distinct().order_by('-order_date')
    
    # Add filtering options
    status_filter = request.query_params.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    serializer = OrderListSerializer(orders, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get order details",
    description="Get detailed information about a specific order. Consumers can see their own orders, producers can see orders containing their products, staff can see all orders.",
    responses={
        200: OrderSerializer,
        404: OpenApiResponse(description="Order not found"),
        403: OpenApiResponse(description="Permission denied")
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_detail(request, order_id):
    """Get order details."""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions
    user = request.user
    if user.is_staff or user.is_superuser:
        # Staff can see all orders
        pass
    elif order.consumer == user:
        # Consumer can see their own order
        pass
    elif (hasattr(user, 'producer_profile') and 
          order.items.filter(producer=user.producer_profile).exists()):
        # Producer can see orders containing their products
        pass
    else:
        return Response(
            {'error': 'Permission denied.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@extend_schema(
    tags=['Orders'],
    summary="Créer commande depuis panier",
    description="Crée une nouvelle commande à partir des articles dans le panier de l'utilisateur",
    request=CreateOrderSerializer,
    responses={
        201: {"description": "Commande créée avec succès"},
        400: {"description": "Erreurs de validation ou panier vide"}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order_from_cart(request):
    """Create order from user's cart."""
    serializer = CreateOrderSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        order = serializer.save()
        order_serializer = OrderSerializer(order)
        return Response({
            'message': 'Order created successfully.',
            'order': order_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    tags=['Orders'],
    summary="Statistiques des commandes",
    description="Récupère les statistiques des commandes pour l'utilisateur connecté",
    responses={
        200: {
            "description": "Statistiques des commandes",
            "examples": {
                "application/json": {
                    "total_orders": 25,
                    "pending_orders": 3,
                    "confirmed_orders": 5,
                    "shipped_orders": 2,
                    "delivered_orders": 14,
                    "cancelled_orders": 1,
                    "total_revenue": "1250.50"
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_statistics(request):
    """Get order statistics."""
    user = request.user
    
    if hasattr(user, 'producer_profile'):
        # Producer statistics
        producer = user.producer_profile
        orders = Order.objects.filter(items__producer=producer).distinct()
        
        stats = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='PENDING').count(),
            'confirmed_orders': orders.filter(status='CONFIRMED').count(),
            'shipped_orders': orders.filter(status='SHIPPED').count(),
            'delivered_orders': orders.filter(status='DELIVERED').count(),
            'cancelled_orders': orders.filter(status='CANCELLED').count(),
            'total_revenue': sum(
                item.total_price for item in OrderItem.objects.filter(
                    producer=producer,
                    order__status='DELIVERED'
                )
            )
        }
    else:
        # Consumer statistics
        orders = Order.objects.filter(consumer=user)
        
        stats = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='PENDING').count(),
            'confirmed_orders': orders.filter(status='CONFIRMED').count(),
            'shipped_orders': orders.filter(status='SHIPPED').count(),
            'delivered_orders': orders.filter(status='DELIVERED').count(),
            'cancelled_orders': orders.filter(status='CANCELLED').count(),
            'total_spent': sum(
                order.total_amount for order in orders.filter(status='DELIVERED')
            )
        }
    
    return Response(stats)