"""
Main API URL configuration.
"""
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
import django


@extend_schema(
    summary="API Root",
    description="Get API information and available endpoints",
    responses={
        200: OpenApiResponse(
            description="API information",
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'version': {'type': 'string'},
                    'description': {'type': 'string'},
                    'django_version': {'type': 'string'},
                    'debug_mode': {'type': 'boolean'},
                    'available_endpoints': {'type': 'object'},
                    'authentication': {'type': 'object'},
                    'status': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints."""
    return Response({
        'message': 'Welcome to GreenCart API! 🌱',
        'version': '1.0.0',
        'description': 'API REST pour une plateforme de circuit court',
        'django_version': django.get_version(),
        'debug_mode': settings.DEBUG,
        'available_endpoints': {
            'authentication': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'profile': '/api/auth/profile/',
                'users': '/api/auth/users/',
                'producers': '/api/auth/producers/',
            },
            'products': {
                'categories': '/api/products/categories/',
                'products': '/api/products/products/',
                'my_products': '/api/products/products/my_products/',
                'featured': '/api/products/products/featured/',
                'by_region': '/api/products/products/by_region/',
            },
            'cart': {
                'current': '/api/cart/cart/current/',
                'add': '/api/cart/add/',
                'summary': '/api/cart/summary/',
                'clear': '/api/cart/cart/clear/',
            },
            'orders': {
                'my_orders': '/api/orders/my-orders/',
                'producer_orders': '/api/orders/producer-orders/',
                'create_from_cart': '/api/orders/create-from-cart/',
                'statistics': '/api/orders/statistics/',
            },
            'documentation': {
                'schema': '/api/schema/',
                'swagger_ui': '/api/docs/',
                'redoc': '/api/redoc/',
            }
        },
        'authentication': {
            'type': 'Token-based',
            'header_format': 'Authorization: Token your_token_here',
            'obtain_token': 'POST /api/auth/login/ with email and password'
        },
        'status': 'operational'
    })


app_name = 'api'

# CSRF-exempt wrapper for Swagger views
@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptSpectacularSwaggerView(SpectacularSwaggerView):
    """Swagger UI with CSRF exemption for production use."""
    pass


@method_decorator(csrf_exempt, name='dispatch') 
class CSRFExemptSpectacularRedocView(SpectacularRedocView):
    """ReDoc with CSRF exemption for production use."""
    pass


urlpatterns = [
    # API root
    path('', api_root, name='api_root'),

    # API Documentation with CSRF exemption
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', CSRFExemptSpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', CSRFExemptSpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),

    # GreenCart API endpoints
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('products/', include('products.urls', namespace='products')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),

    # Health check
    path('health/', api_root, name='health_check'),
]