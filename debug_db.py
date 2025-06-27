#!/usr/bin/env python3
import sys
import os
import sqlite3

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

try:
    from app.schema import DBSchema
    
    # DB 스키마 초기화
    db_schema = DBSchema()
    print(f"DB 경로: {db_schema.db_path}")
    
    # 직접 SQLite 연결해서 데이터 확인
    conn = sqlite3.connect(db_schema.db_path)
    cursor = conn.cursor()
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n테이블 목록: {[table[0] for table in tables]}")
    
    # Equipment_Types 테이블 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM Equipment_Types")
    equipment_count = cursor.fetchone()[0]
    print(f"\nEquipment_Types 개수: {equipment_count}")
    
    if equipment_count > 0:
        cursor.execute("SELECT id, type_name, description FROM Equipment_Types")
        equipment_types = cursor.fetchall()
        print("Equipment_Types 목록:")
        for et in equipment_types:
            print(f"  ID: {et[0]}, Name: {et[1]}, Desc: {et[2]}")
    
    # Default_DB_Values 테이블 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM Default_DB_Values")
    values_count = cursor.fetchone()[0]
    print(f"\nDefault_DB_Values 개수: {values_count}")
    
    if values_count > 0:
        cursor.execute("""
        SELECT d.id, d.parameter_name, d.default_value, e.type_name 
        FROM Default_DB_Values d 
        JOIN Equipment_Types e ON d.equipment_type_id = e.id 
        LIMIT 10
        """)
        values = cursor.fetchall()
        print("Default_DB_Values 샘플 (최대 10개):")
        for v in values:
            print(f"  ID: {v[0]}, Param: {v[1]}, Value: {v[2]}, Type: {v[3]}")
    
    # 특정 장비 유형의 파라미터 확인 (NX-Mask)
    cursor.execute("SELECT id FROM Equipment_Types WHERE type_name = 'NX-Mask'")
    nx_mask_result = cursor.fetchone()
    if nx_mask_result:
        nx_mask_id = nx_mask_result[0]
        print(f"\nNX-Mask 장비 유형 ID: {nx_mask_id}")
        
        cursor.execute("SELECT COUNT(*) FROM Default_DB_Values WHERE equipment_type_id = ?", (nx_mask_id,))
        nx_mask_params = cursor.fetchone()[0]
        print(f"NX-Mask 파라미터 개수: {nx_mask_params}")
        
        if nx_mask_params > 0:
            cursor.execute("""
            SELECT parameter_name, default_value, min_value, max_value 
            FROM Default_DB_Values 
            WHERE equipment_type_id = ? 
            LIMIT 5
            """, (nx_mask_id,))
            params = cursor.fetchall()
            print("NX-Mask 파라미터 샘플:")
            for p in params:
                print(f"  {p[0]}: {p[1]} (min: {p[2]}, max: {p[3]})")
    else:
        print("\nNX-Mask 장비 유형을 찾을 수 없습니다.")
    
    conn.close()
    
except Exception as e:
    print(f"오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()