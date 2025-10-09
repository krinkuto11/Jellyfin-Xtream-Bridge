# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 xtream && \
    mkdir -p /app /config && \
    chown -R xtream:xtream /app /config

# Copy virtual environment from builder
COPY --from=builder --chown=xtream:xtream /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=xtream:xtream src/ ./src/
COPY --chown=xtream:xtream start_server.sh .
COPY --chown=xtream:xtream config/config.json.example /config/

# Make start script executable
RUN chmod +x start_server.sh

# Switch to non-root user
USER xtream

# Expose the default port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/player_api.php', timeout=5)" || exit 1

# Run the application
CMD ["python", "src/xtream_server.py"]
