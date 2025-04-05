from typing import List, Dict, Any, Optional, Union, TypedDict
import aioboto3
from ....interfaces.service_interface import ServiceInterface


class VolumeInfo(TypedDict):
    """EBS volume information type definition"""
    id: str
    name: str
    size: int
    state: str
    type: str
    attached_to: str
    region: str


class VolumeHandler(ServiceInterface[VolumeInfo]):
    """Handler for EBS volume operations"""
    
    async def fetch_data(self) -> List[VolumeInfo]:
        """Fetch EBS volume data asynchronously"""
        async with aioboto3.Session(**self.session_args).client("ec2", region_name=self.region) as ec2:
            try:
                response = await ec2.describe_volumes()
                volumes = response.get("Volumes", [])
                
                result = []
                for volume in volumes:
                    # Check instance attachment information
                    attachments = volume.get("Attachments", [])
                    attached_to = "Detached"
                    if attachments:
                        instance_id = attachments[0].get("InstanceId", "")
                        attached_to = f"Attached to instance {instance_id}"
                    
                    # Check volume name tag
                    volume_name = next(
                        (tag["Value"] for tag in volume.get("Tags", []) if tag["Key"] == "Name"), 
                        "No name"
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
                print(f"Failed to fetch EBS volumes: {e}")
                return []

    async def fetch_unused_volumes(self) -> List[VolumeInfo]:
        """Fetch unused EBS volumes asynchronously"""
        volumes = await self.fetch_data()
        return [v for v in volumes if v["attached_to"] == "Detached"]
