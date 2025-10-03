# Use Python 3.10 slim for better performance and smaller image
FROM python:3.10-slim

# Install system deps: ffmpeg for pydub, libsndfile for broader audio support
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsndfile1 libopenblas-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set working dir
WORKDIR /app

# Copy deps and install (including uvicorn[standard] for better async perf)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard]

# Set up user (HF requirement)
RUN useradd -m -u 1000 user
USER user

# Optimized environment variables for HF Spaces Free CPU
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

WORKDIR $HOME/app

# Copy app
COPY --chown=user . .

# Expose port
EXPOSE 7860

# Run app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]