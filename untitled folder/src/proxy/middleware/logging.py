"""
Logging middleware
"""

import logging
import time
from typing import Callable

from aiohttp import web


@web.middleware
async def logging_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Middleware for logging requests and responses.
    
    Args:
        request: The incoming request
        handler: The request handler
        
    Returns:
        The response
    """
    # Get logger
    logger = logging.getLogger('access')
    
    # Log request
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.path} from {request.remote}")
    
    # Process request
    try:
        response = await handler(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.path} {response.status} "
            f"in {duration:.3f}s"
        )
        
        return response
    except Exception as e:
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log error
        logger.error(
            f"Error: {request.method} {request.path} {type(e).__name__} {str(e)} "
            f"in {duration:.3f}s"
        )
        
        # Re-raise the exception
        raise
