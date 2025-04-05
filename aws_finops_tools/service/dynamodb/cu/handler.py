import asyncio
import datetime
from typing import List, Dict, Any, Optional, Union, TypedDict, Tuple
import aioboto3
from ....interfaces.service_interface import ServiceInterface


class DynamoCUInfo(TypedDict):
    """DynamoDB table CU information type definition"""
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
            provisioned_wcu = 0
            provisioned_rcu = 0
            
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
                    provisioned_wcu = provisioned_wcu_stats[0] if provisioned_wcu_stats[0] > 0 else default_provisioned_wcu
                    provisioned_rcu = provisioned_rcu_stats[0] if provisioned_rcu_stats[0] > 0 else default_provisioned_rcu
                
            # Calculate utilization (handle case where provisioned value is 0)
            wcu_utilization = 0
            if provisioned_wcu > 0:
                wcu_utilization = (consumed_wcu[0] / provisioned_wcu) * 100
                
            rcu_utilization = 0
            if provisioned_rcu > 0:
                rcu_utilization = (consumed_rcu[0] / provisioned_rcu) * 100
            
            # Return result
            return {
                "table_name": table_name,
                "provisioned_wcu": provisioned_wcu,
                "provisioned_rcu": provisioned_rcu,
                "consumed_wcu_avg": consumed_wcu[0],
                "consumed_wcu_min": consumed_wcu[1],
                "consumed_wcu_max": consumed_wcu[2],
                "consumed_rcu_avg": consumed_rcu[0],
                "consumed_rcu_min": consumed_rcu[1],
                "consumed_rcu_max": consumed_rcu[2],
                "wcu_utilization_percent": round(wcu_utilization, 2),
                "rcu_utilization_percent": round(rcu_utilization, 2),
                "billing_mode": billing_mode,
                "period_months": self.months,
                "region": self.region
            }
                
        except Exception as e:
            print(f"Failed to fetch information for table {table_name}: {e}")
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
            print(f"Calculating - {dimensions[0]['Value']}")
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
                
                while chunk_start < end_time:
                    # Ensure chunk_end is also aligned to 5-minute intervals
                    chunk_end = min(chunk_start + chunk_duration, end_time)
                        
                    # Make a request for this chunk
                    response = await cloudwatch.get_metric_statistics(
                        Namespace=namespace,
                        MetricName=metric_name,
                        Dimensions=dimensions,
                        StartTime=chunk_start,
                        EndTime=chunk_end,
                        Period=period,
                        Statistics=['Average', 'Minimum', 'Maximum', 'Sum']
                    )
                    
                    all_datapoints.extend(response.get('Datapoints', []))
                    
                    # Move to next chunk, ensuring 5-minute alignment
                    chunk_start = chunk_end
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
            
            # Calculate true average across all data points
            sum_values = sum(point['Sum'] for point in all_datapoints)
            avg_value = (sum_values / period) / len(all_datapoints)
            # if dimensions[0]['Value'] == 'anipang2.event':
            #     # Fixed syntax error: properly print each datapoint
            #     print(f"All datapoints for {metric_name}:")
            #     for point in all_datapoints:
            #         print(f"point : {point} average : {point['Sum'] / period}\n")
            #     print(f"metric_name: {metric_name}\n")
            #     print(f"avg_value: {avg_value}\n")
            #     print(f"sum_values: {sum_values}\n")
            #     print(f"len(all_datapoints): {len(all_datapoints)}\n")
            #     print('--------')
                
            # Find the absolute minimum and maximum across all data points
            min_value = min((point['Minimum'] for point in all_datapoints), default=0)
            max_value = max((point['Maximum'] for point in all_datapoints), default=0)
            
            return avg_value, min_value, max_value
            
        except Exception as e:
            print(f"Failed to fetch CloudWatch metric {metric_name}: {e}")
            return 0, 0, 0
