from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QMenu, QLabel, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import math

class ProjectScheduleTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.timescale = 1 # 기본 1일
        self.actual_enabled = False # 기본 계획만 보임
        self.max_days = 365 * 3 # 최대 3년
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title = QLabel("📊 공정표 (Project Schedule) - 계획 대비 실행 분석")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        btn_layout = QHBoxLayout()
        btn_add_row = QPushButton("➕ 공정 추가")
        btn_add_row.clicked.connect(self.add_task_group)
        btn_layout.addWidget(btn_add_row)
        
        btn_sync = QPushButton("📉 공정 막대 동기화")
        btn_sync.clicked.connect(self.draw_bars)
        btn_sync.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_layout.addWidget(btn_sync)
        
        btn_layout.addSpacing(20)
        
        btn_layout.addWidget(QLabel("표시 주기:"))
        self.cb_timescale = QComboBox()
        self.cb_timescale.addItems(["1일", "2일", "3일", "5일", "7일(주간)", "15일", "30일(월별)"])
        self.cb_timescale.currentTextChanged.connect(self.on_timescale_changed)
        btn_layout.addWidget(self.cb_timescale)
        
        self.btn_toggle_actual = QPushButton("🛠️ 실행계획 활성화")
        self.btn_toggle_actual.setCheckable(True)
        self.btn_toggle_actual.clicked.connect(self.toggle_actual_rows)
        btn_layout.addWidget(self.btn_toggle_actual)
        
        btn_print = QPushButton("🖨️ PDF 출력/저장")
        btn_print.clicked.connect(self.export_pdf)
        btn_layout.addWidget(btn_print)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 범례
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("범례: [■ 계획 (Planned)] "))
        legend_layout.itemAt(0).widget().setStyleSheet("color: #3498db; font-weight: bold;")
        legend_layout.addWidget(QLabel(" [■ 실행 (Actual)] "))
        legend_layout.itemAt(1).widget().setStyleSheet("color: #27ae60; font-weight: bold;")
        legend_layout.addWidget(QLabel(" [■ 지연 (Delayed)] "))
        legend_layout.itemAt(2).widget().setStyleSheet("color: #e74c3c; font-weight: bold;")
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        # 공정표 테이블
        self.table = QTableWidget(0, 50) # 초기 50열
        self.rebuild_timeline()
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 150)
        for i in range(2, 6): self.table.setColumnWidth(i, 80)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 100) # 공정 총액
        self.table.setColumnWidth(8, 100) # 일일 보합
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.load_from_manager()

    def rebuild_timeline(self):
        """선택된 주기에 따라 타임라인 열을 재구성합니다."""
        interval_map = {"1일":1, "2일":2, "3일":3, "5일":5, "7일(주간)":7, "15일":15, "30일(월별)":30}
        self.timescale = interval_map.get(self.cb_timescale.currentText(), 1)
        
        num_day_cols = math.ceil(self.max_days / self.timescale)
        total_cols = 9 + num_day_cols + 1 # 고정9 + 날짜N + 비고1
        
        self.table.setColumnCount(total_cols)
        
        base_headers = ["구분", "공정명", "계획시작", "계획종료", "실제시작", "실제종료", "성과(%)", "공정 총액", "일일 보합"]
        day_headers = []
        for i in range(num_day_cols):
            start = i * self.timescale + 1
            end = (i + 1) * self.timescale
            if self.timescale == 1:
                day_headers.append(f"{start}일")
            else:
                day_headers.append(f"{start}~{end}")
        
        headers = base_headers + day_headers + ["비고(Remark)"]
        self.table.setHorizontalHeaderLabels(headers)
        
        for i in range(9, total_cols - 1):
            self.table.setColumnWidth(i, 30 if self.timescale > 1 else 25)
        self.table.setColumnWidth(total_cols - 1, 150)

    def on_timescale_changed(self):
        self.rebuild_timeline()
        self.draw_bars()

    def toggle_actual_rows(self, checked):
        self.actual_enabled = checked
        if checked:
            self.btn_toggle_actual.setText("🛠️ 실행계획 숨기기")
        else:
            self.btn_toggle_actual.setText("🛠️ 실행계획 활성화")
        
        # 실행행 숨기기/보이기
        for r in range(self.table.rowCount()):
            if r % 2 == 1:
                self.table.setRowHidden(r, not checked)

    def export_pdf(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Landscape)
        
        # A3/A4 선택 다이얼로그 (간이)
        msg = QMessageBox()
        msg.setWindowTitle("용지 선택")
        msg.setText("출력 용지를 선택하세요.")
        btn_a3 = msg.addButton("A3 (기본)", QMessageBox.ActionRole)
        btn_a4 = msg.addButton("A4", QMessageBox.ActionRole)
        msg.exec()
        
        if msg.clickedButton() == btn_a4:
            printer.setPageSize(QPageSize(QPageSize.A4))
        else:
            printer.setPageSize(QPageSize(QPageSize.A3))

        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            # 여기서는 단순 렌더링 예시 (실제 정교한 PDF 라이브러리 사용 권장)
            painter = QPainter(printer)
            xscale = printer.pageRect(QPrinter.DevicePixel).width() / self.width()
            yscale = printer.pageRect(QPrinter.DevicePixel).height() / self.height()
            scale = min(xscale, yscale)
            painter.scale(scale, scale)
            self.render(painter)
            painter.end()
            QMessageBox.information(self, "완료", "PDF 출력이 완료되었습니다.")

    def load_from_manager(self):
        df = self.manager.df
        self.table.setRowCount(0)
        if df.empty:
            for _ in range(5): self.add_task_group()
            return
            
        for i in range(0, len(df), 2):
            self.add_task_group()
            row_idx = self.table.rowCount() - 2
            # 계획행 (df.iloc[i])
            for col_idx, col_name in enumerate(self.manager.df.columns):
                val = str(df.iloc[i].get(col_name, ""))
                if val == "nan": val = ""
                ui_col = col_idx
                if col_idx == 8: ui_col = self.table.columnCount() - 1
                self.table.setItem(row_idx, ui_col, QTableWidgetItem(val))
            
            # 실행행 (df.iloc[i+1] if exists)
            if i + 1 < len(df):
                for col_idx, col_name in enumerate(self.manager.df.columns):
                    val = str(df.iloc[i+1].get(col_name, ""))
                    if val == "nan": val = ""
                    ui_col = col_idx
                    if col_idx == 8: ui_col = self.table.columnCount() - 1
                    self.table.setItem(row_idx + 1, ui_col, QTableWidgetItem(val))
        
        self.toggle_actual_rows(self.actual_enabled)
        self.draw_bars()

    def save_to_manager(self):
        data = []
        last_col = self.table.columnCount() - 1
        for r in range(self.table.rowCount()):
            row_data = []
            for c in range(8): # 구분 ~ 공정총액
                item = self.table.item(r, c)
                row_data.append(item.text() if item else "")
            # 비고는 마지막 컬럼에서 가져옴
            remark_item = self.table.item(r, last_col)
            row_data.append(remark_item.text() if remark_item else "")
            data.append(row_data)
        
        from core.timeplan_schema import TIMEPLAN_COLUMNS
        self.manager.df = pd.DataFrame(data, columns=TIMEPLAN_COLUMNS)

    def add_task_group(self):
        """계획행과 실행행을 한 쌍으로 추가합니다."""
        row = self.table.rowCount()
        self.table.insertRow(row) # 계획행
        self.table.insertRow(row + 1) # 실행행
        
        # 계획행 설정
        item_p = QTableWidgetItem("계획")
        item_p.setFlags(Qt.ItemIsEnabled)
        item_p.setBackground(QColor(235, 245, 251))
        self.table.setItem(row, 0, item_p)
        
        # 실행행 설정
        item_a = QTableWidgetItem("실행")
        item_a.setFlags(Qt.ItemIsEnabled)
        item_a.setBackground(QColor(234, 250, 241))
        self.table.setItem(row+1, 0, item_a)
        
        # 공정명 병합 (선택 사항이지만 여기선 그냥 두 줄 다 입력 가능하게 함)
        self.table.setItem(row, 1, QTableWidgetItem("신규 공정"))
        
        # 실행행 상태 동기화
        self.table.setRowHidden(row + 1, not self.actual_enabled)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        add_action = menu.addAction("공정 추가")
        del_action = menu.addAction("공정 삭제")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        
        if action == add_action:
            self.add_task_group()
        elif action == del_action:
            row = self.table.rowAt(pos.y())
            if row >= 0:
                # 짝을 맞춰 삭제
                if row % 2 == 1: row -= 1
                self.table.removeRow(row)
                self.table.removeRow(row)

    def draw_bars(self):
        """계획과 실행 기간을 스캔하여 막대를 그리고 '보합'을 계산합니다."""
        # 캔버스 초기화 (9번 열부터 비고 전까지)
        last_col = self.table.columnCount() - 1
        for r in range(self.table.rowCount()):
            for c in range(9, last_col):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(QColor(255, 255, 255))
        
        for r in range(0, self.table.rowCount(), 2):
            try:
                # 1. 계획 막대 그리기 (Row r)
                start_p_item = self.table.item(r, 2)
                end_p_item = self.table.item(r, 3)
                if start_p_item and end_p_item and start_p_item.text() and end_p_item.text():
                    s = int(start_p_item.text())
                    e = int(end_p_item.text())
                    duration = e - s + 1
                    
                    # 주기에 따른 칸 계산
                    s_col = 9 + (s - 1) // self.timescale
                    e_col = 9 + (e - 1) // self.timescale
                    
                    color_p = QColor(52, 152, 219) # Blue
                    for col in range(s_col, e_col + 1):
                        if 9 <= col < last_col:
                            self.set_cell_color(r, col, color_p)
                    
                    # 1-1. 일일 보합 계산 (Total Amount / Duration)
                    amt_item = self.table.item(r, 7)
                    if amt_item and amt_item.text():
                        try:
                            total_amt = float(amt_item.text().replace(',', ''))
                            daily_burn = total_amt / duration if duration > 0 else 0
                            burn_item = QTableWidgetItem(f"{daily_burn:,.0f}")
                            burn_item.setFlags(Qt.ItemIsEnabled)
                            burn_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            self.table.setItem(r, 8, burn_item)
                        except: pass
                
                # 2. 실행 막대 그리기 (Row r + 1)
                start_a = self.table.item(r + 1, 4)
                end_a = self.table.item(r + 1, 5)
                if start_a and end_a and start_a.text() and end_a.text():
                    s_a = int(start_a.text())
                    e_a = int(end_a.text())
                    
                    s_a_col = 9 + (s_a - 1) // self.timescale
                    e_a_col = 9 + (e_a - 1) // self.timescale
                    
                    # 지연 여부 판단 (계획 종료일보다 늦으면 빨간색)
                    color_a = QColor(46, 204, 113) # Green (On track)
                    if end_p_item and end_p_item.text():
                        if e_a > int(end_p_item.text()):
                            color_a = QColor(231, 76, 60) # Red (Delayed)
                    
                    for col in range(s_a_col, e_a_col + 1):
                        if 9 <= col < last_col:
                            self.set_cell_color(r + 1, col, color_a)
                            
                # 3. 성과 표시
                perf = self.table.item(r + 1, 6)
                if perf and perf.text():
                    it_p = QTableWidgetItem(perf.text())
                    it_p.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, 6, it_p)

            except Exception as ex:
                print(f"Error drawing bars for row {r}: {ex}")
        
        self.save_to_manager()

    def set_cell_color(self, r, c, color):
        item = self.table.item(r, c)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(r, c, item)
        item.setBackground(color)
