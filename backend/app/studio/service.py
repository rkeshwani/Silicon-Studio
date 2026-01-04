import pandas as pd
import json
import os
from typing import List, Dict, Any

class DataStudioService:
    def __init__(self):
        pass

    def preview_csv(self, file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Read a CSV and return a preview of the data.
        """
        try:
            df = pd.read_csv(file_path)
            # Replace NaN with None for JSON compatibility
            df = df.where(pd.notnull(df), None)
            return df.head(limit).to_dict(orient="records")
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {str(e)}")

    def convert_csv_to_jsonl(self, file_path: str, output_path: str, instruction_col: str, input_col: str, output_col: str):
        """
        Convert CSV to generic JSONL format for fine-tuning.
        Format: {"instruction": ..., "input": ..., "output": ...}
        """
        try:
            df = pd.read_csv(file_path)
            
            with open(output_path, 'w') as f:
                for _, row in df.iterrows():
                    record = {
                        "instruction": row.get(instruction_col, ""),
                        "input": row.get(input_col, "") if input_col else "",
                        "output": row.get(output_col, "")
                    }
                    f.write(json.dumps(record) + "\n")
            
            return {"status": "success", "rows": len(df), "output_path": output_path}
        except Exception as e:
            raise ValueError(f"Conversion failed: {str(e)}")
