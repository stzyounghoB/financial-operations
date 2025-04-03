from infra_checker import InfraChecker
from typing import List, Dict
import asyncio
import aioboto3

class EBSSnapshotChecker(InfraChecker):
    def __init__(self, region: str, session=None):
        super().__init__(region)
        # print(f"AWS 계정 Profile: {session}")
        self.session_args = {}
        
        # 세션 설정
        if isinstance(session, str):  # 프로필 기반 세션
            self.session_args = {"profile_name": session}
        elif isinstance(session, tuple):  # 키 입력 기반 세션
            access_key, secret_key = session
            self.session_args = {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key
            }
        
    async def fetch_data(self) -> List[Dict]:
        """EBS 스냅샷 정보를 비동기로 가져옴"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            snapshots_response = await ec2.describe_snapshots(OwnerIds=["self"])
            snapshots = snapshots_response["Snapshots"]
            print("size : " + str(len(snapshots)))
            # 스냅샷을 배치로 분할 (예: 각 배치당 10개)
            batch_size = 10
            snapshot_batches = [snapshots[i:i+batch_size] for i in range(0, len(snapshots), batch_size)]
            
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
    
    async def process_snapshot_batch(self, ec2, snapshots) -> List[Dict]:
        """스냅샷 배치를 비동기로 처리"""
        tasks = [self.check_snapshot_usage(ec2, snapshot) for snapshot in snapshots]
        return await asyncio.gather(*tasks)
    
    async def check_snapshot_usage(self, ec2, snapshot) -> Dict:
        """스냅샷 사용 여부 비동기 확인"""
        snapshot_id = snapshot["SnapshotId"]
        snapshot_name = next((tag["Value"] for tag in snapshot.get("Tags", []) if tag["Key"] == "Name"), "이름 없음")
        volume_size = snapshot["VolumeSize"]
        
        # 비동기로 볼륨 및 이미지 정보 조회
        volumes_task = ec2.describe_volumes(Filters=[{"Name": "snapshot-id", "Values": [snapshot_id]}])
        images_task = ec2.describe_images(Filters=[{"Name": "block-device-mapping.snapshot-id", "Values": [snapshot_id]}])
        
        # 두 작업을 동시에 기다림
        volumes, images = await asyncio.gather(volumes_task, images_task)
        
        usage = "X"
        if volumes["Volumes"]:
            usage = f"볼륨 사용 중 (Volume ID: {volumes['Volumes'][0]['VolumeId']})"
        elif images["Images"]:
            usage = f"AMI 사용 중 (AMI ID: {images['Images'][0]['ImageId']})"
            
        return {
            "id": snapshot_id, 
            "name": snapshot_name, 
            "size": volume_size, 
            "usage": usage, 
            "region": self.region
        }
