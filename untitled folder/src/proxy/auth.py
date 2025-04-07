"""
Authentication utilities
"""

import bcrypt
import logging
from typing import Dict, Any


def authenticate_user(config: Dict[str, Any], username: str, password: str) -> bool:
    """
    Authenticate a user.
    
    Args:
        config: Server configuration
        username: Username
        password: Password
        
    Returns:
        True if authentication is successful, False otherwise
    """
    # Get authentication configuration
    auth_config = config.get('security', {}).get('authentication', {})
    
    # Get users
    users = auth_config.get('users', [])
    
    # Find user
    user = next((u for u in users if u['username'] == username), None)
    if not user:
        return False
    
    # Check password
    try:
        password_hash = user['password_hash']
        
        # Check if the hash is a bcrypt hash
        if password_hash.startswith('$2'):
            # Verify bcrypt hash
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        else:
            # Plain text comparison (not recommended)
            logging.warning("Using plain text password comparison")
            return password_hash == password
    except Exception as e:
        logging.error(f"Error authenticating user: {e}")
        return False
