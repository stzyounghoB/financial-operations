import asyncio
import datetime
from typing import List, Dict, Any, Optional, Union, TypedDict, Tuple
import aioboto3
from ....interfaces.service_interface import ServiceInterface


class DynamoCUInfo(TypedDict):
    """DynamoDB table CU information type definition"""
    table_name: str
    provisioned_wcu_avg: float  # 이름 변경
    provisioned_wcu_min: float  # 추가
    provisioned_wcu_max: float  # 추가
    provisioned_rcu_avg: float  # 이름 변경
    provisioned_rcu_min: float  # 추가
    provisioned_rcu_max: float  # 추가
    consumed_wcu_avg: float
    consumed_wcu_min: float
    consumed_wcu_max: float
    consumed_rcu_avg: float
    consumed_rcu_min: float
    consumed_rcu_max: float
    wcu_utilization_percent: float
    rcu_utilization_percent: float
    unused_wcu: float  # 새로 추가: 미사용 WCU
    unused_rcu: float  # 새로 추가: 미사용 RCU
    billing_mode: str
    period_months: int
    region: str


class DynamoCUHandler(ServiceInterface[DynamoCUInfo]):
    """Handler for DynamoDB CU operations"""
    
    def __init__(self, region: str, session: Optional[Union[str, tuple[str, str]]] = None, months: int = 1):
        """
        Initialize DynamoDB CU handler
        
        Args:
            region: AWS region
            session: AWS session info
            months: Period to query (in months)
        """
        super().__init__(region, session)
        self.months = months
    
    async def fetch_data(self) -> List[DynamoCUInfo]:
        """Fetch DynamoDB table CU information asynchronously"""
        # Create DynamoDB client
        async with aioboto3.Session(**self.session_args).client('dynamodb', region_name=self.region) as dynamodb:
            try:
                # Fetch all DynamoDB table list
                response = await dynamodb.list_tables()
                table_names = response.get('TableNames', [])
                
                # Handle pagination
                while 'LastEvaluatedTableName' in response:
                    response = await dynamodb.list_tables(
                        ExclusiveStartTableName=response['LastEvaluatedTableName']
                    )
                    table_names.extend(response.get('TableNames', []))
                
                if not table_names:
                    print(f"No DynamoDB tables found in region {self.region}")
                    return []
                
                # Fetch detailed information and CloudWatch metrics for each table
                tasks = [self.get_table_cu_info(table_name, dynamodb) for table_name in table_names]
                
                return await asyncio.gather(*tasks)
                
            except Exception as e:
                print(f"Failed to fetch DynamoDB tables: {e}")
                return []
    
    async def get_table_cu_info(self, table_name: str, dynamodb: Any) -> DynamoCUInfo:
        """
        Fetch individual DynamoDB table CU information
        
        Args:
            table_name: DynamoDB table name
            dynamodb: DynamoDB client
            
        Returns:
            DynamoCUInfo: Table CU information
        """
        try:
            # Fetch table details
            table_info = await dynamodb.describe_table(TableName=table_name)
            table = table_info.get('Table', {})
            
            # Check billing mode
            billing_mode = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
            
            # Initialize default values
            provisioned_wcu_avg = 0
            provisioned_wcu_min = 0
            provisioned_wcu_max = 0
            provisioned_rcu_avg = 0
            provisioned_rcu_min = 0
            provisioned_rcu_max = 0
            
            # Get initial provisioned values from table description as fallback
            if billing_mode == 'PROVISIONED':
                provisioning_info = table.get('ProvisionedThroughput', {})
                default_provisioned_wcu = float(provisioning_info.get('WriteCapacityUnits', 0))
                default_provisioned_rcu = float(provisioning_info.get('ReadCapacityUnits', 0))
            else:
                default_provisioned_wcu = 0
                default_provisioned_rcu = 0
            
            # Fetch CloudWatch metrics
            async with aioboto3.Session(**self.session_args).client('cloudwatch', region_name=self.region) as cloudwatch:
                # Setup query time
                end_time = datetime.datetime.now()
                # Round end_time up to the nearest 5-minute mark
                minute_remainder = end_time.minute % 5
                if minute_remainder != 0:
                    end_time = end_time + datetime.timedelta(minutes=5-minute_remainder)
                # Set seconds and microseconds to 0
                end_time = end_time.replace(second=0, microsecond=0)
                
                # Calculate start_time and round down to nearest 5-minute mark
                start_time = end_time - datetime.timedelta(days=30 * self.months)
                minute_remainder = start_time.minute % 5
                if minute_remainder != 0:
                    start_time = start_time - datetime.timedelta(minutes=minute_remainder)
                start_time = start_time.replace(second=0, microsecond=0)
                
                dimensions = [{'Name': 'TableName', 'Value': table_name}]
                
                # Fetch consumed metrics
                consumed_wcu = await self._get_cloudwatch_metrics(
                    cloudwatch,
                    'ConsumedWriteCapacityUnits',
                    'AWS/DynamoDB',
                    dimensions,
                    start_time,
                    end_time
                )
                
                consumed_rcu = await self._get_cloudwatch_metrics(
                    cloudwatch, 
                    'ConsumedReadCapacityUnits',
                    'AWS/DynamoDB',
                    dimensions,
                    start_time,
                    end_time
                )
                
                # Fetch provisioned metrics (only for PROVISIONED billing mode)
                if billing_mode == 'PROVISIONED':
                    provisioned_wcu_stats = await self._get_cloudwatch_metrics(
                        cloudwatch,
                        'ProvisionedWriteCapacityUnits',
                        'AWS/DynamoDB',
                        dimensions,
                        start_time,
                        end_time
                    )
                    
                    provisioned_rcu_stats = await self._get_cloudwatch_metrics(
                        cloudwatch,
                        'ProvisionedReadCapacityUnits',
                        'AWS/DynamoDB',
                        dimensions,
                        start_time,
                        end_time
                    )
                    
                    # Use CloudWatch metrics if available, otherwise use the table description values
                    provisioned_wcu_avg = provisioned_wcu_stats[0] if provisioned_wcu_stats[0] > 0 else default_provisioned_wcu
                    provisioned_wcu_min = provisioned_wcu_stats[1] if provisioned_wcu_stats[1] > 0 else default_provisioned_wcu
                    provisioned_wcu_max = provisioned_wcu_stats[2] if provisioned_wcu_stats[2] > 0 else default_provisioned_wcu
                    
                    provisioned_rcu_avg = provisioned_rcu_stats[0] if provisioned_rcu_stats[0] > 0 else default_provisioned_rcu
                    provisioned_rcu_min = provisioned_rcu_stats[1] if provisioned_rcu_stats[1] > 0 else default_provisioned_rcu
                    provisioned_rcu_max = provisioned_rcu_stats[2] if provisioned_rcu_stats[2] > 0 else default_provisioned_rcu
                
            # Calculate utilization (handle case where provisioned value is 0)
            wcu_utilization = 0
            if provisioned_wcu_avg > 0:
                wcu_utilization = (consumed_wcu[0] / provisioned_wcu_avg) * 100
                
            rcu_utilization = 0
            if provisioned_rcu_avg > 0:
                rcu_utilization = (consumed_rcu[0] / provisioned_rcu_avg) * 100
            
            # 미사용 용량 계산
            unused_wcu = provisioned_wcu_avg - consumed_wcu[0]
            unused_rcu = provisioned_rcu_avg - consumed_rcu[0]
            
            # 미사용 용량이 음수인 경우 0으로 설정 (온디맨드나 오토스케일링 경우)
            unused_wcu = max(0, unused_wcu)
            unused_rcu = max(0, unused_rcu)
            
            # Return result
            return {
                "table_name": table_name,
                "provisioned_wcu_avg": provisioned_wcu_avg,
                "provisioned_wcu_min": provisioned_wcu_min,
                "provisioned_wcu_max": provisioned_wcu_max,
                "provisioned_rcu_avg": provisioned_rcu_avg,
                "provisioned_rcu_min": provisioned_rcu_min,
                "provisioned_rcu_max": provisioned_rcu_max,
                "consumed_wcu_avg": consumed_wcu[0],
                "consumed_wcu_min": consumed_wcu[1],
                "consumed_wcu_max": consumed_wcu[2],
                "consumed_rcu_avg": consumed_rcu[0],
                "consumed_rcu_min": consumed_rcu[1],
                "consumed_rcu_max": consumed_rcu[2],
                "wcu_utilization_percent": round(wcu_utilization, 2),
                "rcu_utilization_percent": round(rcu_utilization, 2),
                "unused_wcu": round(unused_wcu, 2),  # 미사용 WCU 추가
                "unused_rcu": round(unused_rcu, 2),  # 미사용 RCU 추가
                "billing_mode": billing_mode,
                "period_months": self.months,
                "region": self.region
            }
                
        except Exception as e:
            print(f"Failed to fetch information for table {table_name}: {e}")
            return {
                "table_name": table_name,
                "provisioned_wcu_avg": 0,
                "provisioned_wcu_min": 0,
                "provisioned_wcu_max": 0,
                "provisioned_rcu_avg": 0,
                "provisioned_rcu_min": 0,
                "provisioned_rcu_max": 0,
                "consumed_wcu_avg": 0,
                "consumed_wcu_min": 0,
                "consumed_wcu_max": 0,
                "consumed_rcu_avg": 0,
                "consumed_rcu_min": 0,
                "consumed_rcu_max": 0,
                "wcu_utilization_percent": 0,
                "rcu_utilization_percent": 0,
                "unused_wcu": 0,  # 미사용 WCU 추가
                "unused_rcu": 0,  # 미사용 RCU 추가
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
        Fetch CloudWatch metrics
        
        Args:
            cloudwatch: CloudWatch client
            metric_name: Metric name
            namespace: Namespace
            dimensions: Measurement dimensions
            start_time: Start time
            end_time: End time
            
        Returns:
            Tuple[float, float, float]: (average, minimum, maximum)
        """
        try:
            # Fixed line below - dimensions is a list of dictionaries
            print(f"Calculating - {dimensions[0]['Value']} - {metric_name}")
            # Use 5-minute periods for more accurate data
            period = 300  # 5 minutes in seconds
            
            # Ensure start and end times are aligned to 5-minute intervals
            # Round start_time down to the nearest 5-minute mark
            minute_remainder = start_time.minute % 5
            if minute_remainder != 0:
                start_time = start_time - datetime.timedelta(minutes=minute_remainder)
            start_time = start_time.replace(second=0, microsecond=0)
            
            # Round end_time up to the nearest 5-minute mark
            minute_remainder = end_time.minute % 5
            if minute_remainder != 0:
                end_time = end_time + datetime.timedelta(minutes=5-minute_remainder)
            end_time = end_time.replace(second=0, microsecond=0)
            
            # Calculate the maximum number of datapoints we can request per API call
            MAX_DATAPOINTS = 1440
            
            # Calculate the total time range in seconds
            total_seconds = int((end_time - start_time).total_seconds())
            
            # Calculate the number of datapoints we would get with the current period
            estimated_datapoints = total_seconds // period
            
            all_datapoints = []
            
            if estimated_datapoints > MAX_DATAPOINTS:
                # We need to chunk the requests
                chunk_duration = datetime.timedelta(seconds=period * MAX_DATAPOINTS)
                chunk_start = start_time
                
                # 비동기 작업 목록 생성
                chunk_tasks = []
                
                while chunk_start < end_time:
                    # Ensure chunk_end is also aligned to 5-minute intervals
                    chunk_end = min(chunk_start + chunk_duration, end_time)
                    
                    # 각 청크를 비동기 작업으로 추가
                    chunk_tasks.append(
                        self._get_chunk_metrics(
                            cloudwatch,
                            namespace,
                            metric_name,
                            dimensions,
                            chunk_start,
                            chunk_end,
                            period
                        )
                    )
                    
                    # Move to next chunk, ensuring 5-minute alignment
                    chunk_start = chunk_end
                
                # 모든 청크 작업을 동시에, 병렬로 실행
                chunk_results = await asyncio.gather(*chunk_tasks)
                
                # 결과 합치기
                for datapoints in chunk_results:
                    all_datapoints.extend(datapoints)
            else:
                # We can make a single request
                response = await cloudwatch.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=dimensions,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period,
                    Statistics=['Average', 'Minimum', 'Maximum', 'Sum']
                )
                
                all_datapoints = response.get('Datapoints', [])
            
            if not all_datapoints:
                return 0, 0, 0
            
            # 메트릭 유형에 따라 계산 방식 다르게 적용
            is_provisioned = metric_name.startswith('Provisioned')
            
            if is_provisioned:
                # Provisioned 메트릭 - Average 값들의 평균
                sum_values = sum(point['Average'] for point in all_datapoints)
                avg_value = sum_values / len(all_datapoints)
                min_value = min((point['Average'] for point in all_datapoints), default=0)
                max_value = max((point['Average'] for point in all_datapoints), default=0)
            else:
                # Consumed 메트릭 - Sum 값들의 평균을 초당 소비량으로 변환
                sum_values = sum(point['Sum'] for point in all_datapoints)
                avg_value = (sum_values / period) / len(all_datapoints)
                min_value = min((point['Sum'] for point in all_datapoints), default=0) / period
                max_value = max((point['Sum'] for point in all_datapoints), default=0) / period
            
            return avg_value, min_value, max_value
            
        except Exception as e:
            print(f"Failed to fetch CloudWatch metric {metric_name}: {e}")
            return 0, 0, 0
    
    # 새로운 헬퍼 메소드 추가
    async def _get_chunk_metrics(
        self,
        cloudwatch: Any,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]],
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        period: int
    ) -> List[Dict[str, Any]]:
        """
        각 청크에 대한 CloudWatch 메트릭을 가져오는 헬퍼 메소드
        """
        response = await cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=['Average', 'Minimum', 'Maximum', 'Sum']
        )
        
        return response.get('Datapoints', [])
