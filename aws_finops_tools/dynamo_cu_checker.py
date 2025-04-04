# dynamo_cu_checker.py
import asyncio
import datetime
from typing import List, Dict, Any, Optional, Union, TypedDict, Tuple
import aioboto3
from .infra_checker import InfraChecker


class DynamoCUInfo(TypedDict):
    """DynamoDB 테이블 CU 정보 타입 정의"""
    table_name: str
    provisioned_wcu: float
    provisioned_rcu: float
    consumed_wcu_avg: float
    consumed_wcu_min: float
    consumed_wcu_max: float
    consumed_rcu_avg: float
    consumed_rcu_min: float
    consumed_rcu_max: float
    wcu_utilization_percent: float
    rcu_utilization_percent: float
    billing_mode: str
    period_months: int
    region: str


class DynamoCUChecker(InfraChecker[DynamoCUInfo]):
    """DynamoDB 테이블의 CU 사용량을 체크하는 클래스"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None, months: int = 1):
        """
        DynamoDB CU 체커 초기화
        
        Args:
            region: AWS 리전
            session: AWS 세션 정보
            months: 조회할 기간(개월)
        """
        super().__init__(region, session)
        self.months = months
    
    async def fetch_data(self) -> List[DynamoCUInfo]:
        """DynamoDB 테이블 CU 정보를 비동기로 조회"""
        # DynamoDB 클라이언트 생성
        async with aioboto3.Session(**self.session_args).client('dynamodb', region_name=self.region) as dynamodb:
            try:
                # 모든 DynamoDB 테이블 목록 조회
                response = await dynamodb.list_tables()
                table_names = response.get('TableNames', [])
                
                # 페이징 처리
                while 'LastEvaluatedTableName' in response:
                    response = await dynamodb.list_tables(
                        ExclusiveStartTableName=response['LastEvaluatedTableName']
                    )
                    table_names.extend(response.get('TableNames', []))
                
                if not table_names:
                    print(f"리전 {self.region}에 DynamoDB 테이블이 없습니다.")
                    return []
                
                # 각 테이블의 상세 정보 및 CloudWatch 지표 조회
                tasks = [self.get_table_cu_info(table_name, dynamodb) for table_name in table_names]
                return await asyncio.gather(*tasks)
                
            except Exception as e:
                print(f"DynamoDB 테이블 조회 실패: {e}")
                return []
    
    async def get_table_cu_info(self, table_name: str, dynamodb: Any) -> DynamoCUInfo:
        """
        개별 DynamoDB 테이블의 CU 정보 조회
        
        Args:
            table_name: DynamoDB 테이블 이름
            dynamodb: DynamoDB 클라이언트
            
        Returns:
            DynamoCUInfo: 테이블 CU 정보
        """
        try:
            # 테이블 상세 정보 조회
            table_info = await dynamodb.describe_table(TableName=table_name)
            table = table_info.get('Table', {})
            
            # 프로비저닝 모드 확인
            billing_mode = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
            
            # 프로비저닝된 RCU/WCU 값 가져오기
            provisioned_wcu = 0
            provisioned_rcu = 0
            
            if billing_mode == 'PROVISIONED':
                provisioning_info = table.get('ProvisionedThroughput', {})
                provisioned_wcu = float(provisioning_info.get('WriteCapacityUnits', 0))
                provisioned_rcu = float(provisioning_info.get('ReadCapacityUnits', 0))
            
            # CloudWatch 지표 조회
            async with aioboto3.Session(**self.session_args).client('cloudwatch', region_name=self.region) as cloudwatch:
                # 조회 시간 설정
                end_time = datetime.datetime.now()
                start_time = end_time - datetime.timedelta(days=30 * self.months)
                
                # Write Capacity Units 사용량
                wcu_stats = await self._get_cloudwatch_metrics(
                    cloudwatch,
                    'ConsumedWriteCapacityUnits',
                    'AWS/DynamoDB',
                    [{'Name': 'TableName', 'Value': table_name}],
                    start_time,
                    end_time
                )
                
                # Read Capacity Units 사용량
                rcu_stats = await self._get_cloudwatch_metrics(
                    cloudwatch, 
                    'ConsumedReadCapacityUnits',
                    'AWS/DynamoDB',
                    [{'Name': 'TableName', 'Value': table_name}],
                    start_time,
                    end_time
                )
            
            # 사용률 계산 (프로비저닝된 값이 0인 경우 처리)
            wcu_utilization = 0
            if provisioned_wcu > 0:
                wcu_utilization = (wcu_stats[0] / provisioned_wcu) * 100
                
            rcu_utilization = 0
            if provisioned_rcu > 0:
                rcu_utilization = (rcu_stats[0] / provisioned_rcu) * 100
            
            # 결과 반환
            return {
                "table_name": table_name,
                "provisioned_wcu": provisioned_wcu,
                "provisioned_rcu": provisioned_rcu,
                "consumed_wcu_avg": wcu_stats[0],
                "consumed_wcu_min": wcu_stats[1],
                "consumed_wcu_max": wcu_stats[2],
                "consumed_rcu_avg": rcu_stats[0],
                "consumed_rcu_min": rcu_stats[1],
                "consumed_rcu_max": rcu_stats[2],
                "wcu_utilization_percent": round(wcu_utilization, 2),
                "rcu_utilization_percent": round(rcu_utilization, 2),
                "billing_mode": billing_mode,
                "period_months": self.months,
                "region": self.region
            }
                
        except Exception as e:
            print(f"테이블 {table_name} 정보 조회 실패: {e}")
            return {
                "table_name": table_name,
                "provisioned_wcu": 0,
                "provisioned_rcu": 0,
                "consumed_wcu_avg": 0,
                "consumed_wcu_min": 0,
                "consumed_wcu_max": 0,
                "consumed_rcu_avg": 0,
                "consumed_rcu_min": 0,
                "consumed_rcu_max": 0,
                "wcu_utilization_percent": 0,
                "rcu_utilization_percent": 0,
                "billing_mode": "ERROR",
                "period_months": self.months,
                "region": self.region
            }
    
    async def _get_cloudwatch_metrics(
        self, 
        cloudwatch: Any, 
        metric_name: str, 
        namespace: str,
        dimensions: List[Dict[str, str]],
        start_time: datetime.datetime,
        end_time: datetime.datetime
    ) -> Tuple[float, float, float]:
        """
        CloudWatch 지표 조회
        
        Args:
            cloudwatch: CloudWatch 클라이언트
            metric_name: 지표 이름
            namespace: 네임스페이스
            dimensions: 측정 차원
            start_time: 시작 시간
            end_time: 종료 시간
            
        Returns:
            Tuple[float, float, float]: (평균값, 최소값, 최대값)
        """
        try:
            # 평균값 조회
            avg_response = await cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1시간 단위로 조회
                Statistics=['Average']
            )
            
            # 최소값 조회
            min_response = await cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Minimum']
            )
            
            # 최대값 조회
            max_response = await cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Maximum']
            )
            
            # 데이터가 없는 경우 처리
            avg_data_points = avg_response.get('Datapoints', [])
            min_data_points = min_response.get('Datapoints', [])
            max_data_points = max_response.get('Datapoints', [])
            
            avg_value = 0
            if avg_data_points:
                avg_value = sum(point['Average'] for point in avg_data_points) / len(avg_data_points)
                
            min_value = 0
            if min_data_points:
                min_value = min(point['Minimum'] for point in min_data_points)
                
            max_value = 0
            if max_data_points:
                max_value = max(point['Maximum'] for point in max_data_points)
                
            return avg_value, min_value, max_value
            
        except Exception as e:
            print(f"CloudWatch 지표 {metric_name} 조회 실패: {e}")
            return 0, 0, 0