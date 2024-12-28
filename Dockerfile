FROM python:3.11-slim-bullseye

# Create a non-root user early
RUN useradd -m -u 1000 appuser

WORKDIR /app
RUN chown appuser:appuser /app

# Set up Chinese mirrors for apt
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up pip to use Alibaba Cloud mirror
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml ./

# Install Python dependencies using uv and pip
RUN pip install --no-cache-dir uv
RUN uv venv
RUN . .venv/bin/activate && uv sync

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application using uv and activate the virtual environment
CMD . .venv/bin/activate && uvicorn app.main:app --host "0.0.0.0" --port "8000" --reload 