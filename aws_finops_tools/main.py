# main.py
import asyncio
import platform
from .menu import Menu

async def main() -> None:
    """Main program"""
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
    # Fix for Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run main program
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()