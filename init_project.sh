#!/bin/bash
set -e

# Create config directory if it doesn't exist
if [ ! -d config ]; then
  mkdir config
  echo "Created config directory"
fi

# Copy servers.json.example to config/servers.json if not present
if [ ! -f config/servers.json ]; then
  cp servers.json.example config/servers.json
  echo "Copied servers.json.example to config/servers.json"
fi


mkdir -p cache/.ssh
touch cache/.ssh/authorized_keys
chown -R 1001:1001 cache

docker compose build

echo "Project initialized."