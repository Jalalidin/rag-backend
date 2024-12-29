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

# Install uv first
RUN pip install uv

# Copy only dependency files
COPY --chown=appuser:appuser pyproject.toml ./

# Create venv and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip sync requirements.txt

# Copy the application code into the container, excluding the .venv directory
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser openrouter_models.json ./

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD . .venv/bin/activate && uvicorn app.main:app --host "0.0.0.0" --port "8000" --reload 