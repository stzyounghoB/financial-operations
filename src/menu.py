# menu.py
import os
from typing import List, Tuple, Optional, Union

class Menu:
    """AWS 인프라 체커 메뉴 인터페이스"""
    
    # 리전 정보
    REGIONS = {
        "1": "ap-northeast-1",
        "2": "ap-northeast-2",
        "3": "us-east-1",
        "4": "us-east-2",
        "5": "us-west-1",
        "6": "모두 다"
    }
    
    # 서비스 정보
    SERVICES = {
        "1": "EBS 스냅샷",
        "2": "EBS 볼륨",
        "3": "AMI",
        "4": "사용되지 않는 AMI (삭제 기능)",  # 사용되지 않는 AMI 및 삭제 기능
        "5": "ALL"
    }
    
    # 출력 형식 정보
    FORMATS = {
        "1": "json",
        "2": "csv",
        "3": "tsv",
        "4": "console"
    }
    
    def pick_region(self) -> List[str]:
        """
        사용할 AWS 리전 선택
        
        Returns:
            List[str]: 선택한 리전 목록
        """
        print("\n어떤 리전을 선택하시겠습니까?")
        for key, region in self.REGIONS.items():
            print(f"{key}. {region}")
        
        region_choice = input("번호를 입력하세요: ")
        
        if region_choice == "6":
            # "모두 다" 제외하고 모든 리전 선택
            return list(value for key, value in self.REGIONS.items() if key != "6")
        elif region_choice in self.REGIONS:
            return [self.REGIONS[region_choice]]
        else:
            print("잘못된 입력입니다. 기본값(ap-northeast-2)을 사용합니다.")
            return ["ap-northeast-2"]
    
    def pick_aws_profile(self) -> Optional[Union[str, Tuple[str, str]]]:
        """
        AWS 세션 정보 선택
        
        Returns:
            Optional[Union[str, Tuple[str, str]]]: 세션 정보
        """
        print("\nAWS 세션을 선택하세요.")
        print("1. 기본 프로필\n2. 입력 프로필\n3. 키 입력")
        
        session_choice = input("번호를 입력하세요: ")
        
        if session_choice == "1":
            return None  # 기본 프로필 사용
        elif session_choice == "2":
            profile_name = input("사용할 AWS 프로필 이름을 입력하세요: ")
            return profile_name if profile_name.strip() else None
        elif session_choice == "3":
            access_key = input("AWS Access Key: ")
            secret_key = input("AWS Secret Key: ")
            if access_key.strip() and secret_key.strip():
                return (access_key, secret_key)
            else:
                print("키 정보가 올바르지 않습니다. 기본 프로필을 사용합니다.")
                return None
        else:
            print("잘못된 입력입니다. 기본 프로필을 사용합니다.")
            return None
    
    def pick_service(self) -> str:
        """
        확인할 AWS 서비스 선택
        
        Returns:
            str: 선택한 서비스 번호
        """
        print("\nAWS 인프라 환경 체크 프로세스입니다. 확인할 서비스를 골라주세요.")
        for key, service in self.SERVICES.items():
            print(f"{key}. {service}")
        
        choice = input("번호를 입력하세요: ")
        
        if choice in self.SERVICES:
            return choice
        else:
            print("잘못된 입력입니다. 기본값(ALL)을 사용합니다.")
            return "5"  # ALL 옵션이 5번으로 변경됨
    
    def pick_output_type(self) -> Tuple[Optional[str], str]:
        """
        출력 형식 및 파일 경로 선택
        
        Returns:
            Tuple[Optional[str], str]: (파일 경로, 출력 형식)
        """
        print("\n어떤 형식으로 데이터를 저장하시겠습니까?")
        for key, fmt in self.FORMATS.items():
            print(f"{key}. {fmt.upper()}")
        
        format_choice = input("번호를 입력하세요: ")
        format_type = self.FORMATS.get(format_choice, "console")
        
        file_path = None
        
        if format_type != "console":
            from datetime import datetime
            default_name = f"aws_infra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            default_path = os.path.join(os.getcwd(), default_name)
            
            file_path = input(f"\n저장할 파일 경로를 입력하세요 (기본값: {default_path}): ").strip()
            if not file_path:
                file_path = default_path
            
            # 확장자 확인 및 수정
            if not file_path.endswith(f".{format_type}"):
                file_path = f"{file_path}.{format_type}"
        
        return file_path, format_type