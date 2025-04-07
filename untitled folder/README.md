# High-Performance Proxy Server

A versatile, high-performance proxy server built with Python that supports multiple proxy modes:
- Forward proxy
- Reverse proxy
- SOCKS5 proxy

## Features

- **High Performance**:
  - Asynchronous I/O with `aiohttp` and `asyncio`
  - Optional `uvloop` for improved performance
  - Efficient connection handling

- **Multiple Proxy Modes**:
  - Forward proxy for client-side proxying
  - Reverse proxy with load balancing
  - SOCKS5 proxy for protocol-agnostic proxying

- **Security Features**:
  - TLS/SSL support
  - Authentication (Basic Auth)
  - Rate limiting
  - Access control

- **Advanced Functionality**:
  - Response caching
  - Request/response filtering
  - Comprehensive logging
  - Metrics collection

## Running on Replit

This proxy server is designed to be run on-demand using Replit:

1. **Fork the Repl**:
   - Create a new Python Repl on [Replit](https://replit.com)
   - Import this repository or upload the files

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run When Needed**:
   - Press the "Run" button in Replit whenever you need the proxy
   - The server will start and be accessible via the URL Replit provides
   - When you're done, you can stop the repl

## Configuration

Edit the `config/config.yaml` file to customize the proxy server settings:

```yaml
proxy:
  mode: forward  # Options: forward, reverse, socks5
```

Key configuration options:

- **Proxy Mode**: Choose between `forward`, `reverse`, or `socks5`
- **Authentication**: Enable/disable and configure authentication
- **SSL**: Configure SSL for secure connections
- **Rate Limiting**: Set rate limits to prevent abuse
- **Caching**: Configure response caching

## Usage Examples

### Forward Proxy

```yaml
proxy:
  mode: forward
  forward:
    require_auth: true
    allowed_domains:
      - "*.example.com"
      - "api.github.com"
```

### Reverse Proxy

```yaml
proxy:
  mode: reverse
  reverse:
    targets:
      - name: api
        host: api.example.com
        port: 443
        ssl: true
      - name: web
        host: web.example.com
        port: 443
        ssl: true
    path_routing:
      "/api": api
      "/": web
```

### SOCKS5 Proxy

```yaml
proxy:
  mode: socks5
  socks5:
    require_auth: true
```

## License

MIT
