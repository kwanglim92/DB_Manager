"""
캐시 서비스

메모리 기반 캐싱을 제공하여 성능을 개선합니다.
LRU(Least Recently Used) 캐시와 TTL(Time To Live) 기능을 지원합니다.
"""

from typing import Any, Optional, Dict, TypeVar
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import logging

T = TypeVar('T')

class CacheEntry:
    """캐시 엔트리"""
    
    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = None
        if ttl_seconds:
            self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """값 접근 (접근 시간 및 횟수 업데이트)"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.value

class CacheService:
    """캐시 서비스 구현"""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        캐시 서비스 초기화
        
        Args:
            max_size: 최대 캐시 항목 수
            default_ttl: 기본 TTL (초)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # 통계 정보
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # 만료 확인
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                self._logger.debug(f"캐시 만료: {key}")
                return None
            
            # LRU 업데이트 (최근 사용된 항목을 끝으로 이동)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.access()
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl_seconds: TTL (초), None이면 default_ttl 사용
        """
        with self._lock:
            # TTL 결정
            effective_ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
            
            # 새 엔트리 생성
            entry = CacheEntry(value, effective_ttl)
            
            # 기존 키가 있으면 업데이트
            if key in self._cache:
                del self._cache[key]
            
            self._cache[key] = entry
            
            # 크기 제한 확인 (LRU 방식으로 제거)
            while len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
                self._logger.debug(f"캐시 LRU 제거: {oldest_key}")
            
            self._logger.debug(f"캐시 저장: {key} (TTL: {effective_ttl})")
    
    def delete(self, key: str) -> bool:
        """
        캐시에서 키 삭제
        
        Args:
            key: 삭제할 키
            
        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._logger.debug(f"캐시 삭제: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """모든 캐시 제거"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self._logger.info(f"캐시 전체 삭제: {cleared_count}개 항목")
    
    def cleanup_expired(self) -> int:
        """
        만료된 항목들 정리
        
        Returns:
            정리된 항목 수
        """
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._logger.info(f"만료된 캐시 항목 정리: {len(expired_keys)}개")
            
            return len(expired_keys)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        캐시 통계 정보 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'evictions': self._evictions,
                'default_ttl': self._default_ttl
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        상세 캐시 정보 조회
        
        Returns:
            캐시 엔트리별 상세 정보
        """
        with self._lock:
            info = {}
            for key, entry in self._cache.items():
                info[key] = {
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                    'is_expired': entry.is_expired()
                }
            return info 