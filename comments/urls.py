from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, CommentReportViewSet

app_name = 'comments'

# Router pour les commentaires
comment_router = DefaultRouter()
comment_router.register(r'comments', CommentViewSet, basename='comment')

# Router pour les signalements
report_router = DefaultRouter()
report_router.register(r'reports', CommentReportViewSet, basename='commentreport')

urlpatterns = [
    # Routes des commentaires
    path('', include(comment_router.urls)),
    
    # Routes des signalements
    path('', include(report_router.urls)),
    
    # Routes personnalisées pour des actions spécifiques
    path('comments/product/<int:product_id>/', 
         CommentViewSet.as_view({'get': 'product_comments'}), 
         name='product-comments'),
    
    path('comments/my-comments/', 
         CommentViewSet.as_view({'get': 'my_comments'}), 
         name='my-comments'),
    
    path('comments/stats/', 
         CommentViewSet.as_view({'get': 'stats'}), 
         name='comment-stats'),
    
    path('comments/popular/', 
         CommentViewSet.as_view({'get': 'popular_comments'}), 
         name='popular-comments'),
]
