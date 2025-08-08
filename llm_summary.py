# llm_summary.py
from openai import OpenAI
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ 환경변수에서 API 키 불러오기
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY가 .env에서 로드되지 않았습니다.")

# ✅ OpenAI 클라이언트 인스턴스 생성
client = OpenAI(api_key=api_key)

def generate_occupancy_summary(predictions: List[float]) -> str:
    print("📥 들어온 예측값:", predictions)

    if not predictions:
        return "예측된 점유율 데이터가 없습니다."

    try:
        scaled_preds = [round(p * 100, 2) for p in predictions]
        prompt = (
            f"향후 3시간 동안의 컨테이너 장치장 점유율 예측은 다음과 같습니다: {scaled_preds}%. "
            "이 데이터를 바탕으로 혼잡도 상태를 요약해서 자연스럽게 설명해주세요. "
            "혼잡 여부와 필요한 대응 조치도 함께 언급해주세요."
        )

        print("📡 OpenAI API 요청 중...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 항만 운영 전문가야."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        result = response.choices[0].message.content
        print("✅ 요약 생성 완료:", result)
        return result

    except Exception as e:
        print("❌ LLM 호출 실패:", e)
        raise RuntimeError(f"요약 생성 실패: {e}")