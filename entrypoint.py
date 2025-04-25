#!/usr/bin/env python3
import os
import subprocess
import json
import logging
import sys
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

SSH_KEY_PATH = os.environ.get("SSH_KEY_PATH", "/config/id_rsa")
USER_SSH_KEY_PATH = f"/home/devuser/.ssh/id_rsa"
SERVERS_CONFIG = os.environ.get("SERVERS_CONFIG", "/config/servers.json")
DEVUSER = "devuser"
SSH_DIR = f"/home/{DEVUSER}/.ssh"
AUTHORIZED_KEYS = os.path.join(SSH_DIR, "authorized_keys")
MOUNT_BASE = "/mnt/sshfs"

current_mounts = {}

def ensure_ssh_key():
    dir_path = os.path.dirname(SSH_KEY_PATH)
    if not os.access(dir_path, os.W_OK):
        logging.error(f"Cannot write SSH key to {SSH_KEY_PATH}. Directory {dir_path} is not writable.")
        return False

    # Get user ID and group ID
    import pwd
    try:
        pw = pwd.getpwnam(DEVUSER)
        uid, gid = pw.pw_uid, pw.pw_gid
    except Exception:
        uid, gid = 1001, 1001  # fallback

    # Generate new key if it doesn't exist
    if not os.path.isfile(SSH_KEY_PATH):
        logging.info(f"No SSH key found at {SSH_KEY_PATH}, generating new key pair...")
        try:
            subprocess.run([
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", SSH_KEY_PATH
            ], check=True)
        except Exception as e:
            logging.error(f"Failed to generate SSH key: {e}")
            return False
        
        # Log public key if generated
        pubkey = SSH_KEY_PATH + ".pub"
        if os.path.isfile(pubkey):
            with open(pubkey) as f:
                logging.info("Generated new SSH key. Public key:\n" + f.read())

    try:
        # Ensure .ssh directory exists
        ensure_ssh_dir_and_auth_keys()
        
        # Set permissions on /config SSH keys (owned by root)
        if os.path.isfile(SSH_KEY_PATH):
            os.chown(SSH_KEY_PATH, 0, 0)  # root ownership
            os.chmod(SSH_KEY_PATH, 0o600)
            pubkey = SSH_KEY_PATH + ".pub"
            if os.path.isfile(pubkey):
                os.chown(pubkey, 0, 0)  # root ownership
                os.chmod(pubkey, 0o644)
        
        # Copy and set permissions in user's directory
        subprocess.run(["cp", "-f", SSH_KEY_PATH, USER_SSH_KEY_PATH], check=True)
        os.chown(USER_SSH_KEY_PATH, uid, gid)  # devuser ownership
        os.chmod(USER_SSH_KEY_PATH, 0o600)
        
        # Handle public key
        pubkey = SSH_KEY_PATH + ".pub"
        if os.path.isfile(pubkey):
            user_pubkey = USER_SSH_KEY_PATH + ".pub"
            subprocess.run(["cp", "-f", pubkey, user_pubkey], check=True)
            os.chown(user_pubkey, uid, gid)  # devuser ownership
            os.chmod(user_pubkey, 0o644)
            
    except Exception as e:
        logging.warning(f"Could not setup SSH keys: {e}")
        return False
        
    return True

def ensure_ssh_dir_and_auth_keys():
    import pwd
    try:
        pw = pwd.getpwnam(DEVUSER)
        uid, gid = pw.pw_uid, pw.pw_gid
    except Exception:
        uid, gid = 1000, 1000  # fallback
    os.makedirs(SSH_DIR, exist_ok=True)
    try:
        os.chown(SSH_DIR, uid, gid)
        os.chmod(SSH_DIR, 0o700)
    except Exception as e:
        logging.warning(f"Could not set permissions on {SSH_DIR}: {e}")
        
    if os.path.isfile(AUTHORIZED_KEYS):
        try:
            os.chown(AUTHORIZED_KEYS, uid, gid)
            os.chmod(AUTHORIZED_KEYS, 0o600)
        except Exception as e:
            logging.warning(f"Could not set permissions on {AUTHORIZED_KEYS}: {e}")

def get_servers():
    if not os.path.isfile(SERVERS_CONFIG):
        logging.info(f"No servers config found at {SERVERS_CONFIG}, skipping sshfs mounts.")
        return []
    try:
        with open(SERVERS_CONFIG) as f:
            config = json.load(f)
        return config.get("servers", [])
    except Exception as e:
        logging.error(f"Error reading or parsing {SERVERS_CONFIG}: {e}")
        return []

