from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
                               QPushButton, QTableView, QTabWidget, QHeaderView,
                               QFileDialog, QMessageBox, QLabel, QGroupBox, QComboBox, QDialog, QInputDialog)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from ui.table_model import PandasModel
from ui.excel_import_wizard import ExcelImportWizard
from ui.revision_compare_dialog import RevisionCompareDialog
import os

class ResourceManagementTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 안내 문구
        header = QLabel("🧱 자원 및 변경 관리 (EVM 기준 데이터)")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        main_layout.addWidget(header)

        # 메타데이터 상단 패널
        self.init_meta_panel(main_layout)

        # 서브 탭 위젯
        self.sub_tabs = QTabWidget()
        
        # 1. 계약 내역 탭 (특별 처리: 엑셀 불러오기 버튼 추가)
        self.tab_contract, self.tv_contract = self.create_table_tab('contract_df', "원계약 및 실행 예산의 기준이 되는 내역을 입력하세요.", return_tv=True, is_contract=True)
        self.sub_tabs.addTab(self.tab_contract, "계약내역 (Baseline)")

        # 2. 자재 관리 탭
        self.tab_material, self.tv_material = self.create_table_tab('material_df', "투입된 자재 내역. 사진경로 셀을 더블클릭하면 사진이 열립니다.", return_tv=True)
        self.tv_material.doubleClicked.connect(self.handle_material_double_click)
        self.sub_tabs.addTab(self.tab_material, "자재 관리 (Materials)")

        # 3. 노무 관리 탭
        self.tab_labor = self.create_table_tab('labor_df', "투입된 노무 인원, 기본급여, 식대, 사적 용돈 등을 입력하세요. '보고공개여부(공적/사적)'을 통해 마스킹이 가능합니다.")
        self.sub_tabs.addTab(self.tab_labor, "노무 관리 (Labor)")
        
        # 4. 장비 관리 탭 (신설)
        self.tab_equip = self.create_table_tab('equipment_df', "투입된 장비 및 중장비 내역, 기사 급여, 식대, 사적 용돈 등을 입력하세요.")
        self.sub_tabs.addTab(self.tab_equip, "장비/중장비 관리 (Equipment)")

        # 5. 리스크/변경 탭
        self.tab_issue = self.create_table_tab('issue_df', "설계변경, 오너 요구사항 등 변수 내역을 입력하세요.")
        self.sub_tabs.addTab(self.tab_issue, "변수/변경 관리 (Issues)")

        main_layout.addWidget(self.sub_tabs)
        self.setLayout(main_layout)
        self.load_meta_to_ui()

    def init_meta_panel(self, parent_layout):
        gb = QGroupBox("프로젝트 간접비 및 기본 정보")
        gb.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        grid = QGridLayout()
        
        self.meta_inputs = {}
        fields = [
            ("프로젝트명", 0, 0), ("프로젝트기간", 0, 2), ("계약조건", 0, 4),
            ("총순공사비", 1, 0), ("세율", 1, 2), ("안전관리비", 1, 4),
            ("일반관리비", 2, 0), ("기타공과잡비", 2, 2), ("총계약금액(도급액)", 2, 4)
        ]
        
        for name, r, c in fields:
            grid.addWidget(QLabel(name), r, c)
            le = QLineEdit()
            le.textChanged.connect(self.save_meta_from_ui)
            grid.addWidget(le, r, c+1)
            self.meta_inputs[name] = le
            
        gb.setLayout(grid)
        parent_layout.addWidget(gb)

    def load_meta_to_ui(self):
        df = self.manager.project_meta_df
        if not df.empty:
            for col in df.columns:
                if col in self.meta_inputs:
                    # 블로킹 시그널로 무한 루프 방지
                    self.meta_inputs[col].blockSignals(True)
                    self.meta_inputs[col].setText(str(df[col].iloc[0]))
                    self.meta_inputs[col].blockSignals(False)

    def save_meta_from_ui(self):
        df = self.manager.project_meta_df
        if df.empty:
            df.loc[0] = [""] * len(df.columns)
        for col, le in self.meta_inputs.items():
            if col in df.columns:
                df.at[0, col] = le.text()
        # 메타데이터가 바뀌면 대시보드도 갱신해야 할 수 있음 (최상위에서 처리)

    def create_table_tab(self, df_attr_name, desc_text, return_tv=False, is_contract=False):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 계약 내역 탭 전용 리비전 컨트롤러
        if is_contract:
            rev_layout = QHBoxLayout()
            rev_layout.addWidget(QLabel("현재 리비전(버전):"))
            
            self.cb_revision = QComboBox()
            self.cb_revision.addItems(self.manager.contract_revisions.keys())
            self.cb_revision.setCurrentText(self.manager.active_rev_key)
            self.cb_revision.currentTextChanged.connect(self.change_revision)
            rev_layout.addWidget(self.cb_revision)
            
            btn_new_rev = QPushButton("➕ 새 버전(Rev)으로 백업/복제")
            btn_new_rev.clicked.connect(self.create_new_revision)
            rev_layout.addWidget(btn_new_rev)
            
            btn_compare = QPushButton("🔍 버전 간 비교 분석(Diff)")
            btn_compare.clicked.connect(self.open_compare_dialog)
            rev_layout.addWidget(btn_compare)
            
            btn_export_eng = QPushButton("🇺🇸 영문(English) 엑셀 내보내기")
            btn_export_eng.setStyleSheet("background-color: #2980b9; color: white;")
            btn_export_eng.clicked.connect(self.export_english_boq)
            rev_layout.addWidget(btn_export_eng)
            
            rev_layout.addStretch()
            layout.addLayout(rev_layout)
        
        desc = QLabel(desc_text)
        desc.setStyleSheet("color: #555;")
        layout.addWidget(desc)
        
        tv = QTableView()
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tv.setShowGrid(True)
        tv.setGridStyle(Qt.SolidLine)
        tv.setStyleSheet("QTableView { gridline-color: #d3d3d3; }")
        layout.addWidget(tv)
        
        btn_layout = QHBoxLayout()
        # 행 추가 버튼 제거: 마지막 줄 입력 시 자동으로 생성되도록 UX 개선
        
        if is_contract:
            btn_excel = QPushButton("📊 다국어 엑셀 내역서 스마트 매핑")
            btn_excel.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
            btn_excel.clicked.connect(self.open_excel_wizard)
            btn_layout.addWidget(btn_excel)
            
        if df_attr_name == 'material_df':
            btn_photo = QPushButton("사진 파일 선택하여 셀에 넣기")
            btn_photo.clicked.connect(lambda: self.attach_photo_to_selected(tv, df_attr_name))
            btn_layout.addWidget(btn_photo)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.refresh_single_table(tv, df_attr_name)
        
        # 참조 보관
        setattr(self, f"tv_{df_attr_name}", tv)
        
        if return_tv:
            return widget, tv
        return widget

    def refresh_single_table(self, tv, df_attr_name):
        df = getattr(self.manager, df_attr_name)
        model = PandasModel(df)
        tv.setModel(model)

    def refresh_all_tables(self):
        for attr in ['contract_df', 'material_df', 'labor_df', 'equipment_df', 'issue_df']:
            tv = getattr(self, f"tv_{attr}")
            self.refresh_single_table(tv, attr)

    def add_row(self, df_attr_name, tv):
        # Deprecated: Auto-expanding table model used instead.
        pass

    def open_excel_wizard(self):
        wizard = ExcelImportWizard(self)
        if wizard.exec() == QDialog.Accepted:
            mapped_df = wizard.mapped_df
            if mapped_df is not None and not mapped_df.empty:
                reply = QMessageBox.question(self, "적용", "매핑된 데이터를 가져오시겠습니까?\n(현재 리비전의 내역이 덮어씌워집니다.)",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.manager.contract_df = mapped_df.copy()
                    self.refresh_single_table(self.tv_contract, 'contract_df')
                    QMessageBox.information(self, "완료", "엑셀 내역이 성공적으로 반영되었습니다.")

    def change_revision(self, rev_name):
        if rev_name and rev_name in self.manager.contract_revisions:
            self.manager.active_rev_key = rev_name
            self.refresh_single_table(self.tv_contract, 'contract_df')

    def create_new_revision(self):
        new_name, ok = QInputDialog.getText(self, "새 버전 생성", "새로운 리비전 이름을 입력하세요:\n(예: Rev.1_설계변경_2408)")
        if ok and new_name:
            try:
                self.manager.create_new_revision(new_name)
                self.cb_revision.addItem(new_name)
                self.cb_revision.setCurrentText(new_name)
                QMessageBox.information(self, "완료", f"{new_name} 버전을 성공적으로 생성하고 원본을 복제했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))

    def open_compare_dialog(self):
        dialog = RevisionCompareDialog(self.manager, self)
        dialog.exec()

    def export_english_boq(self):
        fname, _ = QFileDialog.getSaveFileName(self, "영문 엑셀 내보내기", f"BoQ_{self.manager.active_rev_key}_English.xlsx", "Excel Files (*.xlsx)")
        if fname:
            try:
                self.manager.export_english_boq(fname)
                QMessageBox.information(self, "완료", "영문 내역서(BoQ)가 성공적으로 추출되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))

    def attach_photo_to_selected(self, tv, df_attr_name):
        indexes = tv.selectionModel().selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "경고", "사진 경로를 입력할 셀을 먼저 선택하세요.")
            return
            
        fname, _ = QFileDialog.getOpenFileName(self, "사진 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if fname:
            idx = indexes[0]
            df = getattr(self.manager, df_attr_name)
            df.iloc[idx.row(), idx.column()] = fname
            self.refresh_single_table(tv, df_attr_name)

    def handle_material_double_click(self, index):
        df = self.manager.material_df
        col_name = df.columns[index.column()]
        if col_name == "사진경로":
            path = df.iloc[index.row(), index.column()]
            if path and os.path.exists(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            elif path:
                QMessageBox.warning(self, "경고", f"파일을 찾을 수 없습니다:\n{path}")
