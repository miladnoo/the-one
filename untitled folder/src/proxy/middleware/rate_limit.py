"""
Rate limiting middleware
"""

import time
from typing import Dict, Any, Callable

from aiohttp import web


# Simple in-memory rate limiter
class RateLimiter:
    """
    Simple in-memory rate limiter.
    """
    
    def __init__(self, requests_per_minute: int, burst: int):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests per minute
            burst: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.clients: Dict[str, Dict[str, Any]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a client is allowed to make a request.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if the client is allowed, False otherwise
        """
        now = time.time()
        
        # Initialize client data if not exists
        if client_id not in self.clients:
            self.clients[client_id] = {
                'last_request': now,
                'tokens': self.burst,
                'updated_at': now
            }
            return True
        
        # Get client data
        client = self.clients[client_id]
        
        # Calculate token refill
        time_passed = now - client['updated_at']
        token_refill = time_passed * (self.requests_per_minute / 60.0)
        
        # Update tokens
        client['tokens'] = min(self.burst, client['tokens'] + token_refill)
        client['updated_at'] = now
        
        # Check if client has enough tokens
        if client['tokens'] >= 1.0:
            client['tokens'] -= 1.0
            client['last_request'] = now
            return True
        else:
            return False


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter(config: Dict[str, Any]) -> RateLimiter:
    """
    Get the rate limiter instance.
    
    Args:
        config: Server configuration
        
    Returns:
        The rate limiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        rate_limit_config = config.get('security', {}).get('rate_limiting', {})
        requests_per_minute = rate_limit_config.get('requests_per_minute', 60)
        burst = rate_limit_config.get('burst', 10)
        _rate_limiter = RateLimiter(requests_per_minute, burst)
    
    return _rate_limiter


async def rate_limit_middleware(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    Middleware for rate limiting requests.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    # Skip rate limiting for certain paths
    skip_paths = ['/metrics', '/health']
    if request.path in skip_paths:
        return await handler(request)
    
    # Get client identifier (IP address)
    client_id = request.remote
    
    # Check if client is allowed
    rate_limiter = get_rate_limiter(config)
    if rate_limiter.is_allowed(client_id):
        return await handler(request)
    else:
        return web.Response(
            status=429,
            text="Too Many Requests"
        )
