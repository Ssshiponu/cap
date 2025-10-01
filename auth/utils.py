import re
from django.contrib.auth.models import User

def validate_username(username):
    # Check type first
    if not isinstance(username, str):
        return False, "Username must be a string."
    
    # Check for empty/whitespace
    if not username or username.strip() == "":
        return False, "Username cannot be empty."
    
    # Check length
    if len(username) < 4 or len(username) > 30:
        return False, "Username must be between 4 and 30 characters."
    
    # Check format (letters, numbers, underscores only)
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    
    # Check if username is only numbers
    if username.isdigit():
        return False, "Username cannot be only numbers."
    
    # Check reserved names (case-insensitive)
    if username.lower() in ['admin', 'root', 'superuser']:
        return False, "This username is reserved."
    
    # Check if username already exists (efficient query)
    if User.objects.filter(username__iexact=username).exists():
        return False, "Username already taken."
    
    return True, "Username is valid."