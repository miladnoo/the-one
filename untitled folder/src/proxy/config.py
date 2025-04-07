"""
Configuration management for the proxy server
"""

import os
import yaml
import logging
from typing import Dict, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict containing the configuration
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the configuration file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            logging.info(f"Loaded configuration from {config_path}")
            return config
        except yaml.YAMLError as e:
            logging.error(f"Error parsing configuration file: {e}")
            raise


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if the configuration is valid, False otherwise
    """
    required_keys = ['server', 'proxy']
    
    # Check for required top-level keys
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required configuration key: {key}")
            return False
    
    # Validate server configuration
    server_config = config.get('server', {})
    if not all(k in server_config for k in ['host', 'port']):
        logging.error("Server configuration must include 'host' and 'port'")
        return False
    
    # Validate proxy configuration
    proxy_config = config.get('proxy', {})
    if 'mode' not in proxy_config:
        logging.error("Proxy configuration must include 'mode'")
        return False
    
    mode = proxy_config['mode']
    if mode not in ['forward', 'reverse', 'socks5']:
        logging.error(f"Invalid proxy mode: {mode}")
        return False
    
    # Mode-specific validation
    if mode == 'reverse' and 'targets' not in proxy_config.get('reverse', {}):
        logging.error("Reverse proxy configuration must include 'targets'")
        return False
    
    return True
