from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, conlist
from tensorflow.keras.models import load_model
import numpy as np
import os
import pandas as pd
from occupancy_calculator_functional import calculate_current_occupancy
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from affiliation_api import router as affiliation_router
from llm_summary import generate_occupancy_summary
from typing import List

# ——————————————
# 0) 모델 파일 경로 확인
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best_lstm_model.h5")
if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# ——————————————
# 1) FastAPI 앱 생성
app = FastAPI(
    title="Container Load Forecast API",
    description="현재 점유율 계산 및 과거 48포인트 기반 향후 3시간 정각 예측 API",
    version="1.4.0"
)

def root():
    return {"message": "Affiliation container API is running."}

# ✅ CORS 미들웨어 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 프론트 호스트 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——————————————
# 2) Pydantic 스키마 정의
class PredictRequest(BaseModel):
    load_history: conlist(float, min_length=48, max_length=48)

class PredictMultiResponse(BaseModel):
    predictions: dict  # {timestamp: predicted_value}

# ——————————————
# 3) 모델 로드
model = load_model(MODEL_PATH, compile=False)

# ——————————————
# 4) 헬스체크
@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "Container Load Forecast API is running."}

# ——————————————
# 5) CSV파일 기반 예측 API (기존 /predict 기능 대체)
@app.get("/api/predict-from-file", tags=["Forecast"])
def predict_from_file():
    filename = "터미널 반출입 목록조회_GUEST_2025-08-07_111836.csv"  # 기본 파일명
    file_path = os.path.join("data", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV file not found.")

    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV 로드 실패: {e}")
    
    df.columns = df.columns.str.strip()
    
    df["터미널 반입일시"] = pd.to_datetime(df["터미널 반입일시"], errors="coerce")
    df["터미널 반출일시"] = pd.to_datetime(df["터미널 반출일시"], errors="coerce")

    time_range = pd.date_range(start=df["터미널 반입일시"].min(),
                               end=df["터미널 반출일시"].max(),
                               freq="10min")

    max_capacity = 70000
    load_ratios = []
    for ts in time_range:
        count = ((df["터미널 반입일시"] <= ts) &
                 ((df["터미널 반출일시"].isna()) | (df["터미널 반출일시"] > ts))).sum()
        load_ratios.append(min(count / max_capacity, 1.0))

    if len(load_ratios) < 48:
        raise HTTPException(status_code=400, detail="계산된 적재율 포인트가 48개 미만입니다.")

    input_series = np.array(load_ratios[-48:], dtype=np.float32).reshape(1, 48, 1)

    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    if now.minute != 0:
        next_hour += timedelta(hours=1)

    predictions = {}
    current_input = input_series.copy()

    for i in range(6):
        y_hat = model.predict(current_input, verbose=0).flatten()[0]
        timestamp = (next_hour + timedelta(hours=i)).isoformat()
        predictions[timestamp] = round(float(y_hat), 4)
        current_input = np.append(current_input.flatten()[1:], y_hat).reshape(1, 48, 1)

    return {"filename": filename, "predictions": predictions}

# ——————————————
# 6) 현재 점유율 계산 API
@app.get("/api/occupancy", tags=["Occupancy"])
def get_current_occupancy():
    return calculate_current_occupancy()

app.include_router(affiliation_router)
# ——————————————
# 7) 요약 LLM
class SummaryRequest(BaseModel):
    predictions: List[float]
    
@app.post("/api/summary", tags=["LLM"])
def get_summary(req: SummaryRequest):
    try:
        summary = generate_occupancy_summary(req.predictions)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 요약 실패: {e}")