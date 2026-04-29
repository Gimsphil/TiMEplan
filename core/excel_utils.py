"""
엑셀/CSV 입출력 유틸리티
- pandas, openpyxl 기반
- 기존 HTML Gantt Generator, TimeTableBuilder의 데이터 처리 방식 참고
"""
import pandas as pd
import os

def load_excel_or_csv(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    elif ext == ".csv":
        return pd.read_csv(filepath)
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")

def save_excel_or_csv(df, filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in [".xlsx", ".xls"]:
        df.to_excel(filepath, index=False)
    elif ext == ".csv":
        df.to_csv(filepath, index=False)
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")
