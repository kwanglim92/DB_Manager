# DBSchema 클래스 및 DB 관련 기능

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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                UNIQUE(equipment_type_id, parameter_name)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Change_History (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_type TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                username TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 기존 테이블 업데이트 - 새 컬럼들 추가
            self._update_existing_tables(cursor)
            conn.commit()

    def _update_existing_tables(self, cursor):
        """기존 데이터베이스 테이블에 새 컬럼들을 추가합니다."""
        try:
            # Default_DB_Values 테이블에 새 컬럼들이 있는지 확인
            cursor.execute("PRAGMA table_info(Default_DB_Values)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 필요한 컬럼들을 하나씩 추가
            new_columns = [
                ('occurrence_count', 'INTEGER DEFAULT 1'),
                ('total_files', 'INTEGER DEFAULT 1'),
                ('confidence_score', 'REAL DEFAULT 1.0'),
                ('source_files', 'TEXT DEFAULT ""'),
                ('description', 'TEXT DEFAULT ""'),  # 🆕 설명 컬럼 추가
                ('module_name', 'TEXT DEFAULT ""'),   # 🆕 Module 정보 추가
                ('part_name', 'TEXT DEFAULT ""'),     # 🆕 Part 정보 추가
                ('item_type', 'TEXT DEFAULT ""'),     # 🆕 데이터 타입 정보 추가
                ('is_performance', 'BOOLEAN DEFAULT 0')  # 🆕 Performance 항목 구분 추가
            ]
            
            for column_name, column_def in new_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f'ALTER TABLE Default_DB_Values ADD COLUMN {column_name} {column_def}')
                        print(f"컬럼 '{column_name}' 추가 완료")
                    except Exception as e:
                        print(f"컬럼 '{column_name}' 추가 실패: {e}")
            
            # Change_History 테이블에 username 컬럼이 있는지 확인
            cursor.execute("PRAGMA table_info(Change_History)")
            history_columns = [column[1] for column in cursor.fetchall()]
            
            if 'username' not in history_columns:
                try:
                    cursor.execute('ALTER TABLE Change_History ADD COLUMN username TEXT DEFAULT ""')
                    print("Change_History 테이블에 'username' 컬럼 추가 완료")
                except Exception as e:
                    print(f"Change_History 테이블에 'username' 컬럼 추가 실패: {e}")
                        
        except Exception as e:
            print(f"테이블 업데이트 중 오류: {e}")
            # 테이블이 존재하지 않는 경우는 무시 (새로 생성될 예정)

    def add_equipment_type(self, type_name, description=""):
        """
        새 장비 유형을 추가합니다.
        
        Args:
            type_name (str): 장비 유형 이름
            description (str, optional): 장비 유형 설명
            
        Returns:
            int: 새로 생성된 장비 유형의 ID 또는 이미 존재하는 경우 기존 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 이미 존재하는지 확인
            cursor.execute("SELECT id FROM Equipment_Types WHERE type_name = ?", (type_name,))
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # 새 장비 유형 추가
            cursor.execute(
                "INSERT INTO Equipment_Types (type_name, description) VALUES (?, ?)",
                (type_name, description)
            )
            conn.commit()
            return cursor.lastrowid

    def get_equipment_types(self):
        """
        모든 장비 유형 목록을 반환합니다.
        
        Returns:
            list: (id, type_name, description) 튜플의 리스트
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, type_name, description FROM Equipment_Types ORDER BY type_name")
            return cursor.fetchall()

    def add_default_value(self, equipment_type_id, parameter_name, default_value, min_spec=None, max_spec=None, 
                         occurrence_count=1, total_files=1, source_files="", description="", 
                         module_name="", part_name="", item_type="", is_performance=False, conn_override=None):
        """
        장비 유형에 대한 기본 DB 값을 추가하거나 업데이트합니다.
        중복도 기반 통계 정보를 포함하여 관리합니다.
        
        Args:
            equipment_type_id (int): 장비 유형 ID
            parameter_name (str): 파라미터 이름
            default_value (str): 설정값
            min_spec (str, optional): 최소 허용값
            max_spec (str, optional): 최대 허용값
            occurrence_count (int): 해당 값이 발생한 횟수
            total_files (int): 전체 파일 수
            source_files (str): 소스 파일 목록
            description (str, optional): 파라미터 설명
            module_name (str, optional): 모듈명 (텍스트 파일의 Module)
            part_name (str, optional): 부품명 (텍스트 파일의 Part)
            item_type (str, optional): 데이터 타입 (텍스트 파일의 ItemType)
            is_performance (bool, optional): Performance 항목 여부
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            int: 새로 생성되거나 업데이트된 레코드의 ID
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 이미 존재하는지 확인
            cursor.execute(
                "SELECT id, occurrence_count, total_files, source_files FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                (equipment_type_id, parameter_name)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 기존 값 업데이트 - 통계 정보 누적
                record_id, old_occurrence, old_total, old_sources = existing
                new_occurrence = old_occurrence + occurrence_count
                new_total = old_total + total_files
                confidence_score = new_occurrence / new_total if new_total > 0 else 0.0
                
                # 소스 파일 정보 병합
                old_source_list = old_sources.split(',') if old_sources else []
                new_source_list = source_files.split(',') if source_files else []
                combined_sources = list(set(old_source_list + new_source_list))
                combined_sources_str = ','.join([s.strip() for s in combined_sources if s.strip()])
                
                cursor.execute(
                    """UPDATE Default_DB_Values 
                       SET default_value = ?, min_spec = ?, max_spec = ?, 
                           occurrence_count = ?, total_files = ?, confidence_score = ?,
                           source_files = ?, description = ?, module_name = ?, part_name = ?, item_type = ?, is_performance = ?,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (default_value, min_spec, max_spec, new_occurrence, new_total, 
                     confidence_score, combined_sources_str, description, module_name, part_name, item_type, is_performance, record_id)
                )
                conn.commit()
                return record_id
            else:
                # 새 값 추가
                confidence_score = occurrence_count / total_files if total_files > 0 else 1.0
                cursor.execute(
                    """INSERT INTO Default_DB_Values 
                       (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                        occurrence_count, total_files, confidence_score, source_files, description,
                        module_name, part_name, item_type, is_performance)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                     occurrence_count, total_files, confidence_score, source_files, description,
                     module_name, part_name, item_type, is_performance)
                )
                conn.commit()
                return cursor.lastrowid

    def get_default_values(self, equipment_type_id=None, performance_only=False, conn_override=None):
        """
        특정 장비 유형 또는 모든 장비 유형에 대한 기본 DB 값을 반환합니다.
        
        Args:
            equipment_type_id (int, optional): 장비 유형 ID. None이면 모든 값 반환
            performance_only (bool, optional): True이면 Performance 항목만 반환
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            list: DB 값 레코드 리스트 (id, parameter_name, default_value, min_spec, max_spec, type_name,
                  occurrence_count, total_files, confidence_score, source_files, description,
                  module_name, part_name, item_type, is_performance)
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # Performance 필터 조건 추가
            performance_filter = " AND d.is_performance = 1" if performance_only else ""
            
            if equipment_type_id is not None:
                cursor.execute(
                    f"""SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                              d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                              d.module_name, d.part_name, d.item_type, d.is_performance
                       FROM Default_DB_Values d
                       JOIN Equipment_Types e ON d.equipment_type_id = e.id
                       WHERE d.equipment_type_id = ?{performance_filter}
                       ORDER BY d.confidence_score DESC, d.parameter_name""",
                    (equipment_type_id,)
                )
            else:
                cursor.execute(
                    f"""SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                              d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                              d.module_name, d.part_name, d.item_type, d.is_performance
                       FROM Default_DB_Values d
                       JOIN Equipment_Types e ON d.equipment_type_id = e.id
                       WHERE 1=1{performance_filter}
                       ORDER BY e.type_name, d.confidence_score DESC, d.parameter_name"""
                )
            
            return cursor.fetchall()

    def get_parameter_by_id(self, parameter_id, conn_override=None):
        """
        특정 ID의 파라미터 정보를 반환합니다.
        
        Args:
            parameter_id (int): 파라미터 ID
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            dict: 파라미터 정보 딕셔너리 또는 None
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT d.id, d.equipment_type_id, d.parameter_name, d.default_value, 
                          d.min_spec, d.max_spec, e.type_name, d.description,
                          d.module_name, d.part_name, d.item_type, d.is_performance
                   FROM Default_DB_Values d
                   JOIN Equipment_Types e ON d.equipment_type_id = e.id
                   WHERE d.id = ?""",
                (parameter_id,)
            )
            
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
                    'is_performance': result[11]
                }
            return None

    def get_parameter_statistics(self, equipment_type_id, parameter_name):
        """
        특정 파라미터의 통계 정보를 반환합니다.
        
        Args:
            equipment_type_id (int): 장비 유형 ID
            parameter_name (str): 파라미터 이름
            
        Returns:
            dict: 통계 정보 딕셔너리
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT occurrence_count, total_files, confidence_score, source_files, default_value
                   FROM Default_DB_Values 
                   WHERE equipment_type_id = ? AND parameter_name = ?""",
                (equipment_type_id, parameter_name)
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'occurrence_count': result[0],
                    'total_files': result[1],
                    'confidence_score': result[2],
                    'source_files': result[3].split(',') if result[3] else [],
                    'default_value': result[4],
                    'occurrence_rate': f"{(result[2] * 100):.1f}%" if result[2] else "0%"
                }
            return None

    def delete_equipment_type(self, equipment_type_id):
        """
        장비 유형과 관련된 모든 기본 DB 값을 삭제합니다.
        
        Args:
            equipment_type_id (int): 삭제할 장비 유형 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 트랜잭션 시작
                conn.execute("BEGIN TRANSACTION")
                
                # 관련 설정값 삭제
                cursor.execute("DELETE FROM Default_DB_Values WHERE equipment_type_id = ?", (equipment_type_id,))
                
                # 장비 유형 삭제
                cursor.execute("DELETE FROM Equipment_Types WHERE id = ?", (equipment_type_id,))
                
                # 트랜잭션 완료
                conn.commit()
                return True
            except Exception as e:
                # 오류 발생 시 롤백
                conn.rollback()
                print(f"장비 유형 삭제 중 오류 발생: {str(e)}")
                return False

    def update_default_value(self, value_id, parameter_name, default_value, min_spec=None, max_spec=None, description=None, conn_override=None):
        """
        기존 기본 DB 값을 업데이트합니다.
        
        Args:
            value_id (int): 업데이트할 값의 ID
            parameter_name (str): 파라미터 이름
            default_value (str): 설정값
            min_spec (str, optional): 최소 허용값
            max_spec (str, optional): 최대 허용값
            description (str, optional): 파라미터 설명 (None이면 기존 값 유지)
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            bool: 업데이트 성공 여부
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                # 현재 시간
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # description이 제공되었는지에 따라 쿼리 분기
                if description is not None:
                    cursor.execute(
                        """UPDATE Default_DB_Values 
                           SET parameter_name = ?, default_value = ?, min_spec = ?, max_spec = ?, description = ?, updated_at = ?
                           WHERE id = ?""",
                        (parameter_name, default_value, min_spec, max_spec, description, current_time, value_id)
                    )
                else:
                    cursor.execute(
                        """UPDATE Default_DB_Values 
                           SET parameter_name = ?, default_value = ?, min_spec = ?, max_spec = ?, updated_at = ?
                           WHERE id = ?""",
                        (parameter_name, default_value, min_spec, max_spec, current_time, value_id)
                    )
                
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"기본 DB 값 업데이트 중 오류 발생: {str(e)}")
                return False

    def delete_default_value(self, value_id, conn_override=None):
        """
        특정 기본 DB 값을 삭제합니다.
        
        Args:
            value_id (int): 삭제할 값의 ID
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            bool: 삭제 성공 여부
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM Default_DB_Values WHERE id = ?", (value_id,))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"기본 DB 값 삭제 중 오류 발생: {str(e)}")
                return False

    def log_change_history(self, change_type, item_type, item_name, old_value="", new_value="", changed_by=""):
        """변경 이력을 기록합니다.
        
        Args:
            change_type (str): 변경 유형 (add, update, delete)
            item_type (str): 항목 유형 (equipment_type, parameter)
            item_name (str): 항목 이름
            old_value (str, optional): 변경 전 값. 설정값은 빈 문자열입니다.
            new_value (str, optional): 변경 후 값. 설정값은 빈 문자열입니다.
            changed_by (str, optional): 변경한 사용자. 설정값은 빈 문자열입니다.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO Change_History (change_type, item_type, item_name, old_value, new_value, username, changed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (change_type, item_type, item_name, old_value, new_value, changed_by, timestamp)
                )
                
                conn.commit()
        except Exception as e:
            print(f"변경 이력 기록 중 오류 발생: {str(e)}")

    def set_performance_status(self, value_id, is_performance, conn_override=None):
        """
        특정 파라미터의 Performance 상태를 설정합니다.
        
        Args:
            value_id (int): 설정할 값의 ID
            is_performance (bool): Performance 항목 여부
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            bool: 업데이트 성공 여부
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE Default_DB_Values SET is_performance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (is_performance, value_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Performance 상태 업데이트 중 오류: {e}")
                return False

    def get_performance_parameters(self, equipment_type_id=None, conn_override=None):
        """
        Performance로 설정된 파라미터만 반환합니다.
        
        Args:
            equipment_type_id (int, optional): 장비 유형 ID. None이면 모든 Performance 파라미터 반환
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            list: Performance 파라미터 리스트
        """
        return self.get_default_values(equipment_type_id, performance_only=True, conn_override=conn_override)

    def get_equipment_performance_count(self, equipment_type_id, conn_override=None):
        """
        특정 장비 유형의 Performance 파라미터 개수를 반환합니다.
        
        Args:
            equipment_type_id (int): 장비 유형 ID
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            dict: {'total': 전체 파라미터 수, 'performance': Performance 파라미터 수}
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 전체 파라미터 수
            cursor.execute(
                "SELECT COUNT(*) FROM Default_DB_Values WHERE equipment_type_id = ?",
                (equipment_type_id,)
            )
            total_count = cursor.fetchone()[0]
            
            # Performance 파라미터 수
            cursor.execute(
                "SELECT COUNT(*) FROM Default_DB_Values WHERE equipment_type_id = ? AND is_performance = 1",
                (equipment_type_id,)
            )
            performance_count = cursor.fetchone()[0]
            
            return {
                'total': total_count,
                'performance': performance_count
            }

    # 이하 get_change_history, get_change_history_count, get_change_history_paged 등 모든 메서드 구현됨
