import os

class Menu():
    def pickRegion(self) :
        print("\n어떤 리전을 선택하시겠습니까?")
        REGIONS = {
            "1": "ap-northeast-1",
            "2": "ap-northeast-2",
            "3": "us-east-1",
            "4": "us-east-2",
            "5": "us-west-1",
            "6": "모두 다"  # ✅ 모든 리전 조회 추가
        }
        
        for key, region in REGIONS.items():
            print(f"{key}. {region}")
        region_choice = input("번호를 입력하세요: ")
        
        if region_choice == "6":
            selected_regions = list(REGIONS.values())[:-1]  # "모두 다" 제외하고 모든 리전 선택
        else:
            selected_regions = [REGIONS.get(region_choice)]
        
        if not selected_regions or None in selected_regions:
            print("잘못된 입력입니다.")
            return
        return selected_regions
        
        
    def pickAwsProfile(self) :
        print("AWS 세션을 선택하세요.")
        print("1. 기본 프로필\n2. 입력 프로필\n3. 키 입력")
        session_choice = input("번호를 입력하세요: ")
        session = None
        if session_choice == "1":
            session = None  # 기본 프로필 사용
        elif session_choice == "2":
            profile_name = input("사용할 AWS 프로필 이름을 입력하세요: ")
            session = profile_name
        elif session_choice == "3":
            access_key = input("AWS Access Key: ")
            secret_key = input("AWS Secret Key: ")
            session = (access_key, secret_key)
        else:
            print("잘못된 입력입니다.")
            return
        return session
    
    def pickService(self) :
        print("AWS 인프라 환경 체크 프로세스입니다. 확인할 서비스를 골라주세요.")
        print("1. EBS 스냅샷\n2. EBS 볼륨\n3. AMI\n4. ALL")
        choice = input("번호를 입력하세요: ")
        return choice
    
    def pickOutputType(self) :
        print("\n어떤 형식으로 데이터를 저장하시겠습니까?")
        print("1. JSON\n2. CSV\n3. TSV\n4. 콘솔 출력")
        format_choice = input("번호를 입력하세요: ")
        
        formats = {"1": "json", "2": "csv", "3": "tsv", "4": "console"}
        format_type = formats.get(format_choice, "console")
        
        file_path = None
        
        if format_type != "console":
            file_path = input(f"\n저장할 파일 경로를 입력하세요 (예: /path/to/output.{format_type}): ").strip()
            if not file_path:
                print("❌ 경로를 입력하지 않았습니다.")
                return
        
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)  # ✅ 디렉토리 없으면 생성
        return file_path, format_type
    
    