#!/usr/bin/env python3
"""
DB Manager 최적화 버전 - 메인 진입점
Mother DB 관리를 위한 효율적인 워크플로우 제공
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.app_controller import AppController

def main():
    """메인 함수"""
    try:
        # 애플리케이션 컨트롤러 생성 및 실행
        app = AppController()
        app.run()
    except Exception as e:
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()