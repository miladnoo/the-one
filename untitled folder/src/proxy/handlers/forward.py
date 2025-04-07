"""
Forward proxy handler implementation
"""

import base64
import logging
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from aiohttp import web

from .base import BaseProxyHandler
from ..auth import authenticate_user


class ForwardProxyHandler(BaseProxyHandler):
    """
    Handler for forward proxy requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the forward proxy handler.
        
        Args:
            config: Server configuration
        """
        super().__init__(config)
        self.require_auth = config['proxy']['forward'].get('require_auth', False)
        self.allowed_domains = config['proxy']['forward'].get('allowed_domains', [])
        
        # Compile domain patterns for faster matching
        self.domain_patterns = []
        for domain in self.allowed_domains:
            pattern = domain.replace('.', r'\.').replace('*', r'.*')
            self.domain_patterns.append(re.compile(f"^{pattern}$"))
    
    def _is_domain_allowed(self, domain: str) -> bool:
        """
        Check if a domain is allowed.
        
        Args:
            domain: The domain to check
            
        Returns:
            True if the domain is allowed, False otherwise
        """
        if not self.allowed_domains:
            return True
        
        return any(pattern.match(domain) for pattern in self.domain_patterns)
    
    async def _authenticate(self, request: web.Request) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a user.
        
        Args:
            request: The incoming request
            
        Returns:
            A tuple of (success, error_message)
        """
        if not self.require_auth:
            return True, None
        
        auth_header = request.headers.get('Proxy-Authorization')
        if not auth_header:
            return False, "Proxy authentication required"
        
        try:
            auth_type, auth_value = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return False, "Only Basic authentication is supported"
            
            decoded = base64.b64decode(auth_value).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if authenticate_user(self.config, username, password):
                return True, None
            else:
                return False, "Invalid credentials"
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, "Authentication error"
    
    async def handle(self, request: web.Request) -> web.Response:
        """
        Handle a forward proxy request.
        
        Args:
            request: The incoming request
            
        Returns:
            The response to send back to the client
        """
        # Authenticate the user if required
        if self.require_auth:
            authenticated, error = await self._authenticate(request)
            if not authenticated:
                return web.Response(
                    status=407,
                    headers={'Proxy-Authenticate': 'Basic realm="Proxy"'},
                    text=error
                )
        
        # Get the target URL
        target_url = request.url.human_repr()
        
        # For CONNECT method (HTTPS), we need to establish a tunnel
        if request.method == 'CONNECT':
            return await self._handle_connect(request)
        
        # Check if the domain is allowed
        parsed_url = urlparse(target_url)
        if not self._is_domain_allowed(parsed_url.netloc):
            return web.Response(
                status=403,
                text=f"Access to domain {parsed_url.netloc} is not allowed"
            )
        
        # Forward the request
        return await self._forward_request(request, target_url)
    
    async def _handle_connect(self, request: web.Request) -> web.Response:
        """
        Handle a CONNECT request (for HTTPS).
        
        Args:
            request: The incoming CONNECT request
            
        Returns:
            The response to send back to the client
        """
        # This is a simplified implementation
        # A full implementation would establish a tunnel between the client and the target server
        
        host, port = request.path.split(':')
        
        # Check if the domain is allowed
        if not self._is_domain_allowed(host):
            return web.Response(
                status=403,
                text=f"Access to domain {host} is not allowed"
            )
        
        # In a real implementation, we would establish a tunnel here
        # For now, we'll just return a 200 OK response
        return web.Response(
            status=200,
            text="Connection established"
        )
