import abc
from typing import Dict, List, Any, Optional, Union, Tuple

class MenuInterface(abc.ABC):
    """Interface for menu handlers"""

    @abc.abstractmethod
    def display_options(self) -> Dict[str, str]:
        """
        Display available options
        
        Returns:
            Dict[str, str]: Options mapping (key -> description)
        """
        pass
    
    @abc.abstractmethod
    def get_selection(self, prompt: str) -> str:
        """
        Get user selection
        
        Args:
            prompt: Prompt text to display
            
        Returns:
            str: Selected option key
        """
        pass
