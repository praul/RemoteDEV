#!/bin/bash
set -e

# Create authorized_keys if it doesn't exist
if [ ! -f authorized_keys ]; then
  touch authorized_keys
  echo "# Add your public keys here" > authorized_keys
  echo "Created authorized_keys"
fi

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


mkdir -p cache/.vscode-server
#chown -R root:root cache/.vscode-server
chmod -R 777 cache/.vscode-server


docker compose build

echo "Project initialized."