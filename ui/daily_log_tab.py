import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, 
                               QLabel, QLineEdit, QTextEdit, QPushButton, QFormLayout, 
                               QGroupBox, QScrollArea, QFileDialog, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QDate

class DailyLogTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.current_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.init_ui()
        self.load_date_data(self.current_date)

    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # 좌측 패널: 달력 및 검색
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)
        
        search_group = QGroupBox("로그 검색")
        search_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력 (작업내용 등)...")
        btn_search = QPushButton("검색")
        btn_search.clicked.connect(self.search_logs)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)
        left_layout.addStretch()
        
        # 우측 패널: 일지 작성 폼
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.date_label = QLabel(f"📅 {self.current_date} 작업일지")
        self.date_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        right_layout.addWidget(self.date_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        
        self.inputs = {}
        
        # 기본 정보
        self.add_input("날씨")
        self.add_input("근무시간")
        self.add_input("야간/추가작업")
        
        # 동원 현황
        self.add_input("장비동원")
        self.add_input("노무(인력동원)")
        self.add_input("경비")
        
        # 인원 및 일정
        self.add_input("전일까지인원누계")
        self.add_input("금일출력인원")
        self.add_input("내일작업예정")
        
        # 공정률 (%)
        self.add_input("전일공정률(%)")
        self.add_input("금일성과(%)")
        self.add_input("내일예정(%)")
        self.add_input("잔여공정(%)")
        
        # 텍스트 영역 (상세)
        self.inputs["작업내용"] = QTextEdit()
        self.form_layout.addRow("작업내용", self.inputs["작업내용"])
        
        self.inputs["발주처요구사항"] = QTextEdit()
        self.form_layout.addRow("발주처요구사항", self.inputs["발주처요구사항"])
        
        self.inputs["본사지시사항"] = QTextEdit()
        self.form_layout.addRow("본사지시사항", self.inputs["본사지시사항"])
        
        self.inputs["현장변경/특기사항"] = QTextEdit()
        self.form_layout.addRow("현장변경/특기사항", self.inputs["현장변경/특기사항"])
        
        # 사진 경로
        pic_layout = QHBoxLayout()
        self.inputs["사진경로"] = QLineEdit()
        btn_pic = QPushButton("사진 선택")
        btn_pic.clicked.connect(self.select_photo)
        pic_layout.addWidget(self.inputs["사진경로"])
        pic_layout.addWidget(btn_pic)
        self.form_layout.addRow("사진경로", pic_layout)
        
        scroll.setWidget(form_container)
        right_layout.addWidget(scroll)
        
        btn_save = QPushButton("💾 현재 날짜 일지 저장")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_save.clicked.connect(self.save_current_log)
        right_layout.addWidget(btn_save)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def add_input(self, label):
        le = QLineEdit()
        self.form_layout.addRow(label, le)
        self.inputs[label] = le

    def on_date_selected(self, qdate):
        self.current_date = qdate.toString("yyyy-MM-dd")
        self.date_label.setText(f"📅 {self.current_date} 작업일지")
        self.load_date_data(self.current_date)
        self.auto_calculate_progress()

    def auto_calculate_progress(self):
        """EVM 데이터를 기반으로 금일 성과 및 공정률 자동 계산"""
        evm = self.manager.calculate_evm()
        total_budget = evm.get("최종실행예산", 0)
        if total_budget <= 0: return

        date_str = self.current_date
        
        # 1. 금일 투입 원가 계산
        m_today = self.manager.material_df[self.manager.material_df["일자"] == date_str]["실제총액"].apply(pd.to_numeric, errors='coerce').sum()
        l_today = self.manager.labor_df[self.manager.labor_df["일자"] == date_str]["노무비총액"].apply(pd.to_numeric, errors='coerce').sum()
        e_today = self.manager.equipment_df[self.manager.equipment_df["일자"] == date_str]["장비비총액"].apply(pd.to_numeric, errors='coerce').sum()
        today_cost = m_today + l_today + e_today
        
        # 2. 전일까지 누적 원가 계산
        # 일자를 날짜형으로 변환하여 비교
        m_all = self.manager.material_df.copy()
        m_all["일자"] = pd.to_datetime(m_all["일자"], errors='coerce')
        prev_cost_m = m_all[m_all["일자"] < pd.to_datetime(date_str)]["실제총액"].apply(pd.to_numeric, errors='coerce').sum()
        
        l_all = self.manager.labor_df.copy()
        l_all["일자"] = pd.to_datetime(l_all["일자"], errors='coerce')
        prev_cost_l = l_all[l_all["일자"] < pd.to_datetime(date_str)]["노무비총액"].apply(pd.to_numeric, errors='coerce').sum()
        
        e_all = self.manager.equipment_df.copy()
        e_all["일자"] = pd.to_datetime(e_all["일자"], errors='coerce')
        prev_cost_e = e_all[e_all["일자"] < pd.to_datetime(date_str)]["장비비총액"].apply(pd.to_numeric, errors='coerce').sum()
        
        prev_total_cost = prev_cost_m + prev_cost_l + prev_cost_e
        
        # 3. 퍼센트 산출
        today_perf = (today_cost / total_budget) * 100
        prev_progress = (prev_total_cost / total_budget) * 100
        rem_progress = 100 - (prev_progress + today_perf)
        
        # 4. UI 반영 (사용자 입력값이 없을 때만 자동 채우기)
        if not self.inputs["금일성과(%)"].text():
            self.inputs["금일성과(%)"].setText(f"{today_perf:.2f}")
        if not self.inputs["전일공정률(%)"].text():
            self.inputs["전일공정률(%)"].setText(f"{prev_progress:.2f}")
        if not self.inputs["잔여공정(%)"].text():
            self.inputs["잔여공정(%)"].setText(f"{max(0, rem_progress):.2f}")

    def load_date_data(self, date_str):
        # 데이터프레임에서 해당 날짜 찾기
        df = self.manager.daily_log_df
        row = df[df["일자"] == date_str]
        
        # 폼 초기화
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                widget.setText("")
            elif isinstance(widget, QTextEdit):
                widget.setPlainText("")
        
        if not row.empty:
            for key, widget in self.inputs.items():
                val = row.iloc[0].get(key, "")
                if pd.isna(val): val = ""
                if isinstance(widget, QLineEdit):
                    widget.setText(str(val))
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(str(val))

    def save_current_log(self):
        df = self.manager.daily_log_df
        date_str = self.current_date
        
        new_data = {"일자": date_str}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                new_data[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                new_data[key] = widget.toPlainText()
        
        # 기존 날짜 있으면 업데이트, 없으면 추가
        idx = df[df["일자"] == date_str].index
        if not idx.empty:
            for k, v in new_data.items():
                self.manager.daily_log_df.at[idx[0], k] = v
        else:
            self.manager.daily_log_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            
        QMessageBox.information(self, "저장 완료", f"{date_str} 일지가 성공적으로 저장되었습니다.")

    def select_photo(self):
        fname, _ = QFileDialog.getOpenFileName(self, "사진 선택", "", "Images (*.png *.jpg *.jpeg *.gif)")
        if fname:
            self.inputs["사진경로"].setText(fname)

    def search_logs(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return
            
        df = self.manager.daily_log_df
        # 모든 텍스트 열에서 검색
        mask = df.apply(lambda row: row.astype(str).str.contains(keyword).any(), axis=1)
        results = df[mask]
        
        if results.empty:
            QMessageBox.information(self, "검색 결과", f"'{keyword}'에 대한 검색 결과가 없습니다.")
        else:
            dates = results["일자"].tolist()
            QMessageBox.information(self, "검색 결과", f"다음 날짜에서 검색되었습니다:\n" + "\n".join(dates[:10]) + ("\n..." if len(dates) > 10 else ""))
            # 첫 번째 결과 날짜로 이동할지 물어보기
            if dates:
                first_date = QDate.fromString(dates[0], "yyyy-MM-dd")
                self.calendar.setSelectedDate(first_date)
                self.on_date_selected(first_date)
