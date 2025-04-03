import json
import csv
import os

def save_to_file(data, file_path, format_type):
    """데이터를 JSON, CSV, TSV로 저장"""
    try:
        if format_type == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        elif format_type in ["csv", "tsv"]:
            delimiter = "," if format_type == "csv" else "\t"
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                if data:
                    writer.writerow(data[0].keys())  # 헤더 작성
                    for row in data:
                        writer.writerow(row.values())

        print(f"✅ 데이터가 {file_path} 파일로 저장되었습니다.")

    except Exception as e:
        print(f"❌ 파일 저장 중 오류 발생: {e}")
