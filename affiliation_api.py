from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import pandas as pd
import glob
import numpy as np

router = APIRouter()

@router.get("/container-monitoring/containers-by-affiliation")
def get_containers_by_affiliation(affiliation: Optional[str] = Query(None)):
    if not affiliation:
        raise HTTPException(status_code=400, detail="소속 정보를 입력해주세요.")
    
    # 최근 파일로 수정되면 경로, 파일명 수정필요
    df = pd.read_csv('./data/터미널 반출입 목록조회_GUEST_2025-08-07_111836.csv', encoding = 'cp949')
    df.columns = df.columns.str.strip()

    # ✅ 출력에 사용할 원본 DataFrame은 복사해두고 유지
    df_output = df.copy()

    # ✅ 필터링을 위한 임시 컬럼만 별도로 정제
    df["선사_정제"] = df["선사"].astype(str).str.strip().str.upper()
    affiliation_cleaned = affiliation.strip().upper()

    # ✅ 조건을 만족하는 index만 추출
    matched_idx = df[df["선사_정제"].str.contains(affiliation_cleaned, na=False)].index

    # ✅ index 기반으로 원본에서 필요한 열만 추출 (원본 '선사'는 그대로 유지)
    filtered = df_output.loc[matched_idx, [
        "선사", "컨테이너번호", "터미널 반입일시", "터미널 반출일시", "상태", "장치장위치"
    ]]

    # ✅ NaN → None (JSON 직렬화 안전성)
    filtered.where(pd.notnull(filtered), None, inplace = True)

    return {
        "containers": filtered.to_dict(orient="records")
    }
