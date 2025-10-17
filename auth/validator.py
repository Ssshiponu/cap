import re

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates an email address format.
    Returns (True, "Valid email") if valid, (False, error_message) otherwise.
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, "Valid email"
    else:
        return False, "Invalid email format"

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validates a password strength.
    Returns (True, "Valid password") if valid, (False, error_message) otherwise.
    """
    errors = []
    
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Valid password"
