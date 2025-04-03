# ebs_volume_checker.py
from typing import List, Dict, Any, Optional, Union, TypedDict
import aioboto3
from infra_checker import InfraChecker


class VolumeInfo(TypedDict):
    """EBS 볼륨 정보 타입 정의"""
    id: str
    size: int
    state: str
    type: str
    attached_to: str
    region: str


class EBSVolumeChecker(InfraChecker[VolumeInfo]):
    """EBS 볼륨 정보를 체크하는 클래스"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        EBS 볼륨 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보
        """
        super().__init__(region, session)
    
    async def fetch_data(self) -> List[VolumeInfo]:
        """EBS 볼륨 정보를 비동기로 조회"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                response = await ec2.describe_volumes()
                volumes = response.get("Volumes", [])
                
                result = []
                for volume in volumes:
                    # 볼륨이 연결된 인스턴스 정보 확인
                    attachments = volume.get("Attachments", [])
                    attached_to = "분리됨"
                    if attachments:
                        instance_id = attachments[0].get("InstanceId", "")
                        attached_to = f"인스턴스 {instance_id}에 연결됨"
                    
                    # 볼륨 이름 태그 확인
                    volume_name = next(
                        (tag["Value"] for tag in volume.get("Tags", []) if tag["Key"] == "Name"), 
                        "이름 없음"
                    )
                    
                    result.append({
                        "id": volume["VolumeId"],
                        "name": volume_name,
                        "size": volume["Size"],
                        "state": volume["State"],
                        "type": volume["VolumeType"],
                        "attached_to": attached_to,
                        "region": self.region
                    })
                
                return result
            except Exception as e:
                print(f"EBS 볼륨 조회 실패: {e}")
                return []