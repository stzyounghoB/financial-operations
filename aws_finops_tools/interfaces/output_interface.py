import abc
from typing import List, Dict, Any, Optional

class OutputInterface(abc.ABC):
    """Interface for output handlers"""

    @abc.abstractmethod
    async def output(self, data: List[Dict[str, Any]], path: Optional[str] = None) -> bool:
        """
        Output the data in the specific format
        
        Args:
            data: Data to output
            path: Optional file path (if applicable)
            
        Returns:
            bool: Success status
        """
        pass
