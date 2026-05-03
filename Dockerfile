# ---- Base image ----
FROM python:3.10-slim

# ---- Set environment variables ----
# Sửa lại đường dẫn lưu model vào thư mục home của user mới
ENV INSIGHTFACE_HOME=/home/user/app/insightface_data \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# ---- Install OS dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Thiết lập User (Bắt buộc cho Hugging Face) ----
# HF không cho phép chạy quyền root để đảm bảo bảo mật
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# ---- Copy requirements & Install ----
# Chú ý: Cần đổi quyền sở hữu file cho user mới
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Copy source code ----
COPY --chown=user . .

# ---- Download InsightFace model ----
RUN python download_model.py

# ---- Expose port ----
# HF mặc định dùng 7860, không dùng 8000
EXPOSE 7860

# ---- Start server ----
# Ép port về 7860 để HF có thể nhận diện được service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]