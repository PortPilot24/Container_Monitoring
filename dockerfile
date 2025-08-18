FROM python:3.11-slim AS base

# 0) 런타임 기본 옵션
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul

# 1) OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) 의존성 먼저 설치
COPY requirements.txt ./
RUN python -m pip install --upgrade "pip<25"
RUN pip install -r requirements.txt

# 3) 앱 소스 복사
COPY . .

# 4) 비루트 실행 + 소유권 정리 (쓰기 필요 시 대비)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 5) 네트워크
EXPOSE 8000

# 6) 컨테이너 헬스체크 (애플리케이션이 뜨면 200을 기대)
#   - FastAPI에 /health 엔드포인트가 없다면 / 로 바꾸세요.
HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# 7) 실행
#   !!! 모듈 경로를 실제 구조에 맞게 교체하세요 !!!
#   예) main.py에 app=FastAPI(): "main:app"
#       src/app/main.py: "app.main:app" (PYTHONPATH 조정 필요할 수 있음)
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
