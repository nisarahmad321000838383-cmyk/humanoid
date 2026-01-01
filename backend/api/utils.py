"""
Utility functions for admin permissions and checks.
"""
from django.contrib.auth.models import User
from .models import AccessToken

ADMIN_EMAIL = 'fiafghan@gmail.com'


def is_super_admin(user):
    """
    Check if the user is the super admin account.
    Only the account with email 'fiafghan@gmail.com' is considered super admin.
    """
    return user.is_authenticated and user.email == ADMIN_EMAIL


def assign_access_token_to_user(user):
    """
    Assign an available access token from the api_accesstoken table to a user.
    If user is admin, returns None (admins use env token).
    Releases any previously assigned token first.
    
    Args:
        user: The user to assign a token to
        
    Returns:
        AccessToken object if assigned, None if admin or no tokens available
    """
    # Admins use the env token, so don't assign from table
    if is_super_admin(user):
        return None
    
    # Release any token currently assigned to this user
    release_user_access_token(user)
    
    # Find an available active token (not assigned to anyone)
    available_token = AccessToken.objects.filter(
        is_active=True,
        current_user__isnull=True
    ).first()
    
    if available_token:
        available_token.current_user = user
        available_token.save()
        return available_token
    
    return None


def release_user_access_token(user):
    """
    Release any access token currently assigned to a user.
    
    Args:
        user: The user whose token should be released
    """
    if not user or not user.is_authenticated:
        return
    
    # Find and release any token assigned to this user
    assigned_tokens = AccessToken.objects.filter(current_user=user)
    for token in assigned_tokens:
        token.current_user = None
        token.save()


def get_user_access_token(user):
    """
    Get the access token assigned to a user, or None if admin/no token.
    
    Args:
        user: The user
        
    Returns:
        AccessToken object if assigned, None otherwise
    """
    if not user or not user.is_authenticated:
        return None
    
    # Admins use env token
    if is_super_admin(user):
        return None
    
    # Get token assigned to user
    return AccessToken.objects.filter(current_user=user, is_active=True).first()
