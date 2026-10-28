import statistics
from typing import Dict, Any, List

def calculate_statistics(numbers: List[float]) -> Dict[str, Any]:
    """
    Computes key descriptive statistics for a list of numerical values.
    """
    if not numbers:
        return {"error": "Empty numbers list provided."}

    sorted_nums = sorted(numbers)
    count = len(sorted_nums)
    mean_val = statistics.mean(sorted_nums)
    median_val = statistics.median(sorted_nums)
    stdev_val = statistics.stdev(sorted_nums) if count > 1 else 0.0

    return {
        "count": count,
        "min": sorted_nums[0],
        "max": sorted_nums[-1],
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "stdev": round(stdev_val, 4),
    }

def format_csv_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Transforms structured data into a Markdown table.
    """
    if not headers:
        return ""
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    data_lines = ["| " + " | ".join(str(item) for item in r) + " |" for r in rows]
    return "\n".join([header_line, sep_line] + data_lines)

TOOLS = [
    {
        "name": "calculate_statistics",
        "description": "Calculates descriptive statistics (mean, median, stdev, range) for numerical lists.",
        "parameters": {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Array of numerical data points"
                }
            },
            "required": ["numbers"]
        },
        "handler_name": "calculate_statistics"
    }
]

TOOL_HANDLERS = {
    "calculate_statistics": calculate_statistics,
    "format_csv_table": format_csv_table,
}
