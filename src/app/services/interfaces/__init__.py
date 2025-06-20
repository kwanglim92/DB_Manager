"""
서비스 인터페이스 패키지

모든 서비스의 추상 인터페이스를 정의합니다.
구현체는 concrete 패키지에서 제공됩니다.
"""

from .equipment_service_interface import IEquipmentService, IParameterService
from .data_service_interface import IDataProcessingService, IFileService
from .validation_service_interface import IValidationService, IQCService

__all__ = [
    'IEquipmentService',
    'IParameterService', 
    'IDataProcessingService',
    'IFileService',
    'IValidationService',
    'IQCService'
] 