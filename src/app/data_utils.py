# 데이터 처리 유틸리티 함수들
# manager.py에서 추출된 순수 유틸리티 함수들

def numeric_sort_key(value):
    """
    숫자 정렬을 위한 키 함수
    
    Args:
        value: 정렬할 값
        
    Returns:
        float: 정렬용 숫자 키 (숫자가 아닌 경우 inf 반환)
    """
    try:
        # 빈 값이나 N/A 처리
        if not value or value in ['N/A', 'n/a', '', '-']:
            return float('inf')  # 빈 값은 맨 뒤로
        
        # 숫자로 변환 시도
        return float(value)
    except (ValueError, TypeError):
        # 숫자가 아닌 경우 문자열로 정렬
        return float('inf')


def calculate_string_similarity(str1, str2):
    """
    두 문자열 간의 유사도를 계산합니다 (레벤슈타인 거리 기반).
    
    Args:
        str1, str2: 비교할 문자열
        
    Returns:
        float: 0.0 ~ 1.0 사이의 유사도 (1.0이 완전 동일)
    """
    if str1 == str2:
        return 1.0
    
    len1, len2 = len(str1), len(str2)
    if len1 == 0:
        return 0.0 if len2 > 0 else 1.0
    if len2 == 0:
        return 0.0
    
    # 동적 프로그래밍으로 레벤슈타인 거리 계산
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # 삭제
                matrix[i][j-1] + 1,      # 삽입
                matrix[i-1][j-1] + cost  # 대체
            )
    
    # 유사도 계산 (0.0 ~ 1.0)
    max_len = max(len1, len2)
    distance = matrix[len1][len2]
    similarity = 1.0 - (distance / max_len)
    
    return similarity


def safe_convert_to_float(value, default=0.0):
    """
    값을 안전하게 float로 변환
    
    Args:
        value: 변환할 값
        default: 변환 실패시 기본값
        
    Returns:
        float: 변환된 값 또는 기본값
    """
    try:
        if value is None or value == '' or value == 'N/A':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_convert_to_int(value, default=0):
    """
    값을 안전하게 int로 변환
    
    Args:
        value: 변환할 값
        default: 변환 실패시 기본값
        
    Returns:
        int: 변환된 값 또는 기본값
    """
    try:
        if value is None or value == '' or value == 'N/A':
            return default
        return int(float(value))  # float를 거쳐서 int로 변환 (소수점이 있는 문자열 처리)
    except (ValueError, TypeError):
        return default


def normalize_parameter_name(name):
    """
    파라미터 이름을 정규화
    
    Args:
        name: 파라미터 이름
        
    Returns:
        str: 정규화된 이름
    """
    if not name:
        return ""
    
    # 공백 제거 및 소문자 변환
    normalized = str(name).strip().lower()
    
    # 특수 문자 정리
    normalized = normalized.replace('_', '').replace('-', '').replace(' ', '')
    
    return normalized


def is_numeric_string(value):
    """
    문자열이 숫자인지 확인
    
    Args:
        value: 확인할 값
        
    Returns:
        bool: 숫자 문자열 여부
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def clean_numeric_value(value):
    """
    숫자 값을 정리하여 반환
    
    Args:
        value: 정리할 값
        
    Returns:
        str: 정리된 숫자 문자열
    """
    try:
        if value is None or value == '' or value == 'N/A':
            return 'N/A'
        
        # 숫자로 변환 가능하면 깔끔하게 포맷팅
        num_val = float(value)
        if num_val.is_integer():
            return str(int(num_val))
        else:
            return f"{num_val:.4f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value) if value is not None else 'N/A'