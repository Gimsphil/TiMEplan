TIMEPLAN 프로그램 설계 및 개요

1. 목적
- 시간 계획(TIME PLAN) 관리, 기록, 수정, 보고, 요약을 누구나 쉽게 할 수 있는 심플한 프로그램
- 결과물은 엑셀/LibreOffice에서 열람 가능(표준 xlsx/csv)
- GUI 기반, 별도의 작업 프로그램 제공

2. 주요 기능
- 시간 계획 등록/수정/삭제
- 일정별 메모 및 태그 관리
- 기간별/조건별 요약 및 보고서 자동 생성
- 엑셀/LibreOffice 호환 파일로 내보내기 및 불러오기
- 직관적이고 심플한 인터페이스

3. 폴더 및 파일 구조
- main.py : 프로그램 진입점 (GUI)
- ui/ : GUI 레이아웃 및 리소스
- core/ : 데이터 처리, 엑셀 입출력, 요약/보고 로직
- data/ : 사용자 데이터 저장
- README.txt : 본 파일

4. 사용 기술
- Python 3.x
- PySide6 (GUI)
- pandas, openpyxl (엑셀 처리)

5. 실행 방법
- main.py 실행
- GUI에서 시간 계획 관리 및 엑셀로 내보내기

6. 기타
- 누구나 쉽게 사용 가능하도록 설계
- 심플하고 명확한 UI/UX

7. 설치 및 환경 문제 해결
- Python이 이미 설치되어 있다면, 명령 프롬프트에서 아래 명령으로 패키지 설치:
  pip install -r requirements.txt
- 실행 시 'python이 설치되지 않았다'는 메시지가 나오면:
  1) 명령 프롬프트에서 where python 입력 → 경로 확인
  2) VS Code 좌측 하단 Python 인터프리터 선택에서 올바른 경로 지정
  3) 그래도 안 되면 python 대신 python3 명령 사용
  4) 또는 python 전체 경로로 실행 (예: C:\Python311\python.exe main.py)
- 위 방법으로도 해결되지 않으면, 구체적인 에러 메시지를 복사해 개발자에게 문의
