"""
Utility functions
"""

import logging
import os
import ssl
from typing import Dict, Any, Optional


def setup_ssl(ssl_config: Dict[str, Any]) -> Optional[ssl.SSLContext]:
    """
    Set up SSL context.
    
    Args:
        ssl_config: SSL configuration
        
    Returns:
        SSL context, or None if SSL is not enabled
    """
    if not ssl_config.get('enabled', False):
        return None
    
    cert_file = ssl_config.get('cert_file')
    key_file = ssl_config.get('key_file')
    
    if not cert_file or not key_file:
        logging.error("SSL is enabled but cert_file or key_file is not specified")
        return None
    
    if not os.path.exists(cert_file):
        logging.error(f"SSL certificate file not found: {cert_file}")
        return None
    
    if not os.path.exists(key_file):
        logging.error(f"SSL key file not found: {key_file}")
        return None
    
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_file, key_file)
        return context
    except Exception as e:
        logging.error(f"Error setting up SSL: {e}")
        return None
