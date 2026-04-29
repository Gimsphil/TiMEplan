import pandas as pd
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QComboBox, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
from core.timeplan_schema import CONTRACT_COLUMNS

# 다국어 매핑 사전 (한글, 영어, 중국어, 인도네시아어)
# 각 표준 컬럼에 매칭될 수 있는 키워드들 모음
AUTO_MAP_DICT = {
    "번호": ["번호", "no", "number", "nomor", "序号"],
    "공종명": ["공종", "공사명", "process", "trade", "pekerjaan", "工种"],
    "내역/규격": ["내역", "규격", "품명", "명칭", "description", "spec", "item", "deskripsi", "spesifikasi", "规格", "名称", "블랙리스트"],
    "단위": ["단위", "unit", "satuan", "单位"],
    "수량": ["수량", "qty", "quantity", "kuantitas", "jumlah", "数量"],
    "자재비(단가)": ["자재단가", "재료비단가", "material unit", "material price", "harga material", "材料单价"],
    "자재비(금액)": ["자재금액", "재료비금액", "material amount", "total material", "jumlah material", "材料总价"],
    "노무비(단가)": ["노무단가", "노무비단가", "인건비단가", "labor unit", "labor price", "harga upah", "人工单价"],
    "노무비(금액)": ["노무금액", "노무비합계", "인건비", "labor amount", "total labor", "jumlah upah", "人工总价"],
    "경비(단가)": ["경비단가", "expense unit", "equipment unit", "harga alat", "费用单价"],
    "경비(금액)": ["경비금액", "expense amount", "total expense", "jumlah alat", "费用总价"],
    "합계(단가)": ["합계단가", "일위대가", "단가", "unit price", "harga satuan", "单价"],
    "합계(금액)": ["합계금액", "금액", "총액", "amount", "total", "jumlah harga", "总价", "金额"],
    "비고": ["비고", "remark", "note", "keterangan", "备注"]
}

class ExcelImportWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("다국어 스마트 엑셀 내역서 매핑 위저드")
        self.setGeometry(200, 200, 800, 600)
        
        self.raw_df = None
        self.mapped_df = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        header = QLabel("엑셀 파일의 열(Column)을 TIMEPLAn 표준 양식에 맞게 연결해 주세요.\n(다국어 키워드를 통해 대부분 자동 매핑됩니다)")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        btn_load = QPushButton("엑셀 파일 찾아보기...")
        btn_load.clicked.connect(self.load_excel)
        btn_load.setStyleSheet("padding: 8px; font-weight: bold;")
        layout.addWidget(btn_load)
        
        self.table = QTableWidget(len(CONTRACT_COLUMNS), 2)
        self.table.setHorizontalHeaderLabels(["TIMEPLAn 표준 컬럼", "불러온 엑셀 열 연결"])
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 400)
        
        for r, col_name in enumerate(CONTRACT_COLUMNS):
            lbl = QLabel(f" {col_name} ")
            lbl.setStyleSheet("font-weight: bold;")
            self.table.setCellWidget(r, 0, lbl)
            
            combo = QComboBox()
            combo.addItem("[선택 안 함]")
            self.table.setCellWidget(r, 1, combo)
            
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("매핑 적용 및 가져오기")
        btn_apply.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_apply.clicked.connect(self.apply_mapping)
        
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_excel(self):
        fname, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel/CSV Files (*.xlsx *.xls *.csv)")
        if not fname: return
        
        try:
            if fname.endswith('.csv'):
                self.raw_df = pd.read_csv(fname, encoding='utf-8')
            else:
                self.raw_df = pd.read_excel(fname)
                
            self.populate_combos()
            QMessageBox.information(self, "성공", "파일을 성공적으로 불러왔습니다. 자동 매핑 결과를 확인해 주세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 읽는 중 오류가 발생했습니다.\n{e}")

    def populate_combos(self):
        if self.raw_df is None or self.raw_df.empty: return
        
        raw_cols = list(self.raw_df.columns)
        
        for r, std_col in enumerate(CONTRACT_COLUMNS):
            combo = self.table.cellWidget(r, 1)
            combo.clear()
            combo.addItem("[선택 안 함]")
            combo.addItems([str(c) for c in raw_cols])
            
            # 자동 매핑 시도
            keywords = AUTO_MAP_DICT.get(std_col, [])
            mapped = False
            for raw_col in raw_cols:
                raw_col_lower = str(raw_col).lower().strip()
                for kw in keywords:
                    if kw in raw_col_lower:
                        idx = combo.findText(str(raw_col))
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
                            mapped = True
                            break
                if mapped: break

    def apply_mapping(self):
        if self.raw_df is None:
            QMessageBox.warning(self, "경고", "먼저 엑셀 파일을 불러오세요.")
            return
            
        new_df = pd.DataFrame(columns=CONTRACT_COLUMNS)
        
        for r, std_col in enumerate(CONTRACT_COLUMNS):
            combo = self.table.cellWidget(r, 1)
            selected_col = combo.currentText()
            
            if selected_col != "[선택 안 함]" and selected_col in self.raw_df.columns:
                new_df[std_col] = self.raw_df[selected_col]
        
        # 빈 데이터는 빈 문자열로 초기화
        new_df.fillna("", inplace=True)
        self.mapped_df = new_df
        self.accept()
