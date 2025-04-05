from typing import List, Dict, Any, Optional
from ..interfaces.output_interface import OutputInterface

class ConsoleOutput(OutputInterface):
    """Handler for console output"""
    
    async def output(self, data: List[Dict[str, Any]], path: Optional[str] = None) -> bool:
        """
        Output data to console
        
        Args:
            data: Data to output
            path: Not used for console output
            
        Returns:
            bool: Success status
        """
        try:
            print(f"\nItems count: {len(data)}")
            for item in data:
                print("\n" + "-" * 40)
                for key, value in item.items():
                    print(f"{key}: {value}")
            return True
        except Exception as e:
            print(f"Error outputting to console: {e}")
            return False