def mount_server(server):
    name = server.get("name")
    host = server.get("host")
    remote_path = server.get("remote_path")
    user = server.get("user", DEVUSER)
    port = server.get("port")
    password = server.get("password")
    if not (name and host and remote_path):
        logging.warning(f"Skipping incomplete server config: {server}")
        return False
    mount_point = f"{MOUNT_BASE}/{name}"
    os.makedirs(mount_point, exist_ok=True)
    if password:
        logging.info(f"Attempting password-based mount for {name}")
        cmd = [
            "sshfs",
            "-o", "StrictHostKeyChecking=no",
            "-o", "allow_other",
            "-o", "password_stdin"
            
        ]
        # Optionally, try forcing sftp_server if needed:
        # cmd += ["-o", "sftp_server=/usr/lib/openssh/sftp-server"]
        if port:
            cmd += ["-p", str(port)]
        cmd += [f"{user}@{host}:{remote_path}", mount_point]
    else:
        cmd = [
            "sshfs",
            "-o", f"IdentityFile={SSH_KEY_PATH}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "allow_other"
        ]
        if port:
            cmd += ["-p", str(port)]
        cmd += [f"{user}@{host}:{remote_path}", mount_point]
    try:
        # Redact password from log for password-based mounts
        if password:
            log_cmd = ' '.join(cmd).replace(password, "****")
            logging.info(f"sshfs command: {log_cmd}")
        else:
            logging.info(f"sshfs command: {' '.join(cmd)}")
        if password:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=password + '\n', timeout=30)
            result = type('Result', (), {'returncode': process.returncode, 'stdout': stdout, 'stderr': stderr})()
        else:
            # For key-based auth, just run normally
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logging.info(f"sshfs stdout: {result.stdout}")
        logging.info(f"sshfs stderr: {result.stderr}")
        if result.returncode != 0:
            logging.error(f"sshfs exited with code {result.returncode}")
            return False
        if os.path.ismount(mount_point):
            logging.info(f"Mounted {user}@{host}:{remote_path} to {mount_point}")
            current_mounts[name] = mount_point
            return True
        else:
            logging.warning(f"sshfs command succeeded but {mount_point} is not a mount point. Possible authentication or connection issue.")
            try:
                ls_output = subprocess.run(["ls", "-l", mount_point], capture_output=True, text=True)
                logging.warning(f"Contents of {mount_point}:\n{ls_output.stdout}\n{ls_output.stderr}")
            except Exception as e:
                logging.warning(f"Could not list contents of {mount_point}: {e}")
            return False
    except subprocess.CalledProcessError as e:
        if hasattr(e, 'output') and e.output:
            logging.error(f"SSHFS output: {e.output.decode(errors='ignore')}")
        if hasattr(e, 'stderr') and e.stderr:
            logging.error(f"SSHFS error: {e.stderr.decode(errors='ignore')}")
        logging.error(f"Failed to mount {user}@{host}:{remote_path} to {mount_point}: {e}")
        return False

def unmount_server(name):
    mount_point = f"{MOUNT_BASE}/{name}"
    if os.path.ismount(mount_point):
        try:
            subprocess.run(["fusermount", "-u", mount_point], check=True)
            logging.info(f"Unmounted {mount_point}")
        except Exception as e:
            logging.error(f"Failed to unmount {mount_point}: {e}")
    current_mounts.pop(name, None)

def sync_mounts():
    servers = get_servers()
    logging.info(f"Processing {len(servers)} servers from config.")
    new_names = set()
    for server in servers:
        name = server.get("name")
        host = server.get("host")
        remote_path = server.get("remote_path")
        if not (name and host and remote_path):
            logging.warning(f"Skipping server due to missing fields: {server}")
            continue
        new_names.add(name)
        if name not in current_mounts:
            mount_server(server)
    # Unmount removed servers
    for name in list(current_mounts.keys()):
        if name not in new_names:
            unmount_server(name)

class ServersConfigHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(os.path.basename(SERVERS_CONFIG)):
            logging.info(f"{SERVERS_CONFIG} changed, reloading mounts...")
            sync_mounts()

def patch_sshd_config():
    """Ensure sshd_config has correct settings for key auth."""
    config_path = "/etc/ssh/sshd_config"
    required = {
        "PubkeyAuthentication": "yes",
        "PasswordAuthentication": "no",
        "AuthorizedKeysFile": ".ssh/authorized_keys"
    }
    # Read config
    try:
        with open(config_path, "r") as f:
            lines = f.readlines()
        # Remove any existing lines for these options
        new_lines = []
        for line in lines:
            if not any(line.strip().startswith(k) for k in required):
                new_lines.append(line)
        # Add required options
        for k, v in required.items():
            new_lines.append(f"{k} {v}\n")
        with open(config_path, "w") as f:
            f.writelines(new_lines)
        logging.info("Patched /etc/ssh/sshd_config for key authentication.")
    except Exception as e:
        logging.error(f"Failed to patch sshd_config: {e}")

def restart_sshd():
    try:
        subprocess.run(["service", "ssh", "restart"])
    except Exception as e:
        logging.warning(f"Could not restart sshd: {e}")

def start_sshd():
    logging.info("Starting SSH server...")
    try:
        subprocess.run(["/usr/sbin/sshd", "-D"])
    except Exception as e:
        logging.error(f"Failed to start SSH server: {e}")
        sys.exit(1)

def main():
    ensure_ssh_key()
    ensure_ssh_dir_and_auth_keys()
    patch_sshd_config()
    restart_sshd()
    sync_mounts()

    # Start SSHD in a thread
    sshd_thread = threading.Thread(target=start_sshd, daemon=True)
    sshd_thread.start()

    # Watch servers.json for changes
    observer = Observer()
    handler = ServersConfigHandler()
    observer.schedule(handler, path=os.path.dirname(SERVERS_CONFIG) or ".", recursive=False)
    observer.start()
    logging.info(f"Watching {SERVERS_CONFIG} for changes...")

    try:
        while True:
            time.sleep(1)
            if not sshd_thread.is_alive():
                logging.info("SSHD process exited.")
                break
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()