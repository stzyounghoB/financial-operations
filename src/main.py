from concurrent.futures import ThreadPoolExecutor
from ebs_snapshot_checker import EBSSnapshotChecker
from ebs_volume_checker import EBSVolumeChecker
from ami_checker import AMIChecker
from utils import save_to_file
from menu import Menu
import asyncio

async def main():
    menuObj = Menu()
    session = menuObj.pickAwsProfile()
    choiceService = menuObj.pickService()
    selected_regions = menuObj.pickRegion()
    
    services = {
        "1": EBSSnapshotChecker,
        "2": EBSVolumeChecker,
        "3": AMIChecker,
    }
    
    if choiceService == "4":
        selected_services = [EBSSnapshotChecker, EBSVolumeChecker, AMIChecker]
    else:
        service_class = services.get(choiceService)
        if not service_class:
            print("잘못된 입력입니다.")
            return
        selected_services = [service_class]
    
    file_path, format_type = menuObj.pickOutputType()
    
    # 비동기로 모든 작업 실행
    tasks = []
    for region in selected_regions:
        for service_class in selected_services:
            service = service_class(region, session)
            tasks.append(service.fetch_data())
    
    # 모든 작업 동시 실행 및 결과 수집
    results = []
    try:
        batch_results = await asyncio.gather(*tasks)
        for batch in batch_results:
            results.extend(batch)
    except Exception as e:
        print(f"데이터 조회 실패: {e}")
    
    # 결과 출력 또는 저장
    if format_type == "console":
        print("item size : " + str(len(results)))
        for item in results:
            print(item)
    else:
        save_to_file(results, file_path, format_type)
        print(f"{file_path} 파일로 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
