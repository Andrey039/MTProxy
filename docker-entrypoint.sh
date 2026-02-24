#!/bin/sh
set -e

echo "Downloading proxy files..."
curl -s https://core.telegram.org/getProxySecret -o /app/proxy-secret || exit 1
curl -s https://core.telegram.org/getProxyConfig -o /app/proxy-multi.conf || exit 1

echo "Starting mtproto-proxy..."
exec mtproto-proxy --aes-pwd /app/proxy-secret /app/proxy-multi.conf "$@"
