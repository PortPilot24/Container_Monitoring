import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob

YARD_CAPACITY = 70000

def calculate_current_occupancy():
    file_pattern = './터미널 반출입 목록조회_GUEST_*.csv' # 프로젝트 마감할 때 루트에 최신파일 같이 첨부
    file_list = glob.glob(file_pattern)

    dataframes = []
    for file in file_list:
        df = pd.read_csv(file, encoding='cp949')
        df.columns = df.columns.str.strip()
        df.dropna(subset=['터미널 반입일시'], inplace=True)
        df['터미널 반입일시'] = pd.to_datetime(df['터미널 반입일시'])
        df['터미널 반출일시'] = pd.to_datetime(df['터미널 반출일시'])
        dataframes.append(df)

    all_data = pd.concat(dataframes, ignore_index=True)

    now = datetime.now()
    current_count = all_data[
    (all_data['터미널 반입일시'] <= now) & 
    (
        (all_data['터미널 반출일시'].isna()) | 
        (all_data['터미널 반출일시'] >= now)
    )
].shape[0]


    occupancy_rate = round(current_count / YARD_CAPACITY, 4)

    return {"timestamp": now.isoformat(), "occupancy_rate": occupancy_rate}