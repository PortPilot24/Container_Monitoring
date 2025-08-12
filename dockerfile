FROM python:3.11-slim AS base

# 0) 런타임 안정화 옵션
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 1) OS deps (빌드/런타임 최소셋)
# - build-essential: 일부 패키지 빌드 시 필요(휠 없을 때 대비)
# - curl: 디버그/헬스체크 등 유틸
# - tzdata: 로컬 타임존 필요 시
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) 의존성 먼저 복사 + 설치
COPY requirements.txt ./
# pip 버전 과업데이트로 인한 충돌 회피(선택)
RUN python -m pip install --upgrade "pip<25"
RUN pip install -r requirements.txt

# 3) 앱 소스 복사
COPY . .

# 4) 비루트 실행
RUN useradd -m appuser
USER appuser

# 5) 네트워크
EXPOSE 8000

# 6) 실행
# ※ 네 프로젝트 구조에 맞춰 "main:app" or "app.main:app"로 바꿔!
#    (현재 CMD의 "app:app"은 app.py에 app=FastAPI()가 있을 때만 동작)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
