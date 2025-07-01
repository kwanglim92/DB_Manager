#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB Manager Debug Toolkit
통합된 디버그 및 진단 도구

이 도구는 다음 기능들을 제공합니다:
1. DB 스키마 및 연결 상태 확인
2. 파라미터 조회 및 검증
3. 서비스 레이어 상태 진단
4. 데이터 무결성 검사
"""

import sys
import os
import sqlite3
from datetime import datetime

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

class DebugToolkit:
    """통합 디버그 도구"""
    
    def __init__(self):
        self.db_schema = None
        self.service_factory = None
        
    def initialize_components(self):
        """컴포넌트 초기화"""
        try:
            from app.schema import DBSchema
            self.db_schema = DBSchema()
            print(f"✅ DB 스키마 초기화 성공: {self.db_schema.db_path}")
            
            # 서비스 팩토리 초기화 시도
            try:
                from app.services import ServiceFactory, SERVICES_AVAILABLE
                if SERVICES_AVAILABLE:
                    self.service_factory = ServiceFactory(self.db_schema)
                    print("✅ 서비ス 팩토리 초기화 성공")
                else:
                    print("⚠️ 서비스 레이어 비활성화")
            except ImportError:
                print("⚠️ 서비스 팩토리 사용 불가")
                
            return True
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            return False
    
    def check_database_health(self):
        """데이터베이스 상태 확인"""
        print("\n🔍 데이터베이스 상태 확인")
        print("=" * 50)
        
        if not self.db_schema:
            print("❌ DB 스키마가 초기화되지 않음")
            return False
            
        try:
            conn = sqlite3.connect(self.db_schema.db_path)
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 테이블 목록: {tables}")
            
            # 각 테이블 데이터 개수 확인
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count}개 레코드")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ DB 상태 확인 실패: {e}")
            return False
    
    def check_equipment_types(self):
        """장비 유형 확인"""
        print("\n🔍 장비 유형 확인")
        print("=" * 50)
        
        if not self.db_schema:
            return False
            
        try:
            equipment_types = self.db_schema.get_equipment_types()
            print(f"📊 총 {len(equipment_types)}개 장비 유형:")
            
            for et in equipment_types:
                print(f"  🏭 ID: {et[0]}, Name: {et[1]}, Desc: {et[2]}")
                
                # 각 장비 유형별 파라미터 개수 확인
                try:
                    default_values = self.db_schema.get_default_values(et[0])
                    performance_count = sum(1 for dv in default_values if len(dv) > 14 and dv[14] == 1)
                    print(f"    📋 파라미터: {len(default_values)}개 (Check list: {performance_count}개)")
                except Exception as e:
                    print(f"    ❌ 파라미터 조회 실패: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 장비 유형 확인 실패: {e}")
            return False
    
    def check_service_layer(self):
        """서비스 레이어 상태 확인"""
        print("\n🔍 서비스 레이어 상태 확인")
        print("=" * 50)
        
        if not self.service_factory:
            print("⚠️ 서비스 팩토리 비활성화")
            return False
            
        try:
            status = self.service_factory.get_service_status()
            print(f"📊 등록된 서비스: {len(status)}개")
            
            for service_name, service_info in status.items():
                print(f"  🔧 {service_name}: {service_info}")
            
            return True
            
        except Exception as e:
            print(f"❌ 서비스 레이어 확인 실패: {e}")
            return False
    
    def test_parameter_operations(self, equipment_type_name="NX-Mask"):
        """파라미터 조작 테스트"""
        print(f"\n🔍 {equipment_type_name} 파라미터 조작 테스트")
        print("=" * 50)
        
        if not self.db_schema:
            return False
            
        try:
            # 장비 유형 조회
            equipment_type = self.db_schema.get_equipment_type_by_name(equipment_type_name)
            if not equipment_type:
                print(f"❌ {equipment_type_name} 장비 유형을 찾을 수 없음")
                return False
            
            type_id = equipment_type[0]
            print(f"✅ {equipment_type_name} ID: {type_id}")
            
            # 파라미터 조회 테스트
            default_values = self.db_schema.get_default_values(type_id)
            print(f"📊 조회된 파라미터: {len(default_values)}개")
            
            # Check list 필터링 테스트
            checklist_values = self.db_schema.get_default_values(type_id, checklist_only=True)
            print(f"📊 Check list 파라미터: {len(checklist_values)}개")
            
            # 샘플 파라미터 표시
            if default_values:
                print("📋 샘플 파라미터 (최대 5개):")
                for i, param in enumerate(default_values[:5]):
                    param_name = param[1] if len(param) > 1 else "Unknown"
                    param_value = param[2] if len(param) > 2 else "N/A"
                    is_checklist = "Yes" if len(param) > 14 and param[14] == 1 else "No"
                    print(f"  {i+1}. {param_name}: {param_value} (Check list: {is_checklist})")
            
            return True
            
        except Exception as e:
            print(f"❌ 파라미터 테스트 실패: {e}")
            return False
    
    def run_comprehensive_check(self):
        """종합 진단 실행"""
        print("🚀 DB Manager 종합 진단 시작")
        print("=" * 60)
        print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 초기화
        if not self.initialize_components():
            return False
        
        # 진단 항목들
        checks = [
            ("데이터베이스 상태", self.check_database_health),
            ("장비 유형", self.check_equipment_types),
            ("서비스 레이어", self.check_service_layer),
            ("파라미터 조작", self.test_parameter_operations)
        ]
        
        results = []
        for check_name, check_func in checks:
            print()
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                print(f"❌ {check_name} 진단 중 예외: {e}")
                results.append((check_name, False))
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 진단 결과 요약")
        print("=" * 60)
        
        passed = 0
        for check_name, result in results:
            status = "✅ 정상" if result else "❌ 문제"
            print(f"{status} {check_name}")
            if result:
                passed += 1
        
        print("=" * 60)
        print(f"전체 결과: {passed}/{len(results)} 정상")
        
        if passed == len(results):
            print("\n🎉 모든 진단 항목이 정상입니다!")
        else:
            print(f"\n⚠️ {len(results) - passed}개 항목에 문제가 있습니다.")
        
        return passed == len(results)

def main():
    """메인 실행 함수"""
    toolkit = DebugToolkit()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            toolkit.initialize_components()
            toolkit.check_database_health()
        elif command == "equipment":
            toolkit.initialize_components()
            toolkit.check_equipment_types()
        elif command == "services":
            toolkit.initialize_components()
            toolkit.check_service_layer()
        elif command == "params":
            toolkit.initialize_components()
            equipment_name = sys.argv[2] if len(sys.argv) > 2 else "NX-Mask"
            toolkit.test_parameter_operations(equipment_name)
        else:
            print("사용법: python debug_toolkit.py [health|equipment|services|params] [equipment_name]")
    else:
        # 기본: 종합 진단
        toolkit.run_comprehensive_check()

if __name__ == "__main__":
    main()