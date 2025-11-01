#!/usr/bin/env python3
"""
Security Testing Tools MCP Server with full LLM command access.
Commands are executed remotely on Kali VM or locally after explicit approval.
"""
import os
import sys
import logging
import subprocess
import re
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

# === CONFIGURATION ===
KALI_VM_USER = "mcpuser"
KALI_VM_HOST = "192.168.56.101"   # Set your Kali VM IP here
KALI_VM_KEY_PATH = "/app/mcp_id_rsa"  # Mounted SSH private key in Docker

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

def sanitize_input(input_str: str, allow_chars: str = r"[a-zA-Z0-9\.\-_:/]") -> str:
    """Sanitize input for logging or display purposes (not for security enforcement)."""
    pattern = re.compile(allow_chars)
    sanitized = ''.join(pattern.findall(input_str))
    if sanitized != input_str:
        logger.warning(f"Input sanitized for display: '{input_str}' -> '{sanitized}'")
    return sanitized

def run_command(cmd: list, timeout: int = 300) -> str:
    """Execute a command locally or via SSH, capturing output."""
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

def run_command_interactive(command: str = "", args: str = "") -> str:
    """
    Execute ANY command (LLM full access) with explicit approval prompt.
    Can run locally or on remote Kali VM via SSH.
    """
    if not command.strip():
        return "❌ Error: Command is required"

    full_cmd = f"{command} {args}".strip()
    logger.warning(f"⚠️ LLM requested command: {full_cmd}")

    # Prompt for approval (manual input)
    approval = input(f"Approve execution of command? (yes/no): ").strip().lower()
    if approval != "yes":
        return "❌ Command execution denied"

    # Build SSH command for Kali VM
    ssh_cmd = [
        "ssh",
        "-i", KALI_VM_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{KALI_VM_USER}@{KALI_VM_HOST}",
        "--", command
    ]
    if args.strip():
        ssh_cmd.extend(args.split())

    # Execute command
    output = run_command(ssh_cmd, timeout=600)
    return f"✅ Command executed:\n\n{output}"

# === MCP TOOL DEFINITIONS ===

@mcp.tool()
async def execute(command: str = "", args: str = "") -> str:
    """
    MCP tool to execute any command with LLM.
    command: main command (tool, script, etc.)
    args: space-separated arguments
    """
    return run_command_interactive(command, args)

@mcp.tool()
async def help_command(command: str = "") -> str:
    """Show basic help/manual for a tool."""
    if not command.strip():
        return "❌ Error: Command required"
    try:
        cmd = [command, "--help"]
        return run_command_interactive(cmd[0], " ".join(cmd[1:]))
    except Exception as e:
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def list_tools() -> str:
    """List installed packages on Kali VM."""
    return run_command_interactive("dpkg", "-l")

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Security Testing Tools MCP server (full LLM access)...")
    logger.warning("⚠️ WARNING: LLM can execute ANY command, approval is required for safety.")
    logger.warning("⚠️ Only use on systems you own or have explicit permission to test.")

    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
