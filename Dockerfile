# Use Kali Linux rolling as base
FROM kalilinux/kali-rolling:latest

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Update and install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip \
    # Network scanning
    nmap masscan rustscan \
    # Web scanning
    nikto sqlmap wpscan whatweb wafw00f \
    # Directory bruteforce
    dirb gobuster ffuf feroxbuster \
    # Exploitation
    exploitdb metasploit-framework \
    # Password attacks
    hydra john hashcat crunch \
    # Wireless (if needed)
    aircrack-ng reaver wifite \
    # Enumeration
    enum4linux smbclient rpcclient \
    # SSL/TLS
    sslyze testssl.sh \
    # Subdomain enumeration
    sublist3r amass \
    # Web proxies
    burpsuite zaproxy \
    # Utilities
    git curl wget net-tools dnsutils whois \
    netcat-traditional socat \
    && rm -rf /var/lib/apt/lists/*

# Update exploitdb
RUN searchsploit -u || true

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy the server code
COPY sectest_server.py .

# Create non-root user
RUN useradd -m -u 1000 -G sudo mcpuser && \
    chown -R mcpuser:mcpuser /app && \
    echo "mcpuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python3", "sectest_server.py"]