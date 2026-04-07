"""
Core Middleware - Login and access control
"""

from django.shortcuts import redirect, reverse
from django.urls import resolve


class LoginCheckMiddleWare:
    """
    Middleware to check login status and redirect users based on role.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Get the module name (to identify which section the URL belongs to)
        modulename = view_func.__module__
        
        # Get the current path
        path = request.path_info.lstrip('/')
        
        # Paths that don't require authentication
        allowed_paths = [
            '',  # home page
            'doLogin/',
            'login/',
            'admin/',
            'accounts/password_reset/',
            'accounts/password_reset/done/',
            'accounts/reset/',
            'media/',
            'static/',
            'check_email_availability',
            # OTP login paths for first-time student login
            'student/first-login/',
            'student/send-otp/',
            'student/verify-otp/',
            'student/set-password/',
        ]
        
        # Check if path starts with any allowed path
        is_allowed = any(path.startswith(p) for p in allowed_paths if p)
        
        # Allow unauthenticated access to allowed paths
        if is_allowed or path == '':
            return None
        
        # Allow static and media files
        if path.startswith('static/') or path.startswith('media/'):
            return None
        
        # Allow Django admin
        if 'django.contrib.admin' in modulename:
            return None
        
        # Require authentication for all other paths
        user = request.user
        if not user.is_authenticated:
            return redirect('/')
        
        # Role-based access control
        if user.role == 'HOD':
            # HOD can access everything
            pass
        elif user.role in ['FACULTY', 'GUEST']:
            # Faculty can only access staff routes and common routes
            if 'hod_views' in modulename:
                return redirect('staff_home')
        elif user.role == 'STUDENT':
            # Students can only access student routes
            if 'hod_views' in modulename or 'staff_views' in modulename:
                return redirect('student_home')
        elif user.role == 'STAFF':
            # Non-teaching staff - limited access
            if 'hod_views' in modulename or 'student_views' in modulename:
                return redirect('/')
        
        return None
