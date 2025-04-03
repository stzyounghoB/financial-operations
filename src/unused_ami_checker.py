# unused_ami_checker.py
from typing import List, Dict, Any, Optional, Union, TypedDict, Set
import aioboto3
import asyncio
from infra_checker import InfraChecker


class UnusedAMIInfo(TypedDict):
    """사용되지 않는 AMI 정보 타입 정의"""
    id: str
    name: str
    creation_date: str
    state: str
    description: str
    is_public: bool
    region: str
    snapshot_ids: List[str]  # AMI와 연결된 스냅샷 ID 목록


class UnusedAMIChecker(InfraChecker[UnusedAMIInfo]):
    """사용되지 않는 AMI 정보를 체크하는 클래스"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None):
        """
        사용되지 않는 AMI 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보
        """
        super().__init__(region, session)
    
    async def fetch_data(self) -> List[UnusedAMIInfo]:
        """사용되지 않는 AMI 정보를 비동기로 조회"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                # 모든 AMI 정보 조회 (자체 소유)
                ami_response = await ec2.describe_images(Owners=["self"])
                all_amis = ami_response.get("Images", [])
                
                if not all_amis:
                    return []
                
                # 모든 EC2 인스턴스 정보 조회
                instances_response = await ec2.describe_instances()
                reservations = instances_response.get("Reservations", [])
                
                # 사용 중인 AMI ID 목록 생성
                used_ami_ids = set()
                for reservation in reservations:
                    for instance in reservation.get("Instances", []):
                        image_id = instance.get("ImageId")
                        if image_id:
                            used_ami_ids.add(image_id)
                
                # 사용되지 않는 AMI 정보 생성
                unused_amis = []
                for ami in all_amis:
                    ami_id = ami.get("ImageId")
                    if ami_id not in used_ami_ids:
                        # 스냅샷 ID 수집
                        snapshot_ids = []
                        for mapping in ami.get("BlockDeviceMappings", []):
                            if "Ebs" in mapping and "SnapshotId" in mapping["Ebs"]:
                                snapshot_ids.append(mapping["Ebs"]["SnapshotId"])
                        
                        unused_amis.append({
                            "id": ami_id,
                            "name": ami.get("Name", "이름 없음"),
                            "creation_date": ami.get("CreationDate", ""),
                            "state": ami.get("State", ""),
                            "description": ami.get("Description", ""),
                            "is_public": ami.get("Public", False),
                            "region": self.region,
                            "snapshot_ids": snapshot_ids
                        })
                
                return unused_amis
            except Exception as e:
                print(f"사용되지 않는 AMI 조회 실패: {e}")
                return []
    
    async def delete_ami(self, ami_id: str, delete_snapshots: bool = False) -> Dict[str, Any]:
        """
        AMI 삭제 실행
        
        Args:
            ami_id: 삭제할 AMI ID
            delete_snapshots: 연결된 스냅샷도 함께 삭제할지 여부
            
        Returns:
            Dict[str, Any]: 삭제 결과 정보
        """
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                # AMI 정보 조회
                ami_response = await ec2.describe_images(ImageIds=[ami_id])
                images = ami_response.get("Images", [])
                
                if not images:
                    return {"success": False, "message": f"AMI {ami_id}를 찾을 수 없습니다.", "ami_id": ami_id}
                
                # 스냅샷 ID 추출
                snapshot_ids = []
                for image in images:
                    for mapping in image.get("BlockDeviceMappings", []):
                        if "Ebs" in mapping and "SnapshotId" in mapping["Ebs"]:
                            snapshot_ids.append(mapping["Ebs"]["SnapshotId"])
                
                # AMI 등록 취소
                await ec2.deregister_image(ImageId=ami_id)
                
                # 연결된 스냅샷도 삭제
                deleted_snapshots = []
                if delete_snapshots and snapshot_ids:
                    for snapshot_id in snapshot_ids:
                        try:
                            await ec2.delete_snapshot(SnapshotId=snapshot_id)
                            deleted_snapshots.append(snapshot_id)
                        except Exception as e:
                            print(f"스냅샷 {snapshot_id} 삭제 실패: {e}")
                
                return {
                    "success": True, 
                    "message": f"AMI {ami_id} 삭제 완료" + 
                              (f", 연결된 스냅샷 {len(deleted_snapshots)}개 삭제됨" if deleted_snapshots else ""),
                    "ami_id": ami_id,
                    "deleted_snapshots": deleted_snapshots
                }
            except Exception as e:
                return {"success": False, "message": f"AMI {ami_id} 삭제 실패: {e}", "ami_id": ami_id}
    
    async def batch_delete_amis(self, ami_ids: List[str], delete_snapshots: bool = False) -> List[Dict[str, Any]]:
        """
        여러 AMI 일괄 삭제
        
        Args:
            ami_ids: 삭제할 AMI ID 목록
            delete_snapshots: 연결된 스냅샷도 함께 삭제할지 여부
            
        Returns:
            List[Dict[str, Any]]: 각 AMI 삭제 결과 목록
        """
        tasks = [self.delete_ami(ami_id, delete_snapshots) for ami_id in ami_ids]
        return await asyncio.gather(*tasks)