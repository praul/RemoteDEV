# SSH Proxy Docker

A Docker-based SSH proxy that mounts remote SSH filesystems and provides a devtools environment (php, npm, git, etc.) with an SSH server.

## Usage

1. **Configure servers**

   Edit `servers.json` to list remote filesystems to mount:
   ```json
   {
     "servers": [
       {
         "name": "server1",
         "host": "example.com",
         "remote_path": "/remote/path"
       }
     ]
   }
   ```

2. **SSH Key**

   - To use your own SSH key, place it as `id_rsa` in the project root.
   - If not supplied, the container will generate a new key pair on startup and print the public key in the logs. Add this public key to `authorized_keys` on your remote servers.

3. **Build and run**

   ```
   docker-compose up --build
   ```

4. **Access**

   - SSH server runs on port 2222 (user: `devuser`, password: `devpass`).
   - Mounted remote filesystems are available in `/mnt/sshfs` inside the container.

## Notes

- The container uses `sshfs` to mount remote filesystems as specified in `servers.json`.
- The SSH key is available at `/config/id_rsa` inside the container.
- You can add more devtools by editing the `Dockerfile`.