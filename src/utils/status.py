# -*- coding: utf-8 -*-
"""
订单状态处理工具
Inspired by Claude Code architecture - focused domain utils
"""
from typing import List
from src.utils.helpers import safe_text
from src import constants


def _normalize_with_map(value: any, default: str, mapping: dict[str, str]) -> str:
    text = safe_text(value)
    if not text:
        return default
    return mapping.get(text, text)


def normalize_order_status(value: any, default: str = "审核") -> str:
    return _normalize_with_map(value, default, constants.LEGACY_ORDER_STATUS_MAP)


def normalize_settlement_status(value: any, default: str = "未结算") -> str:
    return _normalize_with_map(value, default, constants.LEGACY_SETTLEMENT_STATUS_MAP)


def can_transition_order_status(current_status: any, next_status: any) -> bool:
    current = normalize_order_status(current_status)
    target = normalize_order_status(next_status)
    if current == target:
        return True
    if current == "配货" and target == "审核":
        return True
    if current == "发货" and target in {"配货", "审核"}:
        return True
    try:
        current_index = constants.ORDER_STATUS_FLOW.index(current)
        target_index = constants.ORDER_STATUS_FLOW.index(target)
    except ValueError:
        return False
    return target_index == current_index + 1


def get_next_order_status(current_status: any) -> str:
    current = normalize_order_status(current_status)
    try:
        current_index = constants.ORDER_STATUS_FLOW.index(current)
    except ValueError:
        return constants.ORDER_STATUS_FLOW[0]
    if current_index >= len(constants.ORDER_STATUS_FLOW) - 1:
        return current
    return constants.ORDER_STATUS_FLOW[current_index + 1]


def get_allowed_order_status_options(current_status: any) -> List[str]:
    current = normalize_order_status(current_status)
    if current not in constants.ORDER_STATUS_FLOW:
        return [constants.ORDER_STATUS_FLOW[0]]
    next_status = get_next_order_status(current)
    if next_status == current:
        return [current]
    return [current, next_status]


def get_status_transition_text(current_status: any, target_status: any) -> str:
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


def get_audit_required_field_errors(current_row, data: dict) -> List[str]:
    from src.utils.helpers import to_float

    procurement_order_no = safe_text(data.get("procurement_order_no", current_row["procurement_order_no"]))
    procurement_cost_raw = data.get("procurement_cost", current_row["procurement_cost"])
    procurement_cost_text = safe_text(procurement_cost_raw)
    procurement_cost = to_float(procurement_cost_raw, 0.0)

    missing_fields: List[str] = []
    if not procurement_order_no:
        missing_fields.append("采购单号")
    if not procurement_cost_text or procurement_cost <= 0:
        missing_fields.append("采购成本")
    return missing_fields


def get_delivery_required_field_errors(current_row, data: dict) -> List[str]:
    from src.utils.helpers import safe_text

    procurement_missing = get_audit_required_field_errors(current_row, data)
    courier_company = safe_text(data.get("courier_company", current_row["courier_company"]))
    tracking_no = safe_text(data.get("tracking_no", current_row["tracking_no"]))

    missing_fields = procurement_missing[:]
    if not courier_company:
        missing_fields.append("快递公司")
    if not tracking_no:
        missing_fields.append("物流单号")
    return missing_fields
