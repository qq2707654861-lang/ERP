# -*- coding: utf-8 -*-
"""
通用工具函数 — 纯函数，无副作用，无外部依赖
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import (
    FREE_SHIPPING_EXCLUDED_REGIONS,
    FREE_SHIPPING_THRESHOLD,
    LEGACY_ORDER_STATUS_MAP,
    LEGACY_SETTLEMENT_STATUS_MAP,
)


# ---------- 基础工具 ----------
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
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"""
    return text.replace("/", "-")


def normalize_header_text(value: Any) -> str:
    text = safe_text(value)
    text = text.replace("\n", "").replace("\r", "").replace("\t", "")
    text = text.replace(" ", "").replace("　", "")
    text = text.replace("（", "(").replace("）", ")")
    return text


def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        if "A" <= ch <= "Z":
            n = n * 26 + (ord(ch) - 64)
    return n


def excel_col_name(index: int) -> str:
    result = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def pick_value(row: Dict[str, Any], *aliases: str) -> str:
    lowered = {safe_text(k).lower(): safe_text(v) for k, v in row.items()}
    for alias in aliases:
        direct = safe_text(row.get(alias))
        if direct:
            return direct
        via_lower = lowered.get(alias.lower(), "")
        if via_lower:
            return via_lower
    return ""


# ---------- 运费计算 ----------
def is_free_shipping_excluded_region(address: Any) -> bool:
    address_text = safe_text(address)
    if not address_text:
        return False
    return any(keyword in address_text for keyword in FREE_SHIPPING_EXCLUDED_REGIONS)


def calculate_receivable_shipping_fee(
    book_amount: Any,
    recipient_address: Any,
    default_shipping_fee: Any = 6.0,
) -> float:
    from .config import DEFAULT_SHIPPING_FEE
    book_amount_value = to_float(book_amount, 0.0)
    shipping_fee = to_float(default_shipping_fee, DEFAULT_SHIPPING_FEE)
    if book_amount_value >= FREE_SHIPPING_THRESHOLD and not is_free_shipping_excluded_region(recipient_address):
        return 0.0
    return shipping_fee


# ---------- 状态规范化 ----------
def _normalize_with_map(value: Any, default: str, mapping: Dict[str, str]) -> str:
    text = safe_text(value)
    if not text:
        return default
    return mapping.get(text, text)


def normalize_order_status(value: Any, default: str = "审核") -> str:
    return _normalize_with_map(value, default, LEGACY_ORDER_STATUS_MAP)


def normalize_settlement_status(value: Any, default: str = "未结算") -> str:
    return _normalize_with_map(value, default, LEGACY_SETTLEMENT_STATUS_MAP)


def can_transition_order_status(current_status: Any, next_status: Any) -> bool:
    from .config import ORDER_STATUS_FLOW
    current = normalize_order_status(current_status)
    target = normalize_order_status(next_status)
    if current == target:
        return True
    if current == "配货" and target == "审核":
        return True
    if current == "发货" and target in {"配货", "审核"}:
        return True
    try:
        current_index = ORDER_STATUS_FLOW.index(current)
        target_index = ORDER_STATUS_FLOW.index(target)
    except ValueError:
        return False
    return target_index == current_index + 1


def get_next_order_status(current_status: Any) -> str:
    from .config import ORDER_STATUS_FLOW
    current = normalize_order_status(current_status)
    try:
        current_index = ORDER_STATUS_FLOW.index(current)
    except ValueError:
        return ORDER_STATUS_FLOW[0]
    if current_index >= len(ORDER_STATUS_FLOW) - 1:
        return current
    return ORDER_STATUS_FLOW[current_index + 1]


def get_allowed_order_status_options(current_status: Any) -> List[str]:
    from .config import ORDER_STATUS_FLOW
    current = normalize_order_status(current_status)
    if current not in ORDER_STATUS_FLOW:
        return [ORDER_STATUS_FLOW[0]]
    next_status = get_next_order_status(current)
    if next_status == current:
        return [current]
    return [current, next_status]


def get_status_transition_text(current_status: Any, target_status: Any) -> str:
    current = normalize_order_status(current_status)
    target = normalize_order_status(target_status)
    if current == "审核" and target == "配货":
        return "审核完成，已进入配货环节"
    if current == "配货" and target == "审核":
        return "订单已打回审核环节"
    if current == "配货" and target == "发货":
        return "配货完成，已进入发货环节"
    if current == "发货" and target == "配货":
        return "订单已打回配货环节"
    if current == "发货" and target == "审核":
        return "订单已打回审核环节"
    if current == "发货" and target == "已完成":
        return "确认发货完成，订单已从发货页面移除"
    return f"状态已从{current}更新为{target}"


def get_audit_required_field_errors(current_row: Any, data: Dict[str, Any]) -> List[str]:
    procurement_order_no = safe_text(data.get("procurement_order_no", current_row["procurement_order_no"]))
    procurement_cost_raw = data.get("procurement_cost", current_row["procurement_cost"])
    procurement_cost_text = safe_text(procurement_cost_raw)
    procurement_cost = to_float(procurement_cost_raw, 0.0)
    missing: List[str] = []
    if not procurement_order_no:
        missing.append("采购单号")
    if not procurement_cost_text or procurement_cost <= 0:
        missing.append("采购成本")
    return missing


def get_delivery_required_field_errors(current_row: Any, data: Dict[str, Any]) -> List[str]:
    procurement_missing = get_audit_required_field_errors(current_row, data)
    courier_company = safe_text(data.get("courier_company", current_row["courier_company"]))
    tracking_no = safe_text(data.get("tracking_no", current_row["tracking_no"]))
    missing = procurement_missing[:]
    if not courier_company:
        missing.append("快递公司")
    if not tracking_no:
        missing.append("物流单号")
    return missing
