# AWS FinOps 도구

AWS 리소스를 분석하고 비용 최적화 기회를 식별하는 도구입니다.

## 기능

- EBS 스냅샷 및 볼륨 분석
- AMI 및 사용되지 않는 AMI 분석 (삭제 기능 포함)
- DynamoDB 테이블 CU 사용량 분석
- 여러 리전 동시 분석 지원
- JSON, CSV, TSV 형식으로 결과 저장

## 설치 방법

### 방법 1: GitHub에서 직접 설치(권장)

#### 최신 버전 설치
```bash
# 항상 최신 버전 설치
pip install git+https://github.com/Cha-Young-Ho/financial-operations.git
```

#### 특정 버전 설치
```bash
# 특정 태그 버전 설치 (예: v0.1.2)
pip install git+https://github.com/Cha-Young-Ho/financial-operations.git@v0.1.2
```

#### 업그레이드
```bash
# 이미 설치된 경우 최신 버전으로 업그레이드
pip install --upgrade git+https://github.com/Cha-Young-Ho/financial-operations.git
```

### 방법 2: GitHub 클론 후 실행
```bash
# 1. 저장소 클론
git clone https://github.com/Cha-Young-Ho/financial-operations.git
cd financial-operations

# 2. 가상환경 생성 (선택사항이지만 권장)
python -m venv venv
source venv/bin/activate  
# Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -e .
```

## 사용 가능한 버전

현재 사용 가능한 버전 태그:
- v0.1.0: 초기 릴리스
  - EBS Snapshot
  - EBS Volume
  - DynamoDB Capacity Unit
  - AMI

최신 버전 태그 확인:
```bash
git ls-remote --tags https://github.com/Cha-Young-Ho/financial-operations.git
```

## 실행 방법
```bash
finops
```



https://github.com/user-attachments/assets/f17a5936-5b5d-458d-a3cf-81c3dcd22906





