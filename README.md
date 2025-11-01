# Security Testing Tools MCP Server

A Model Context Protocol (MCP) server that provides secure access to security testing tools running on a Kali Linux VM via SSH.

## ⚠️ LEGAL WARNING

**FOR AUTHORIZED TESTING ONLY**

This server is designed for educational purposes and authorized security testing. Using these tools against systems you don't own or have explicit written permission to test is illegal. Always:

- Obtain written authorization before testing
- Stay within the scope of authorization
- Follow responsible disclosure practices
- Comply with all applicable laws

## Purpose

This MCP server provides a secure interface for AI assistants to execute security testing tools on a remote Kali Linux VM. All commands are executed via SSH with proper authentication.

## Features

### Current Implementation

- **`All Tools`**: Runs all installed security tools.

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Kali Linux VM with SSH access configured
- SSH key pair for authentication
- Network connectivity between Docker and Kali VM

## Kali VM Setup

Before using this server, set up your Kali Linux VM:

1. **Install Kali Linux** (VirtualBox, VMware, or physical machine)

2. **Configure SSH**:
```bash
   sudo apt update
   sudo apt install openssh-server
   sudo systemctl enable ssh
   sudo systemctl start ssh
```

3. **Create SSH key pair** (on your host machine):
```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/kali_mcp_key
```

4. **Copy public key to Kali VM**:
```bash
   ssh-copy-id -i ~/.ssh/kali_mcp_key.pub kali@<KALI_VM_IP>
```

5. **Test SSH connection**:
```bash
   ssh -i ~/.ssh/kali_mcp_key kali@<KALI_VM_IP>
```

6. **Install security tools** (if not already installed):
```bash
   sudo apt install nmap nikto sqlmap wpscan dirb exploitdb
```

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In LLM Desktop, you can ask:

- "Scan 192.168.1.100 with nmap to find open ports"
- "Run a Nikto scan on http://testsite.local"
- "Search for WordPress vulnerabilities with WPScan on http://example.com"
- "Use dirb to find hidden directories on http://target.com"
- "Search for Apache exploits with searchsploit"
- "Test http://vulnerable.com for SQL injection with SQLMap"
- "List all security tools installed on the Kali VM"
- "Test the connection to the Kali VM"

## Architecture
```
LLM Desktop → MCP Gateway → SecTest MCP Server → SSH → Kali Linux VM
                                         ↓
                               Docker Desktop Secrets
                          (KALI_VM_HOST, KALI_VM_USER)
                                         ↓
                                 SSH Private Key
                                   (mounted file)
```

## Development

### Local Testing
```bash
# Set environment variables for testing
export KALI_VM_HOST="192.168.56.101"
export KALI_VM_USER="kali"
export KALI_VM_KEY_PATH="/path/to/ssh/key"

# Run directly
python sectest_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python sectest_server.py
```

### Adding New Tools

1. Add the function to `sectest_server.py`
2. Decorate with `@mcp.tool()`
3. Update the catalog entry with the new tool name
4. Rebuild the Docker image

## Troubleshooting

### SSH Connection Fails

- Verify Kali VM IP address is correct
- Check SSH service is running on Kali: `sudo systemctl status ssh`
- Verify SSH key permissions: `chmod 600 /path/to/key`
- Test SSH manually: `ssh -i /path/to/key user@host`
- Check firewall rules on Kali VM

### Tools Not Appearing

- Verify Docker image built successfully
- Check catalog and registry files
- Ensure LLM config includes custom catalog
- Restart LLM

### Command Timeouts

- Increase timeout values for long-running scans
- Check network connectivity
- Verify target is accessible from Kali VM

## Security Considerations

- SSH keys stored securely in Docker volumes
- Never hardcode credentials
- Running as non-root user in container
- SSH keys should have restrictive permissions (600)
- All commands logged for audit purposes
- Use strong SSH keys (minimum 2048-bit RSA or ed25519)

## Ethical Use Guidelines

1. **Authorization**: Always obtain written permission
2. **Scope**: Stay within authorized testing boundaries
3. **Documentation**: Keep detailed logs of all testing
4. **Disclosure**: Report vulnerabilities responsibly
5. **Legal Compliance**: Follow all applicable laws and regulations

## License

MIT License - For educational and authorized testing purposes only.