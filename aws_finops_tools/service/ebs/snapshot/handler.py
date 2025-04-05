from typing import List, Dict, Any, Optional, Union, TypedDict
import asyncio
import aioboto3
from ....interfaces.service_interface import ServiceInterface

class SnapshotInfo(TypedDict):
    """EBS snapshot information type definition"""
    id: str
    name: str
    size: int
    usage: str
    region: str
    created: str


class SnapshotHandler(ServiceInterface[SnapshotInfo]):
    """Handler for EBS snapshot operations"""
    
    async def fetch_data(self) -> List[SnapshotInfo]:
        """Fetch EBS snapshot data asynchronously"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                snapshots_response = await ec2.describe_snapshots(OwnerIds=["self"])
                snapshots = snapshots_response.get("Snapshots", [])
                
                # Split snapshots into batches (10 per batch)
                batch_size = 10
                snapshot_batches = [
                    snapshots[i:i+batch_size] 
                    for i in range(0, len(snapshots), batch_size)
                ]
                
                # Process each batch asynchronously
                tasks = [
                    self.process_snapshot_batch(ec2, batch) 
                    for batch in snapshot_batches
                ]
                
                # Wait for all batch tasks to complete
                batch_results = await asyncio.gather(*tasks)
                
                # Merge results
                results = []
                for batch in batch_results:
                    results.extend(batch)
                
                return results
            except Exception as e:
                print(f"Failed to fetch EBS snapshots: {e}")
                return []
    
    async def process_snapshot_batch(self, ec2: Any, snapshots: List[Dict[str, Any]]) -> List[SnapshotInfo]:
        """Process a batch of snapshots asynchronously"""
        tasks = [self.check_snapshot_usage(ec2, snapshot) for snapshot in snapshots]
        return await asyncio.gather(*tasks)
    
    async def check_snapshot_usage(self, ec2: Any, snapshot: Dict[str, Any]) -> SnapshotInfo:
        """Check snapshot usage asynchronously"""
        snapshot_id = snapshot["SnapshotId"]
        snapshot_name = next(
            (tag["Value"] for tag in snapshot.get("Tags", []) if tag["Key"] == "Name"), 
            "No name"
        )
        volume_size = snapshot["VolumeSize"]
        created_date = str(snapshot.get("StartTime", ""))
        
        # Fetch volume and image information asynchronously
        volumes_task = ec2.describe_volumes(
            Filters=[{"Name": "snapshot-id", "Values": [snapshot_id]}]
        )
        images_task = ec2.describe_images(
            Filters=[{"Name": "block-device-mapping.snapshot-id", "Values": [snapshot_id]}]
        )
        
        # Wait for both tasks simultaneously
        volumes_response, images_response = await asyncio.gather(volumes_task, images_task)
        
        volumes = volumes_response.get("Volumes", [])
        images = images_response.get("Images", [])
        
        usage = "Unused"
        if volumes:
            usage = f"Used by volume (Volume ID: {volumes[0]['VolumeId']})"
        elif images:
            usage = f"Used by AMI (AMI ID: {images[0]['ImageId']})"
            
        return {
            "id": snapshot_id, 
            "name": snapshot_name, 
            "size": volume_size, 
            "usage": usage,
            "region": self.region,
            "created": created_date
        }

