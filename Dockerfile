# Dockerfile: build this first before running docker-compose up

# Use the latest Airflow image as the base image (use a specific version for stability)
FROM apache/airflow:2.9.0

# Switch to root user to install system packages
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
    # --no-install-recommends: avoid installing unnecessary extra packages
    # apt-get clean: reduce image size by cleaning cache
    # rm -rf /var/lib/apt/lists/*: remove package lists to further reduce image size

# Switch back to airflow user (important for security & Airflow compatibility)
USER airflow

# Install Python dependencies (if any)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# --no-cache-dir to reduce image size by not caching packages