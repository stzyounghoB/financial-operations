# main.py
import asyncio
from typing import List, Dict, Any, Type, Optional, Union
from ebs_snapshot_checker import EBSSnapshotChecker
from ebs_volume_checker import EBSVolumeChecker
from ami_checker import AMIChecker
from unused_ami_checker import UnusedAMIChecker
from dynamo_cu_checker import DynamoCUChecker  # 추가
from utils import save_to_file
from menu import Menu
from infra_checker import InfraChecker


async def run_all_checks(
    service_classes: List[Type[InfraChecker]], 
    regions: List[str], 
    session: Optional[Union[str, tuple[str, str]]]
) -> List[Dict[str, Any]]:
    """
    모든 체크 작업 실행
    
    Args:
        service_classes: 체크할 서비스 클래스 목록
        regions: 체크할 리전 목록
        session: AWS 세션 정보
        
    Returns:
        List[Dict[str, Any]]: 체크 결과 목록
    """
    # 비동기로 모든 작업 실행
    tasks = []
    for region in regions:
        for service_class in service_classes:
            service = service_class(region, session)
            tasks.append(service.fetch_data())
    
    # 모든 작업 동시 실행 및 결과 수집
    results = []
    try:
        batch_results = await asyncio.gather(*tasks)
        for batch in batch_results:
            if batch:  # None이 아닌 결과만 추가
                results.extend(batch)
    except Exception as e:
        print(f"데이터 조회 중 오류 발생: {e}")
    
    return results


async def main() -> None:
    """메인 프로그램"""
    # 서비스 매핑 업데이트
    services = {
        "1": EBSSnapshotChecker,
        "2": EBSVolumeChecker,
        "3": AMIChecker,
        "4": UnusedAMIChecker,  
        "5": DynamoCUChecker,    # DynamoDB CU 체커 추가
        "6": "ALL"               # ALL 옵션이 6번으로 변경
    }
    
    # 메뉴 객체 생성 및 사용자 입력 받기
    menu_obj = Menu()
    session = menu_obj.pick_aws_profile()
    choice_service = menu_obj.pick_service()
    selected_regions = menu_obj.pick_region()
    
    # 사용되지 않는 AMI 체크 및 삭제 처리
    if choice_service == "4":
        await menu_obj.handle_unused_ami(selected_regions, session)
        return
    
    # DynamoDB CU 분석 처리
    if choice_service == "5":
        await menu_obj.handle_dynamo_cu(selected_regions, session)
        return
    
    # 다른 서비스 선택 처리
    if choice_service == "6":  # ALL 선택 (번호 업데이트)
        selected_services = [EBSSnapshotChecker, EBSVolumeChecker, AMIChecker, UnusedAMIChecker, DynamoCUChecker]
    else:
        service_class = services.get(choice_service)
        if not service_class or service_class == "ALL":
            print("잘못된 서비스를 선택했습니다.")
            return
        selected_services = [service_class]
    
    # 출력 형식 선택
    file_path, format_type = menu_obj.pick_output_type()
    
    # 작업 실행
    print(f"\n{len(selected_regions)}개 리전, {len(selected_services)}개 서비스 체크 중...")
    
    # DynamoCUChecker가 포함된 경우 개월 수 선택
    if DynamoCUChecker in selected_services:
        months = menu_obj.pick_dynamo_months()
        # service 생성 시 months 파라미터 전달을 위해 수정된 실행
        tasks = []
        for region in selected_regions:
            for service_class in selected_services:
                if service_class == DynamoCUChecker:
                    service = service_class(region, session, months)
                else:
                    service = service_class(region, session)
                tasks.append(service.fetch_data())
                
        results = []
        try:
            batch_results = await asyncio.gather(*tasks)
            for batch in batch_results:
                if batch:
                    results.extend(batch)
        except Exception as e:
            print(f"데이터 조회 중 오류 발생: {e}")
    else:
        # 기존 방식으로 실행
        results = await run_all_checks(selected_services, selected_regions, session)
    
    # 결과 출력 또는 저장
    if format_type == "console":
        print(f"\n결과 항목 수: {len(results)}")
        for item in results:
            print(item)
    else:
        success = await save_to_file(results, file_path, format_type)
        if success:
            print(f"\n총 {len(results)}개 항목이 {file_path} 파일로 저장되었습니다.")


def main_cli():
    """명령줄 인터페이스 진입점"""
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 메인 프로그램 실행
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()