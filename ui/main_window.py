"""
TIMEPLAN 메인 윈도우 (GUI)
- 현대적이고 풍부한 인터페이스
- 간트 차트 및 타임테이블 기능 통합
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QFileDialog, QMessageBox, 
                               QTabWidget, QTableView, QHeaderView, QToolBar,
                               QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QIcon, QFont, QTextListFormat, QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QTextEdit

from core.timeplan_manager import TimePlanManager
from core.gantt_generator import GanttGenerator
from ui.table_model import PandasModel
from ui.project_schedule_tab import ProjectScheduleTab
from ui.resource_management_tab import ResourceManagementTab
from ui.pm_dashboard_tab import PMDashboardTab
from ui.daily_log_tab import DailyLogTab
from ui.master_db_tab import MasterDBTab
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TIMEPLAn - 프리미엄 시간 계획 관리 및 간트/타임테이블 빌더")
        self.setGeometry(100, 100, 1024, 768)
        self.manager = TimePlanManager()
        self.apply_stylesheet()
        self.init_ui()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f5f7;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #2c3e50;
                border: 1px solid #c0c0c0;
                border-bottom: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTableView, QTableWidget {
                border: none;
                gridline-color: #e0e0e0;
                selection-background-color: #ebf5fb;
                selection-color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                border: 1px solid #1a252f;
                font-weight: bold;
            }
            QToolBar {
                background: white;
                border-bottom: 1px solid #d0d0d0;
                spacing: 10px;
                padding: 5px;
            }
        """)

    def init_ui(self):
        self.create_actions_and_toolbar()
        
        self.tabs = QTabWidget()
        
        # 1. PM 대시보드 탭
        self.tab_dashboard = PMDashboardTab(self.manager)
        self.tabs.addTab(self.tab_dashboard, "종합 대시보드 (EVM)")

        # 2. 자원 및 계약/변경 관리 탭
        self.tab_resource = ResourceManagementTab(self.manager)
        self.tabs.addTab(self.tab_resource, "자원/계약 관리")
        
        # 3. 반응형 공정표 (Project Schedule) 탭
        self.tab_gantt = ProjectScheduleTab(self.manager)
        self.tabs.addTab(self.tab_gantt, "📈 공정표 (Project Schedule)")
        
        # 4. 타임테이블 빌더 탭
        self.tab_timetable = QWidget()
        self.init_timetable_tab()
        self.tabs.addTab(self.tab_timetable, "타임테이블 (24H)")
        
        # 5. 일일 작업일지 탭
        self.tab_daily_log = DailyLogTab(self.manager)
        self.tabs.addTab(self.tab_daily_log, "📝 일일 작업일지")
        
        # 6. 마스터 DB 탭
        self.tab_master_db = MasterDBTab(self.manager)
        self.tabs.addTab(self.tab_master_db, "🗂️ 마스터 DB")
        
        self.setCentralWidget(self.tabs)

    def create_actions_and_toolbar(self):
        toolbar = QToolBar("메인 툴바")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        action_load = QAction("불러오기", self)
        action_load.triggered.connect(self.load_file)
        toolbar.addAction(action_load)

        action_save = QAction("저장하기", self)
        action_save.triggered.connect(self.save_file)
        toolbar.addAction(action_save)

        toolbar.addSeparator()

        action_report = QAction("요약 보고서", self)
        action_report.triggered.connect(self.generate_report)
        toolbar.addAction(action_report)

    # ------------------ (Old Data Tab Deprecated in favor of ResourceManagementTab) ------------------

    # ------------------ (HTML Gantt Deprecated in favor of InteractiveGantt) ------------------
    # def init_gantt_tab(self): ...

    def init_timetable_tab(self):
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        header_label = QLabel("📅 타임테이블 빌더")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        top_layout.addWidget(header_label)
        
        btn_build = QPushButton("시간표 빌드")
        btn_build.clicked.connect(self.build_timetable)
        top_layout.addWidget(btn_build)
        
        layout.addLayout(top_layout)

        self.timetable_widget = QTableWidget(24, 7) # 24시간, 7일
        self.timetable_widget.setHorizontalHeaderLabels(["월", "화", "수", "목", "금", "토", "일"])
        self.timetable_widget.setVerticalHeaderLabels([f"{(i+6)%24}:00" for i in range(24)])
        self.timetable_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timetable_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 모든 셀에 QTextEdit 배치하여 자동 글머리기호(Bullet) 및 들여쓰기 지원
        for r in range(24):
            for c in range(7):
                text_edit = QTextEdit()
                text_edit.setStyleSheet("border: none; background: transparent;")
                # 처음 클릭하여 타이핑할 때 자동으로 글머리 기호가 시작되도록 설정
                cursor = text_edit.textCursor()
                list_format = QTextListFormat()
                list_format.setStyle(QTextListFormat.ListDisc)
                cursor.createList(list_format)
                self.timetable_widget.setCellWidget(r, c, text_edit)
        
        layout.addWidget(self.timetable_widget)
        
        self.tab_timetable.setLayout(layout)

    def refresh_table(self):
        self.tab_resource.refresh_all_tables()
        self.tab_resource.load_meta_to_ui()
        self.tab_dashboard.update_dashboard()
        self.tab_master_db.refresh_all_tables()
        # 일지 탭은 달력 선택에 따라 로드되므로 강제 리프레시는 생략하거나 필요시 추가

    def add_empty_row(self):
        # Deprecated logic. Add rows directly from ResourceManagementTab or Gantt
        pass

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "파일 불러오기", "", "Excel/CSV Files (*.xlsx *.xls *.csv)")
        if fname:
            try:
                self.manager.load(fname)
                self.refresh_table()
                self.tabs.setCurrentIndex(0)
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))

    def save_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "파일 저장", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if fname:
            try:
                self.manager.save(fname)
                QMessageBox.information(self, "성공", "파일을 성공적으로 저장했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))

    def generate_report(self):
        try:
            report_path = self.manager.generate_report()
            QMessageBox.information(self, "보고서 생성", f"보고서가 생성되었습니다:\n{report_path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    # ------------------ (HTML Gantt Methods Deprecated) ------------------
    # def render_gantt(self): ...

    def build_timetable(self):
        if self.manager.df.empty:
            QMessageBox.warning(self, "경고", "데이터가 없습니다.")
            return
            
        self.timetable_widget.clearContents()
        
        # 단순 매핑 데모 (실제로는 요일/시간을 파싱해야 함)
        # 예: 첫 번째 일정을 월요일 9시에 배치
        try:
            for index, row in self.manager.df.iterrows():
                title = str(row.iloc[4]) if len(row) > 4 else f"Task {index}" # 4: 작업명(공종)
                day_col = index % 7
                time_row = (index // 7) % 24
                
                cell_widget = self.timetable_widget.cellWidget(time_row, day_col)
                if isinstance(cell_widget, QTextEdit):
                    cell_widget.append(title)
            
            QMessageBox.information(self, "완료", "타임테이블이 빌드되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
