#!/bin/sh
set -e

echo "Starting mtproto-proxy..."
exec mtproto-proxy --aes-pwd /app/proxy-secret /app/proxy-multi.conf "$@"
