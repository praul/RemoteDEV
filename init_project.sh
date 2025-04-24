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
chmod 700 cache/.ssh
chmod 600 cache/.ssh/authorized_keys

docker compose build

echo "## Add your SSH key (for loggin into RemoteDEV) to cache/.ssh/authorized_keys (you may need superuser privileges, alternatively do this inside the container)."
echo "You will find your SSH keys for mounts in config dir. (This is the key you add to authorized_keys in your remote servers)."
echo "Project initialized."
echo "Edit config/servers.json to add your servers."
echo "You can now run the project using 'docker compose up'."