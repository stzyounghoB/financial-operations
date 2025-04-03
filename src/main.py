# main.py
import asyncio
from typing import List, Dict, Any, Type, Optional, Union
from ebs_snapshot_checker import EBSSnapshotChecker
from ebs_volume_checker import EBSVolumeChecker
from ami_checker import AMIChecker
from unused_ami_checker import UnusedAMIChecker
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


async def handle_unused_ami_deletion(
    regions: List[str], 
    session: Optional[Union[str, tuple[str, str]]]
) -> None:
    """
    사용되지 않는 AMI 삭제 처리
    
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
    
    # 삭제 여부 선택
    delete_choice = input("\n사용되지 않는 AMI를 삭제하시겠습니까? (y/n): ").strip().lower()
    if delete_choice != 'y':
        print("삭제 작업을 취소합니다.")
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


async def main() -> None:
    """메인 프로그램"""
    # 서비스 매핑
    services = {
        "1": EBSSnapshotChecker,
        "2": EBSVolumeChecker,
        "3": AMIChecker,
        "4": UnusedAMIChecker,  # 사용되지 않는 AMI 체커
        "5": "ALL"
    }
    
    # 메뉴 객체 생성 및 사용자 입력 받기
    menu_obj = Menu()
    session = menu_obj.pick_aws_profile()
    choice_service = menu_obj.pick_service()
    selected_regions = menu_obj.pick_region()
    
    # 사용되지 않는 AMI 체크 및 삭제 처리
    if choice_service == "4":
        await handle_unused_ami_deletion(selected_regions, session)
        return
    
    # 다른 서비스 선택 처리
    if choice_service == "5":  # ALL 선택
        selected_services = [EBSSnapshotChecker, EBSVolumeChecker, AMIChecker, UnusedAMIChecker]
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


if __name__ == "__main__":
    # Windows에서 비동기 이벤트 루프 설정
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 메인 프로그램 실행
    asyncio.run(main())