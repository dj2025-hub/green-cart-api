"""
URL configuration for the accounts app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'producers', views.ProducerViewSet, basename='producer')

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.user_profile, name='profile'),

    # API info
    path('', views.api_info, name='api_info'),

    # ViewSet routes (users CRUD)
    path('', include(router.urls)),
]