"""
보고서/요약 생성 유틸리티
- 시간 계획 데이터의 요약, 통계, 보고서 파일 생성
- 기존 두 프로그램의 요약/보고 방식 참고
"""
import pandas as pd
import os

def generate_simple_report(df, out_dir="data"): 
    if df.empty:
        raise ValueError("데이터가 없습니다.")
    summary = {
        "총 일정 수": len(df),
        "시작일": str(df.iloc[:,0].min()),
        "종료일": str(df.iloc[:,1].max())
    }
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "report.xlsx")
    pd.DataFrame([summary]).to_excel(report_path, index=False)
    return report_path
