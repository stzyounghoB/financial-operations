import json
import csv
import os
from typing import List, Dict, Any, Optional
from ..interfaces.output_interface import OutputInterface

class FileOutput(OutputInterface):
    """Base handler for file output"""
    
    async def output(self, data: List[Dict[str, Any]], path: Optional[str] = None) -> bool:
        """
        Output data to file
        
        Args:
            data: Data to output
            path: File path
            
        Returns:
            bool: Success status
        """
        if not path:
            print("No file path provided.")
            return False
            
        try:
            # Check and create directory
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
                
            return self._write_to_file(data, path)
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False
    
    def _write_to_file(self, data: List[Dict[str, Any]], path: str) -> bool:
        """
        Write data to file (to be implemented by subclasses)
        
        Args:
            data: Data to write
            path: File path
            
        Returns:
            bool: Success status
        """
        raise NotImplementedError("Subclasses must implement _write_to_file")


class JsonOutput(FileOutput):
    """Handler for JSON output"""
    
    def _write_to_file(self, data: List[Dict[str, Any]], path: str) -> bool:
        """
        Write data to JSON file
        
        Args:
            data: Data to write
            path: File path
            
        Returns:
            bool: Success status
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {path}")
        return True


class DelimitedOutput(FileOutput):
    """Base handler for delimited file output"""
    
    def __init__(self, delimiter: str):
        """
        Initialize delimited output handler
        
        Args:
            delimiter: Field delimiter
        """
        self.delimiter = delimiter
    
    def _write_to_file(self, data: List[Dict[str, Any]], path: str) -> bool:
        """
        Write data to delimited file
        
        Args:
            data: Data to write
            path: File path
            
        Returns:
            bool: Success status
        """
        if not data:
            print("No data to save.")
            return False
            
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=self.delimiter)
            writer.writerow(data[0].keys())  # Write header
            for row in data:
                writer.writerow(row.values())
        
        print(f"Data saved to {path}")
        return True


class CsvOutput(DelimitedOutput):
    """Handler for CSV output"""
    
    def __init__(self):
        """Initialize CSV output handler"""
        super().__init__(delimiter=",")


class TsvOutput(DelimitedOutput):
    """Handler for TSV output"""
    
    def __init__(self):
        """Initialize TSV output handler"""
        super().__init__(delimiter="\t")
