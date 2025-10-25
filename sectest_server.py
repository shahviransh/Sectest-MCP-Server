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

#!/usr/bin/env python3
"""
Add these tools to your sectest_server.py file (after the existing tools, before the SERVER STARTUP section)
"""

@mcp.tool()
async def run_command_safe(command: str = "", args: str = "") -> str:
    """Execute a Kali tool command safely - command is the tool name, args are the parameters separated by spaces."""
    if not command.strip():
        return "❌ Error: Command is required"
    
    # Whitelist of allowed commands (expand this list as needed)
    allowed_commands = [
        "nmap", "nikto", "sqlmap", "wpscan", "dirb", "searchsploit",
        "whois", "dig", "host", "nslookup", "curl", "wget",
        "hydra", "john", "hashcat", "metasploit", "msfconsole",
        "gobuster", "ffuf", "whatweb", "wafw00f", "sublist3r",
        "masscan", "zap-cli", "commix", "sslyze", "testssl",
        "enum4linux", "smbclient", "rpcclient", "crackmapexec",
        "responder", "impacket-scripts", "bloodhound", "neo4j",
        "apt-cache", "dpkg", "ls", "cat", "head", "tail", "grep"
    ]
    
    command_clean = sanitize_input(command, r"[a-zA-Z0-9\-_]")
    
    # Check if command is in whitelist
    if command_clean not in allowed_commands:
        return f"❌ Error: Command '{command_clean}' not in allowed list. Safe commands: {', '.join(allowed_commands[:10])}..."
    
    try:
        cmd = [command_clean]
        
        # Parse arguments safely
        if args.strip():
            # Split args and sanitize each
            arg_list = args.split()
            for arg in arg_list:
                # Allow common argument patterns
                arg_clean = sanitize_input(arg, r"[a-zA-Z0-9\.\-_:/=]")
                if arg_clean:
                    cmd.append(arg_clean)
        
        logger.info(f"Executing whitelisted command: {' '.join(cmd)}")
        output = run_command(cmd, timeout=600)
        return f"⚡ Command Output:\n\n{output}"
        
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def install_kali_tool(tool_name: str = "", auto_yes: str = "no") -> str:
    """Install a tool from Kali repositories - tool_name required, auto_yes can be yes to skip confirmation."""
    if not tool_name.strip():
        return "❌ Error: Tool name is required"
    
    tool_clean = sanitize_input(tool_name, r"[a-zA-Z0-9\-_]")
    if not tool_clean:
        return "❌ Error: Invalid tool name"
    
    try:
        # First, search for the package
        search_cmd = ["apt-cache", "search", tool_clean]
        search_result = run_command(search_cmd, timeout=30)
        
        if not search_result or search_result == "Command completed with no output":
            return f"❌ Tool '{tool_clean}' not found in Kali repositories"
        
        # Show what was found
        result = f"📦 Found in repositories:\n\n{search_result}\n\n"
        
        # If auto_yes, attempt installation
        if auto_yes.lower() == "yes":
            logger.warning(f"⚠️ Installing tool: {tool_clean}")
            install_cmd = ["sudo", "apt-get", "install", "-y", tool_clean]
            install_result = run_command(install_cmd, timeout=300)
            result += f"📥 Installation output:\n\n{install_result}"
        else:
            result += f"⚠️ To install, run: install_kali_tool with tool_name='{tool_clean}' and auto_yes='yes'"
        
        return result
        
    except Exception as e:
        logger.error(f"Installation error: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def list_installed_tools(category: str = "all") -> str:
    """List installed Kali tools - category can be all, web, network, exploit, password, wireless, forensics."""
    try:
        if category == "all":
            cmd = ["dpkg", "-l"]
        else:
            # Search for tools in specific categories
            category_keywords = {
                "web": "web",
                "network": "nmap|netcat|wireshark",
                "exploit": "metasploit|exploit|sqlmap",
                "password": "john|hydra|hashcat|crunch",
                "wireless": "aircrack|reaver|wifite",
                "forensics": "autopsy|volatility|binwalk"
            }
            
            if category in category_keywords:
                cmd = ["dpkg", "-l"]
                output = run_command(cmd, timeout=30)
                # Filter output by keywords
                lines = output.split('\n')
                filtered = [line for line in lines if any(kw in line.lower() for kw in category_keywords[category].split('|'))]
                return f"🔧 Installed tools ({category}):\n\n" + '\n'.join(filtered)
            else:
                return f"❌ Invalid category. Use: all, web, network, exploit, password, wireless, forensics"
        
        output = run_command(cmd, timeout=30)
        # Just show first 50 lines to avoid overwhelming output
        lines = output.split('\n')[:50]
        return f"🔧 Installed packages (first 50):\n\n" + '\n'.join(lines) + "\n\n... (use category filter for specific tools)"
        
    except Exception as e:
        logger.error(f"List tools error: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def get_tool_help(tool_name: str = "") -> str:
    """Get help information for a specific tool - shows usage and options."""
    if not tool_name.strip():
        return "❌ Error: Tool name is required"
    
    tool_clean = sanitize_input(tool_name, r"[a-zA-Z0-9\-_]")
    if not tool_clean:
        return "❌ Error: Invalid tool name"
    
    try:
        # Try common help flags
        help_flags = ["--help", "-h", "-help", "help"]
        
        for flag in help_flags:
            cmd = [tool_clean, flag]
            output = run_command(cmd, timeout=30)
            
            # If we got useful output, return it
            if output and len(output) > 50 and "Error" not in output:
                return f"📖 Help for {tool_clean}:\n\n{output}"
        
        # If no help flag worked, try man page
        cmd = ["man", tool_clean]
        output = run_command(cmd, timeout=30)
        
        if output and len(output) > 50:
            # Limit man page output
            lines = output.split('\n')[:100]
            return f"📖 Manual for {tool_clean}:\n\n" + '\n'.join(lines)
        
        return f"⚠️ No help available for '{tool_clean}'. Tool may not be installed or may not have help documentation."
        
    except Exception as e:
        logger.error(f"Get help error: {e}")
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