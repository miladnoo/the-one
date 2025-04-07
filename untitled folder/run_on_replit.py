#!/usr/bin/env python3
"""
Helper script for running the proxy server on Replit
"""

import os
import sys
import subprocess
import yaml

def check_dependencies():
    """Check if all dependencies are installed."""
    try:
        import aiohttp
        import uvloop
        import yaml
        print("✅ All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return False

def check_config():
    """Check if the config file exists and is valid."""
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for required sections
        if 'server' not in config:
            print("❌ Missing 'server' section in config file.")
            return False
        
        if 'proxy' not in config:
            print("❌ Missing 'proxy' section in config file.")
            return False
        
        # Check for required server settings
        if 'host' not in config['server']:
            print("❌ Missing 'host' in server config.")
            return False
        
        if 'port' not in config['server']:
            print("❌ Missing 'port' in server config.")
            return False
        
        # Check for required proxy settings
        if 'mode' not in config['proxy']:
            print("❌ Missing 'mode' in proxy config.")
            return False
        
        mode = config['proxy']['mode']
        if mode not in ['forward', 'reverse', 'socks5']:
            print(f"❌ Invalid proxy mode: {mode}")
            return False
        
        print(f"✅ Config file is valid. Proxy mode: {mode}")
        return True
    except Exception as e:
        print(f"❌ Error parsing config file: {e}")
        return False

def setup_replit_environment():
    """Set up the Replit environment."""
    # Add the current directory to PYTHONPATH
    sys.path.insert(0, os.getcwd())
    
    # Set environment variables for Replit
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('certs', exist_ok=True)

def run_proxy_server():
    """Run the proxy server."""
    print("🚀 Starting proxy server...")
    try:
        subprocess.run([sys.executable, "src/main.py"])
    except KeyboardInterrupt:
        print("\n🛑 Proxy server stopped.")
    except Exception as e:
        print(f"❌ Error running proxy server: {e}")

def main():
    """Main entry point."""
    print("🔄 Setting up proxy server on Replit...")
    
    # Set up the environment
    setup_replit_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("⚠️ Please restart the script after installing dependencies.")
        return
    
    # Check config
    if not check_config():
        print("⚠️ Please fix the config file and restart the script.")
        return
    
    # Run the proxy server
    run_proxy_server()

if __name__ == "__main__":
    main()
