# Stage 1: Builder
FROM python:3.10-slim AS builder

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install Miniconda for managing scientific packages
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh

# Add conda to the PATH
ENV PATH=/opt/conda/bin:$PATH

# Create conda environment with Python 3.10 and install RDKit
RUN conda create -y -n rdkit-env python=3.10 && \
    conda install -y -n rdkit-env -c conda-forge rdkit=2023.03

# Set shell to use conda environment
SHELL ["conda", "run", "-n", "rdkit-env", "/bin/bash", "-c"]

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM builder AS final

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Run the FastAPI application with Gunicorn
CMD ["conda", "run", "-n", "rdkit-env", "gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]