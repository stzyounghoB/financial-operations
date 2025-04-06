# main.py
import asyncio
import platform
import sys
from .menu import Menu

# 버전 정보 추가
__version__ = "0.1.5"  # Current version

async def main() -> None:
    """Main program"""
    # Show version information
    print(f"AWS FinOps Tools v{__version__}")
    
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
        print(f"AWS FinOps Tools v{__version__}")
        return

    # Fix for Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run main program
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()