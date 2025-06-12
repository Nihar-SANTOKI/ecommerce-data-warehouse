FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements first for better Docker layer caching
COPY config/requirements.txt /tmp/requirements.txt

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Copy application code
COPY . /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV DBT_PROFILES_DIR=/root/.dbt
ENV PYTHONUNBUFFERED=1

# Create dbt profiles directory
RUN mkdir -p /root/.dbt

CMD ["tail", "-f", "/dev/null"]