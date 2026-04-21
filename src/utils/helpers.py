# -*- coding: utf-8 -*-
"""
通用工具函数
Inspired by Claude Code architecture - each utility in a focused module
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
import re
import os


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def to_float(value: Any, default: float = 0.0) -> float:
    text = safe_text(value).replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group()) if match else default


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(safe_text(value)))
    except (TypeError, ValueError):
        return default


def normalize_discount(value: Any, default: float = 1.0) -> float:
    text = safe_text(value).replace("%", "").replace("折", "")
    if not text:
        return default
    try:
        num = float(text)
    except ValueError:
        return default
    if num > 10:
        return round(num / 100.0, 4)
    if num > 1:
        return round(num / 10.0, 4)
    return round(num, 4)


def excel_date_to_text(value: Any) -> str:
    try:
        days = float(value)
        dt = datetime(1899, 12, 30) + timedelta(days=days)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return safe_text(value)


def clean_date_text(value: Any) -> str:
    text = safe_text(value)
    if not text:
        return ""
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return excel_date_to_text(text)
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text.replace("/", "-")


def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        if "A" <= ch <= "Z":
            n = n * 26 + (ord(ch) - 64)
    return n


def pick_value(row: Dict[str, Any], *aliases: str) -> str:
    lowered = {safe_text(k).lower(): v for k, v in row.items()}
    for alias in aliases:
        alias_value = row.get(alias)
        if safe_text(alias_value):
            return safe_text(alias_value)
        alias_value = lowered.get(alias.lower())
        if safe_text(alias_value):
            return safe_text(alias_value)
    return ""


def normalize_header_text(value: Any) -> str:
    text = safe_text(value)
    text = text.replace("\n", "").replace("\r", "").replace("\t", "")
    text = text.replace(" ", "").replace("　", "")
    text = text.replace("（", "(").replace("）", ")")
    return text


def is_free_shipping_excluded_region(address: Any) -> bool:
    address_text = safe_text(address)
    if not address_text:
        return False
    excluded_keywords = ["新疆", "西藏", "新疆维吾尔自治区", "西藏自治区"]
    return any(keyword in address_text for keyword in excluded_keywords)


def calculate_receivable_shipping_fee(
    book_amount: Any,
    recipient_address: Any,
    default_shipping_fee: Any = 6.0
) -> float:
    book_amount_value = to_float(book_amount, 0.0)
    shipping_fee = to_float(default_shipping_fee, 6.0)
    if book_amount_value >= 59.0 and not is_free_shipping_excluded_region(recipient_address):
        return 0.0
    return shipping_fee


def get_path_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def get_path_key(path: Path) -> str:
    try:
        return str(path.resolve()).lower()
    except OSError:
        return str(path).lower()


def is_today_file(file_path: Path) -> bool:
    try:
        return datetime.fromtimestamp(file_path.stat().st_ctime).date() == datetime.now().date()
    except OSError:
        return False


def append_runtime_log(message: str, exc_info: Any = None) -> None:
    from pathlib import Path
    from main import BASE_DIR
    APP_RUNTIME_LOG_PATH = BASE_DIR / 'software_runtime.log'
    lines = [f"[{now_str()}] {message}"]
    if exc_info:
        import traceback
        lines.append("".join(traceback.format_exception(*exc_info)).rstrip())
    try:
        with open(APP_RUNTIME_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines) + "\n\n")
    except Exception:
        pass
