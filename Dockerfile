# ---- Base image ----
FROM python:3.10-slim

# ---- Set environment variables ----
ENV INSIGHTFACE_HOME=/app/insightface_data \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---- Install OS dependencies ----
# Cần thiết cho OpenCV (headless) và InsightFace/ONNX Runtime trên Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Set working directory ----
WORKDIR /app

# ---- Copy requirements first (layer caching) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy source code ----
COPY . .

# ---- Download InsightFace model during build ----
RUN python download_model.py

# ---- Expose port ----
EXPOSE 8000

# ---- Start server ----
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
