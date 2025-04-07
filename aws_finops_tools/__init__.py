"""AWS FinOps Tools 패키지"""
import atexit
import asyncio
from .main import main_cli
from .utils.aws_utils import cleanup_resources

# 애플리케이션 종료 시 모든 리소스 정리
def _cleanup_on_exit():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(cleanup_resources())
    finally:
        loop.close()

atexit.register(_cleanup_on_exit)