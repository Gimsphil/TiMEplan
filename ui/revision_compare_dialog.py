import pandas as pd
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class RevisionCompareDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("설계변경(리비전) 비교 분석")
        self.setGeometry(150, 150, 1000, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 상단 컨트롤 패널
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("기준 리비전 (원본):"))
        self.cb_base = QComboBox()
        self.cb_base.addItems(self.manager.contract_revisions.keys())
        ctrl_layout.addWidget(self.cb_base)
        
        ctrl_layout.addWidget(QLabel("비교 대상 리비전 (변경본):"))
        self.cb_target = QComboBox()
        self.cb_target.addItems(self.manager.contract_revisions.keys())
        # 기본적으로 최신 버전을 Target으로 설정
        if len(self.manager.contract_revisions) > 1:
            self.cb_target.setCurrentIndex(len(self.manager.contract_revisions) - 1)
            self.cb_base.setCurrentIndex(len(self.manager.contract_revisions) - 2)
        ctrl_layout.addWidget(self.cb_target)
        
        btn_compare = QPushButton("비교하기")
        btn_compare.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_compare.clicked.connect(self.do_compare)
        ctrl_layout.addWidget(btn_compare)
        
        layout.addLayout(ctrl_layout)
        
        # 범례
        legend_layout = QHBoxLayout()
        l1 = QLabel("■ 신규 추가됨")
        l1.setStyleSheet("color: #27ae60; font-weight: bold;")
        l2 = QLabel("■ 삭제됨")
        l2.setStyleSheet("color: #e74c3c; font-weight: bold;")
        l3 = QLabel("■ 수량/금액 변경됨")
        l3.setStyleSheet("color: #f39c12; font-weight: bold;")
        legend_layout.addWidget(l1)
        legend_layout.addWidget(l2)
        legend_layout.addWidget(l3)
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        # 결과 테이블
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)

    def do_compare(self):
        base_key = self.cb_base.currentText()
        target_key = self.cb_target.currentText()
        
        df_base = self.manager.contract_revisions[base_key].copy()
        df_target = self.manager.contract_revisions[target_key].copy()
        
        # 빈 데이터프레임 처리
        if df_base.empty and df_target.empty:
            QMessageBox.information(self, "결과", "비교할 데이터가 없습니다.")
            return

        # 병합 키 설정 (번호가 있으면 번호 위주, 없으면 내역/규격 위주)
        merge_keys = ["번호", "내역/규격"]
        
        # merge로 차이점 분석
        df_base['_merge_status'] = '삭제됨'
        df_target['_merge_status'] = '신규추가'
        
        merged = pd.merge(df_base, df_target, on=merge_keys, how='outer', suffixes=('_원본', '_변경'))
        
        # 결과 테이블 세팅
        show_cols = merge_keys + ["수량_원본", "수량_변경", "합계(금액)_원본", "합계(금액)_변경", "비고_변경"]
        self.table.setColumnCount(len(show_cols) + 1)
        self.table.setHorizontalHeaderLabels(["상태"] + show_cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setRowCount(len(merged))
        
        row_idx = 0
        for i, row in merged.iterrows():
            status = ""
            color = QColor(255, 255, 255)
            
            # 신규 추가 (원본에는 없고 변경본에만 있음)
            if pd.isna(row.get('합계(금액)_원본')):
                status = "신규추가"
                color = QColor(234, 250, 241) # 연녹색
            # 삭제됨 (변경본에 없음)
            elif pd.isna(row.get('합계(금액)_변경')):
                status = "삭제됨"
                color = QColor(253, 237, 236) # 연적색
            else:
                # 둘 다 있는데 수량이나 금액이 다른 경우
                qty_base = pd.to_numeric(row.get('수량_원본', 0), errors='coerce')
                qty_target = pd.to_numeric(row.get('수량_변경', 0), errors='coerce')
                amt_base = pd.to_numeric(row.get('합계(금액)_원본', 0), errors='coerce')
                amt_target = pd.to_numeric(row.get('합계(금액)_변경', 0), errors='coerce')
                
                if qty_base != qty_target or amt_base != amt_target:
                    status = "변경됨"
                    color = QColor(254, 249, 231) # 연노랑
                else:
                    status = "동일"
                    
            if status == "동일": 
                continue # 변경점만 표시하려면 continue. 하지만 다 보여주기로 함 (주석처리 안함)
                
            self.table.insertRow(row_idx)
            
            # 상태 표시
            it_status = QTableWidgetItem(status)
            it_status.setBackground(color)
            self.table.setItem(row_idx, 0, it_status)
            
            # 데이터 표시
            for col_idx, col_name in enumerate(show_cols):
                val = str(row.get(col_name, ""))
                if val == "nan": val = ""
                it = QTableWidgetItem(val)
                it.setBackground(color)
                self.table.setItem(row_idx, col_idx + 1, it)
                
            row_idx += 1
            
        self.table.setRowCount(row_idx)
        if row_idx == 0:
            QMessageBox.information(self, "결과", "두 리비전 간에 차이점이 없습니다!")
