# Dockerfile for Python Code Execution API
# This provides a containerized deployment for better security and isolation

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and CA certificates
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Fix CA certificates directory permissions
# Docker may restrict access to /etc/ssl/certs, so copy cert to accessible location
RUN update-ca-certificates \
    && cp /etc/ssl/cert.pem /usr/local/share/ca-certificates.crt \
    && chmod 644 /usr/local/share/ca-certificates.crt

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .

# Expose port
EXPOSE 8000

# Create non-root user for security
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Run the application
CMD ["python", "main.py"]
