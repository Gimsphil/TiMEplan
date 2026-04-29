from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QGridLayout, QFrame, QCheckBox)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PMDashboardTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        header = QLabel("📈 프로젝트 종합 성과 대시보드 (EVM)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # 상단 요약 패널
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 8px; }
            QLabel { border: none; }
        """)
        summary_layout = QGridLayout(summary_frame)
        
        self.lbl_contract = self.create_value_label("원계약액", "0")
        self.lbl_changes = self.create_value_label("설계변경/증감", "0")
        self.lbl_final_budget = self.create_value_label("최종실행예산", "0")
        self.lbl_cost = self.create_value_label("총투입원가(기성)", "0")
        self.lbl_progress = self.create_value_label("공정진행률", "0%")
        self.lbl_remaining = self.create_value_label("잔여예산", "0")
        
        summary_layout.addWidget(self.lbl_contract, 0, 0)
        summary_layout.addWidget(self.lbl_changes, 0, 1)
        summary_layout.addWidget(self.lbl_final_budget, 0, 2)
        summary_layout.addWidget(self.lbl_cost, 1, 0)
        summary_layout.addWidget(self.lbl_progress, 1, 1)
        summary_layout.addWidget(self.lbl_remaining, 1, 2)
        
        layout.addWidget(summary_frame)
        
        # 버튼 패널
        btn_layout = QHBoxLayout()
        
        self.chk_public_only = QCheckBox("🔒 공식 보고용 모드 (사적/개인 지출 숨김)")
        self.chk_public_only.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0392b;")
        btn_layout.addWidget(self.chk_public_only)
        
        btn_refresh = QPushButton("EVM 데이터 계산 및 그래프 갱신")
        btn_refresh.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: #27ae60; color: white;")
        btn_refresh.clicked.connect(self.update_dashboard)
        btn_layout.addWidget(btn_refresh)
        layout.addLayout(btn_layout)
        
        # 하단 그래프
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)

    def create_value_label(self, title, init_value):
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(10, 10, 10, 10)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_val = QLabel(init_value)
        lbl_val.setStyleSheet("color: #2c3e50; font-size: 18px; font-weight: bold;")
        lbl_val.setAlignment(Qt.AlignCenter)
        
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_val)
        
        # hacky way to store reference to value label
        container.value_label = lbl_val
        return container

    def update_dashboard(self):
        is_public = self.chk_public_only.isChecked()
        evm = self.manager.calculate_evm(public_only=is_public)
        
        # 텍스트 업데이트
        self.lbl_contract.value_label.setText(f"{evm['원계약액']:,.0f}")
        self.lbl_changes.value_label.setText(f"{evm['설계변경증감']:,.0f}")
        self.lbl_final_budget.value_label.setText(f"{evm['최종실행예산']:,.0f}")
        self.lbl_cost.value_label.setText(f"{evm['총투입원가(기성)']:,.0f}")
        self.lbl_progress.value_label.setText(f"{evm['진행률']:.2f}%")
        
        # 잔여예산 색상 처리
        rem = evm['잔여예산']
        rem_str = f"{rem:,.0f}"
        if rem < 0:
            self.lbl_remaining.value_label.setStyleSheet("color: #c0392b; font-size: 18px; font-weight: bold;")
        else:
            self.lbl_remaining.value_label.setStyleSheet("color: #27ae60; font-size: 18px; font-weight: bold;")
        self.lbl_remaining.value_label.setText(rem_str)
        
        # 그래프 업데이트
        self.figure.clear()
        ax1 = self.figure.add_subplot(221)
        ax2 = self.figure.add_subplot(222)
        ax3 = self.figure.add_subplot(212) # S-Curve (하단 전체)
        
        # 1. Budget vs Cost Bar Chart
        categories = ['Final Budget', 'Actual Cost']
        values = [evm['최종실행예산'], evm['총투입원가(기성)']]
        ax1.bar(categories, values, color=['#3498db', '#e67e22'])
        ax1.set_title("Budget vs Cost", fontsize=10)
        for i, v in enumerate(values):
            ax1.text(i, v + (max(values)*0.02) if max(values) > 0 else 0, f"{v:,.0f}", ha='center', fontsize=8)
            
        # 2. Daily Burn Rate (보합) per Process
        df_sch = self.manager.df.copy()
        if not df_sch.empty:
            # 계획행만 필터링
            df_p = df_sch[df_sch.iloc[:, 0] == "계획"].copy()
            burn_data = []
            for _, row in df_p.iterrows():
                try:
                    name = row["공정명"]
                    total = float(str(row["공정총액"]).replace(',', ''))
                    s = int(row["계획시작일"])
                    e = int(row["계획종료일"])
                    duration = e - s + 1
                    if duration > 0:
                        burn_data.append((name, total / duration))
                except: continue
            
            if burn_data:
                names, burns = zip(*burn_data)
                ax2.barh(names, burns, color='#f39c12')
                ax2.set_title("Daily Burn Rate per Process", fontsize=10)
                ax2.tick_params(axis='both', which='major', labelsize=8)
            else:
                ax2.text(0.5, 0.5, "No Amount Data", ha='center', va='center')
        else:
            ax2.text(0.5, 0.5, "No Schedule Data", ha='center', va='center')
            
        # 3. S-Curve (Progress over Time)
        df_log = self.manager.daily_log_df.copy()
        if not df_log.empty:
            df_log["일자"] = pd.to_datetime(df_log["일자"], errors='coerce')
            df_log = df_log.sort_values("일자")
            df_log["금일성과(%)"] = pd.to_numeric(df_log["금일성과(%)"], errors='coerce').fillna(0)
            df_log["누적실적(%)"] = df_log["금일성과(%)"].cumsum()
            
            # 실제 실적 곡선 (Actual)
            ax3.plot(df_log["일자"], df_log["누적실적(%)"], marker='o', label='Actual Achievement', color='#27ae60', linewidth=2)
            
            # 목표 계획 곡선 (Simple Target - 30일 기준 선형 예시)
            if not df_log["일자"].empty:
                start_date = df_log["일자"].min()
                end_date = start_date + pd.Timedelta(days=30)
                ax3.plot([start_date, end_date], [0, 100], linestyle='--', label='Planned Target', color='#3498db', alpha=0.6)
            
            ax3.set_title("S-Curve (Progress Tracking)")
            ax3.set_ylabel("Cumulative %")
            ax3.set_ylim(0, 110)
            ax3.legend()
            ax3.grid(True, linestyle=':', alpha=0.6)
        else:
            ax3.text(0.5, 0.5, "Daily Log required for S-Curve", ha='center', va='center')
            
        self.figure.tight_layout()
        self.canvas.draw()
