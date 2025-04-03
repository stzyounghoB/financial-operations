# ami_checker.py
from typing import List, Dict, Any, Optional, Union, TypedDict
import aioboto3
from infra_checker import InfraChecker


class AMIInfo(TypedDict):
    """AMI 정보 타입 정의"""
    id: str
    name: str
    state: str
    public: bool
    created: str
    region: str


class AMIChecker(InfraChecker[AMIInfo]):
    """AMI 정보를 체크하는 클래스"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        AMI 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보
        """
        super().__init__(region, session)
    
    async def fetch_data(self) -> List[AMIInfo]:
        """AMI 목록을 비동기로 조회"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                response = await ec2.describe_images(Owners=["self"])
                images = response.get("Images", [])
                
                result = []
                for img in images:
                    result.append({
                        "id": img["ImageId"],
                        "name": img.get("Name", "이름 없음"),
                        "state": img.get("State", "unknown"),
                        "public": img.get("Public", False),
                        "created": img.get("CreationDate", ""),
                        "region": self.region
                    })
                
                return result
            except Exception as e:
                print(f"AMI 조회 실패: {e}")
                return []