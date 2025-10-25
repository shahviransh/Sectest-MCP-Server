#!/usr/bin/env python3
"""
Security Testing Tools MCP Server - Provides penetration testing tools for educational purposes
"""
import os
import sys
import logging
import subprocess
import re
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

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
    """Sanitize user input to prevent command injection."""
    pattern = re.compile(allow_chars)
    sanitized = ''.join(pattern.findall(input_str))
    if sanitized != input_str:
        logger.warning(f"Input sanitized: '{input_str}' -> '{sanitized}'")
    return sanitized

def run_command(cmd: list, timeout: int = 300) -> str:
    """Execute a command safely with timeout."""
    try:
        logger.info(f"Executing command: {' '.join(cmd)}")
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

def validate_target(target: str) -> str:
    """Validate and sanitize target input."""
    if not target.strip():
        return ""
    
    # Remove dangerous characters
    sanitized = sanitize_input(target, r"[a-zA-Z0-9\.\-_:/]")
    
    # Basic validation
    if not sanitized:
        return ""
    
    return sanitized

# === MCP TOOLS ===

@mcp.tool()
async def nmap_scan(target: str = "", scan_type: str = "basic", ports: str = "") -> str:
    """Perform network scanning with nmap on specified target - scan_type can be basic, full, or stealth."""
    if not target.strip():
        return "❌ Error: Target is required (IP address or hostname)"
    
    target = validate_target(target)
    if not target:
        return "❌ Error: Invalid target format"
    
    try:
        # Build nmap command based on scan type
        if scan_type == "basic":
            cmd = ["nmap", "-sV", target]
        elif scan_type == "full":
            cmd = ["nmap", "-sV", "-sC", "-O", target]
        elif scan_type == "stealth":
            cmd = ["sudo", "nmap", "-sS", target]
        else:
            return f"❌ Error: Invalid scan type '{scan_type}'. Use: basic, full, or stealth"
        
        # Add port specification if provided
        if ports.strip():
            ports_clean = sanitize_input(ports, r"[0-9,\-]")
            if ports_clean:
                cmd.extend(["-p", ports_clean])
        
        output = run_command(cmd, timeout=600)
        return f"🔍 Nmap Scan Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"Nmap scan error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def nikto_scan(target: str = "", port: str = "80", ssl: str = "no") -> str:
    """Scan web server for vulnerabilities using Nikto - target should be hostname or IP, ssl can be yes or no."""
    if not target.strip():
        return "❌ Error: Target is required (hostname or IP address)"
    
    target = validate_target(target)
    if not target:
        return "❌ Error: Invalid target format"
    
    try:
        port_clean = sanitize_input(port, r"[0-9]")
        if not port_clean:
            port_clean = "80"
        
        cmd = ["nikto", "-h", target, "-p", port_clean]
        
        if ssl.lower() == "yes":
            cmd.append("-ssl")
        
        output = run_command(cmd, timeout=600)
        return f"🌐 Nikto Scan Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"Nikto scan error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def sqlmap_test(url: str = "", data: str = "", cookie: str = "") -> str:
    """Test URL for SQL injection vulnerabilities using sqlmap - url is required, data for POST params, cookie for session."""
    if not url.strip():
        return "❌ Error: URL is required"
    
    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        return "❌ Error: URL must start with http:// or https://"
    
    try:
        cmd = ["sqlmap", "-u", url, "--batch", "--level=1", "--risk=1"]
        
        if data.strip():
            cmd.extend(["--data", data])
        
        if cookie.strip():
            cmd.extend(["--cookie", cookie])
        
        logger.warning(f"⚠️ SQLMap testing URL: {url}")
        output = run_command(cmd, timeout=600)
        return f"🔒 SQLMap Test Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"SQLMap test error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def wpscan_scan(url: str = "", enumerate: str = "vp") -> str:
    """Scan WordPress site for vulnerabilities - url is WordPress site, enumerate can be vp for plugins, vt for themes, u for users."""
    if not url.strip():
        return "❌ Error: URL is required"
    
    if not url.startswith(("http://", "https://")):
        return "❌ Error: URL must start with http:// or https://"
    
    try:
        enumerate_clean = sanitize_input(enumerate, r"[a-z,]")
        if not enumerate_clean:
            enumerate_clean = "vp"
        
        cmd = ["wpscan", "--url", url, "--enumerate", enumerate_clean, "--no-banner"]
        
        output = run_command(cmd, timeout=600)
        return f"📊 WPScan Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"WPScan error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def dirb_scan(url: str = "", wordlist: str = "", extensions: str = "") -> str:
    """Discover hidden directories and files on web server - url is target, wordlist path optional, extensions like php,html optional."""
    if not url.strip():
        return "❌ Error: URL is required"
    
    if not url.startswith(("http://", "https://")):
        return "❌ Error: URL must start with http:// or https://"
    
    try:
        cmd = ["dirb", url]
        
        if wordlist.strip():
            wordlist_clean = sanitize_input(wordlist, r"[a-zA-Z0-9\.\-_/]")
            if wordlist_clean:
                cmd.append(wordlist_clean)
        
        if extensions.strip():
            ext_clean = sanitize_input(extensions, r"[a-zA-Z,]")
            if ext_clean:
                cmd.extend(["-X", ext_clean])
        
        output = run_command(cmd, timeout=600)
        return f"📁 Dirb Scan Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"Dirb scan error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def searchsploit_query(search_term: str = "", exact: str = "no") -> str:
    """Search ExploitDB for vulnerabilities and exploits - search_term is required, exact can be yes for exact match."""
    if not search_term.strip():
        return "❌ Error: Search term is required"
    
    try:
        search_clean = sanitize_input(search_term, r"[a-zA-Z0-9\s\.\-_]")
        if not search_clean:
            return "❌ Error: Invalid search term"
        
        cmd = ["searchsploit"]
        
        if exact.lower() == "yes":
            cmd.append("--exact")
        
        cmd.append(search_clean)
        
        output = run_command(cmd, timeout=60)
        return f"🔍 SearchSploit Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"SearchSploit error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def whois_lookup(domain: str = "") -> str:
    """Perform WHOIS lookup on domain or IP address."""
    if not domain.strip():
        return "❌ Error: Domain or IP address is required"
    
    domain = validate_target(domain)
    if not domain:
        return "❌ Error: Invalid domain format"
    
    try:
        cmd = ["whois", domain]
        output = run_command(cmd, timeout=30)
        return f"📋 WHOIS Information:\n\n{output}"
        
    except Exception as e:
        logger.error(f"WHOIS error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def dns_lookup(domain: str = "", record_type: str = "A") -> str:
    """Perform DNS lookup - domain required, record_type can be A, AAAA, MX, NS, TXT, CNAME."""
    if not domain.strip():
        return "❌ Error: Domain is required"
    
    domain = validate_target(domain)
    if not domain:
        return "❌ Error: Invalid domain format"
    
    try:
        record_clean = sanitize_input(record_type, r"[A-Z]").upper()
        if not record_clean:
            record_clean = "A"
        
        cmd = ["dig", domain, record_clean, "+short"]
        output = run_command(cmd, timeout=30)
        
        if not output or output == "Command completed with no output":
            return f"⚠️ No {record_clean} records found for {domain}"
        
        return f"🌐 DNS Lookup ({record_clean} records):\n\n{output}"
        
    except Exception as e:
        logger.error(f"DNS lookup error: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def install_tool(tool_name: str = "") -> str:
    """Install additional security tool from Kali repositories - requires confirmation and tool must be in Kali repos."""
    if not tool_name.strip():
        return "❌ Error: Tool name is required"
    
    tool_clean = sanitize_input(tool_name, r"[a-zA-Z0-9\-_]")
    if not tool_clean:
        return "❌ Error: Invalid tool name"
    
    try:
        logger.warning(f"⚠️ Installation requested for: {tool_clean}")
        
        # Search for package first
        search_cmd = ["apt-cache", "search", tool_clean]
        search_result = run_command(search_cmd, timeout=30)
        
        if not search_result or search_result == "Command completed with no output":
            return f"❌ Tool '{tool_clean}' not found in Kali repositories"
        
        return f"📦 Tool found in repositories:\n\n{search_result}\n\n⚠️ To install, use: sudo apt-get install {tool_clean}\n\nNote: Installation requires manual confirmation due to security restrictions."
        
    except Exception as e:
        logger.error(f"Tool search error: {e}")
        return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Security Testing Tools MCP server...")
    logger.warning("⚠️ This server provides powerful security testing tools")
    logger.warning("⚠️ Only use on systems you own or have explicit permission to test")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)