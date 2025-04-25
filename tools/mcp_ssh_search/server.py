from typing import Any, List
import os
import subprocess
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("ssh_search")

def load_servers() -> dict:
    """Load server configurations from /config/servers.json."""
    with open("/config/servers.json", "r") as f:
        return json.load(f)

@mcp.tool()
def list_folders() -> List[str]:
    """List all available project folders."""
    mount_base = "/mnt/sshfs"
    if os.path.exists(mount_base):
        return [f for f in os.listdir(mount_base) 
                if os.path.isdir(os.path.join(mount_base, f))]
    return []

@mcp.tool()
def remote_search(folder: str, regex: str, file_pattern: str = "*") -> str:
    """Search files on remote server via SSH.
    
    Args:
        folder: Project/folder name matching server name in servers.json
        regex: Regular expression pattern to search for
        file_pattern: Optional file pattern (e.g., *.php) to filter files
    """
    config = load_servers()
    servers = config.get("servers", [])
    
    # Find server config for folder
    server = None
    for s in servers:
        if s.get("name") == folder:
            server = s
            break
    if not server:
        raise Exception(f"No server entry found for folder: {folder}")
    
    # Build SSH command
    user = server["user"]
    host = server["host"]
    port = server.get("port", 22)
    password = server.get("password")
    remote_path = server.get("remote_path", ".")

    if password:
        ssh_cmd = [
            "sshpass", "-p", password,
            "ssh",
            "-p", str(port),
            "-o", "StrictHostKeyChecking=no",
            f"{user}@{host}"
        ]
    else:
        ssh_cmd = [
            "ssh",
            "-p", str(port),
            "-o", "StrictHostKeyChecking=no",
            f"{user}@{host}"
        ]

    # Use ripgrep if available, else fallback to grep
    search_cmd = (
        f"cd {remote_path} && "
        f"(command -v rg >/dev/null 2>&1 && rg --with-filename --line-number --color never -e '{regex}' '{file_pattern}') "
        f"|| grep -r -n -H --include='{file_pattern}' '{regex}' ."
    )
    ssh_cmd += [search_cmd]
    
    result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 and not result.stdout:
        raise Exception(f"SSH search failed: {result.stderr}")
    return result.stdout

if __name__ == "__main__":
    mcp.run()