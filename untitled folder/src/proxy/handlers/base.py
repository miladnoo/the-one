"""
Base handler for proxy implementations
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import aiohttp
from aiohttp import web


class BaseProxyHandler(ABC):
    """
    Base class for all proxy handlers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the handler.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create a client session for making requests
        self.session = None
    
    async def setup_session(self):
        """Set up the aiohttp client session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close the aiohttp client session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @abstractmethod
    async def handle(self, request: web.Request) -> web.Response:
        """
        Handle a proxy request.
        
        Args:
            request: The incoming request
            
        Returns:
            The response to send back to the client
        """
        pass
    
    async def _forward_request(
        self, 
        request: web.Request, 
        target_url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> web.Response:
        """
        Forward a request to a target URL.
        
        Args:
            request: The incoming request
            target_url: The URL to forward the request to
            headers: Additional headers to include in the forwarded request
            
        Returns:
            The response from the target server
        """
        await self.setup_session()
        
        # Prepare headers
        request_headers = dict(request.headers)
        if headers:
            request_headers.update(headers)
        
        # Remove hop-by-hop headers
        hop_by_hop_headers = {
            'Connection', 'Keep-Alive', 'Proxy-Authenticate', 'Proxy-Authorization',
            'TE', 'Trailers', 'Transfer-Encoding', 'Upgrade'
        }
        for header in hop_by_hop_headers:
            if header in request_headers:
                del request_headers[header]
        
        # Get request body
        body = await request.read()
        
        try:
            # Forward the request
            async with self.session.request(
                request.method,
                target_url,
                headers=request_headers,
                data=body,
                allow_redirects=False,
                ssl=None  # We'll handle SSL verification separately
            ) as resp:
                # Read response body
                response_body = await resp.read()
                
                # Prepare response headers
                response_headers = dict(resp.headers)
                
                # Create response
                return web.Response(
                    status=resp.status,
                    headers=response_headers,
                    body=response_body
                )
        except aiohttp.ClientError as e:
            self.logger.error(f"Error forwarding request to {target_url}: {e}")
            return web.Response(
                status=502,
                text=f"Error forwarding request: {str(e)}"
            )
