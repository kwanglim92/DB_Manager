#!/usr/bin/env python3
import sys
import os

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

try:
    from app.schema import DBSchema
    
    # DB 스키마 초기화
    db_schema = DBSchema()
    print(f"DB 경로: {db_schema.db_path}")
    
    # NX-Mask 장비 유형 확인
    equipment_types = db_schema.get_equipment_types()
    print(f"\n장비 유형 목록:")
    for et in equipment_types:
        print(f"  ID: {et[0]}, Name: {et[1]}, Desc: {et[2]}")
    
    # NX-Mask의 파라미터 조회
    nx_mask_type = db_schema.get_equipment_type_by_name("NX-Mask")
    if nx_mask_type:
        type_id = nx_mask_type[0]
        print(f"\nNX-Mask ID: {type_id}")
        
        # get_default_values 호출 테스트
        print("\n=== get_default_values 테스트 ===")
        try:
            default_values = db_schema.get_default_values(type_id)
            print(f"조회된 파라미터 수: {len(default_values)}")
            
            for i, param in enumerate(default_values):
                print(f"  {i+1}. {param}")
                
        except Exception as e:
            print(f"get_default_values 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # checklist_only=False로 테스트
        print("\n=== checklist_only=False 테스트 ===")
        try:
            default_values = db_schema.get_default_values(type_id, checklist_only=False)
            print(f"조회된 파라미터 수: {len(default_values)}")
            
            for param in default_values:
                print(f"  - {param[1]}: {param[2]}")
                
        except Exception as e:
            print(f"checklist_only=False 오류: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("NX-Mask 장비 유형을 찾을 수 없습니다.")
    
except Exception as e:
    print(f"전체 오류: {str(e)}")
    import traceback
    traceback.print_exc()