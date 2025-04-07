"""
Core proxy server implementation
"""

import asyncio
import logging
import ssl
from typing import Dict, Any, Optional, List, Tuple

import aiohttp
from aiohttp import web

from .handlers import (
    ForwardProxyHandler,
    ReverseProxyHandler,
    Socks5ProxyHandler
)
from .middleware import (
    setup_middlewares,
    error_middleware
)
from .utils import setup_ssl


class ProxyServer:
    """
    High-performance proxy server that supports multiple proxy modes.
    """
    
    def __init__(self, config: Dict[str, Any], loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        Initialize the proxy server.
        
        Args:
            config: Server configuration
            loop: Event loop to use (optional)
        """
        self.config = config
        self.loop = loop or asyncio.get_event_loop()
        self.app = web.Application(middlewares=[error_middleware])
        self.runner = None
        self.site = None
        self.proxy_mode = config['proxy']['mode']
        
        # Set up the appropriate handler based on the proxy mode
        self._setup_handlers()
        
        # Set up middlewares
        setup_middlewares(self.app, config)
        
        # Set up SSL if enabled
        self.ssl_context = None
        if config.get('security', {}).get('ssl', {}).get('enabled', False):
            self.ssl_context = setup_ssl(config['security']['ssl'])
    
    def _setup_handlers(self):
        """Set up the appropriate handlers based on the proxy mode."""
        if self.proxy_mode == 'forward':
            handler = ForwardProxyHandler(self.config)
            self.app.add_routes([
                web.get('/{path:.*}', handler.handle),
                web.post('/{path:.*}', handler.handle),
                web.put('/{path:.*}', handler.handle),
                web.delete('/{path:.*}', handler.handle),
                web.patch('/{path:.*}', handler.handle),
                web.head('/{path:.*}', handler.handle),
                web.options('/{path:.*}', handler.handle),
            ])
        elif self.proxy_mode == 'reverse':
            handler = ReverseProxyHandler(self.config)
            self.app.add_routes([
                web.get('/{path:.*}', handler.handle),
                web.post('/{path:.*}', handler.handle),
                web.put('/{path:.*}', handler.handle),
                web.delete('/{path:.*}', handler.handle),
                web.patch('/{path:.*}', handler.handle),
                web.head('/{path:.*}', handler.handle),
                web.options('/{path:.*}', handler.handle),
            ])
        elif self.proxy_mode == 'socks5':
            # SOCKS5 uses a different protocol, so we need a separate server
            self.socks5_handler = Socks5ProxyHandler(self.config)
        else:
            raise ValueError(f"Unsupported proxy mode: {self.proxy_mode}")
    
    async def start_socks5_server(self):
        """Start the SOCKS5 server if in SOCKS5 mode."""
        if self.proxy_mode != 'socks5':
            return
        
        host = self.config['server']['host']
        port = self.config['server']['port']
        
        server = await asyncio.start_server(
            self.socks5_handler.handle_connection,
            host,
            port,
            ssl=self.ssl_context
        )
        
        logging.info(f"SOCKS5 proxy server running on {host}:{port}")
        return server
    
    def start(self):
        """Start the proxy server."""
        host = self.config['server']['host']
        port = self.config['server']['port']
        
        if self.proxy_mode == 'socks5':
            # Start SOCKS5 server
            self.loop.create_task(self.start_socks5_server())
        else:
            # Start HTTP/HTTPS proxy server
            self.runner = web.AppRunner(self.app)
            self.loop.run_until_complete(self.runner.setup())
            self.site = web.TCPSite(
                self.runner,
                host,
                port,
                ssl_context=self.ssl_context
            )
            self.loop.run_until_complete(self.site.start())
            logging.info(f"{self.proxy_mode.capitalize()} proxy server running on {host}:{port}")
    
    def close(self):
        """Close the proxy server."""
        if self.site:
            self.site.stop()
        
        if self.runner:
            return self.runner.cleanup()
        
        return asyncio.Future()
    
    async def wait_closed(self):
        """Wait for the server to close."""
        if self.runner:
            await self.runner.cleanup()
