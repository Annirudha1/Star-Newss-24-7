from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for social account handling"""
    
    def pre_social_login(self, request, sociallogin):
        """Called after user successfully authenticates with social provider"""
        pass
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow automatic signup for all users"""
        return True
    
    def get_login_redirect_url(self, request):
        """Redirect to homepage after successful login"""
        return '/'
