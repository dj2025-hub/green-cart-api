"""
Custom middleware for GreenCart API.
"""
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class CSRFDebugMiddleware(MiddlewareMixin):
    """
    Debug middleware for CSRF issues in production.
    Only active when DEBUG=True or specific setting is enabled.
    """
    
    def process_request(self, request):
        if getattr(settings, 'CSRF_DEBUG_ENABLED', settings.DEBUG):
            logger.info(f"CSRF Debug - Path: {request.path}")
            logger.info(f"CSRF Debug - Method: {request.method}")
            logger.info(f"CSRF Debug - Headers: {dict(request.headers)}")
            logger.info(f"CSRF Debug - Origin: {request.META.get('HTTP_ORIGIN', 'None')}")
            logger.info(f"CSRF Debug - Referer: {request.META.get('HTTP_REFERER', 'None')}")
    
    def process_response(self, request, response):
        # Add CORS headers for Swagger/Admin access
        if request.path.startswith('/api/docs/') or request.path.startswith('/api/schema/') or request.path.startswith('/admin/'):
            response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Accept, Accept-Language, Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            
        return response


class SwaggerCSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to handle CSRF exemption for Swagger UI.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exempt Swagger paths from CSRF
        exempt_paths = [
            '/api/docs/',
            '/api/redoc/', 
            '/api/schema/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        return None