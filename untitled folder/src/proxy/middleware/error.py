"""
Error handling middleware
"""

import logging
import traceback
from typing import Callable

from aiohttp import web


@web.middleware
async def error_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Middleware for handling errors.
    
    Args:
        request: The incoming request
        handler: The request handler
        
    Returns:
        The response
    """
    try:
        return await handler(request)
    except web.HTTPException as ex:
        # Pass through HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        logger = logging.getLogger('error_middleware')
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        
        # Return a 500 response
        return web.Response(
            status=500,
            text="Internal Server Error"
        )
