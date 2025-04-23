# SSH Proxy Docker

A Docker-based SSH proxy that mounts remote SSH filesystems and provides a devtools environment (php, npm, git, etc.) with an SSH server.

I use this to mitigate VS-Code Remote Server dropping legacy support.

With this you can:
- SSHFS-Mount all your projects and servers inside this container
- Container will spin up an ssh Server at port 2222. Inside you will have php, python, npm and all your mounts at /mnt/sshfs
- You can simply connect your vcscode to the container and work on legacy servers

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
