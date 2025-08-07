import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob

YARD_CAPACITY = 70000

def calculate_current_occupancy():
    df = pd.read_csv('./data/터미널 반출입 목록조회_GUEST_2025-08-07_111836.csv', encoding='cp949')
    df.columns = df.columns.str.strip()
    df.dropna(subset=['터미널 반입일시'], inplace=True)
    df['터미널 반입일시'] = pd.to_datetime(df['터미널 반입일시'])
    df['터미널 반출일시'] = pd.to_datetime(df['터미널 반출일시'])

    now = datetime.now()
    current_count = df[
    (df['터미널 반입일시'] <= now) & 
    (
        (df['터미널 반출일시'].isna()) | 
        (df['터미널 반출일시'] >= now)
    )
].shape[0]


    occupancy_rate = round(current_count / YARD_CAPACITY, 4)

    return {"timestamp": now.isoformat(), "occupancy_rate": occupancy_rate}