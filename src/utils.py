# utils.py
import json
import csv
import os
from typing import List, Dict, Any, Optional


async def save_to_file(data: List[Dict[str, Any]], file_path: str, format_type: str) -> bool:
    """
    데이터를 파일로 저장
    
    Args:
        data: 저장할 데이터
        file_path: 저장할 파일 경로
        format_type: 저장 형식 (json, csv, tsv)
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 디렉토리 확인 및 생성
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        if format_type == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        elif format_type in ["csv", "tsv"]:
            delimiter = "," if format_type == "csv" else "\t"
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                if not data:
                    print("저장할 데이터가 없습니다.")
                    return False
                    
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(data[0].keys())  # 헤더 작성
                for row in data:
                    writer.writerow(row.values())

        print(f"데이터가 {file_path} 파일로 저장되었습니다.")
        return True

    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        return False
        

def create_output_path(base_dir: Optional[str] = None) -> str:
    """
    출력 파일 디렉토리 생성
    
    Args:
        base_dir: 기본 디렉토리 경로
        
    Returns:
        str: 생성된 디렉토리 경로
    """
    
    from datetime import datetime
    
    if not base_dir:
        base_dir = os.path.join(os.getcwd(), "aws_reports")
    
    # 날짜별 디렉토리 생성
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(base_dir, date_str)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    return output_dir