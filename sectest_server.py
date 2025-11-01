#!/usr/bin/env python3
"""
Security Testing Tools MCP Server with optional password auth fallback.
"""
import os
import sys
import logging
import subprocess
import re
import getpass
from typing import Optional

# optional dependency for password-based SSH
try:
    import paramiko
    _HAS_PARAMIKO = True
except Exception:
    _HAS_PARAMIKO = False

from mcp.server.fastmcp import FastMCP

# === CONFIGURATION ===
KALI_VM_USER = os.environ.get("KALI_VM_USER", "viransh")
KALI_VM_HOST = os.environ.get("KALI_VM_HOST", "host.docker.internal")
KALI_VM_KEY_PATH = os.environ.get("KALI_VM_KEY_PATH", "/home/mcpuser/.ssh/id_rsa")
KALI_VM_PORT = int(os.environ.get("KALI_VM_PORT", "2222"))
# optional: provide password via env var (not recommended for production)
KALI_VM_PASS = os.environ.get("KALI_VM_PASS", "")

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("sectest-server")

# Initialize MCP server
mcp = FastMCP("sectest")

# === UTILITY FUNCTIONS ===

def run_command(cmd: list, timeout: int = 300) -> str:
    """Execute a local command (list) capturing output."""
    try:
        # Avoid logging secrets - log only command outline
        logger.info(f"Running command: {' '.join(cmd[:3])} ...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors='replace'
        )
        output = result.stdout if result.stdout else result.stderr
        return output.strip() if output else "Command completed with no output"
    except subprocess.TimeoutExpired:
        return f"⏱️ Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return f"❌ Error executing command: {str(e)}"

def _try_key_based_ssh(remote_cmd: str, timeout: int = 600) -> (bool, str):
    """Try key-based SSH using the system ssh client. Returns (success, output)."""
    ssh_cmd = [
        "ssh",
        "-i", KALI_VM_KEY_PATH,
        "-p", str(KALI_VM_PORT),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        "-o", "BatchMode=yes",   # fail fast if password required
        f"{KALI_VM_USER}@{KALI_VM_HOST}",
        remote_cmd
    ]
    output = run_command(ssh_cmd, timeout=timeout)
    # crude check: if permission denied, treat as failure
    if re.search(r'Permission denied', output, re.IGNORECASE) or output.startswith('❌ SSH error'):
        return False, output
    return True, output

def _paramiko_ssh(remote_cmd: str, password: str, timeout: int = 60) -> str:
    """Execute remote_cmd using Paramiko (password auth)."""
    if not _HAS_PARAMIKO:
        return "❌ Paramiko not installed. Install with `pip install paramiko` to use password auth."
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=KALI_VM_HOST,
            port=KALI_VM_PORT,
            username=KALI_VM_USER,
            password=password,
            allow_agent=False,
            look_for_keys=False,
            timeout=10
        )
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        client.close()
        result = (out or "") + (err or "")
        return result.strip() if result else "Command completed with no output"
    except paramiko.AuthenticationException:
        return "❌ Authentication failed (Paramiko). Check username/password."
    except Exception as e:
        return f"❌ Paramiko SSH error: {e}"

def run_ssh_command(command: str = "", args: str = "") -> str:
    """
    Execute command on Kali VM via SSH.
    Behavior:
      1. If key path exists and no explicit password provided, try key-based SSH (fast).
      2. If key-based fails or a password is provided (KALI_VM_PASS or interactive), use Paramiko password auth.
    """
    if not command.strip():
        return "❌ Error: Command is required"

    full_cmd = f"{command} {args}".strip()
    logger.warning(f"⚠️ Executing command: {full_cmd}")

    # First try key-based ssh if key file exists and is readable
    if os.path.exists(KALI_VM_KEY_PATH) and not KALI_VM_PASS:
        success, output = _try_key_based_ssh(full_cmd, timeout=600)
        if success:
            return f"✅ Command executed (key auth):\n\n{output}"
        else:
            logger.info("Key-based SSH failed or returned permission denied. Will attempt password auth if available.")
            logger.debug(f"Key-based SSH output: {output}")

    # If we reach here, either key isn't present, failed, or a password was provided
    password = KALI_VM_PASS
    if not password:
        # Prompt user interactively (only if running in a TTY)
        if sys.stdin.isatty():
            try:
                password = getpass.getpass(f"SSH password for {KALI_VM_USER}@{KALI_VM_HOST}: ")
            except Exception as e:
                return f"❌ Unable to read password interactively: {e}"
        else:
            return ("❌ No key auth succeeded and no password provided. "
                    "Set KALI_VM_PASS environment variable or run interactively to enter a password.")

    # Use Paramiko for password authentication
    paramiko_out = _paramiko_ssh(full_cmd, password, timeout=600)
    if paramiko_out.startswith("❌"):
        return f"❌ Password-based SSH failed:\n\n{paramiko_out}"
    return f"✅ Command executed (password auth):\n\n{paramiko_out}"

# === MCP TOOL DEFINITIONS ===

@mcp.tool()
async def execute(command: str = "", args: str = "") -> str:
    """Execute any command on Kali VM via SSH."""
    return run_ssh_command(command, args)

@mcp.tool()
async def help_command(command: str = "") -> str:
    """Show basic help manual for a tool."""
    if not command.strip():
        return "❌ Error: Command required"
    return run_ssh_command(command, "--help")

@mcp.tool()
async def list_tools() -> str:
    """List installed packages on Kali VM."""
    return run_ssh_command("dpkg", "-l")

@mcp.tool()
async def test_connection() -> str:
    """Test SSH connection to Kali VM."""
    return run_ssh_command("echo 'Connection successful' && uname -a")

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Security Testing Tools MCP server...")
    logger.warning("⚠️ WARNING: This server executes commands on Kali VM.")
    logger.warning("⚠️ Only use on systems you own or have explicit permission to test.")
    if not _HAS_PARAMIKO:
        logger.info("NOTE: paramiko not installed. Password auth will not work until you `pip install paramiko`.")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
