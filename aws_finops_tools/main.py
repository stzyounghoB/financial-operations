# main.py
import asyncio
import platform
import sys
from .menu import Menu

# 런타임에 버전 정보 가져오기
def get_version():
    try:
        # Python 3.8+ 방식
        from importlib.metadata import version
        return version("aws_finops_tools")
    except ImportError:
        # 이전 Python 버전 방식
        import pkg_resources
        return pkg_resources.get_distribution("aws_finops_tools").version
    except Exception:
        # 개발 환경일 경우 git describe 명령어로 직접 가져오기
        try:
            import subprocess
            return subprocess.check_output(["git", "describe", "--tags"]).decode().strip()
        except:
            return "개발 버전"

# 버전 출력 부분 수정
VERSION = get_version()

async def main() -> None:
    """Main program"""
    # Show version information
    print(f"AWS FinOps Tools v{VERSION}")
    
    # Create menu and get user selections
    menu = Menu()
    
    # Get AWS profile
    session = menu.pick_aws_profile()
    
    # Get AWS regions
    regions = menu.pick_region()
    
    # Show main menu
    await menu.main_menu(session, regions)

def main_cli():
    """CLI entry point"""
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(f"AWS FinOps Tools v{VERSION}")
        return

    # Fix for Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run main program
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()