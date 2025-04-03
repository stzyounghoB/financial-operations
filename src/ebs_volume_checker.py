import boto3
from typing import List, Dict
from infra_checker import InfraChecker

class EBSVolumeChecker(InfraChecker):
    def __init__(self, region: str):
        super().__init__(region)
        self.ec2_client = boto3.client("ec2", region_name=self.region)

    def fetch_data(self) -> List[Dict]:
        """EBS 볼륨 정보를 조회"""
        volumes = self.ec2_client.describe_volumes()["Volumes"]
        return [{"id": v["VolumeId"], "size": v["Size"], "state": v["State"], "region": self.region} for v in volumes]
