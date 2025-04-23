# SSH Proxy Docker

A Docker-based SSH proxy that mounts remote SSH filesystems and provides a devtools environment (php, npm, git, etc.) with an SSH server.

## Quickstart

1. **Initialize the project**

   Run the provided script to set up your environment:
   ```sh
   ./init_project.sh
   ```
   This will:
   - Create an `authorized_keys` file if it doesn't exist (add your public keys here).
   - Create a `config` directory if missing.
- The SSH key is available at `/config/id_rsa` inside the container.
- You can add more devtools by editing the `Dockerfile`.
- The SSH server is configured for public key authentication by default.