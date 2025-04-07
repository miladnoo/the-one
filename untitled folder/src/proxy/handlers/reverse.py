"""
Reverse proxy handler implementation
"""

import logging
import random
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from aiohttp import web

from .base import BaseProxyHandler


class Target:
    """
    Represents a target server for the reverse proxy.
    """
    
    def __init__(self, name: str, host: str, port: int, ssl: bool = False, weight: int = 1):
        """
        Initialize a target.
        
        Args:
            name: Target name
            host: Target hostname
            port: Target port
            ssl: Whether to use SSL
            weight: Load balancing weight
        """
        self.name = name
        self.host = host
        self.port = port
        self.ssl = ssl
        self.weight = weight
        self.scheme = "https" if ssl else "http"
        self.base_url = f"{self.scheme}://{self.host}:{self.port}"
    
    def get_url(self, path: str) -> str:
        """
        Get the full URL for a path.
        
        Args:
            path: The path to append to the base URL
            
        Returns:
            The full URL
        """
        return urljoin(self.base_url, path)


class ReverseProxyHandler(BaseProxyHandler):
    """
    Handler for reverse proxy requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the reverse proxy handler.
        
        Args:
            config: Server configuration
        """
        super().__init__(config)
        
        # Parse targets
        self.targets: Dict[str, Target] = {}
        self.path_routing: Dict[str, str] = {}
        
        reverse_config = config['proxy'].get('reverse', {})
        
        # Load targets
        for target_config in reverse_config.get('targets', []):
            target = Target(
                name=target_config['name'],
                host=target_config['host'],
                port=target_config['port'],
                ssl=target_config.get('ssl', False),
                weight=target_config.get('weight', 1)
            )
            self.targets[target.name] = target
        
        # Load path routing
        self.path_routing = reverse_config.get('path_routing', {})
        
        self.logger.info(f"Initialized reverse proxy with {len(self.targets)} targets")
    
    def _get_target_for_path(self, path: str) -> Optional[Target]:
        """
        Get the target for a path based on the path routing configuration.
        
        Args:
            path: The request path
            
        Returns:
            The target for the path, or None if no target is found
        """
        # Find the longest matching path prefix
        matching_prefix = None
        for prefix in self.path_routing:
            if path.startswith(prefix):
                if matching_prefix is None or len(prefix) > len(matching_prefix):
                    matching_prefix = prefix
        
        if matching_prefix is None:
            return None
        
        target_name = self.path_routing[matching_prefix]
        return self.targets.get(target_name)
    
    def _select_target(self, targets: List[Target]) -> Target:
        """
        Select a target using weighted random selection.
        
        Args:
            targets: List of targets to choose from
            
        Returns:
            The selected target
        """
        total_weight = sum(target.weight for target in targets)
        r = random.uniform(0, total_weight)
        upto = 0
        
        for target in targets:
            upto += target.weight
            if upto >= r:
                return target
        
        # Fallback to the first target
        return targets[0]
    
    async def handle(self, request: web.Request) -> web.Response:
        """
        Handle a reverse proxy request.
        
        Args:
            request: The incoming request
            
        Returns:
            The response to send back to the client
        """
        path = request.path
        
        # Get the target for the path
        target = self._get_target_for_path(path)
        if target is None:
            return web.Response(
                status=404,
                text=f"No target found for path: {path}"
            )
        
        # Build the target URL
        target_url = target.get_url(path)
        
        # Add X-Forwarded headers
        headers = {
            'X-Forwarded-For': request.remote,
            'X-Forwarded-Proto': request.scheme,
            'X-Forwarded-Host': request.host,
            'X-Forwarded-Path': request.path,
        }
        
        # Forward the request
        return await self._forward_request(request, target_url, headers)
