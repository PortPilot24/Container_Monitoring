# backend/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
from tensorflow.keras.models import load_model
import numpy as np
import os

# ——————————————
# 0) 모델 파일 경로 확인
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best_lstm_model.h5")
if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# ——————————————
# 1) FastAPI 앱 생성
app = FastAPI(
    title="Container Load Forecast API",
    description="과거 24시간(48포인트) 적재율 리스트를 받아 다음 30분 예측값을 반환합니다.",
    version="1.0.0"
)

# ——————————————
# 2) Pydantic 스키마 정의: 입력을 48개의 float 리스트로 강제
class PredictRequest(BaseModel):
    # Pydantic v2: conlist의 인자명이 min_length/max_length로 변경됨
    load_history: conlist(float, min_length=48, max_length=48)

class PredictResponse(BaseModel):
    predicted_load: float

# ——————————————
# 3) 서버 시작 시 모델 로드 (컴파일 정보 생략)
model = load_model(MODEL_PATH, compile=False)

# ——————————————
# 4) 헬스체크용 엔드포인트 (선택)
@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "Container Load Forecast API is running."}

# ——————————————
# 5) 예측 엔드포인트
@app.post("/predict", response_model=PredictResponse, tags=["Forecast"])
def predict(req: PredictRequest):
    """
    요청 바디 JSON:
    {
      "load_history": [0.0123, 0.0134, ..., 0.0112]    # 길이 48
    }
    반환값:
    {
      "predicted_load": 0.01456
    }
    """
    # 1) 입력 배열로 변환
    arr = np.array(req.load_history, dtype=np.float32).reshape(1, 48, 1)

    # 2) 예측
    try:
        y_hat = model.predict(arr, verbose=0).flatten()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction error: {e}")

    # 3) 결과 반환
    return PredictResponse(predicted_load=float(y_hat))
