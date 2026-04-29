"""
TIMEPLAN 메인 실행 파일
- GUI 기반 시간 계획 관리 프로그램
- 엑셀/LibreOffice 호환 결과물 생성
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
