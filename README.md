# Security Testing Tools MCP Server

A Model Context Protocol (MCP) server that provides penetration testing and security assessment tools for educational purposes and controlled testing environments.

## ⚠️ IMPORTANT SECURITY NOTICE

**THIS SERVER CONTAINS POWERFUL SECURITY TESTING TOOLS**

- Only use on systems you own or have explicit written permission to test
- Unauthorized testing is illegal and unethical
- Tools can cause service disruption or data exposure
- Always obtain proper authorization before scanning
- Use responsibly and within legal boundaries

## Purpose

This MCP server provides a secure interface for AI assistants to perform web application penetration testing and security assessments in controlled environments. All tools run in an isolated Docker container with input sanitization and non-root execution.

## Features

### Current Implementation

- **`nmap_scan`** - Network port scanning and service detection (basic, full, or stealth modes)
- **`nikto_scan`** - Web server vulnerability scanning
- **`sqlmap_test`** - SQL injection vulnerability testing
- **`wpscan_scan`** - WordPress security scanning
- **`dirb_scan`** - Directory and file discovery on web servers
- **`searchsploit_query`** - Search ExploitDB for known vulnerabilities
- **`whois_lookup`** - Domain registration information lookup
- **`dns_lookup`** - DNS record queries (A, AAAA, MX, NS, TXT, CNAME)
- **`install_tool`** - Search for additional security tools in Kali repositories

### Security Features

- Input sanitization to prevent command injection
- Non-root user execution (except where necessary with sudo)
- Timeout protection on all commands
- Comprehensive logging
- Isolated Docker environment

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Adequate system resources for security scanning
- Legal authorization to test target systems

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In LLM, you can ask:

- "Run a basic nmap scan on 192.168.1.1"
- "Scan example.com with nikto on port 443 with SSL"
- "Test http://testsite.local/login.php for SQL injection"
- "Scan WordPress site at http://example.com for vulnerable plugins"
- "Find hidden directories on http://testsite.local"
- "Search exploitdb for Apache 2.4 vulnerabilities"
- "Look up DNS records for example.com"
- "Get WHOIS information for example.com"

## Architecture
```
LLM → MCP Gateway → SecTest MCP Server → Security Tools
                                       ↓
                              Kali Linux Container
                              (nmap, nikto, sqlmap, etc.)
```

## Development

### Local Testing
```bash
# Build and run the container
docker build -t sectest-mcp-server .
docker run -it sectest-mcp-server

# Test individual tools inside container
docker run -it sectest-mcp-server /bin/bash
nmap --version
nikto -Version
```

### Adding New Tools

1. Add tool installation to Dockerfile (apt-get install)
2. Add function to `sectest_server.py` with @mcp.tool() decorator
3. Implement input sanitization and validation
4. Update catalog entry with new tool name
5. Rebuild Docker image

## Troubleshooting

### Tools Not Appearing

- Verify Docker image built successfully: `docker images | grep sectest`
- Check catalog and registry files for syntax errors
- Ensure LLM config includes custom catalog
- Restart LLM completely
- Check logs: `docker logs <container_name>`

### Scan Failures

- Verify target is accessible from Docker container
- Check network connectivity: `docker run -it sectest-mcp-server ping target`
- Some scans require elevated privileges (use stealth mode carefully)
- Increase timeout for large scans

### Permission Errors

- Most tools run as non-root user
- Some operations (like SYN scans) require sudo
- Dockerfile configures necessary sudo permissions

## Security Considerations

- All inputs are sanitized to prevent command injection
- Commands execute with timeout protection
- Running as non-root user where possible
- Isolated in Docker container
- Comprehensive logging for audit trails
- No credentials stored or transmitted

## Legal and Ethical Use

**You are responsible for:**
- Obtaining proper authorization before testing
- Complying with all applicable laws
- Using tools ethically and responsibly
- Understanding the impact of security tests
- Respecting privacy and data protection laws

**Prohibited uses:**
- Testing systems without authorization
- Accessing data you're not authorized to access
- Causing service disruptions
- Any illegal activity

## Performance Notes

- Scans can take several minutes depending on scope
- Default timeout is 10 minutes per operation
- Large scans may require timeout adjustments
- Container uses ~500MB-1GB RAM during active scanning

## License

MIT License - Use at your own risk with proper authorization