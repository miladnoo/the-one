# Running the Proxy Server on Replit

This guide will help you set up and run the high-performance proxy server on Replit.

## Setup Instructions

### 1. Create a New Repl

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Select "Import from GitHub" or choose "Python" as the language
4. If importing from GitHub, paste your repository URL
5. Give your repl a name (e.g., "proxy-server")
6. Click "Create Repl"

### 2. Install Dependencies

The `.replit` file should automatically set up the environment, but if you need to manually install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure the Proxy

Edit the `config/config.yaml` file to customize your proxy settings:

- Change the proxy mode (`forward`, `reverse`, or `socks5`)
- Configure authentication if needed
- Set up allowed domains for forward proxy
- Configure target servers for reverse proxy

### 4. Run the Proxy Server

Click the "Run" button in Replit to start the proxy server. The server will be accessible at your Replit URL:

```
https://proxy-server.yourusername.repl.co
```

### 5. Using the Proxy

#### Forward Proxy

Configure your client to use the proxy:

- Proxy Host: proxy-server.yourusername.repl.co
- Proxy Port: 443 (HTTPS)
- Proxy Type: HTTP/HTTPS

#### Reverse Proxy

Access the reverse proxy directly:

```
https://proxy-server.yourusername.repl.co/api/endpoint
```

#### SOCKS5 Proxy

Configure your client to use the SOCKS5 proxy:

- Proxy Host: proxy-server.yourusername.repl.co
- Proxy Port: 443 (HTTPS)
- Proxy Type: SOCKS5

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the proxy server is running and the port is accessible.
2. **Authentication Failed**: Check your authentication credentials in the config file.
3. **SSL Certificate Error**: You may need to accept the self-signed certificate or configure proper certificates.

### Replit-Specific Issues

1. **Repl Goes to Sleep**: Free Replit accounts will have the repl go to sleep after inactivity. You'll need to restart it when needed.
2. **Port Restrictions**: Replit may restrict certain ports. The proxy server uses port 8080 internally, but Replit will map this to HTTPS (443) externally.
3. **Memory Limitations**: Free Replit accounts have memory limitations. If you encounter out-of-memory errors, consider upgrading or optimizing the configuration.

## Advanced Configuration

### Custom SSL Certificates

To use custom SSL certificates:

1. Upload your certificate and key files to the `certs/` directory
2. Update the `config.yaml` file to point to your certificate files:

```yaml
security:
  ssl:
    enabled: true
    cert_file: certs/your-cert.crt
    key_file: certs/your-key.key
```

### Performance Tuning

For better performance:

1. Increase the number of workers in `config.yaml`:

```yaml
server:
  workers: 8  # Increase based on available CPU cores
```

2. Enable caching for frequently accessed resources:

```yaml
caching:
  enabled: true
  ttl: 300  # Cache time-to-live in seconds
```

## Stopping the Proxy

To stop the proxy server, simply click the "Stop" button in Replit or close the repl tab. The proxy will shut down gracefully.
