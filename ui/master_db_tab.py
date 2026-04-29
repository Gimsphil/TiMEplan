from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                               QTabWidget, QHeaderView, QPushButton, QLabel)
from ui.table_model import PandasModel

class MasterDBTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        header = QLabel("🗂️ 마스터 DB (자재 구매처 및 인력풀 관리)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        self.tabs = QTabWidget()
        
        # 1. 자재 구매처 DB
        self.tab_vendor = self.create_table_tab('vendor_df', "자재 공급업체 정보를 관리합니다.")
        self.tabs.addTab(self.tab_vendor, "자재 구매처 DB")
        
        # 2. 인력 풀 DB
        self.tab_hr = self.create_table_tab('hr_pool_df', "현장 투입 인력(작업자/관리자/임원)의 정보를 관리합니다.")
        self.tabs.addTab(self.tab_hr, "인력 풀(HR) DB")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_table_tab(self, df_attr_name, desc_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        desc = QLabel(desc_text)
        desc.setStyleSheet("color: #555;")
        layout.addWidget(desc)
        
        tv = QTableView()
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(tv)
        
        # 데이터 로드
        df = getattr(self.manager, df_attr_name)
        model = PandasModel(df)
        tv.setModel(model)
        
        return widget

    def refresh_all_tables(self):
        # 자재 구매처
        tv_vendor = self.tab_vendor.findChild(QTableView)
        if tv_vendor:
            tv_vendor.setModel(PandasModel(self.manager.vendor_df))
            
        # 인력 풀
        tv_hr = self.tab_hr.findChild(QTableView)
        if tv_hr:
            tv_hr.setModel(PandasModel(self.manager.hr_pool_df))
