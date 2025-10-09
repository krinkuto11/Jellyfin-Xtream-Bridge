# Deployment Guide

This guide covers various deployment options for Jellyfin-Xtream-Server.

## Table of Contents
- [Docker Deployment (Recommended)](#docker-deployment-recommended)
- [Docker Compose](#docker-compose)
- [Manual Deployment](#manual-deployment)
- [Production Best Practices](#production-best-practices)

## Docker Deployment (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+ (optional)

### Quick Start

1. **Pull the image from GitHub Container Registry:**
```bash
docker pull ghcr.io/krinkuto11/jellyfin-xtream-server:latest
```

2. **Create configuration:**
```bash
mkdir -p config
docker run --rm ghcr.io/krinkuto11/jellyfin-xtream-server:latest \
  cat /config/config.json.example > config/config.json.example
cp config/config.json.example config/config.json
```

3. **Edit configuration:**
```bash
nano config/config.json
```

4. **Run the container:**
```bash
docker run -d \
  --name jellyfin-xtream-server \
  -p 8080:8080 \
  -v $(pwd)/config:/config \
  --restart unless-stopped \
  ghcr.io/krinkuto11/jellyfin-xtream-server:latest
```

### Docker Environment Variables

You can override configuration using environment variables:

```bash
docker run -d \
  --name jellyfin-xtream-server \
  -p 8080:8080 \
  -v $(pwd)/config:/config \
  -e TZ=America/New_York \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  ghcr.io/krinkuto11/jellyfin-xtream-server:latest
```

## Docker Compose

### Basic Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  jellyfin-xtream-server:
    image: ghcr.io/krinkuto11/jellyfin-xtream-server:latest
    container_name: jellyfin-xtream-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./config:/config:rw
    environment:
      - TZ=UTC
      - PYTHONUNBUFFERED=1
```

Run with:
```bash
docker-compose up -d
```

### Advanced Setup with Traefik

For production deployments with reverse proxy and SSL:

```yaml
version: '3.8'

services:
  jellyfin-xtream-server:
    image: ghcr.io/krinkuto11/jellyfin-xtream-server:latest
    container_name: jellyfin-xtream-server
    restart: unless-stopped
    networks:
      - traefik
    volumes:
      - ./config:/config:rw
    environment:
      - TZ=UTC
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.xtream.rule=Host(`xtream.example.com`)"
      - "traefik.http.routers.xtream.entrypoints=websecure"
      - "traefik.http.routers.xtream.tls.certresolver=letsencrypt"
      - "traefik.http.services.xtream.loadbalancer.server.port=8080"

networks:
  traefik:
    external: true
```

## Manual Deployment

### System Requirements
- Python 3.9+
- pip
- systemd (for service management)

### Installation Steps

1. **Clone repository:**
```bash
git clone https://github.com/krinkuto11/Jellyfin-Xtream-Server.git
cd Jellyfin-Xtream-Server
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure:**
```bash
cp config/config.json.example config/config.json
nano config/config.json
```

5. **Test run:**
```bash
python src/xtream_server.py
```

### Systemd Service

Create `/etc/systemd/system/jellyfin-xtream.service`:

```ini
[Unit]
Description=Jellyfin Xtream Server
After=network.target

[Service]
Type=simple
User=xtream
WorkingDirectory=/opt/jellyfin-xtream-server
Environment="PATH=/opt/jellyfin-xtream-server/venv/bin"
ExecStart=/opt/jellyfin-xtream-server/venv/bin/python src/xtream_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable jellyfin-xtream
sudo systemctl start jellyfin-xtream
sudo systemctl status jellyfin-xtream
```

## Production Best Practices

### Security

1. **Use HTTPS:** Always deploy behind a reverse proxy with SSL/TLS
2. **Strong passwords:** Use strong, unique passwords in config
3. **Network isolation:** Consider using Docker networks or firewalls
4. **Regular updates:** Keep the container/software updated

### Monitoring

1. **Health checks:** Docker includes built-in health checks
2. **Logs:** Monitor logs for errors and issues
```bash
# Docker
docker logs -f jellyfin-xtream-server

# Systemd
journalctl -u jellyfin-xtream -f
```

3. **Resource monitoring:** Monitor CPU, memory, and network usage

### Backup

Backup the configuration directory regularly:
```bash
tar -czf xtream-backup-$(date +%Y%m%d).tar.gz config/
```

### Reverse Proxy Examples

#### Nginx
```nginx
server {
    listen 80;
    server_name xtream.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name xtream.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Apache
```apache
<VirtualHost *:80>
    ServerName xtream.example.com
    Redirect permanent / https://xtream.example.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName xtream.example.com

    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem

    ProxyPreserveHost On
    ProxyPass / http://localhost:8080/
    ProxyPassReverse / http://localhost:8080/
</VirtualHost>
```

#### Caddy
```
xtream.example.com {
    reverse_proxy localhost:8080
}
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs jellyfin-xtream-server

# Verify config
docker run --rm -v $(pwd)/config:/config \
  ghcr.io/krinkuto11/jellyfin-xtream-server:latest \
  python -c "import json; json.load(open('/config/config.json'))"
```

### Permission issues
```bash
# Fix ownership
sudo chown -R 1000:1000 config/
```

### Port conflicts
```bash
# Check what's using port 8080
sudo lsof -i :8080

# Use different port
docker run -d -p 8081:8080 ...
```

## Updating

### Docker
```bash
# Pull latest image
docker pull ghcr.io/krinkuto11/jellyfin-xtream-server:latest

# Recreate container
docker-compose down
docker-compose up -d
```

### Manual
```bash
cd /opt/jellyfin-xtream-server
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart jellyfin-xtream
```
