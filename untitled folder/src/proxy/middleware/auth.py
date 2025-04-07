"""
Authentication middleware
"""

import base64
import logging
from typing import Dict, Any, Callable

from aiohttp import web

from ..auth import authenticate_user


async def auth_middleware(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    Middleware for authenticating requests.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    # Skip authentication for certain paths
    skip_paths = ['/metrics', '/health']
    if request.path in skip_paths:
        return await handler(request)
    
    # Get authentication configuration
    auth_config = config.get('security', {}).get('authentication', {})
    method = auth_config.get('method', 'basic')
    
    # Authenticate based on the method
    if method == 'basic':
        return await _basic_auth(request, handler, config)
    elif method == 'jwt':
        return await _jwt_auth(request, handler, config)
    elif method == 'oauth':
        return await _oauth_auth(request, handler, config)
    else:
        logging.error(f"Unsupported authentication method: {method}")
        return web.Response(
            status=500,
            text="Internal Server Error: Unsupported authentication method"
        )


async def _basic_auth(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    Basic authentication.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return web.Response(
            status=401,
            headers={'WWW-Authenticate': 'Basic realm="Proxy"'},
            text="Authentication required"
        )
    
    try:
        auth_type, auth_value = auth_header.split(' ', 1)
        if auth_type.lower() != 'basic':
            return web.Response(
                status=401,
                headers={'WWW-Authenticate': 'Basic realm="Proxy"'},
                text="Only Basic authentication is supported"
            )
        
        decoded = base64.b64decode(auth_value).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        if authenticate_user(config, username, password):
            # Authentication successful
            return await handler(request)
        else:
            # Authentication failed
            return web.Response(
                status=401,
                headers={'WWW-Authenticate': 'Basic realm="Proxy"'},
                text="Invalid credentials"
            )
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        return web.Response(
            status=401,
            headers={'WWW-Authenticate': 'Basic realm="Proxy"'},
            text="Authentication error"
        )


async def _jwt_auth(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    JWT authentication.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    # JWT authentication is not implemented yet
    return web.Response(
        status=501,
        text="JWT authentication is not implemented yet"
    )


async def _oauth_auth(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    OAuth authentication.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    # OAuth authentication is not implemented yet
    return web.Response(
        status=501,
        text="OAuth authentication is not implemented yet"
    )
