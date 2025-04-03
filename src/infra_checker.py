import abc
from typing import List, Dict

class InfraChecker(abc.ABC):
    """AWS 인프라 체크 인터페이스"""

    def __init__(self, region: str):
        self.region = region

    @abc.abstractmethod
    def fetch_data(self) -> List[Dict]:
        """AWS 리소스 데이터를 조회하여 반환"""
        pass
