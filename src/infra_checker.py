# infra_checker.py
import abc
from typing import List, Dict, Any, Optional, Union, TypeVar, Generic

T = TypeVar('T', bound=Dict[str, Any])

class InfraChecker(abc.ABC, Generic[T]):
    """AWS 인프라 리소스 체크를 위한 기본 인터페이스"""

    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        AWS 인프라 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보 (None=기본 프로필, str=프로필명, tuple=(액세스키, 시크릿키))
        """
        self.region = region
        self.session_args = self._setup_session(session)

    def _setup_session(self, session: Optional[Union[str, tuple[str, str]]]) -> Dict[str, str]:
        """세션 설정 정보 초기화"""
        if isinstance(session, str):  # 프로필 기반 세션
            return {"profile_name": session}
        elif isinstance(session, tuple) and len(session) == 2:  # 키 입력 기반 세션
            access_key, secret_key = session
            return {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key
            }
        return {}  # 기본 프로필 사용

    @abc.abstractmethod
    async def fetch_data(self) -> List[T]:
        """AWS 리소스 데이터를 비동기로 조회하여 반환"""
        pass