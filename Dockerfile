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


# Create virtual environment and install watchdog
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir --upgrade pip && /venv/bin/pip install watchdog


# Create SSH directory and set up SSH server
RUN mkdir /var/run/sshd

# Add a user for SSH access
RUN useradd -ms /bin/bash devuser && \
    echo 'devuser:devpass' | chpasswd && \
    adduser devuser sudo

# Copy entrypoint script
COPY entrypoint.py /entrypoint.py

EXPOSE 22

ENTRYPOINT ["/venv/bin/python", "/entrypoint.py"]