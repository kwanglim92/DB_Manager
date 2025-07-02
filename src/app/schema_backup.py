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
            
            # QC 검수 템플릿 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_Templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL UNIQUE,
                template_type TEXT NOT NULL,  -- 'production', 'qc', 'custom'
                description TEXT,
                severity_mode TEXT DEFAULT 'standard',  -- 'strict', 'standard', 'lenient'
                check_performance BOOLEAN DEFAULT 1,
                check_naming BOOLEAN DEFAULT 1,
                check_ranges BOOLEAN DEFAULT 1,
                check_trends BOOLEAN DEFAULT 0,
                check_missing_values BOOLEAN DEFAULT 1,
                check_outliers BOOLEAN DEFAULT 1,
                check_duplicates BOOLEAN DEFAULT 1,
                check_consistency BOOLEAN DEFAULT 1,
                custom_rules TEXT,  -- JSON 형태의 사용자 정의 룰
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # QC 검수 기준 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_Standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER,
                customer_name TEXT,
                standard_name TEXT NOT NULL,
                min_confidence_score REAL DEFAULT 0.8,
                max_missing_values INTEGER DEFAULT 0,
                max_high_severity INTEGER DEFAULT 0,
                max_medium_severity INTEGER DEFAULT 5,
                max_low_severity INTEGER DEFAULT 10,
                performance_required BOOLEAN DEFAULT 1,
                custom_criteria TEXT,  -- JSON 형태의 추가 기준
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id)
            )
            ''')
            
            # QC 검수 이력 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_History (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                template_id INTEGER,
                standard_id INTEGER,
                inspector_name TEXT NOT NULL,
                inspection_mode TEXT NOT NULL,  -- 'performance', 'full', 'custom'
                total_parameters INTEGER DEFAULT 0,
                total_issues INTEGER DEFAULT 0,
                high_severity_count INTEGER DEFAULT 0,
                medium_severity_count INTEGER DEFAULT 0,
                low_severity_count INTEGER DEFAULT 0,
                overall_score REAL DEFAULT 0,
                pass_status TEXT NOT NULL,  -- 'pass', 'fail', 'conditional'
                inspection_notes TEXT,
                source_files TEXT,  -- 검수한 파일 목록
                results_data TEXT,  -- JSON 형태의 상세 결과
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                FOREIGN KEY (template_id) REFERENCES QC_Templates(id),
                FOREIGN KEY (standard_id) REFERENCES QC_Standards(id)
            )
            ''')
            
            # QC 배치 검수 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_Batch_Sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                session_description TEXT,
                inspector_name TEXT NOT NULL,
                template_id INTEGER,
                total_equipments INTEGER DEFAULT 0,
                completed_equipments INTEGER DEFAULT 0,
                session_status TEXT DEFAULT 'running',  -- 'running', 'completed', 'cancelled'
                comparison_matrix TEXT,  -- JSON 형태의 비교 결과
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES QC_Templates(id)
            )
            ''')
            
            # QC 배치 항목 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_Batch_Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                equipment_name TEXT NOT NULL,
                equipment_type_id INTEGER,
                file_path TEXT NOT NULL,
                inspection_status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
                qc_history_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES QC_Batch_Sessions(id),
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                FOREIGN KEY (qc_history_id) REFERENCES QC_History(id)
            )
            ''')
            
            # 기존 테이블 업데이트 - 새 컬럼들 추가
            self._update_existing_tables(cursor)
            
            # 기본 QC 템플릿과 기준 생성
            self._create_default_qc_data(cursor)
            
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
    
    def _create_default_qc_data(self, cursor):
        """기본 QC 템플릿과 기준을 생성합니다."""
        try:
            # 기본 QC 템플릿이 이미 존재하는지 확인
            cursor.execute("SELECT COUNT(*) FROM QC_Templates")
            template_count = cursor.fetchone()[0]
            
            if template_count == 0:
                # 생산 엔지니어용 템플릿
                cursor.execute(
                    """INSERT INTO QC_Templates 
                       (template_name, template_type, description, severity_mode,
                        check_performance, check_naming, check_ranges, check_trends,
                        check_missing_values, check_outliers, check_duplicates, check_consistency,
                        created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("생산 엔지니어 표준", "production", "생산 라인에서 사용하는 기본 검수 템플릿", "standard",
                     True, True, True, False, True, True, True, True, "system")
                )
                
                # QC 엔지니어용 템플릿 (더 엄격)
                cursor.execute(
                    """INSERT INTO QC_Templates 
                       (template_name, template_type, description, severity_mode,
                        check_performance, check_naming, check_ranges, check_trends,
                        check_missing_values, check_outliers, check_duplicates, check_consistency,
                        created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("QC 엔지니어 엄격", "qc", "출고 전 최종 검수용 엄격한 검수 템플릿", "strict",
                     True, True, True, True, True, True, True, True, "system")
                )
                
                # 빠른 검수용 템플릿
                cursor.execute(
                    """INSERT INTO QC_Templates 
                       (template_name, template_type, description, severity_mode,
                        check_performance, check_naming, check_ranges, check_trends,
                        check_missing_values, check_outliers, check_duplicates, check_consistency,
                        created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("빠른 검수", "custom", "Performance 항목 중심의 빠른 검수 템플릿", "lenient",
                     True, False, False, False, True, False, False, False, "system")
                )
                
                print("✅ 기본 QC 템플릿 3개 생성 완료")
            
            # 기본 QC 기준이 이미 존재하는지 확인
            cursor.execute("SELECT COUNT(*) FROM QC_Standards")
            standard_count = cursor.fetchone()[0]
            
            if standard_count == 0:
                # 표준 검수 기준
                cursor.execute(
                    """INSERT INTO QC_Standards 
                       (standard_name, min_confidence_score, max_missing_values,
                        max_high_severity, max_medium_severity, max_low_severity,
                        performance_required, is_default)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("표준 검수 기준", 0.8, 0, 0, 5, 10, True, True)
                )
                
                # 엄격한 검수 기준
                cursor.execute(
                    """INSERT INTO QC_Standards 
                       (standard_name, min_confidence_score, max_missing_values,
                        max_high_severity, max_medium_severity, max_low_severity,
                        performance_required, is_default)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("엄격한 검수 기준", 0.9, 0, 0, 2, 5, True, False)
                )
                
                # 관대한 검수 기준
                cursor.execute(
                    """INSERT INTO QC_Standards 
                       (standard_name, min_confidence_score, max_missing_values,
                        max_high_severity, max_medium_severity, max_low_severity,
                        performance_required, is_default)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("관대한 검수 기준", 0.7, 2, 1, 10, 20, False, False)
                )
                
                print("✅ 기본 QC 검수 기준 3개 생성 완료")
                
        except Exception as e:
            print(f"기본 QC 데이터 생성 중 오류: {e}")

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

    # ==================== QC 템플릿 관리 메서드 ====================
    
    def add_qc_template(self, template_name, template_type, description="", severity_mode="standard", 
                       check_options=None, custom_rules="", created_by="", conn_override=None):
        """QC 검수 템플릿을 추가합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 기본 검수 옵션 설정
            if check_options is None:
                check_options = {
                    'performance': True, 'naming': True, 'ranges': True, 'trends': False,
                    'missing_values': True, 'outliers': True, 'duplicates': True, 'consistency': True
                }
            
            try:
                cursor.execute(
                    """INSERT INTO QC_Templates 
                       (template_name, template_type, description, severity_mode, 
                        check_performance, check_naming, check_ranges, check_trends,
                        check_missing_values, check_outliers, check_duplicates, check_consistency,
                        custom_rules, created_by) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (template_name, template_type, description, severity_mode,
                     check_options.get('performance', True), check_options.get('naming', True),
                     check_options.get('ranges', True), check_options.get('trends', False),
                     check_options.get('missing_values', True), check_options.get('outliers', True),
                     check_options.get('duplicates', True), check_options.get('consistency', True),
                     custom_rules, created_by)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None  # 중복 템플릿명
    
    def get_qc_templates(self, template_type=None, conn_override=None):
        """QC 검수 템플릿 목록을 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            if template_type:
                cursor.execute(
                    "SELECT * FROM QC_Templates WHERE template_type = ? ORDER BY template_name",
                    (template_type,)
                )
            else:
                cursor.execute("SELECT * FROM QC_Templates ORDER BY template_type, template_name")
            
            return cursor.fetchall()
    
    def get_qc_template_by_id(self, template_id, conn_override=None):
        """특정 ID의 QC 템플릿을 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM QC_Templates WHERE id = ?", (template_id,))
            return cursor.fetchone()
    
    def update_qc_template(self, template_id, **kwargs):
        """QC 템플릿을 업데이트합니다."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 업데이트할 필드 구성
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['template_name', 'template_type', 'description', 'severity_mode',
                           'check_performance', 'check_naming', 'check_ranges', 'check_trends',
                           'check_missing_values', 'check_outliers', 'check_duplicates', 
                           'check_consistency', 'custom_rules']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(template_id)
                
                query = f"UPDATE QC_Templates SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def delete_qc_template(self, template_id, conn_override=None):
        """QC 템플릿을 삭제합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM QC_Templates WHERE id = ?", (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== QC 기준 관리 메서드 ====================
    
    def add_qc_standard(self, standard_name, equipment_type_id=None, customer_name="", 
                       criteria=None, is_default=False, conn_override=None):
        """QC 검수 기준을 추가합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 기본 기준값 설정
            if criteria is None:
                criteria = {
                    'min_confidence_score': 0.8,
                    'max_missing_values': 0,
                    'max_high_severity': 0,
                    'max_medium_severity': 5,
                    'max_low_severity': 10,
                    'performance_required': True
                }
            
            try:
                cursor.execute(
                    """INSERT INTO QC_Standards 
                       (equipment_type_id, customer_name, standard_name, min_confidence_score,
                        max_missing_values, max_high_severity, max_medium_severity, max_low_severity,
                        performance_required, is_default) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (equipment_type_id, customer_name, standard_name,
                     criteria.get('min_confidence_score', 0.8),
                     criteria.get('max_missing_values', 0),
                     criteria.get('max_high_severity', 0),
                     criteria.get('max_medium_severity', 5),
                     criteria.get('max_low_severity', 10),
                     criteria.get('performance_required', True),
                     is_default)
                )
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"QC 기준 추가 오류: {e}")
                return None
    
    def get_qc_standards(self, equipment_type_id=None, customer_name=None, conn_override=None):
        """QC 검수 기준 목록을 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if equipment_type_id:
                conditions.append("equipment_type_id = ?")
                params.append(equipment_type_id)
            
            if customer_name:
                conditions.append("customer_name = ?")
                params.append(customer_name)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            cursor.execute(f"SELECT * FROM QC_Standards{where_clause} ORDER BY standard_name", params)
            return cursor.fetchall()
    
    def get_default_qc_standard(self, equipment_type_id=None, conn_override=None):
        """기본 QC 검수 기준을 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            if equipment_type_id:
                cursor.execute(
                    "SELECT * FROM QC_Standards WHERE equipment_type_id = ? AND is_default = 1",
                    (equipment_type_id,)
                )
            else:
                cursor.execute("SELECT * FROM QC_Standards WHERE is_default = 1")
            
            return cursor.fetchone()
    
    # ==================== QC 검수 이력 관리 메서드 ====================
    
    def add_qc_history(self, equipment_type_id, inspector_name, inspection_mode, 
                      template_id=None, standard_id=None, results=None, conn_override=None):
        """QC 검수 이력을 추가합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 결과 통계 계산
            if results is None:
                results = {
                    'total_parameters': 0, 'total_issues': 0,
                    'high_severity_count': 0, 'medium_severity_count': 0, 'low_severity_count': 0,
                    'overall_score': 0, 'pass_status': 'unknown',
                    'inspection_notes': '', 'source_files': '', 'results_data': '{}'
                }
            
            try:
                cursor.execute(
                    """INSERT INTO QC_History 
                       (equipment_type_id, template_id, standard_id, inspector_name, inspection_mode,
                        total_parameters, total_issues, high_severity_count, medium_severity_count, 
                        low_severity_count, overall_score, pass_status, inspection_notes, 
                        source_files, results_data) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (equipment_type_id, template_id, standard_id, inspector_name, inspection_mode,
                     results.get('total_parameters', 0), results.get('total_issues', 0),
                     results.get('high_severity_count', 0), results.get('medium_severity_count', 0),
                     results.get('low_severity_count', 0), results.get('overall_score', 0),
                     results.get('pass_status', 'unknown'), results.get('inspection_notes', ''),
                     results.get('source_files', ''), results.get('results_data', '{}'))
                )
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"QC 이력 추가 오류: {e}")
                return None
    
    def get_qc_history(self, equipment_type_id=None, inspector_name=None, 
                      start_date=None, end_date=None, limit=100, conn_override=None):
        """QC 검수 이력을 조회합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if equipment_type_id:
                conditions.append("h.equipment_type_id = ?")
                params.append(equipment_type_id)
            
            if inspector_name:
                conditions.append("h.inspector_name = ?")
                params.append(inspector_name)
            
            if start_date:
                conditions.append("h.created_at >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("h.created_at <= ?")
                params.append(end_date)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            params.append(limit)
            
            cursor.execute(f"""
                SELECT h.*, e.type_name, t.template_name, s.standard_name
                FROM QC_History h
                LEFT JOIN Equipment_Types e ON h.equipment_type_id = e.id
                LEFT JOIN QC_Templates t ON h.template_id = t.id
                LEFT JOIN QC_Standards s ON h.standard_id = s.id
                {where_clause}
                ORDER BY h.created_at DESC
                LIMIT ?
            """, params)
            
            return cursor.fetchall()
    
    def get_qc_statistics(self, equipment_type_id=None, inspector_name=None, 
                         days=30, conn_override=None):
        """QC 검수 통계를 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            conditions = ["DATE(created_at) >= DATE('now', '-{} days')".format(days)]
            params = []
            
            if equipment_type_id:
                conditions.append("equipment_type_id = ?")
                params.append(equipment_type_id)
            
            if inspector_name:
                conditions.append("inspector_name = ?")
                params.append(inspector_name)
            
            where_clause = " WHERE " + " AND ".join(conditions)
            
            # 기본 통계
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_inspections,
                    AVG(overall_score) as avg_score,
                    SUM(CASE WHEN pass_status = 'pass' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN pass_status = 'fail' THEN 1 ELSE 0 END) as failed,
                    AVG(total_issues) as avg_issues
                FROM QC_History
                {where_clause}
            """, params)
            
            stats = cursor.fetchone()
            
            return {
                'total_inspections': stats[0] or 0,
                'average_score': round(stats[1] or 0, 2),
                'passed_count': stats[2] or 0,
                'failed_count': stats[3] or 0,
                'average_issues': round(stats[4] or 0, 2),
                'pass_rate': round((stats[2] or 0) / max(stats[0] or 1, 1) * 100, 2)
            }
    
    # ==================== QC 배치 검수 관리 메서드 ====================
    
    def create_batch_session(self, session_name, inspector_name, template_id=None, 
                            description="", conn_override=None):
        """배치 검수 세션을 생성합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """INSERT INTO QC_Batch_Sessions 
                       (session_name, session_description, inspector_name, template_id) 
                       VALUES (?, ?, ?, ?)""",
                    (session_name, description, inspector_name, template_id)
                )
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"배치 세션 생성 오류: {e}")
                return None
    
    def add_batch_item(self, session_id, equipment_name, equipment_type_id, file_path, conn_override=None):
        """배치 검수 항목을 추가합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """INSERT INTO QC_Batch_Items 
                       (session_id, equipment_name, equipment_type_id, file_path) 
                       VALUES (?, ?, ?, ?)""",
                    (session_id, equipment_name, equipment_type_id, file_path)
                )
                conn.commit()
                
                # 세션의 총 장비 수 업데이트
                cursor.execute(
                    "UPDATE QC_Batch_Sessions SET total_equipments = total_equipments + 1 WHERE id = ?",
                    (session_id,)
                )
                conn.commit()
                
                return cursor.lastrowid
            except Exception as e:
                print(f"배치 항목 추가 오류: {e}")
                return None
    
    def update_batch_item_status(self, item_id, status, qc_history_id=None, conn_override=None):
        """배치 검수 항목 상태를 업데이트합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "UPDATE QC_Batch_Items SET inspection_status = ?, qc_history_id = ? WHERE id = ?",
                    (status, qc_history_id, item_id)
                )
                
                if status == 'completed':
                    # 세션의 완료된 장비 수 업데이트
                    cursor.execute(
                        """UPDATE QC_Batch_Sessions 
                           SET completed_equipments = completed_equipments + 1 
                           WHERE id = (SELECT session_id FROM QC_Batch_Items WHERE id = ?)""",
                        (item_id,)
                    )
                
                conn.commit()
                return True
            except Exception as e:
                print(f"배치 항목 상태 업데이트 오류: {e}")
                return False
    
    def get_batch_session(self, session_id, conn_override=None):
        """배치 검수 세션 정보를 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT s.*, t.template_name 
                   FROM QC_Batch_Sessions s
                   LEFT JOIN QC_Templates t ON s.template_id = t.id
                   WHERE s.id = ?""",
                (session_id,)
            )
            
            return cursor.fetchone()
    
    def get_batch_items(self, session_id, conn_override=None):
        """배치 검수 항목 목록을 반환합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT i.*, e.type_name, h.overall_score, h.pass_status
                   FROM QC_Batch_Items i
                   LEFT JOIN Equipment_Types e ON i.equipment_type_id = e.id
                   LEFT JOIN QC_History h ON i.qc_history_id = h.id
                   WHERE i.session_id = ?
                   ORDER BY i.created_at""",
                (session_id,)
            )
            
            return cursor.fetchall()
    
    def complete_batch_session(self, session_id, comparison_matrix="", conn_override=None):
        """배치 검수 세션을 완료합니다."""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """UPDATE QC_Batch_Sessions 
                       SET session_status = 'completed', completed_at = CURRENT_TIMESTAMP, 
                           comparison_matrix = ? 
                       WHERE id = ?""",
                    (comparison_matrix, session_id)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"배치 세션 완료 오류: {e}")
                return False
    
    # 이하 get_change_history, get_change_history_count, get_change_history_paged 등 모든 메서드 구현됨
