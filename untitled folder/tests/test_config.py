"""
Tests for configuration management
"""

import os
import tempfile
import unittest
import yaml

from src.proxy.config import load_config, validate_config


class TestConfig(unittest.TestCase):
    """
    Test cases for configuration management.
    """
    
    def test_load_config(self):
        """Test loading configuration from a file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump({
                'server': {
                    'host': '127.0.0.1',
                    'port': 8080
                },
                'proxy': {
                    'mode': 'forward'
                }
            }, f)
        
        try:
            # Load the config
            config = load_config(f.name)
            
            # Check the config
            self.assertEqual(config['server']['host'], '127.0.0.1')
            self.assertEqual(config['server']['port'], 8080)
            self.assertEqual(config['proxy']['mode'], 'forward')
        finally:
            # Clean up
            os.unlink(f.name)
    
    def test_load_config_file_not_found(self):
        """Test loading configuration from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_config('non_existent_file.yaml')
    
    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'forward'
            }
        }
        
        self.assertTrue(validate_config(config))
    
    def test_validate_config_missing_server(self):
        """Test validating a configuration with missing server section."""
        config = {
            'proxy': {
                'mode': 'forward'
            }
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_missing_proxy(self):
        """Test validating a configuration with missing proxy section."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            }
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_missing_server_host(self):
        """Test validating a configuration with missing server host."""
        config = {
            'server': {
                'port': 8080
            },
            'proxy': {
                'mode': 'forward'
            }
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_missing_server_port(self):
        """Test validating a configuration with missing server port."""
        config = {
            'server': {
                'host': '127.0.0.1'
            },
            'proxy': {
                'mode': 'forward'
            }
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_missing_proxy_mode(self):
        """Test validating a configuration with missing proxy mode."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {}
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_invalid_proxy_mode(self):
        """Test validating a configuration with invalid proxy mode."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'invalid'
            }
        }
        
        self.assertFalse(validate_config(config))
    
    def test_validate_config_reverse_missing_targets(self):
        """Test validating a reverse proxy configuration with missing targets."""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080
            },
            'proxy': {
                'mode': 'reverse',
                'reverse': {}
            }
        }
        
        self.assertFalse(validate_config(config))


if __name__ == '__main__':
    unittest.main()
