#!/usr/bin/env python3
import sys
import os

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

try:
    from app.schema import DBSchema
    print("DBSchema 클래스 import 성공")
    
    # DBSchema 인스턴스 생성 시도
    try:
        db_schema = DBSchema()
        print(f"DBSchema 초기화 성공: {db_schema}")
        print(f"DB 경로: {db_schema.db_path}")
        
        # DB 파일 존재 여부 확인
        if os.path.exists(db_schema.db_path):
            print("DB 파일 존재함")
        else:
            print("DB 파일 존재하지 않음")
            
    except Exception as e:
        print(f"DBSchema 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"DBSchema import 실패: {str(e)}")
    import traceback
    traceback.print_exc()