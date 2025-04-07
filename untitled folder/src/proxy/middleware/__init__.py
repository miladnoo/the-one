"""
Middleware package for the proxy server
"""

from typing import Dict, Any, List, Callable

from aiohttp import web

from .error import error_middleware
from .auth import auth_middleware
from .rate_limit import rate_limit_middleware
from .logging import logging_middleware
from .cache import cache_middleware


def setup_middlewares(app: web.Application, config: Dict[str, Any]):
    """
    Set up middlewares for the application.
    
    Args:
        app: The web application
        config: Server configuration
    """
    # Add middlewares in the correct order
    middlewares = []
    
    # Add logging middleware
    middlewares.append(logging_middleware)
    
    # Add authentication middleware if enabled
    if config.get('security', {}).get('authentication', {}).get('enabled', False):
        middlewares.append(lambda request, handler: auth_middleware(request, handler, config))
    
    # Add rate limiting middleware if enabled
    if config.get('security', {}).get('rate_limiting', {}).get('enabled', False):
        middlewares.append(lambda request, handler: rate_limit_middleware(request, handler, config))
    
    # Add caching middleware if enabled
    if config.get('caching', {}).get('enabled', False):
        middlewares.append(lambda request, handler: cache_middleware(request, handler, config))
    
    # Apply middlewares
    for middleware in middlewares:
        app.middlewares.append(middleware)


__all__ = [
    'error_middleware',
    'auth_middleware',
    'rate_limit_middleware',
    'logging_middleware',
    'cache_middleware',
    'setup_middlewares'
]
