# Asterisk Docker image for integration testing
FROM debian:bookworm-slim

# Install Asterisk and dependencies
RUN apt-get update && \
    apt-get install -y \
    asterisk \
    asterisk-config \
    asterisk-modules \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /etc/asterisk /var/lib/asterisk /var/log/asterisk /var/run/asterisk && \
    chown -R asterisk:asterisk /etc/asterisk /var/lib/asterisk /var/log/asterisk /var/run/asterisk

# Copy test configuration files
COPY asterisk.conf /etc/asterisk/asterisk.conf
COPY manager.conf /etc/asterisk/manager.conf
COPY pjsip.conf /etc/asterisk/pjsip.conf
COPY extensions.conf /etc/asterisk/extensions.conf

# Set proper permissions
RUN chown asterisk:asterisk /etc/asterisk/*.conf

# Expose AMI and SIP ports
EXPOSE 5038 5060/udp

# Run Asterisk in foreground
CMD ["/usr/sbin/asterisk", "-f", "-vvv", "-U", "asterisk", "-G", "asterisk"]
