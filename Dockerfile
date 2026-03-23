FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (OpenCV headless용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 업로드 디렉토리
RUN mkdir -p /tmp/uploads
