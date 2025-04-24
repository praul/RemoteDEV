FROM ubuntu:latest

# Install devtools and SSH server
RUN apt-get update && \
    apt-get install -y \
      openssh-server \
      sshfs \
      php \
      npm \
      git \
      curl \
      sudo \
      ca-certificates \
      jq \
      python3 \
      python3-pip \
      python3-venv && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y sshpass



# Create virtual environment and install watchdog
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir --upgrade pip && /venv/bin/pip install watchdog uv


# Create SSH directory and set up SSH server
RUN mkdir /var/run/sshd

# Add a user for SSH access
RUN useradd -ms /bin/bash devuser && \
    echo 'devuser:devpass' | chpasswd && \
    adduser devuser sudo

# Copy entrypoint script
COPY entrypoint.py /entrypoint.py

# Install user software
WORKDIR /home/devuser
USER devuser
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MCP SSH Search server dependencies and copy code
USER root
COPY mcp_ssh_search /mcp_ssh_search
RUN /venv/bin/pip install -r /mcp_ssh_search/requirements.txt

# Expose SSH port
EXPOSE 22

# Start entrypoint
ENTRYPOINT ["/venv/bin/python", "/entrypoint.py"]