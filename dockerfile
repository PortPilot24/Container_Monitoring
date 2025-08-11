FROM python:3.11-slim AS base

# 기본 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 먼저 복사 (캐시)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# 모델 파일이 여기 있다고 가정: /app/models/best_lstm_model.h5
# 포트
EXPOSE 8000

# 비루트 실행
RUN useradd -m appuser
USER appuser

# uvicorn 실행 (gunicorn+uvicorn workers도 가능)
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
