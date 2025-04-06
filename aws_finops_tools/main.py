# main.py
import asyncio
import platform
from .menu import Menu
from .menu import Menu
# 버전 정보 업데이트
__version__ = "0.1.2"  # setup.py와 동일한 버전으로 유지

async def main() -> None:
    """Main program"""c def main() -> None:
    # Create menu and get user selections"
    menu = Menu()ion__}")
    
    # Get AWS profile get user selections
    session = menu.pick_aws_profile()
    
    # Get AWS regionse
    regions = menu.pick_region()
        
    # Show main menuegions
    await menu.main_menu(session, regions)egion()

def main_cli():
    """CLI entry point"""
    # Fix for Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())""
        # 버전 정보 확인 처리
    # Run main programnd sys.argv[1] == "--version":
    asyncio.run(main())f"AWS FinOps Tools v{__version__}")



    main_cli()if __name__ == "__main__":        return

    # Fix for Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run main program
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()