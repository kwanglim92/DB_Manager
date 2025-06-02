# 이 파일은 리팩토링되어 실제 코드는 app/schema.py에서 확인하세요.
# 프로그램 실행은 main.py를 사용하세요.

# 버전: 1.0.1
# 작성일: 2025-05-25
# 최적화: 컨텍스트 매니저 패턴 적용, 코드 중복 감소

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
        """
        DBSchema 클래스 초기화
        
        Args:
            db_path (str, optional): 데이터베이스 파일 경로. 기본값은 애플리케이션 폴더 내 'data/local_db.sqlite'
        """
        if db_path is None:
            # 기본 데이터 디렉토리 설정
            app_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            
            # 데이터 디렉토리가 없으면 생성
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
                
            self.db_path = os.path.join(app_data_dir, 'local_db.sqlite')
        else:
            self.db_path = db_path
            
        self.create_tables()
        
    @contextmanager
    def get_connection(self, conn_override=None):
        """
        데이터베이스 연결을 위한 컨텍스트 매니저
        
        Args:
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Yields:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        conn_provided = conn_override is not None
        conn = conn_override if conn_provided else sqlite3.connect(self.db_path)
        
        try:
            yield conn
        finally:
            if not conn_provided and conn:
                conn.close()
    
    def create_tables(self):
        """
        필요한 테이블 구조를 생성합니다.
        - Equipment_Types: 장비 유형 정보
        - Default_DB_Values: 장비 유형별 기본 DB 값
        - Change_History: 변경 이력 관리
        """
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
            
            # 기본 DB 값 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Default_DB_Values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                default_value TEXT NOT NULL,
                min_spec TEXT,
                max_spec TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                UNIQUE (equipment_type_id, parameter_name)
            )
            ''')
            
            # 변경 이력 관리 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Change_History (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_type TEXT NOT NULL,         -- 'add', 'update', 'delete' 등
                item_type TEXT NOT NULL,           -- 'equipment_type', 'parameter' 등
                item_name TEXT NOT NULL,           -- 장비 유형명 또는 파라미터명
                old_value TEXT,                    -- 변경 전 값 (삭제 또는 수정시)
                new_value TEXT,                    -- 변경 후 값 (추가 또는 수정시)
                changed_by TEXT,                   -- 변경한 사용자
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP -- 변경 시간
            )
            ''')
            
            conn.commit()
    
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
    
    def add_default_value(self, equipment_type_id, parameter_name, default_value, min_spec=None, max_spec=None, conn_override=None):
        """
        장비 유형에 대한 기본 DB 값을 추가하거나 업데이트합니다.
        
        Args:
            equipment_type_id (int): 장비 유형 ID
            parameter_name (str): 파라미터 이름
            default_value (str): 기본값
            min_spec (str, optional): 최소 허용값
            max_spec (str, optional): 최대 허용값
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            int: 새로 생성되거나 업데이트된 레코드의 ID
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            # 이미 존재하는지 확인
            cursor.execute(
                "SELECT id FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                (equipment_type_id, parameter_name)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 기존 값 업데이트
                cursor.execute(
                    """UPDATE Default_DB_Values 
                       SET default_value = ?, min_spec = ?, max_spec = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (default_value, min_spec, max_spec, existing[0])
                )
                conn.commit()
                return existing[0]
            else:
                # 새 값 추가
                cursor.execute(
                    """INSERT INTO Default_DB_Values 
                       (equipment_type_id, parameter_name, default_value, min_spec, max_spec)
                       VALUES (?, ?, ?, ?, ?)""",
                    (equipment_type_id, parameter_name, default_value, min_spec, max_spec)
                )
                conn.commit()
                return cursor.lastrowid
    
    def get_default_values(self, equipment_type_id=None, conn_override=None):
        """
        특정 장비 유형 또는 모든 장비 유형에 대한 기본 DB 값을 반환합니다.
        
        Args:
            equipment_type_id (int, optional): 장비 유형 ID. None이면 모든 값 반환
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            list: DB 값 레코드 리스트
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            if equipment_type_id is not None:
                cursor.execute(
                    """SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name
                       FROM Default_DB_Values d
                       JOIN Equipment_Types e ON d.equipment_type_id = e.id
                       WHERE d.equipment_type_id = ?
                       ORDER BY d.parameter_name""",
                    (equipment_type_id,)
                )
            else:
                cursor.execute(
                    """SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name
                       FROM Default_DB_Values d
                       JOIN Equipment_Types e ON d.equipment_type_id = e.id
                       ORDER BY e.type_name, d.parameter_name"""
                )
            
            return cursor.fetchall()
    
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
                
                # 관련 기본값 삭제
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
    
    def update_default_value(self, value_id, parameter_name, default_value, min_spec=None, max_spec=None, conn_override=None):
        """
        기존 기본 DB 값을 업데이트합니다.
        
        Args:
            value_id (int): 업데이트할 값의 ID
            parameter_name (str): 파라미터 이름
            default_value (str): 기본값
            min_spec (str, optional): 최소 허용값
            max_spec (str, optional): 최대 허용값
            conn_override (sqlite3.Connection, optional): 외부에서 전달한 데이터베이스 연결 객체
            
        Returns:
            bool: 업데이트 성공 여부
        """
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            try:
                # 현재 시간
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 기존 값 업데이트
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
            old_value (str, optional): 변경 전 값. 기본값은 빈 문자열입니다.
            new_value (str, optional): 변경 후 값. 기본값은 빈 문자열입니다.
            changed_by (str, optional): 변경한 사용자. 기본값은 빈 문자열입니다.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO Change_History (change_type, item_type, item_name, old_value, new_value, changed_by, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (change_type, item_type, item_name, old_value, new_value, changed_by, timestamp)
                )
                
                conn.commit()
        except Exception as e:
            print(f"변경 이력 기록 중 오류 발생: {str(e)}")
            
    def get_change_history(self, start_date=None, end_date=None, item_type=None, change_type=None):
        """변경 이력을 조회합니다.
        
        Args:
            start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            item_type (str, optional): 항목 유형 필터. 기본값은 None입니다.
            change_type (str, optional): 변경 유형 필터. 기본값은 None입니다.
            
        Returns:
            list: 변경 이력 데이터 목록
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT id, change_type, item_type, item_name, old_value, new_value, changed_by, timestamp FROM Change_History"
                conditions = []
                params = []
                
                # 날짜 필터 적용
                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(f"{start_date} 00:00:00")
                
                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(f"{end_date} 23:59:59")
                
                # 항목 유형 필터 적용
                if item_type:
                    conditions.append("item_type = ?")
                    params.append(item_type)
                
                # 변경 유형 필터 적용
                if change_type:
                    conditions.append("change_type = ?")
                    params.append(change_type)
                
                # 조건 조합
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # 정렬 (최신순)
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return results
                
        except Exception as e:
            print(f"변경 이력 조회 중 오류 발생: {str(e)}")
            return []
            
    def get_change_history_count(self, start_date=None, end_date=None, item_type=None, change_type=None):
        """필터링 조건에 맞는 변경 이력의 총 개수를 반환합니다.
        
        Args:
            start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            item_type (str, optional): 항목 유형 필터. 기본값은 None입니다.
            change_type (str, optional): 변경 유형 필터. 기본값은 None입니다.
            
        Returns:
            int: 변경 이력 데이터 총 개수
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT COUNT(*) FROM Change_History"
                conditions = []
                params = []
                
                # 날짜 필터 적용
                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(f"{start_date} 00:00:00")
                
                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(f"{end_date} 23:59:59")
                
                # 항목 유형 필터 적용
                if item_type:
                    conditions.append("item_type = ?")
                    params.append(item_type)
                
                # 변경 유형 필터 적용
                if change_type:
                    conditions.append("change_type = ?")
                    params.append(change_type)
                
                # 조건 조합
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            print(f"변경 이력 개수 조회 중 오류 발생: {str(e)}")
            return 0
            
    def get_change_history_paged(self, start_date=None, end_date=None, item_type=None, change_type=None, limit=100, offset=0):
        """페이징 처리된 변경 이력을 조회합니다.
        
        Args:
            start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식). 기본값은 None입니다.
            item_type (str, optional): 항목 유형 필터. 기본값은 None입니다.
            change_type (str, optional): 변경 유형 필터. 기본값은 None입니다.
            limit (int, optional): 한 페이지에 표시할 항목 수. 기본값은 100입니다.
            offset (int, optional): 조회 시작 위치. 기본값은 0입니다.
            
        Returns:
            list: 변경 이력 데이터 목록 (페이징 처리됨)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT id, change_type, item_type, item_name, old_value, new_value, changed_by, timestamp FROM Change_History"
                conditions = []
                params = []
                
                # 날짜 필터 적용
                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(f"{start_date} 00:00:00")
                
                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(f"{end_date} 23:59:59")
                
                # 항목 유형 필터 적용
                if item_type:
                    conditions.append("item_type = ?")
                    params.append(item_type)
                
                # 변경 유형 필터 적용
                if change_type:
                    conditions.append("change_type = ?")
                    params.append(change_type)
                
                # 조건 조합
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # 정렬 (최신순)
                query += " ORDER BY timestamp DESC"
                
                # 페이징 처리
                query += " LIMIT ? OFFSET ?"
                params.append(limit)
                params.append(offset)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return results
                
        except Exception as e:
            print(f"페이징 처리된 변경 이력 조회 중 오류 발생: {str(e)}")
            return []