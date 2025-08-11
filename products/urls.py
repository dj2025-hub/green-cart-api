"""
URL configuration for the products app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'images', views.ProductImageViewSet, basename='productimage')

app_name = 'products'

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
]