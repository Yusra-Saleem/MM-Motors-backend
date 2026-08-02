FROM python:3.11-slim

# Note: This Dockerfile runs as a non-root user. Because .env is ignored in .dockerignore for security,
# if running this container directly (outside docker-compose), you must pass the env-file:
#   docker build -t mmmotors-backend .
#   docker run -p 8000:8000 --env-file .env mmmotors-backend


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /code

# Install system dependencies required for image processing (libavif for AVIF support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavif-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a non-root user and switch to it for Hugging Face compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy application files with proper ownership
COPY --chown=user . $HOME/app

# Expose the default Hugging Face Space port
EXPOSE 8000

# Run migrations and start FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]




