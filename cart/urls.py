"""
URL configuration for the cart app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart')

app_name = 'cart'

urlpatterns = [
    # Cart management endpoints
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('items/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('items/<uuid:item_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('products/<uuid:product_id>/add/', views.add_product_to_cart, name='add_product_to_cart'),
    path('summary/', views.cart_summary, name='cart_summary'),
    
    # ViewSet routes
    path('', include(router.urls)),
]