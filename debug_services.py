#!/usr/bin/env python3
import sys
import os

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

# 서비스 팩토리 import 확인
try:
    from app.services import ServiceFactory, LegacyAdapter, SERVICES_AVAILABLE
    print(f"SERVICES_AVAILABLE: {SERVICES_AVAILABLE}")
    print("ServiceFactory import 성공")
    
    # DBSchema도 함께 초기화
    from app.schema import DBSchema
    db_schema = DBSchema()
    print(f"DB 스키마 초기화 성공: {db_schema}")
    
    # 서비스 팩토리 초기화
    service_factory = ServiceFactory(db_schema)
    print(f"ServiceFactory 초기화 성공: {service_factory}")
    print(f"서비스 팩토리의 DB 스키마: {service_factory._db_schema}")
    
    # 서비스 상태 확인
    status = service_factory.get_service_status()
    print(f"서비스 상태: {status}")
    
except Exception as e:
    print(f"ServiceFactory 초기화 실패: {str(e)}")
    import traceback
    traceback.print_exc()