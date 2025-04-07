#!/usr/bin/env python3
"""
High-Performance Proxy Server - Main Entry Point
"""

import asyncio
import logging
import os
import signal
import sys
from argparse import ArgumentParser

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logging.warning("uvloop not available, falling back to standard event loop")

from proxy.server import ProxyServer
from proxy.config import load_config


def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description="High-Performance Proxy Server")
    parser.add_argument(
        "-c", "--config", 
        default="config/config.yaml", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    return parser.parse_args()


async def shutdown(server, loop, signal=None):
    """Gracefully shut down the server."""
    if signal:
        logging.info(f"Received exit signal {signal.name}...")
    
    logging.info("Shutting down server...")
    server.close()
    await server.wait_closed()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logging.info("Server shutdown complete.")


def main():
    """Main entry point for the proxy server."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Set up event loop
    loop = asyncio.get_event_loop()
    
    # Create and start the proxy server
    try:
        server = ProxyServer(config, loop)
        server.start()
        
        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, 
                lambda sig=sig: asyncio.create_task(shutdown(server, loop, sig))
            )
        
        logging.info(f"Proxy server running on {config['server']['host']}:{config['server']['port']}")
        loop.run_forever()
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        loop.close()
        logging.info("Server process ended")


if __name__ == "__main__":
    main()
