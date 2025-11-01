#!/usr/bin/env python3
"""
Security Testing Tools MCP Server with full LLM command access.
Commands are executed remotely on Kali VM via SSH.
"""
import os
import sys
import logging
import subprocess
import re

from mcp.server.fastmcp import FastMCP

# === CONFIGURATION ===
KALI_VM_USER = os.environ.get("KALI_VM_USER", "viransh")
KALI_VM_HOST = os.environ.get("KALI_VM_HOST", "host.docker.internal")
KALI_VM_KEY_PATH = os.environ.get("KALI_VM_KEY_PATH", "/home/mcpuser/.ssh/id_rsa")
KALI_VM_PORT = os.environ.get("KALI_VM_PORT", "2222")

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
    """Execute a command via SSH, capturing output."""
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
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

def run_ssh_command(command: str = "", args: str = "") -> str:
    """
    Execute command on Kali VM via SSH.
    """
    if not command.strip():
        return "❌ Error: Command is required"

    full_cmd = f"{command} {args}".strip()
    logger.warning(f"⚠️ Executing command: {full_cmd}")

    # Build SSH command for Kali VM
    ssh_cmd = [
        "ssh",
        "-i", KALI_VM_KEY_PATH,
        "-p", KALI_VM_PORT,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        f"{KALI_VM_USER}@{KALI_VM_HOST}",
        full_cmd
    ]

    # Execute command
    output = run_command(ssh_cmd, timeout=600)
    return f"✅ Command executed:\n\n{output}"

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
    return run_ssh_command("echo", "'Connection successful' && uname -a")

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Security Testing Tools MCP server...")
    logger.warning("⚠️ WARNING: This server executes commands on Kali VM.")
    logger.warning("⚠️ Only use on systems you own or have explicit permission to test.")

    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)