import boto3
from typing import List, Dict
from infra_checker import InfraChecker

class AMIChecker(InfraChecker):
    def __init__(self, region: str):
        super().__init__(region)
        self.ec2_client = boto3.client("ec2", region_name=self.region)

    def fetch_data(self) -> List[Dict]:
        """AMI 목록 조회"""
        images = self.ec2_client.describe_images(Owners=["self"])["Images"]
        return [{"id": img["ImageId"], "name": img.get("Name", "이름 없음"), "region": self.region} for img in images]
