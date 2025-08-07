# # llm_summary.py
# import openai
# from typing import List

# # TODO: API 키 입력 (환경변수 또는 직접 삽입 가능 – 보안 고려 권장)
# openai.api_key = ""  # 여기에 API 키를 입력하거나 os.environ["OPENAI_API_KEY"]로 설정하세요

# def generate_occupancy_summary(predictions: List[float]) -> str:
#     """
#     LLM을 이용해 예측된 점유율 수치를 기반으로 자연어 요약을 생성합니다.
    
#     :param predictions: 예측된 점유율 리스트 (0~1 스케일)
#     :return: 자연어 요약 문자열
#     """
#     try:
#         if not predictions:
#             return "예측된 점유율 데이터가 없습니다."

#         scaled_preds = [round(p * 100, 2) for p in predictions]
#         prompt = (
#             f"향후 3시간 동안의 컨테이너 장치장 점유율 예측은 다음과 같습니다: {scaled_preds}%. "
#             "이 데이터를 바탕으로 혼잡도 상태를 요약해서 자연스럽게 설명해주세요. "
#             "혼잡 여부와 필요한 대응 조치도 함께 언급해주세요."
#         )

#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",  # 또는 "gpt-4"
#             messages=[
#                 {"role": "system", "content": "너는 항만 운영 전문가야."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=200,
#             temperature=0.7
#         )

#         return response["choices"][0]["message"]["content"]

#     except Exception as e:
#         return f"⚠️ 요약 생성 중 오류 발생: {e}"
