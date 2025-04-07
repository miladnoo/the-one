"""
Tests for the proxy server
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.proxy.server import ProxyServer


class TestProxyServer(unittest.TestCase):
    """
    Test cases for the proxy server.
    """
    
    def setUp(self):
        """Set up the test case."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Tear down the test case."""
        self.loop.close()
    
    def test_init_forward_proxy(self):
        """Test initializing a forward proxy server."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'forward',
                'forward': {
                    'require_auth': False
                }
            }
        }
        
        server = ProxyServer(config, self.loop)
        
        self.assertEqual(server.proxy_mode, 'forward')
        self.assertIsNotNone(server.app)
        self.assertIsNone(server.ssl_context)
    
    def test_init_reverse_proxy(self):
        """Test initializing a reverse proxy server."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'reverse',
                'reverse': {
                    'targets': [
                        {
                            'name': 'test',
                            'host': 'example.com',
                            'port': 80
                        }
                    ]
                }
            }
        }
        
        server = ProxyServer(config, self.loop)
        
        self.assertEqual(server.proxy_mode, 'reverse')
        self.assertIsNotNone(server.app)
        self.assertIsNone(server.ssl_context)
    
    def test_init_socks5_proxy(self):
        """Test initializing a SOCKS5 proxy server."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'socks5',
                'socks5': {
                    'require_auth': False
                }
            }
        }
        
        server = ProxyServer(config, self.loop)
        
        self.assertEqual(server.proxy_mode, 'socks5')
        self.assertIsNotNone(server.app)
        self.assertIsNone(server.ssl_context)
    
    def test_init_invalid_proxy_mode(self):
        """Test initializing a proxy server with an invalid mode."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'invalid'
            }
        }
        
        with self.assertRaises(ValueError):
            ProxyServer(config, self.loop)
    
    @patch('src.proxy.server.setup_ssl')
    def test_init_with_ssl(self, mock_setup_ssl):
        """Test initializing a proxy server with SSL."""
        # Mock SSL context
        mock_ssl_context = MagicMock()
        mock_setup_ssl.return_value = mock_ssl_context
        
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'forward',
                'forward': {
                    'require_auth': False
                }
            },
            'security': {
                'ssl': {
                    'enabled': True,
                    'cert_file': 'cert.pem',
                    'key_file': 'key.pem'
                }
            }
        }
        
        server = ProxyServer(config, self.loop)
        
        self.assertEqual(server.proxy_mode, 'forward')
        self.assertIsNotNone(server.app)
        self.assertEqual(server.ssl_context, mock_ssl_context)
        mock_setup_ssl.assert_called_once_with(config['security']['ssl'])


class TestProxyServerIntegration(AioHTTPTestCase):
    """
    Integration tests for the proxy server.
    """
    
    async def get_application(self):
        """Get the application for testing."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'forward',
                'forward': {
                    'require_auth': False
                }
            }
        }
        
        server = ProxyServer(config)
        return server.app
    
    @unittest_run_loop
    async def test_forward_proxy_get(self):
        """Test a GET request through the forward proxy."""
        # This is a simplified test that doesn't actually proxy a request
        # In a real test, we would set up a mock server to respond to the proxied request
        
        # Make a request to the proxy
        resp = await self.client.get('/')
        
        # Check the response
        self.assertEqual(resp.status, 404)  # No target found


if __name__ == '__main__':
    unittest.main()
