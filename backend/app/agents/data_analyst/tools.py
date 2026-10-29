import csv
import io
import math
import statistics
from typing import Dict, Any, List, Optional


def calculate_statistics(numbers: List[float]) -> Dict[str, Any]:
    """Computes key descriptive statistics for a list of numerical values."""
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
        "sum": round(sum(sorted_nums), 4),
    }


def format_csv_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    """Transforms structured tabular data into clean GitHub Flavored Markdown."""
    if not headers:
        return {"table_markdown": "", "row_count": 0}
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    data_lines = ["| " + " | ".join(str(item) for item in r) + " |" for r in rows]
    table = "\n".join([header_line, sep_line] + data_lines)
    return {
        "table_markdown": table,
        "headers": headers,
        "row_count": len(rows),
    }


def correlate_variables(x: List[float], y: List[float]) -> Dict[str, Any]:
    """Computes the Pearson correlation coefficient and R-squared between two variables."""
    if len(x) != len(y) or len(x) < 2:
        return {"error": "Variables must have identical lengths greater than 1."}

    n = len(x)
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / (n - 1)
    stdev_x = statistics.stdev(x)
    stdev_y = statistics.stdev(y)

    if stdev_x == 0 or stdev_y == 0:
        return {"pearson_r": 0.0, "r_squared": 0.0, "interpretation": "Constant variable (zero variance)"}

    r = cov / (stdev_x * stdev_y)
    r = max(-1.0, min(1.0, r))
    r2 = r ** 2

    strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.4 else "weak"
    direction = "positive" if r > 0 else "negative" if r < 0 else "neutral"

    return {
        "pearson_r": round(r, 4),
        "r_squared": round(r2, 4),
        "sample_size": n,
        "relationship": f"{strength} {direction} correlation",
    }


def linear_forecast(data_points: List[float], periods_ahead: int = 3) -> Dict[str, Any]:
    """Computes linear trend regression slope/intercept and forecasts upcoming periods."""
    if len(data_points) < 2:
        return {"error": "At least 2 data points required for linear forecasting."}

    n = len(data_points)
    x = list(range(n))
    y = data_points

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0.0
    intercept = mean_y - slope * mean_x

    forecast = []
    for step in range(1, periods_ahead + 1):
        target_x = n - 1 + step
        pred = intercept + slope * target_x
        forecast.append({"period": target_x, "forecasted_value": round(pred, 4)})

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "trend_direction": "upward" if slope > 0 else "downward" if slope < 0 else "flat",
        "forecast": forecast,
    }


def parse_tabular_csv(csv_content: str, delimiter: str = ",") -> Dict[str, Any]:
    """Parses raw CSV string, returns headers, sample data, and column profile metrics."""
    reader = csv.reader(io.StringIO(csv_content.strip()), delimiter=delimiter)
    all_rows = list(reader)
    if not all_rows:
        return {"error": "Empty CSV content provided."}

    headers = all_rows[0]
    data_rows = all_rows[1:]

    col_stats = []
    for col_idx, col_name in enumerate(headers):
        vals = [r[col_idx] for r in data_rows if len(r) > col_idx and r[col_idx].strip() != ""]
        numeric_vals = []
        for v in vals:
            try:
                numeric_vals.append(float(v))
            except ValueError:
                pass
        col_stats.append({
            "name": col_name,
            "non_empty_count": len(vals),
            "is_numeric": len(numeric_vals) == len(vals) and len(vals) > 0,
            "min": min(numeric_vals) if numeric_vals else None,
            "max": max(numeric_vals) if numeric_vals else None,
        })

    return {
        "headers": headers,
        "total_rows": len(data_rows),
        "columns_count": len(headers),
        "columns_summary": col_stats,
        "sample_preview": data_rows[:5],
    }


def detect_anomalies(numbers: List[float], threshold_z: float = 2.0) -> Dict[str, Any]:
    """Identifies statistical outlier values using standard Z-score analysis."""
    if len(numbers) < 3:
        return {"error": "At least 3 values required to calculate statistical outliers."}

    mean_val = statistics.mean(numbers)
    stdev_val = statistics.stdev(numbers)

    if stdev_val == 0.0:
        return {"outliers_count": 0, "outliers": [], "note": "Zero standard deviation in dataset."}

    outliers = []
    for idx, val in enumerate(numbers):
        z_score = (val - mean_val) / stdev_val
        if abs(z_score) >= threshold_z:
            outliers.append({
                "index": idx,
                "value": val,
                "z_score": round(z_score, 3),
                "type": "high_spike" if z_score > 0 else "low_dip",
            })

    return {
        "total_points": len(numbers),
        "threshold_z": threshold_z,
        "outliers_count": len(outliers),
        "outliers": outliers,
    }


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
                    "description": "Array of numerical data points",
                }
            },
            "required": ["numbers"],
        },
        "handler_name": "calculate_statistics",
    },
    {
        "name": "format_csv_table",
        "description": "Transforms structured data rows and headers into a markdown table.",
        "parameters": {
            "type": "object",
            "properties": {
                "headers": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
                "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Data rows"},
            },
            "required": ["headers", "rows"],
        },
        "handler_name": "format_csv_table",
    },
    {
        "name": "correlate_variables",
        "description": "Calculates Pearson correlation coefficient and R-squared between two numerical series.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "array", "items": {"type": "number"}, "description": "First variable dataset"},
                "y": {"type": "array", "items": {"type": "number"}, "description": "Second variable dataset"},
            },
            "required": ["x", "y"],
        },
        "handler_name": "correlate_variables",
    },
    {
        "name": "linear_forecast",
        "description": "Fits linear regression trendline to historical sequence and forecasts future periods.",
        "parameters": {
            "type": "object",
            "properties": {
                "data_points": {"type": "array", "items": {"type": "number"}, "description": "Sequential data values"},
                "periods_ahead": {"type": "integer", "description": "Number of future periods to project"},
            },
            "required": ["data_points"],
        },
        "handler_name": "linear_forecast",
    },
    {
        "name": "parse_tabular_csv",
        "description": "Parses raw CSV string into structured schema, row counts, and column summaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "csv_content": {"type": "string", "description": "Raw CSV string data"},
                "delimiter": {"type": "string", "description": "CSV delimiter character (default ',')"},
            },
            "required": ["csv_content"],
        },
        "handler_name": "parse_tabular_csv",
    },
    {
        "name": "detect_anomalies",
        "description": "Discovers numerical outliers and extreme variations via Z-score thresholding.",
        "parameters": {
            "type": "object",
            "properties": {
                "numbers": {"type": "array", "items": {"type": "number"}, "description": "Numerical sample dataset"},
                "threshold_z": {"type": "number", "description": "Z-score threshold (default 2.0)"},
            },
            "required": ["numbers"],
        },
        "handler_name": "detect_anomalies",
    },
]

TOOL_HANDLERS = {
    "calculate_statistics": calculate_statistics,
    "format_csv_table": format_csv_table,
    "correlate_variables": correlate_variables,
    "linear_forecast": linear_forecast,
    "parse_tabular_csv": parse_tabular_csv,
    "detect_anomalies": detect_anomalies,
}
