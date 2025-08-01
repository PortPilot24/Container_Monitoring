from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
from tensorflow.keras.models import load_model
import numpy as np
import os
from occupancy_calculator_functional import calculate_current_occupancy
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

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
    version="1.3.0"
)
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
# 5) 예측 API (향후 3시간 정각 시각 예측)
@app.post("/predict", response_model=PredictMultiResponse, tags=["Forecast"])
def predict(req: PredictRequest):
    try:
        base_input = np.array(req.load_history, dtype=np.float32).reshape(1, 48, 1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input format: {e}")

    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    if now.minute != 0:
        next_hour += timedelta(hours=1)

    predictions = {}

    current_input = base_input.copy()
    for i in range(3):  # 3개 시점 예측 (1시간 간격)
        try:
            y_hat = model.predict(current_input, verbose=0).flatten()[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model prediction error at T+{i}: {e}")

        # 저장
        timestamp = (next_hour + timedelta(hours=i)).isoformat()
        predictions[timestamp] = round(float(y_hat), 4)

        # 슬라이딩 입력값 업데이트 (예측값을 다음 입력에 추가)
        new_input = np.append(current_input.flatten()[1:], y_hat).reshape(1, 48, 1)
        current_input = new_input

    return PredictMultiResponse(predictions=predictions)

# ——————————————
# 6) 현재 점유율 계산 API
@app.get("/api/occupancy", tags=["Occupancy"])
def get_current_occupancy():
    return calculate_current_occupancy()