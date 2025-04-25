# SSH Proxy Dev Container

This container is designed for using VSCode with multiple remote locations mounted via SSHFS. It enables seamless development across several remote servers, with all mounts accessible under `/mnt/sshfs/{project}`.

It also mitigates VSCode deprecating old servers. You can mount your old servers into this container and keep on using VSCode.

## Features

- **SSHFS Mounts:** Automatically mounts remote project folders as defined in `/config/servers.json` to `/mnt/sshfs/{name}`.
- **Integrated MCP Server (`ssh_search`):** Provides fast, credential-aware remote file and string search for use with Roo, Cline, or other MCP-compatible agents.
- **Password and key-based SSH support:** Uses credentials from `/config/servers.json`.
- **Remote Command Execution (`dremote`):** Execute commands directly on remote servers while maintaining correct paths.

## The dremote Command

The `dremote` command allows you to execute commands directly on the remote server while preserving the correct path mapping. This is particularly useful for operations that are faster to perform directly on the server rather than through SSHFS, such as:

- Git operations (add, commit, push)
- File operations on large sets of files
- Server-side build or deployment commands
- Database operations

### Usage

```bash
dremote <command>
```

Example: When you're in an SSHFS mounted directory like `/mnt/sshfs/myproject/src` and run:
```bash
dremote git status
```
The command executes in the corresponding remote directory (e.g., `/var/www/myproject/src`).

### Common Use Cases

1. **Git Operations:**
   ```bash
   dremote git add .
   dremote git commit -m "Update files"
   dremote git push
   ```

2. **File Operations:**
   ```bash
   dremote find . -name "*.log"
   dremote rm -rf cache/*
   ```

3. **Build Commands:**
   ```bash
   dremote npm run build
   dremote composer install
   ```

The command automatically:
- Determines which server to use based on your current SSHFS mount
- Maps the local path to the correct remote path
- Uses the appropriate SSH credentials from your config

## How to Start the Container

1. **Build the container:**
   ```bash
   docker build -t ssh-proxy .
   ```

2. **Run the container (mount your config):**
   ```bash
   docker run -v $(pwd)/config:/config ssh-proxy
   ```

   - Ensure your `servers.json` is in the `config` directory.

## Included MCP Server: `ssh_search`

- **Purpose:** Exposes two tools for Roo/Cline or other MCP clients:
  - `list_folders()`: Lists available project folders (from `/mnt/sshfs`).
  - `remote_search(folder, regex, file_pattern)`: Searches for strings or patterns on the remote server using SSH, with credentials from `/config/servers.json`.

- **How it works:**  
  The MCP server is started automatically by Roo/Cline when needed. It uses the FastMCP protocol to expose its tools. No manual port or server management is required.

- **Config**
  Add this to your mcp-server config
  ```json
     "ssh_search": {
        "command": "/venv/bin/python",
        "args": [
            "/tools/mcp_ssh_search/server.py"
        ]
    }
  ```


## Using with Roo/Cline

**Add this to your system prompt:**

> When searching for files or strings in files, always use mcp tool ssh_search. List folders before first use and determine the right folder from current workspace.

**Typical workflow:**
1. Use `list_folders()` to see available projects.
2. Use `remote_search(folder, regex, file_pattern)` to search files or strings in the correct project.

## Example `servers.json` (structure only)

```json
{
  "servers": [
    {
      "name": "project_name",
      "user": "ssh_user",
      "password": "your_password_or_remove_for_key_auth",
      "host": "example.com",
      "port": 22,
      "remote_path": "/"
    }
    // ... more servers
  ]
}
```

## Notes

- All SSHFS mounts appear under `/mnt/sshfs/{name}`.
- The MCP server is only accessible inside the container.
- Roo/Cline will automatically discover and use the MCP server for search operations.