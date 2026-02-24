#!/bin/sh
set -e

echo "Downloading proxy-secret..."
if ! curl -f -s https://core.telegram.org/getProxySecret -o /app/proxy-secret; then
    echo "ERROR: Failed to download proxy-secret"
    exit 1
fi

echo "Downloading proxy-multi.conf..."
if ! curl -f -s https://core.telegram.org/getProxyConfig -o /app/proxy-multi.conf; then
    echo "ERROR: Failed to download proxy-multi.conf"
    exit 1
fi

echo "Starting mtproto-proxy..."
exec mtproto-proxy --aes-pwd /app/proxy-secret /app/proxy-multi.conf "$@"
