#!/bin/sh
set -e

echo "Downloading proxy-secret..."
curl -s https://core.telegram.org/getProxySecret -o /app/proxy-secret

echo "Downloading proxy-multi.conf..."
curl -s https://core.telegram.org/getProxyConfig -o /app/proxy-multi.conf

exec mtproto-proxy --aes-pwd /app/proxy-secret /app/proxy-multi.conf "$@"
