"""
URL configuration for the orders app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')

app_name = 'orders'

urlpatterns = [
    # Order management endpoints
    path('my-orders/', views.my_orders, name='my_orders'),
    path('producer-orders/', views.producer_orders, name='producer_orders'),
    path('create-from-cart/', views.create_order_from_cart, name='create_from_cart'),
    path('statistics/', views.order_statistics, name='statistics'),
    path('<uuid:order_id>/', views.order_detail, name='order_detail'),
    
    # ViewSet routes
    path('', include(router.urls)),
]