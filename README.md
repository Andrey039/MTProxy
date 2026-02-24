# MTProxy Docker

Simple MT-Proto proxy for Telegram in Docker container.

## Quick Start

1. Clone and setup:
```bash
git clone https://github.com/your-username/MTProxy
cd MTProxy
cp .env.example .env
```

2. Configure Docker Hub username in `.env`:
```bash
DOCKERHUB_USERNAME=your_dockerhub_username
```

3. Generate secret:
```bash
head -c 16 /dev/urandom | xxd -ps
```

4. Edit `.env` file and set your secret:
```bash
nano .env
```

5. Download Telegram configuration files:
```bash
curl -s https://core.telegram.org/getProxySecret -o proxy-secret
curl -s https://core.telegram.org/getProxyConfig -o proxy-multi.conf
```

6. Start the proxy:
```bash
docker-compose up -d
```

## Getting Connection Link

After starting the proxy, generate a connection link for Telegram clients:

```bash
SECRET=$(grep SECRET .env | cut -d= -f2)
SERVER_IP=$(curl -s ifconfig.me)
echo "tg://proxy?server=$SERVER_IP&port=443&secret=$SECRET"
```

### For random padding (recommended):
Add `dd` prefix to your secret in `.env`:
```
SECRET=ddyour_32_character_hex_secret_here
```

## Verification

Check if proxy is working:

```bash
# Check stats
curl localhost:8888/stats

# Check listening ports
ss -tlnp | grep -E ':(443|8888)'

# View logs
docker-compose logs -f
```

## Register with MTProxybot

1. Send your server IP and port 443 to [@MTProxybot](https://t.me/MTProxybot)
2. Get proxy tag from the bot
3. Add proxy tag to docker-compose.yml:
```yaml
command: [
  "-u", "nobody",
  "-p", "8888", 
  "-H", "443",
  "-S", "${SECRET}",
  "-P", "your_proxy_tag_here",
  "-M", "1"
]
```
4. Restart: `docker-compose restart`

## Update Configuration

Telegram configuration files should be updated daily:

```bash
curl -s https://core.telegram.org/getProxySecret -o proxy-secret
curl -s https://core.telegram.org/getProxyConfig -o proxy-multi.conf
docker-compose restart
```

## Building from Source

```bash
docker build -t mtproxy .
```

## Using Pre-built Images

Images are automatically built and tagged with commit SHA:

```bash
# Use specific version
IMAGE_TAG=abc1234 docker-compose up -d

# Use latest
docker-compose up -d
```

Available tags:
- `latest` - latest build from main branch
- `abc1234` - specific commit (7-character SHA)
- `main` - latest from main branch
- `v1.0.0` - semantic version tags

## Environment Variables

- `SECRET` - 32-character hex secret for client connections
- Add `dd` prefix for random padding support

## Ports

- `443` - Client connections
- `8888` - Statistics (localhost only)

## License

This project uses the original MTProxy source code. See `LGPLv2` and `GPLv2` files.