"""AWS 리소스 사용을 위한 유틸리티"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable
import aioboto3
from contextlib import asynccontextmanager

# 공유 세션 및 클라이언트 관리자
_sessions = {}
_clients = {}
_init_complete = False


@asynccontextmanager
async def get_aws_client(service_name: str, region_name: str, session_args: Dict[str, Any] = None):
    """
    AWS 서비스 클라이언트를 반환하는 컨텍스트 매니저
    
    이 함수는 세션과 클라이언트를 재사용하여 리소스 누수를 방지합니다.
    
    사용법:
    ```
    async with get_aws_client('ec2', 'us-east-1') as ec2:
        volumes = await ec2.describe_volumes()
    ```
    
    Args:
        service_name: AWS 서비스 이름 (예: 'ec2', 'dynamodb')
        region_name: AWS 리전 이름
        session_args: AWS 세션 생성 인자
        
    Yields:
        AWS 서비스 클라이언트
    """
    global _sessions, _clients, _init_complete
    
    if session_args is None:
        session_args = {}
    
    # 세션 키 생성
    session_key = hash(frozenset(session_args.items()))
    # 클라이언트 키 생성
    client_key = f"{service_name}:{region_name}:{session_key}"
    
    try:
        # 기존 클라이언트가 있으면 재사용
        if client_key in _clients:
            yield _clients[client_key]
            return
        
        # 세션 생성 또는 재사용
        if session_key not in _sessions:
            _sessions[session_key] = aioboto3.Session(**session_args)
            
        # 클라이언트 생성 및 저장
        client = await _sessions[session_key].client(
            service_name, 
            region_name=region_name
        ).__aenter__()
        
        _clients[client_key] = client
        yield client
    
    except Exception as e:
        print(f"AWS 클라이언트 에러: {e}")
        raise
    # finally 블록은 필요 없음 - 여기서 클라이언트를 닫지 않음


async def cleanup_resources():
    """
    모든 AWS 클라이언트와 세션을 정리합니다.
    애플리케이션 종료 시 호출해야 합니다.
    """
    global _clients, _sessions, _init_complete
    
    # 모든 클라이언트 닫기
    close_tasks = []
    for key, client in list(_clients.items()):
        try:
            close_tasks.append(client.__aexit__(None, None, None))
        except Exception as e:
            print(f"클라이언트 닫기 오류 ({key}): {e}")
    
    if close_tasks:
        await asyncio.gather(*close_tasks, return_exceptions=True)
    
    # 세션과 클라이언트 딕셔너리 비우기
    _clients.clear()
    _sessions.clear()
    
    # aiohttp 세션이 완전히 닫힐 시간 주기
    await asyncio.sleep(0.5)
    
    print("모든 AWS 리소스가 정리되었습니다.")
