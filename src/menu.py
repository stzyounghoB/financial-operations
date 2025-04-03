# menu.py
import os
from typing import List, Tuple, Optional, Union
from unused_ami_checker import UnusedAMIChecker
from dynamo_cu_checker import DynamoCUChecker

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
        "4": "사용되지 않는 AMI (삭제 기능)",
        "5": "DynamoDB CU 사용량",  # DynamoDB CU 옵션 추가
        "6": "ALL"  # 번호 업데이트
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
            return "6"  # ALL 옵션이 6번으로 변경됨
    
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
    
    def pick_dynamo_months(self) -> int:
        """
        DynamoDB 지표 조회 기간(월) 선택
        
        Returns:
            int: 조회 개월 수
        """
        print("\nDynamoDB 지표를 몇 개월치 조회하시겠습니까?")
        print("1. 1개월 (기본)")
        print("2. 3개월")
        print("3. 6개월")
        print("4. 12개월")
        
        choice = input("번호를 입력하세요: ").strip()
        
        months_map = {
            "1": 1,
            "2": 3,
            "3": 6,
            "4": 12
        }
        
        return months_map.get(choice, 1)  # 기본값은 1개월
    
    async def handle_unused_ami(self, regions: List[str], session: Optional[Union[str, tuple[str, str]]]) -> None:
        """
        사용되지 않는 AMI 메뉴 처리
        
        Args:
            regions: 처리할 리전 목록
            session: AWS 세션 정보
        """
        print("\n사용되지 않는 AMI 조회 중...")
        results = []
        
        # 각 리전에서 사용되지 않는 AMI 조회
        for region in regions:
            checker = UnusedAMIChecker(region, session)
            unused_amis = await checker.fetch_data()
            results.extend(unused_amis)
        
        if not results:
            print("사용되지 않는 AMI가 없습니다.")
            return
        
        # 결과 출력
        print(f"\n사용되지 않는 AMI {len(results)}개 발견:")
        for i, ami in enumerate(results, 1):
            print(f"{i}. ID: {ami['id']}, 이름: {ami['name']}, 리전: {ami['region']}, " +
                  f"생성일: {ami['creation_date']}, 연결 스냅샷: {len(ami['snapshot_ids'])}개")
        
        # 작업 선택
        print("\n사용하지 않는 AMI에 대한 작업을 선택해주세요.")
        print("1. 삭제")
        print("2. 출력")
        action_choice = input("번호를 입력하세요: ").strip()
        
        if action_choice == "2":
            # 출력 형식 선택
            file_path, format_type = self.pick_output_type()
            
            # 결과 출력 또는 저장
            if format_type == "console":
                print(f"\n결과 항목 수: {len(results)}")
                for item in results:
                    print(item)
            else:
                from utils import save_to_file
                success = await save_to_file(results, file_path, format_type)
                if success:
                    print(f"\n총 {len(results)}개 항목이 {file_path} 파일로 저장되었습니다.")
            return
        
        if action_choice != "1":
            print("작업을 취소합니다.")
            return
        
        # 삭제할 AMI 선택
        selection = input("\n삭제할 AMI 번호를 선택하세요 (쉼표로 구분, 'all'은 모두 선택): ").strip().lower()
        ami_to_delete = []
        
        if selection == 'all':
            ami_to_delete = [(ami['id'], ami['region']) for ami in results]
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(results):
                        ami_to_delete.append((results[idx]['id'], results[idx]['region']))
                    else:
                        print(f"잘못된 인덱스: {idx + 1}")
            except ValueError:
                print("잘못된 입력입니다.")
                return
        
        if not ami_to_delete:
            print("선택된 AMI가 없습니다.")
            return
        
        # 스냅샷 삭제 여부 확인
        delete_snapshots = input("AMI와 연결된 스냅샷도 함께 삭제하시겠습니까? (y/n): ").strip().lower() == 'y'
        
        # 리전별로 그룹화하여 삭제
        region_ami_map = {}
        for ami_id, region in ami_to_delete:
            if region not in region_ami_map:
                region_ami_map[region] = []
            region_ami_map[region].append(ami_id)
        
        # 각 리전에서 AMI 삭제 실행
        delete_results = []
        for region, ami_ids in region_ami_map.items():
            checker = UnusedAMIChecker(region, session)
            results = await checker.batch_delete_amis(ami_ids, delete_snapshots)
            delete_results.extend(results)
        
        # 삭제 결과 출력
        success_count = sum(1 for result in delete_results if result.get('success', False))
        print(f"\nAMI 삭제 완료: {success_count}/{len(delete_results)}개 성공")
        
        for result in delete_results:
            if result.get('success', False):
                print(f"성공: {result.get('message', '')}")
            else:
                print(f"실패: {result.get('message', '')}")
    
    async def handle_dynamo_cu(self, regions: List[str], session: Optional[Union[str, tuple[str, str]]]) -> None:
        """
        DynamoDB CU 사용량 분석 및 결과 출력
        
        Args:
            regions: 처리할 리전 목록
            session: AWS 세션 정보
        """
        # 조회 개월 수 선택
        months = self.pick_dynamo_months()
        
        print(f"\nDynamoDB CU 사용량 분석 중... ({months}개월 기준)")
        results = []
        
        # 각 리전에서 DynamoDB 테이블 조회
        for region in regions:
            checker = DynamoCUChecker(region, session, months)
            table_metrics = await checker.fetch_data()
            results.extend(table_metrics)
        
        if not results:
            print("분석할 DynamoDB 테이블이 없습니다.")
            return
        
        # 결과 요약 출력
        print(f"\nDynamoDB 테이블 {len(results)}개 분석 결과:")
        print(f"조회 기간: 최근 {months}개월")
        
        # 낮은 활용률 테이블 찾기 (20% 미만)
        low_utilization = [t for t in results if t["billing_mode"] == "PROVISIONED" and 
                           (t["wcu_utilization_percent"] < 20 or t["rcu_utilization_percent"] < 20)]
        
        if low_utilization:
            print(f"\n활용률이 낮은 테이블 ({len(low_utilization)}개):")
            for table in low_utilization:
                print(f"  - {table['table_name']} (리전: {table['region']})")
                print(f"    WCU 사용률: {table['wcu_utilization_percent']}%, RCU 사용률: {table['rcu_utilization_percent']}%")
        
        # 출력 형식 선택
        file_path, format_type = self.pick_output_type()
        
        # 결과 출력 또는 저장
        if format_type == "console":
            print("\n상세 분석 결과:")
            for item in results:
                print(f"\n테이블: {item['table_name']} (리전: {item['region']})")
                print(f"청구 모드: {item['billing_mode']}")
                if item['billing_mode'] == 'PROVISIONED':
                    print(f"프로비저닝: WCU {item['provisioned_wcu']}, RCU {item['provisioned_rcu']}")
                    print(f"사용률: WCU {item['wcu_utilization_percent']}%, RCU {item['rcu_utilization_percent']}%")
                print(f"WCU 사용량: 평균 {item['consumed_wcu_avg']:.2f}, 최소 {item['consumed_wcu_min']:.2f}, 최대 {item['consumed_wcu_max']:.2f}")
                print(f"RCU 사용량: 평균 {item['consumed_rcu_avg']:.2f}, 최소 {item['consumed_rcu_min']:.2f}, 최대 {item['consumed_rcu_max']:.2f}")
        else:
            from utils import save_to_file
            success = await save_to_file(results, file_path, format_type)
            if success:
                print(f"\n총 {len(results)}개 항목이 {file_path} 파일로 저장되었습니다.")