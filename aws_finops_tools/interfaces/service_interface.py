import abc
from typing import List, Dict, Any, Optional, Union, TypeVar, Generic

T = TypeVar('T', bound=Dict[str, Any])

class ServiceInterface(abc.ABC, Generic[T]):
    """Interface for all AWS service handlers"""

    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        Initialize AWS service handler
        
        Args:
            region: AWS region
            session: AWS session info (None=default profile, str=profile name, tuple=(access key, secret key))
        """
        self.region = region
        self.session_args = self._setup_session(session)

    def _setup_session(self, session: Optional[Union[str, tuple[str, str]]]) -> Dict[str, str]:
        """Initialize session settings"""
        if isinstance(session, str):  # Profile-based session
            return {"profile_name": session}
        elif isinstance(session, tuple) and len(session) == 2:  # Key-based session
            access_key, secret_key = session
            return {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key
            }
        return {}  # Use default profile

    @abc.abstractmethod
    async def fetch_data(self) -> List[T]:
        """Fetch AWS resource data asynchronously"""
        pass
