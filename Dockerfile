# Use Kali Linux rolling as base
FROM kalilinux/kali-rolling:latest

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# First update and install basic tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install network scanning tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nmap \
    masscan \
    && rm -rf /var/lib/apt/lists/*

# Install web scanning tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nikto \
    sqlmap \
    wpscan \
    whatweb \
    wafw00f \
    && rm -rf /var/lib/apt/lists/*

# Install directory brute force tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    dirb \
    gobuster \
    ffuf \
    && rm -rf /var/lib/apt/lists/*

# Install exploitation tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    exploitdb \
    && rm -rf /var/lib/apt/lists/*

# Install password attack tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    hydra \
    john \
    crunch \
    && rm -rf /var/lib/apt/lists/*

# Install enumeration tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    enum4linux \
    smbclient \
    && rm -rf /var/lib/apt/lists/*

# Install network utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    net-tools \
    dnsutils \
    whois \
    netcat-traditional \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Update exploitdb
RUN searchsploit -u || true

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy the server code
COPY sectest_server.py .

# Create non-root user with sudo access
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app && \
    apt-get update && \
    apt-get install -y sudo && \
    echo "mcpuser ALL=(ALL) NOPASSWD: /usr/bin/nmap, /usr/bin/nikto, /usr/bin/sqlmap, /usr/bin/wpscan, /usr/bin/dirb, /usr/bin/masscan, /usr/bin/gobuster, /usr/bin/ffuf, /usr/bin/hydra, /usr/bin/apt-get" >> /etc/sudoers && \
    rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python3", "sectest_server.py"]