from typing import List, Dict, Any, Optional, Union, TypedDict
import asyncio
from ...interfaces.service_interface import ServiceInterface
from ...utils.aws_utils import get_aws_client


class AMIInfo(TypedDict):
    """AMI information type definition"""
    id: str
    name: str
    state: str
    public: bool
    created: str
    region: str
    usage: str  # 새로 추가된 필드: 어디에서 AMI가 사용되고 있는지


class UnusedAMIInfo(TypedDict):
    """Unused AMI information type definition"""
    id: str
    name: str
    creation_date: str
    state: str
    description: str
    is_public: bool
    region: str
    snapshot_ids: List[str]


class AMIHandler(ServiceInterface[AMIInfo]):
    """Handler for AMI operations"""
    
    async def fetch_data(self) -> List[AMIInfo]:
        """Fetch AMI data asynchronously with usage information"""
        try:
            # EC2 클라이언트로 AMI 정보 가져오기
            async with get_aws_client("ec2", self.region, self.session_args) as ec2:
                response = await ec2.describe_images(Owners=["self"])
                images = response.get("Images", [])
                
                # Fetch all instances to check AMI usage
                instances_response = await ec2.describe_instances()
                reservations = instances_response.get("Reservations", [])
                
                # Map of AMI ID to instance IDs
                ami_to_instances = {}
                for reservation in reservations:
                    for instance in reservation.get("Instances", []):
                        image_id = instance.get("ImageId")
                        instance_id = instance.get("InstanceId")
                        if image_id and instance_id:
                            if image_id not in ami_to_instances:
                                ami_to_instances[image_id] = []
                            ami_to_instances[image_id].append(instance_id)
                
                # Fetch launch templates
                ami_to_launch_templates = {}
                try:
                    lt_response = await ec2.describe_launch_templates()
                    for lt in lt_response.get("LaunchTemplates", []):
                        lt_id = lt.get("LaunchTemplateId")
                        lt_name = lt.get("LaunchTemplateName")
                        versions = await ec2.describe_launch_template_versions(LaunchTemplateId=lt_id)
                        for v in versions.get("LaunchTemplateVersions", []):
                            img_id = v.get("LaunchTemplateData", {}).get("ImageId")
                            if img_id:
                                if img_id not in ami_to_launch_templates:
                                    ami_to_launch_templates[img_id] = []
                                ami_to_launch_templates[img_id].append(f"{lt_name} (v{v.get('VersionNumber')})")
                except Exception as e:
                    print(f"Error checking launch templates: {e}")
            
            # AutoScaling 정보 가져오기
            async with get_aws_client("autoscaling", self.region, self.session_args) as autoscaling:
                # Fetch launch configurations and ASGs
                ami_to_asg_resources = {}
                try:
                    # Get all launch configurations
                    lc_response = await autoscaling.describe_launch_configurations()
                    ami_to_lc = {}
                    for lc in lc_response.get("LaunchConfigurations", []):
                        img_id = lc.get("ImageId")
                        lc_name = lc.get("LaunchConfigurationName")
                        if img_id and lc_name:
                            if img_id not in ami_to_lc:
                                ami_to_lc[img_id] = []
                            ami_to_lc[img_id].append(lc_name)
                    
                    # Get ASGs using these launch configurations
                    asg_response = await autoscaling.describe_auto_scaling_groups()
                    for asg in asg_response.get("AutoScalingGroups", []):
                        asg_name = asg.get("AutoScalingGroupName")
                        lc_name = asg.get("LaunchConfigurationName")
                        lt_id = asg.get("LaunchTemplate", {}).get("LaunchTemplateId")
                        lt_version = asg.get("LaunchTemplate", {}).get("Version")
                        
                        # Process AMIs used via launch configurations
                        if lc_name:
                            for ami_id, lc_names in ami_to_lc.items():
                                if lc_name in lc_names:
                                    if ami_id not in ami_to_asg_resources:
                                        ami_to_asg_resources[ami_id] = []
                                    ami_to_asg_resources[ami_id].append(f"ASG {asg_name} via LC {lc_name}")
                except Exception as e:
                    print(f"Error checking autoscaling resources: {e}")
            
            # 최종 결과 정리
            async with get_aws_client("ec2", self.region, self.session_args) as ec2:
                # Process AMIs used via launch templates in ASGs
                for asg in asg_response.get("AutoScalingGroups", []):
                    lt = asg.get("LaunchTemplate")
                    if lt:
                        lt_id = lt.get("LaunchTemplateId")
                        lt_version = lt.get("Version")
                        if lt_id and lt_version:
                            asg_name = asg.get("AutoScalingGroupName")
                            try:
                                lt_details = await ec2.describe_launch_template_versions(
                                    LaunchTemplateId=lt_id,
                                    Versions=[lt_version]
                                )
                                for version in lt_details.get("LaunchTemplateVersions", []):
                                    ami_id = version.get("LaunchTemplateData", {}).get("ImageId")
                                    if ami_id:
                                        if ami_id not in ami_to_asg_resources:
                                            ami_to_asg_resources[ami_id] = []
                                        ami_to_asg_resources[ami_id].append(f"ASG {asg_name} via LT {lt_id} (v{lt_version})")
                            except Exception as e:
                                print(f"Error checking launch template in ASG: {e}")
            
            # Process all AMIs with usage information
            result = []
            for img in images:
                img_id = img["ImageId"]
                usage_details = []
                
                # Check EC2 instances
                if img_id in ami_to_instances:
                    instances = ami_to_instances[img_id]
                    usage_details.append(f"EC2 instances: {', '.join(instances[:3])}" + 
                                        (f" and {len(instances)-3} more" if len(instances) > 3 else ""))
                
                # Check launch templates
                if img_id in ami_to_launch_templates:
                    templates = ami_to_launch_templates[img_id]
                    usage_details.append(f"Launch templates: {', '.join(templates[:3])}" + 
                                        (f" and {len(templates)-3} more" if len(templates) > 3 else ""))
                
                # Check ASG resources
                if img_id in ami_to_asg_resources:
                    asgs = ami_to_asg_resources[img_id]
                    usage_details.append(f"ASG resources: {', '.join(asgs[:3])}" + 
                                        (f" and {len(asgs)-3} more" if len(asgs) > 3 else ""))
                
                # Set usage string
                usage = "; ".join(usage_details) if usage_details else "Unused"
                
                result.append({
                    "id": img_id,
                    "name": img.get("Name", "No name"),
                    "state": img.get("State", "unknown"),
                    "public": img.get("Public", False),
                    "created": img.get("CreationDate", ""),
                    "region": self.region,
                    "usage": usage
                })
            
            return result
        except Exception as e:
            print(f"Failed to fetch AMIs: {e}")
            return []
    
    async def fetch_unused_amis(self) -> List[UnusedAMIInfo]:
        """Fetch unused AMI data asynchronously, including Auto Scaling references"""
        async with get_aws_client("ec2", self.region, self.session_args) as ec2, \
                get_aws_client("autoscaling", self.region, self.session_args) as autoscaling:
            try:
                # Fetch all AMIs
                ami_response = await ec2.describe_images(Owners=["self"])
                all_amis = ami_response.get("Images", [])
                if not all_amis:
                    return []

                # Fetch all EC2 instances
                instances_response = await ec2.describe_instances()
                reservations = instances_response.get("Reservations", [])

                used_ami_ids = set()
                for reservation in reservations:
                    for instance in reservation.get("Instances", []):
                        image_id = instance.get("ImageId")
                        if image_id:
                            used_ami_ids.add(image_id)

                # Fetch AMI IDs from launch templates
                lt_response = await ec2.describe_launch_templates()
                for lt in lt_response.get("LaunchTemplates", []):
                    versions = await ec2.describe_launch_template_versions(LaunchTemplateId=lt["LaunchTemplateId"])
                    for v in versions.get("LaunchTemplateVersions", []):
                        img_id = v.get("LaunchTemplateData", {}).get("ImageId")
                        if img_id:
                            used_ami_ids.add(img_id)

                # Fetch AMI IDs from launch configurations
                lc_response = await autoscaling.describe_launch_configurations()
                for lc in lc_response.get("LaunchConfigurations", []):
                    img_id = lc.get("ImageId")
                    if img_id:
                        used_ami_ids.add(img_id)

                # Identify unused AMIs
                unused_amis = []
                for ami in all_amis:
                    ami_id = ami.get("ImageId")
                    if ami_id not in used_ami_ids:
                        snapshot_ids = []
                        for mapping in ami.get("BlockDeviceMappings", []):
                            if "Ebs" in mapping and "SnapshotId" in mapping["Ebs"]:
                                snapshot_ids.append(mapping["Ebs"]["SnapshotId"])
                        
                        unused_amis.append({
                            "id": ami_id,
                            "name": ami.get("Name", "No name"),
                            "creation_date": ami.get("CreationDate", ""),
                            "state": ami.get("State", ""),
                            "description": ami.get("Description", ""),
                            "is_public": ami.get("Public", False),
                            "region": self.region,
                            "snapshot_ids": snapshot_ids
                        })

                return unused_amis
            except Exception as e:
                print(f"Failed to fetch unused AMIs: {e}")
                return []


    async def delete_ami(self, ami_id: str, delete_snapshots: bool = False) -> Dict[str, Any]:
        """
        Delete an AMI
        
        Args:
            ami_id: AMI ID to delete
            delete_snapshots: Whether to delete associated snapshots
            
        Returns:
            Dict[str, Any]: Deletion result
        """
        async with get_aws_client("ec2", self.region, self.session_args) as ec2:
            try:
                # Fetch AMI information
                ami_response = await ec2.describe_images(ImageIds=[ami_id])
                images = ami_response.get("Images", [])
                
                if not images:
                    return {"success": False, "message": f"AMI {ami_id} not found.", "ami_id": ami_id}
                
                # Extract snapshot IDs
                snapshot_ids = []
                for image in images:
                    for mapping in image.get("BlockDeviceMappings", []):
                        if "Ebs" in mapping and "SnapshotId" in mapping["Ebs"]:
                            snapshot_ids.append(mapping["Ebs"]["SnapshotId"])
                
                # Deregister AMI
                await ec2.deregister_image(ImageId=ami_id)
                
                # Delete associated snapshots if requested
                deleted_snapshots = []
                if delete_snapshots and snapshot_ids:
                    for snapshot_id in snapshot_ids:
                        try:
                            await ec2.delete_snapshot(SnapshotId=snapshot_id)
                            deleted_snapshots.append(snapshot_id)
                        except Exception as e:
                            print(f"Failed to delete snapshot {snapshot_id}: {e}")
                
                return {
                    "success": True, 
                    "message": f"AMI {ami_id} deleted successfully" + 
                              (f", {len(deleted_snapshots)} associated snapshots deleted" if deleted_snapshots else ""),
                    "ami_id": ami_id,
                    "deleted_snapshots": deleted_snapshots
                }
            except Exception as e:
                return {"success": False, "message": f"Failed to delete AMI {ami_id}: {e}", "ami_id": ami_id}
    
    async def batch_delete_amis(self, ami_ids: List[str], delete_snapshots: bool = False) -> List[Dict[str, Any]]:
        """
        Delete multiple AMIs in batch
        
        Args:
            ami_ids: List of AMI IDs to delete
            delete_snapshots: Whether to delete associated snapshots
            
        Returns:
            List[Dict[str, Any]]: List of deletion results
        """
        tasks = [self.delete_ami(ami_id, delete_snapshots) for ami_id in ami_ids]
        return await asyncio.gather(*tasks)
