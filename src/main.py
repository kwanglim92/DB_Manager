#!/usr/bin/env python3
"""
DB Manager 애플리케이션 메인 진입점
"""

import sys
import os

# 현재 파일의 디렉토리를 sys.path에 추가하여 app 모듈을 찾을 수 있도록 함
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.manager import DBManager

def main():
    """메인 함수"""
    try:
        app = DBManager()
        app.window.mainloop()
    except Exception as e:
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
