from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableView, QLabel, QHeaderView, QSplitter)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ui.table_model import PandasModel
import pandas as pd

class FinanceTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        splitter = QSplitter(Qt.Vertical)
        
        # 상단: 데이터 테이블
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0,0,0,0)
        
        header_label = QLabel("💰 프로젝트 금전 관리 (계약금, 지출, 기성)")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        top_layout.addWidget(header_label)
        
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        top_layout.addWidget(self.table_view)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("내역 추가")
        btn_add.clicked.connect(self.add_row)
        btn_layout.addWidget(btn_add)
        
        btn_refresh = QPushButton("그래프 새로고침")
        btn_refresh.clicked.connect(self.draw_graph)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        
        top_layout.addLayout(btn_layout)
        splitter.addWidget(top_widget)
        
        # 하단: 캐시플로우 그래프
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0,0,0,0)
        
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        bottom_layout.addWidget(self.canvas)
        
        splitter.addWidget(bottom_widget)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        self.refresh_table()

    def refresh_table(self):
        if not self.manager.finance_df.empty:
            model = PandasModel(self.manager.finance_df)
            self.table_view.setModel(model)
            
    def add_row(self):
        self.manager.finance_df.loc[len(self.manager.finance_df)] = [""] * len(self.manager.finance_df.columns)
        self.refresh_table()

    def draw_graph(self):
        df = self.manager.finance_df.copy()
        if df.empty:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        try:
            # 항목별 합계 계산 (예제 로직)
            # 항목이 '지출', '자재구매'면 마이너스, '계약금액', '기성'이면 플러스로 가정
            df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0)
            
            incomes = df[df['항목'].isin(['계약금액', '기성'])]['금액'].sum()
            expenses = df[df['항목'].isin(['지출', '자재구매'])]['금액'].sum()
            
            # Bar chart
            categories = ['Income (기성/계약)', 'Expenses (지출/자재)', 'Net Cash Flow']
            values = [incomes, expenses, incomes - expenses]
            colors = ['#2ecc71', '#e74c3c', '#3498db']
            
            ax.bar(categories, values, color=colors)
            ax.set_title("Project Cash Flow Dashboard")
            ax.set_ylabel("Amount")
            
            for i, v in enumerate(values):
                ax.text(i, v + (max(values)*0.01), str(int(v)), ha='center')
                
        except Exception as e:
            ax.text(0.5, 0.5, f"Graph Error: {str(e)}", ha='center', va='center')
            
        self.canvas.draw()
