# 간소화된 DBSchema 클래스 - 핵심 기능만 유지

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

class DBSchema:
    """
    DB Manager 애플리케이션의 로컬 데이터베이스 스키마를 관리하는 클래스
    장비 유형 및 Default DB 값 저장을 위한 테이블 구조를 생성하고 관리합니다.
    컨텍스트 매니저 패턴을 사용하여 데이터베이스 연결을 효율적으로 관리합니다.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # 기존 데이터베이스 위치 사용 (프로젝트 루트/data/)
            app_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
            self.db_path = os.path.join(app_data_dir, 'local_db.sqlite')
        else:
            self.db_path = db_path
        self.create_tables()

    @contextmanager
    def get_connection(self, conn_override=None):
        conn_provided = conn_override is not None
        conn = conn_override if conn_provided else sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            if not conn_provided and conn:
                conn.close()

    def create_tables(self):
        """핵심 테이블들만 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 장비 유형 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Default DB 값 테이블 (is_performance → is_checklist로 변경)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Default_DB_Values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                default_value TEXT NOT NULL,
                min_spec TEXT,
                max_spec TEXT,
                occurrence_count INTEGER DEFAULT 1,
                total_files INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 1.0,
                source_files TEXT,
                description TEXT,
                module_name TEXT,
                part_name TEXT,
                item_type TEXT,
                is_checklist INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                UNIQUE(equipment_type_id, parameter_name)
            )
            ''')
            
            
            conn.commit()
            
            # is_performance 컬럼이 있다면 is_checklist로 마이그레이션
            self._migrate_performance_to_checklist(cursor, conn)

    def _migrate_performance_to_checklist(self, cursor, conn):
        """is_performance 컬럼을 is_checklist로 마이그레이션"""
        try:
            # 기존 컬럼이 있는지 확인
            cursor.execute("PRAGMA table_info(Default_DB_Values)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_performance' in columns and 'is_checklist' not in columns:
                # is_checklist 컬럼 추가
                cursor.execute("ALTER TABLE Default_DB_Values ADD COLUMN is_checklist INTEGER DEFAULT 0")
                
                # 기존 is_performance 값을 is_checklist로 복사
                cursor.execute("UPDATE Default_DB_Values SET is_checklist = is_performance")
                
                conn.commit()
                print("✅ is_performance → is_checklist 마이그레이션 완료")
                
        except Exception as e:
            print(f"마이그레이션 중 오류 (무시 가능): {e}")

    # ==================== 장비 유형 관리 ====================
    
    def add_equipment_type(self, type_name, description="", conn_override=None):
        """새 장비 유형 추가"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO Equipment_Types (type_name, description)
                VALUES (?, ?)
                ''', (type_name, description))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_equipment_types(self, conn_override=None):
        """모든 장비 유형 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type_name, description FROM Equipment_Types ORDER BY type_name')
            return cursor.fetchall()

    def get_equipment_type_by_name(self, type_name, conn_override=None):
        """이름으로 장비 유형 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type_name, description FROM Equipment_Types WHERE type_name = ?', (type_name,))
            return cursor.fetchone()

    def update_equipment_type(self, type_id, type_name=None, description=None, conn_override=None):
        """장비 유형 정보 업데이트"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if type_name is not None:
                update_fields.append("type_name = ?")
                params.append(type_name)
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(type_id)
                
                query = f"UPDATE Equipment_Types SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False

    def delete_equipment_type(self, type_id, conn_override=None):
        """장비 유형 삭제 (관련 Default DB 값들도 함께 삭제)"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                # 트랜잭션 시작
                cursor.execute('BEGIN TRANSACTION')
                
                # 먼저 관련된 Default DB 값들 삭제
                cursor.execute('DELETE FROM Default_DB_Values WHERE equipment_type_id = ?', (type_id,))
                deleted_params = cursor.rowcount
                
                # 장비 유형 삭제
                cursor.execute('DELETE FROM Equipment_Types WHERE id = ?', (type_id,))
                deleted_types = cursor.rowcount
                
                # 트랜잭션 커밋
                conn.commit()
                
                # 삭제된 항목이 있으면 성공
                return deleted_types > 0
                
            except Exception as e:
                # 오류 발생 시 롤백
                conn.rollback()
                raise e

    # ==================== Default DB 값 관리 ====================
    
    def add_default_value(self, equipment_type_id, parameter_name, default_value, 
                         min_spec=None, max_spec=None, occurrence_count=1, total_files=1,
                         confidence_score=1.0, source_files="", description="", 
                         module_name="", part_name="", item_type="", is_checklist=0, conn_override=None):
        """새 Default DB 값 추가"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO Default_DB_Values 
                (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                 occurrence_count, total_files, confidence_score, source_files, description,
                 module_name, part_name, item_type, is_checklist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                      occurrence_count, total_files, confidence_score, source_files, description,
                      module_name, part_name, item_type, is_checklist))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_default_values(self, equipment_type_id, checklist_only=False, conn_override=None):
        """장비 유형별 Default DB 값 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            if checklist_only:
                cursor.execute('''
                SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                       d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                       d.module_name, d.part_name, d.item_type, d.is_checklist
                FROM Default_DB_Values d
                JOIN Equipment_Types e ON d.equipment_type_id = e.id
                WHERE d.equipment_type_id = ? AND d.is_checklist = 1
                ORDER BY d.parameter_name
                ''', (equipment_type_id,))
            else:
                cursor.execute('''
                SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                       d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                       d.module_name, d.part_name, d.item_type, d.is_checklist
                FROM Default_DB_Values d
                JOIN Equipment_Types e ON d.equipment_type_id = e.id
                WHERE d.equipment_type_id = ?
                ORDER BY d.parameter_name
                ''', (equipment_type_id,))
            
            return cursor.fetchall()

    def update_default_value(self, value_id, **kwargs):
        """Default DB 값 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 업데이트 가능한 필드들
            allowed_fields = [
                'parameter_name', 'default_value', 'min_spec', 'max_spec',
                'occurrence_count', 'total_files', 'confidence_score', 'source_files',
                'description', 'module_name', 'part_name', 'item_type', 'is_checklist'
            ]
            
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(value_id)
                
                query = f"UPDATE Default_DB_Values SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False

    def delete_default_value(self, value_id, conn_override=None):
        """Default DB 값 삭제"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Default_DB_Values WHERE id = ?', (value_id,))
            conn.commit()
            return cursor.rowcount > 0


    def get_parameter_by_id(self, parameter_id, conn_override=None):
        """특정 ID의 파라미터 정보를 반환합니다"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT d.id, d.equipment_type_id, d.parameter_name, d.default_value, 
                   d.min_spec, d.max_spec, e.type_name, d.description,
                   d.module_name, d.part_name, d.item_type, d.is_checklist,
                   d.occurrence_count, d.total_files, d.confidence_score, d.source_files
            FROM Default_DB_Values d
            JOIN Equipment_Types e ON d.equipment_type_id = e.id
            WHERE d.id = ?
            ''', (parameter_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'equipment_type_id': result[1],
                    'parameter_name': result[2],
                    'default_value': result[3],
                    'min_spec': result[4],
                    'max_spec': result[5],
                    'equipment_type': result[6],
                    'description': result[7],
                    'module_name': result[8],
                    'part_name': result[9],
                    'item_type': result[10],
                    'is_performance': result[11],  # is_checklist을 is_performance로 매핑 (호환성)
                    'occurrence_count': result[12],
                    'total_files': result[13],
                    'confidence_score': result[14],
                    'source_files': result[15]
                }
            return None

    def get_parameter_statistics(self, equipment_type_id, parameter_name, conn_override=None):
        """파라미터 통계 정보 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT occurrence_count, total_files, confidence_score, source_files, default_value
            FROM Default_DB_Values 
            WHERE equipment_type_id = ? AND parameter_name = ?
            ''', (equipment_type_id, parameter_name))
            result = cursor.fetchone()
            
            if result:
                return {
                    'occurrence_count': result[0],
                    'total_files': result[1],
                    'confidence_score': result[2],
                    'source_files': result[3],
                    'default_value': result[4]
                }
            return None

    def set_performance_status(self, parameter_id, is_performance, conn_override=None):
        """파라미터의 Performance 상태 설정"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE Default_DB_Values 
            SET is_checklist = ? 
            WHERE id = ?
            ''', (1 if is_performance else 0, parameter_id))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== 유틸리티 메서드 ====================
    
    def get_checklist_parameter_count(self, equipment_type_id, conn_override=None):
        """Check list 파라미터 개수 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT COUNT(*) FROM Default_DB_Values 
            WHERE equipment_type_id = ? AND is_checklist = 1
            ''', (equipment_type_id,))
            return cursor.fetchone()[0]

    def get_total_parameter_count(self, equipment_type_id, conn_override=None):
        """전체 파라미터 개수 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT COUNT(*) FROM Default_DB_Values 
            WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            return cursor.fetchone()[0]