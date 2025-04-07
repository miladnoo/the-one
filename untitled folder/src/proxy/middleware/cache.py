"""
Caching middleware
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Callable, Optional

from aiohttp import web


# Simple in-memory cache
class MemoryCache:
    """
    Simple in-memory cache.
    """
    
    def __init__(self, ttl: int, max_size: int):
        """
        Initialize the cache.
        
        Args:
            ttl: Time-to-live in seconds
            max_size: Maximum cache size in MB
        """
        self.ttl = ttl
        self.max_size = max_size * 1024 * 1024  # Convert to bytes
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.size = 0
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if entry is expired
        if time.time() > entry['expires']:
            self.delete(key)
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
            
        Returns:
            True if the value was cached, False otherwise
        """
        # Calculate entry size
        entry_size = len(json.dumps(value).encode('utf-8'))
        
        # Check if entry is too large
        if entry_size > self.max_size:
            logging.warning(f"Cache entry too large: {entry_size} bytes")
            return False
        
        # Remove old entry if exists
        if key in self.cache:
            self.delete(key)
        
        # Check if we need to make room
        if self.size + entry_size > self.max_size:
            self._evict(entry_size)
        
        # Add entry
        self.cache[key] = {
            'value': value,
            'expires': time.time() + (ttl or self.ttl),
            'size': entry_size
        }
        self.size += entry_size
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the value was deleted, False otherwise
        """
        if key not in self.cache:
            return False
        
        # Update size
        self.size -= self.cache[key]['size']
        
        # Remove entry
        del self.cache[key]
        
        return True
    
    def _evict(self, needed_space: int):
        """
        Evict entries to make room for a new entry.
        
        Args:
            needed_space: Space needed in bytes
        """
        # Sort entries by expiration time
        entries = sorted(
            [(k, v['expires']) for k, v in self.cache.items()],
            key=lambda x: x[1]
        )
        
        # Evict entries until we have enough space
        for key, _ in entries:
            if self.size + needed_space <= self.max_size:
                break
            
            self.delete(key)


# Global cache instance
_cache = None


def get_cache(config: Dict[str, Any]) -> MemoryCache:
    """
    Get the cache instance.
    
    Args:
        config: Server configuration
        
    Returns:
        The cache instance
    """
    global _cache
    
    if _cache is None:
        cache_config = config.get('caching', {})
        ttl = cache_config.get('ttl', 300)
        max_size = cache_config.get('max_size', 100)
        _cache = MemoryCache(ttl, max_size)
    
    return _cache


def _get_cache_key(request: web.Request) -> str:
    """
    Generate a cache key for a request.
    
    Args:
        request: The request
        
    Returns:
        The cache key
    """
    # Create a string representation of the request
    key_parts = [
        request.method,
        str(request.url),
        request.headers.get('Accept', ''),
        request.headers.get('Accept-Encoding', '')
    ]
    
    # Add query parameters
    for k, v in request.query.items():
        key_parts.append(f"{k}={v}")
    
    # Generate a hash
    key = hashlib.md5(''.join(key_parts).encode('utf-8')).hexdigest()
    
    return key


async def cache_middleware(request: web.Request, handler: Callable, config: Dict[str, Any]) -> web.Response:
    """
    Middleware for caching responses.
    
    Args:
        request: The incoming request
        handler: The request handler
        config: Server configuration
        
    Returns:
        The response
    """
    # Only cache GET requests
    if request.method != 'GET':
        return await handler(request)
    
    # Skip caching for certain paths
    skip_paths = ['/metrics', '/health']
    if request.path in skip_paths:
        return await handler(request)
    
    # Generate cache key
    cache_key = _get_cache_key(request)
    
    # Try to get from cache
    cache = get_cache(config)
    cached = cache.get(cache_key)
    
    if cached:
        # Return cached response
        return web.Response(
            status=cached['status'],
            headers=cached['headers'],
            body=cached['body']
        )
    
    # Process request
    response = await handler(request)
    
    # Cache response if cacheable
    if 200 <= response.status < 300:
        # Read response body
        body = await response.read()
        
        # Cache response
        cache.set(cache_key, {
            'status': response.status,
            'headers': dict(response.headers),
            'body': body
        })
        
        # Create a new response with the same body
        return web.Response(
            status=response.status,
            headers=response.headers,
            body=body
        )
    
    return response
