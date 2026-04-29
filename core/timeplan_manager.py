"""
TIMEPLAN 데이터 및 로직 관리 (EVM / ERP 확장판 + 프라이버시 필터링)
- 다중 데이터프레임 (계약, 자재, 노무, 장비, 리스크, 일정)
- EVM 성과 계산 및 사적 데이터 마스킹
"""
import pandas as pd
import os
from core.timeplan_schema import (TIMEPLAN_COLUMNS, CONTRACT_COLUMNS, 
                                  MATERIAL_COLUMNS, LABOR_COLUMNS, 
                                  EQUIPMENT_COLUMNS, ISSUE_COLUMNS, PROJECT_META_COLUMNS,
                                  DAILY_LOG_COLUMNS, VENDOR_DB_COLUMNS, HR_POOL_COLUMNS)

class TimePlanManager:
    def __init__(self):
        self.reset_data()

    def reset_data(self):
        self.df = pd.DataFrame(columns=TIMEPLAN_COLUMNS)
        self.contract_revisions = {"Rev.0": pd.DataFrame(columns=CONTRACT_COLUMNS)}
        self.active_rev_key = "Rev.0"
        self.project_meta_df = pd.DataFrame(columns=PROJECT_META_COLUMNS)
        self.project_meta_df.loc[0] = [""] * len(PROJECT_META_COLUMNS) # 초기 메타데이터 1행 생성
        self.material_df = pd.DataFrame(columns=MATERIAL_COLUMNS)
        self.labor_df = pd.DataFrame(columns=LABOR_COLUMNS)
        self.equipment_df = pd.DataFrame(columns=EQUIPMENT_COLUMNS)
        self.issue_df = pd.DataFrame(columns=ISSUE_COLUMNS)
        self.daily_log_df = pd.DataFrame(columns=DAILY_LOG_COLUMNS)
        self.vendor_df = pd.DataFrame(columns=VENDOR_DB_COLUMNS)
        self.hr_pool_df = pd.DataFrame(columns=HR_POOL_COLUMNS)

    def load(self, filepath):
        ext = os.path.splitext(filepath)[-1].lower()
        if ext not in [".xlsx", ".xls"]:
            raise ValueError("EVM 통합 관리는 엑셀(.xlsx) 형식만 지원합니다.")
            
        try:
            xl = pd.ExcelFile(filepath)
            sheets = xl.sheet_names
            
            if "일정" in sheets: self.df = xl.parse("일정")
            
            # 과거 버전 호환 및 다중 리비전 로드
            self.contract_revisions = {}
            for sheet in sheets:
                if sheet == "계약내역":
                    self.contract_revisions["Rev.0"] = xl.parse(sheet)
                elif sheet.startswith("계약내역_"):
                    rev_name = sheet.replace("계약내역_", "")
                    self.contract_revisions[rev_name] = xl.parse(sheet)
            
            if not self.contract_revisions:
                self.contract_revisions["Rev.0"] = pd.DataFrame(columns=CONTRACT_COLUMNS)
            
            # 마지막 버전을 활성화
            self.active_rev_key = list(self.contract_revisions.keys())[-1]

            if "프로젝트메타" in sheets: self.project_meta_df = xl.parse("프로젝트메타")
            if "자재관리" in sheets: self.material_df = xl.parse("자재관리")
            if "노무관리" in sheets: self.labor_df = xl.parse("노무관리")
            if "장비관리" in sheets: self.equipment_df = xl.parse("장비관리")
            if "변수관리" in sheets: self.issue_df = xl.parse("변수관리")
            if "작업일지" in sheets: self.daily_log_df = xl.parse("작업일지")
            if "구매처DB" in sheets: self.vendor_df = xl.parse("구매처DB")
            if "인력풀DB" in sheets: self.hr_pool_df = xl.parse("인력풀DB")
        except Exception as e:
            raise ValueError(f"파일 불러오기 실패: {e}")

    def save(self, filepath):
        ext = os.path.splitext(filepath)[-1].lower()
        if ext not in [".xlsx", ".xls"]:
            raise ValueError("EVM 통합 관리는 엑셀(.xlsx) 형식만 지원합니다.")
            
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            self.df.to_excel(writer, sheet_name="일정", index=False)
            for rev_key, df in self.contract_revisions.items():
                if rev_key == "Rev.0" and len(self.contract_revisions) == 1:
                    sheet_name = "계약내역"
                else:
                    sheet_name = f"계약내역_{rev_key}"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
            self.project_meta_df.to_excel(writer, sheet_name="프로젝트메타", index=False)
            self.material_df.to_excel(writer, sheet_name="자재관리", index=False)
            self.labor_df.to_excel(writer, sheet_name="노무관리", index=False)
            self.equipment_df.to_excel(writer, sheet_name="장비관리", index=False)
            self.issue_df.to_excel(writer, sheet_name="변수관리", index=False)
            self.daily_log_df.to_excel(writer, sheet_name="작업일지", index=False)
            self.vendor_df.to_excel(writer, sheet_name="구매처DB", index=False)
            self.hr_pool_df.to_excel(writer, sheet_name="인력풀DB", index=False)

    @property
    def contract_df(self):
        if self.active_rev_key not in self.contract_revisions:
            self.active_rev_key = list(self.contract_revisions.keys())[0] if self.contract_revisions else "Rev.0"
        return self.contract_revisions.get(self.active_rev_key, pd.DataFrame(columns=CONTRACT_COLUMNS))

    @contract_df.setter
    def contract_df(self, df):
        self.contract_revisions[self.active_rev_key] = df

    def create_new_revision(self, new_rev_name):
        if new_rev_name in self.contract_revisions:
            raise ValueError("이미 존재하는 리비전 이름입니다.")
        current_df = self.contract_df.copy()
        self.contract_revisions[new_rev_name] = current_df
        self.active_rev_key = new_rev_name

    def export_english_boq(self, filepath, rev_key=None):
        if rev_key is None: rev_key = self.active_rev_key
        df = self.contract_revisions.get(rev_key, pd.DataFrame()).copy()
        
        # 영어 컬럼 매핑
        eng_mapping = {
            "번호": "No", "공종명": "Trade/Process", "내역/규격": "Description/Spec", 
            "단위": "Unit", "수량": "Qty", 
            "자재비(단가)": "Material Unit Price", "자재비(금액)": "Material Amount", 
            "노무비(단가)": "Labor Unit Price", "노무비(금액)": "Labor Amount", 
            "경비(단가)": "Expense Unit Price", "경비(금액)": "Expense Amount", 
            "합계(단가)": "Total Unit Price", "합계(금액)": "Total Amount", 
            "비고": "Remark"
        }
        df.rename(columns=eng_mapping, inplace=True)
        df.to_excel(filepath, index=False)

    def calculate_evm(self, public_only=False):
        """계약 대비 성과 및 진행률 계산. public_only=True면 사적 지출 제외."""
        
        # 복사본으로 안전하게 계산
        c_df = self.contract_df.copy()
        meta_df = self.project_meta_df.copy()
        m_df = self.material_df.copy()
        l_df = self.labor_df.copy()
        e_df = self.equipment_df.copy()
        i_df = self.issue_df.copy()
        
        # 숫자형 변환
        if '합계(금액)' in c_df.columns:
            c_df['합계(금액)'] = pd.to_numeric(c_df['합계(금액)'], errors='coerce').fillna(0)
        m_df['실제총액'] = pd.to_numeric(m_df['실제총액'], errors='coerce').fillna(0)
        l_df['노무비총액'] = pd.to_numeric(l_df['노무비총액'], errors='coerce').fillna(0)
        l_df['간식/용돈(사적)'] = pd.to_numeric(l_df['간식/용돈(사적)'], errors='coerce').fillna(0)
        e_df['장비비총액'] = pd.to_numeric(e_df['장비비총액'], errors='coerce').fillna(0)
        e_df['간식/용돈(사적)'] = pd.to_numeric(e_df['간식/용돈(사적)'], errors='coerce').fillna(0)
        i_df['계약금액증감'] = pd.to_numeric(i_df['계약금액증감'], errors='coerce').fillna(0)
        
        # 사적 데이터 마스킹 (Public 모드)
        private_cost_masked = 0
        if public_only:
            # 1. 행 자체가 '사적'인 경우 필터링
            if '보고공개여부(공적/사적)' in m_df.columns:
                m_df = m_df[m_df['보고공개여부(공적/사적)'] != '사적']
            if '보고공개여부(공적/사적)' in l_df.columns:
                l_df = l_df[l_df['보고공개여부(공적/사적)'] != '사적']
            if '보고공개여부(공적/사적)' in e_df.columns:
                e_df = e_df[e_df['보고공개여부(공적/사적)'] != '사적']
            if '보고공개여부(공적/사적)' in i_df.columns:
                i_df = i_df[i_df['보고공개여부(공적/사적)'] != '사적']
                
            # 2. '공적' 행이라도 '간식/용돈(사적)' 컬럼은 비용에서 차감
            private_cost_masked += l_df['간식/용돈(사적)'].sum()
            private_cost_masked += e_df['간식/용돈(사적)'].sum()

        # 원계약액 산출
        base_contract = 0
        if not self.project_meta_df.empty:
            val = self.project_meta_df['총계약금액(도급액)'].iloc[0]
            if str(val).strip():
                try:
                    base_contract = float(str(val).replace(',', ''))
                except:
                    pass
        
        # 메타데이터가 비어있다면 상세 내역서에서 합계(금액) 합산
        if base_contract == 0:
            c_df['합계(금액)'] = pd.to_numeric(c_df['합계(금액)'], errors='coerce').fillna(0)
            base_contract = c_df['합계(금액)'].sum()

        change_orders = i_df['계약금액증감'].sum()
        final_budget = base_contract + change_orders
        
        total_material = m_df['실제총액'].sum()
        total_labor = l_df['노무비총액'].sum()
        total_equip = e_df['장비비총액'].sum()
        
        actual_cost = total_material + total_labor + total_equip
        
        if public_only:
            actual_cost -= private_cost_masked
            total_labor -= l_df['간식/용돈(사적)'].sum()
            total_equip -= e_df['간식/용돈(사적)'].sum()

        progress_rate = (actual_cost / final_budget * 100) if final_budget > 0 else 0.0
        remaining = final_budget - actual_cost
        
        return {
            "원계약액": base_contract,
            "설계변경증감": change_orders,
            "최종실행예산": final_budget,
            "자재비누계": total_material,
            "노무비누계": total_labor,
            "장비비누계": total_equip,
            "총투입원가(기성)": actual_cost,
            "진행률": progress_rate,
            "잔여예산": remaining
        }
