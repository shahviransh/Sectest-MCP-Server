# Security Testing Tools MCP Server - Implementation Guide

## Overview

This MCP server provides penetration testing tools through a Kali Linux Docker container. It's designed for educational purposes and authorized security testing.

## Security Architecture

### Input Sanitization

All user inputs pass through `sanitize_input()` which:
- Removes potentially dangerous characters
- Validates format matches expected patterns
- Logs any modifications for audit
- Returns empty string if completely invalid

### Execution Safety

- **Non-root execution**: Default user is `mcpuser` (UID 1000)
- **Sudo whitelist**: Only specific tools allowed with sudo
- **Timeout protection**: All commands have 5-10 minute timeouts
- **No shell injection**: Commands built as arrays, not strings
- **Error isolation**: Exceptions caught and returned as formatted strings

### Container Isolation

- Network isolated by default (user controls port exposure)
- No persistent state between runs
- Limited filesystem access
- Resource constraints via Docker

## Tool Implementation Patterns

### Standard Tool Pattern
```python
@mcp.tool()
async def tool_name(param: str = "") -> str:
    """Single line description with param details."""
    
    # 1. Validate required parameters
    if not param.strip():
        return "❌ Error: Parameter is required"
    
    # 2. Sanitize inputs
    param_clean = validate_target(param)
    if not param_clean:
        return "❌ Error: Invalid parameter format"
    
    # 3. Build command safely
    try:
        cmd = ["tool", param_clean]
        
        # 4. Execute with timeout
        output = run_command(cmd, timeout=600)
        
        # 5. Return formatted result
        return f"✅ Tool Results:\n\n{output}"
        
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return f"❌ Error: {str(e)}"
```

### Allowed Character Patterns

- **Hostnames/IPs**: `[a-zA-Z0-9\.\-_:/]`
- **Ports**: `[0-9,\-]`
- **File extensions**: `[a-zA-Z,]`
- **Tool names**: `[a-zA-Z0-9\-_]`
- **Search terms**: `[a-zA-Z0-9\s\.\-_]`

## Adding New Security Tools

### Step 1: Add to Dockerfile
```dockerfile
RUN apt-get install -y toolname
```

### Step 2: Configure Sudo (if needed)
```dockerfile
RUN echo "mcpuser ALL=(ALL) NOPASSWD: /usr/bin/toolname" >> /etc/sudoers
```

### Step 3: Implement Tool Function
```python
@mcp.tool()
async def new_tool(target: str = "", option: str = "") -> str:
    """Tool description - specify all parameters."""
    
    if not target.strip():
        return "❌ Error: Target is required"
    
    target = validate_target(target)
    if not target:
        return "❌ Error: Invalid target"
    
    try:
        cmd = ["toolname", target]
        
        if option.strip():
            option_clean = sanitize_input(option, r"[a-zA-Z0-9\-]")
            cmd.extend(["--option", option_clean])
        
        output = run_command(cmd, timeout=300)
        return f"🔍 Results:\n\n{output}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Step 4: Update Catalog

Add tool to `custom.yaml`:
```yaml
tools:
  - name: new_tool
```

## Error Handling Strategy

1. **Input Validation Errors**: Return user-friendly message about requirements
2. **Command Execution Errors**: Log to stderr, return sanitized error message
3. **Timeout Errors**: Return clear timeout message with duration
4. **Permission Errors**: Indicate if sudo required or permission denied

## Testing Checklist

- [ ] Input sanitization prevents injection
- [ ] Invalid inputs return helpful errors
- [ ] Command timeouts work correctly
- [ ] Output is properly formatted
- [ ] Tool runs as non-root (or with sudo if needed)
- [ ] Logging captures important events
- [ ] Container builds successfully
- [ ] Tool appears in LLM

## Common Issues

### Tool Not Found

**Symptom**: "command not found" error
**Solution**: Verify tool installed in Dockerfile, rebuild image

### Permission Denied

**Symptom**: Permission errors during scan
**Solution**: Add tool to sudoers in Dockerfile with NOPASSWD

### Timeout Too Short

**Symptom**: Scans abort early
**Solution**: Increase timeout parameter in run_command()

### Invalid Characters in Input

**Symptom**: Command fails or behaves unexpectedly
**Solution**: Adjust regex pattern in sanitize_input() call

## Best Practices

1. **Always sanitize inputs** - Never trust user input
2. **Use command arrays** - Never construct shell strings
3. **Validate first** - Check parameters before building commands
4. **Log everything** - Use logger for debugging and audit
5. **Timeout all commands** - Prevent hanging operations
6. **Return strings** - All tools must return formatted strings
7. **Use emojis** - Make output scannable and clear
8. **Handle exceptions** - Catch and format all errors

## Maintenance

### Updating ExploitDB

The Dockerfile runs `searchsploit -u` during build. To update:
```bash
docker build --no-cache -t sectest-mcp-server .
```

### Updating Kali Packages
```dockerfile
RUN apt-get update && apt-get upgrade -y
```

Then rebuild the image.

### Adding Custom Scripts

1. Create script file
2. COPY into Dockerfile
3. Set executable permissions
4. Add tool function to call script

## Performance Optimization

- Use `--no-install-recommends` in apt-get
- Clean apt cache: `rm -rf /var/lib/apt/lists/*`
- Minimize layers in Dockerfile
- Consider multi-stage builds for smaller images

## Compliance Notes

This server is designed for authorized testing only. Ensure:

- Documentation includes legal warnings
- Logging captures all scan activities
- User confirms targets are authorized
- No credentials are stored or logged
- Audit trail is maintainable