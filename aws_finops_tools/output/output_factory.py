from typing import Dict, Optional, Type
from .console_output import ConsoleOutput
from .file_output import JsonOutput, CsvOutput, TsvOutput
from ..interfaces.output_interface import OutputInterface

class OutputFactory:
    """Factory for creating output handlers"""
    
    # Map of format types to output handler classes
    _handlers: Dict[str, Type[OutputInterface]] = {
        "console": ConsoleOutput,
        "json": JsonOutput,
        "csv": CsvOutput,
        "tsv": TsvOutput
    }
    
    @classmethod
    def get_handler(cls, format_type: str) -> OutputInterface:
        """
        Get an output handler for the specified format
        
        Args:
            format_type: Output format type
            
        Returns:
            OutputInterface: Output handler
        """
        handler_class = cls._handlers.get(format_type.lower())
        if not handler_class:
            print(f"Unknown output format: {format_type}. Using console output.")
            handler_class = ConsoleOutput
            
        return handler_class()
