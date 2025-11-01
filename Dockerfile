# Use Python base (slim to reduce size)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Avoid prompts during package install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies and SSH client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    openssh-client \
    sudo \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY sectest_server.py .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

RUN mkdir -p /home/mcpuser/.ssh && \
    chown mcpuser:mcpuser /home/mcpuser/.ssh && \
    chmod 700 /home/mcpuser/.ssh

COPY kali_mcp_key /home/mcpuser/.ssh/id_rsa

RUN chown mcpuser:mcpuser /home/mcpuser/.ssh/id_rsa && \
    chmod 600 /home/mcpuser/.ssh/id_rsa

USER mcpuser

# Expose working directory for SSH key mount
VOLUME ["/app"]

# Command to run the server
CMD ["python3", "sectest_server.py"]
