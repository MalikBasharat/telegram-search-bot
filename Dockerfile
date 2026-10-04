# Python 3.12 Slim base image
FROM python:3.12-slim

# Set environment variables for Hugging Face Spaces & Cloud
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose Hugging Face Space default port
EXPOSE 7860

# Run 24/7 Bot & Crawler Service
CMD ["python", "main.py"]
