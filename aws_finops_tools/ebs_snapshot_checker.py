# ebs_snapshot_checker.py
from typing import List, Dict, Any, Optional, Union, TypedDict
import asyncio
import aioboto3
from .infra_checker import InfraChecker

class SnapshotInfo(TypedDict):
    """EBS 스냅샷 정보 타입 정의"""
    id: str
    name: str
    size: int
    usage: str
    region: str
    created: str


class EBSSnapshotChecker(InfraChecker[SnapshotInfo]):
    """EBS 스냅샷 정보를 체크하는 클래스"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        EBS 스냅샷 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보
        """
        super().__init__(region, session)
        
    async def fetch_data(self) -> List[SnapshotInfo]:
        """EBS 스냅샷 정보를 비동기로 가져옴"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                snapshots_response = await ec2.describe_snapshots(OwnerIds=["self"])
                snapshots = snapshots_response.get("Snapshots", [])
                
                # 스냅샷을 배치로 분할 (각 배치당 10개)
                batch_size = 10
                snapshot_batches = [
                    snapshots[i:i+batch_size] 
                    for i in range(0, len(snapshots), batch_size)
                ]
                
                # 각 배치를 비동기로 처리
                tasks = [
                    self.process_snapshot_batch(ec2, batch) 
                    for batch in snapshot_batches
                ]
                
                # 모든 배치 작업이 완료될 때까지 대기
                batch_results = await asyncio.gather(*tasks)
                
                # 결과 병합
                results = []
                for batch in batch_results:
                    results.extend(batch)
                
                return results
            except Exception as e:
                print(f"EBS 스냅샷 조회 실패: {e}")
                return []
    
    async def process_snapshot_batch(self, ec2: Any, snapshots: List[Dict[str, Any]]) -> List[SnapshotInfo]:
        """스냅샷 배치를 비동기로 처리"""
        tasks = [self.check_snapshot_usage(ec2, snapshot) for snapshot in snapshots]
        return await asyncio.gather(*tasks)
    
    async def check_snapshot_usage(self, ec2: Any, snapshot: Dict[str, Any]) -> SnapshotInfo:
        """스냅샷 사용 여부 비동기 확인"""
        snapshot_id = snapshot["SnapshotId"]
        snapshot_name = next(
            (tag["Value"] for tag in snapshot.get("Tags", []) if tag["Key"] == "Name"), 
            "이름 없음"
        )
        volume_size = snapshot["VolumeSize"]
        created_date = str(snapshot.get("StartTime", ""))
        
        # 비동기로 볼륨 및 이미지 정보 조회
        volumes_task = ec2.describe_volumes(
            Filters=[{"Name": "snapshot-id", "Values": [snapshot_id]}]
        )
        images_task = ec2.describe_images(
            Filters=[{"Name": "block-device-mapping.snapshot-id", "Values": [snapshot_id]}]
        )
        
        # 두 작업을 동시에 기다림
        volumes_response, images_response = await asyncio.gather(volumes_task, images_task)
        
        volumes = volumes_response.get("Volumes", [])
        images = images_response.get("Images", [])
        
        usage = "X"
        if volumes:
            usage = f"볼륨 사용 중 (Volume ID: {volumes[0]['VolumeId']})"
        elif images:
            usage = f"AMI 사용 중 (AMI ID: {images[0]['ImageId']})"
            
        return {
            "id": snapshot_id, 
            "name": snapshot_name, 
            "size": volume_size, 
            "usage": usage,
            "region": self.region,
            "created": created_date
        }
