# -*- coding: utf-8 -*-
"""
全局配置 — 路径、常量、平台定义
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # 包向上一级：core/ -> ERP/
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "ERP.db"
DEFAULT_SAMPLE_FILE = BASE_DIR / "表格.xlsx"
APP_RUNTIME_LOG_PATH = BASE_DIR / "software_runtime.log"
APP_TITLE = "ERP订单管理系统"

# ---------- 订单网格列定义 ----------
ORDER_GRID_COLUMNS: List[Tuple[str, str, int]] = [
    ("created_at", "导入时间", 100),
    ("order_no", "订单号", 180),
    ("platform_source", "平台", 80),
    ("shop_name", "店铺", 100),
    ("sku", "SKU编码(自定义)", 140),
    ("product_name", "商品名称", 280),
    ("quantity", "商品数量", 80),
    ("list_price", "定价", 80),
    ("discount", "折扣", 80),
    ("book_amount", "应收书款", 90),
    ("shipping_fee", "应收运费", 90),
    ("receivable_amount", "应收金额", 90),
    ("remark", "备注", 120),
    ("courier_company", "快递公司", 100),
    ("tracking_no", "单号", 130),
    ("recipient_name", "收货人", 90),
    ("recipient_address", "地址", 260),
    ("recipient_phone", "收件人手机", 120),
    ("settlement_status", "结算状态", 100),
    ("invoice_status", "发票状态", 100),
    ("procurement_date", "采购日期", 100),
    ("procurement_order_no", "采购订单号", 130),
    ("procurement_cost", "采购成本", 90),
    ("procurement_remark", "采购备注", 120),
    ("profit", "利润", 90),
]
ORDER_EXPORT_COLUMN_KEYS = [key for key, _title, _width in ORDER_GRID_COLUMNS]

# ---------- 订单状态流程 ----------
ORDER_STATUS_FLOW = ["审核", "配货", "发货", "已完成"]
ORDER_STATUS_FILTER_OPTIONS = ["全部", *ORDER_STATUS_FLOW]
SETTLEMENT_STATUS_FILTER_OPTIONS = ["全部", "未结算", "已结算"]
INVOICE_STATUS_FILTER_OPTIONS = ["全部", "未开票", "已开票", "未开", "已开", "作废"]
ORDER_STATUS_EDIT_OPTIONS = ORDER_STATUS_FLOW[:]
SETTLEMENT_STATUS_EDIT_OPTIONS = ["未结算", "已结算"]
INVOICE_STATUS_EDIT_OPTIONS = ["未开票", "已开票", "未开", "已开", "作废"]

COURIER_COMPANY_OPTIONS = [
    "申通快递", "圆通快递", "中通快递", "韵达快递",
    "顺丰快递", "极兔快递", "中国邮政", "京东快递", "德邦快递",
]

# ---------- 平台定义 ----------
PLATFORM_SOURCES = ["知护", "淘宝", "天猫", "京东", "拼多多", "抖音", "快手", "闲鱼", "其他"]

# ---------- 智能导入表头映射 ----------
SMART_ORDER_REQUIRED_HEADERS = [
    "订单号", "订单下单时间", "收件人姓名", "收件人地址",
    "收件人手机", "商品名称", "SKU编码(自定义)", "商品数量",
]

SMART_ORDER_HEADER_ALIASES: Dict[str, List[str]] = {
    "订单号": ["订单号"],
    "订单下单时间": ["订单下单时间", "下单时间", "下单日期", "订单时间"],
    "收件人姓名": ["收件人姓名", "收货人姓名", "收件人", "收货人"],
    "收件人地址": [
        "收件人地址", "收货地址", "收件地址", "详细地址", "地址",
        "收件人详细地址", "收货详细地址", "收货地址(省市区)",
        "收货地址（省市区）", "省市区地址", "收件地址详情",
    ],
    "收件人手机": [
        "收件人手机", "收货人手机", "收件人电话",
        "收货人电话", "手机号", "手机号码", "联系电话", "手机",
    ],
    "商品名称": ["商品名称", "商品", "宝贝名称", "商品标题", "书名", "商品名"],
    "SKU编码(自定义)": [
        "SKU编码(自定义)", "SKU编码（自定义）", "SKU编码",
        "商家编码", "商品编码", "SKU", "书号",
    ],
    "商品数量": ["商品数量", "数量", "购买数量"],
}

LEGACY_ORDER_STATUS_MAP = {"待处理": "审核", "已发货": "已完成"}
LEGACY_SETTLEMENT_STATUS_MAP = {"未结账": "未结算", "已结账": "已结算"}

LATEST_ORDER_FILENAME_KEYWORDS = ("百华图书", "百华")

SETTINGS_CLEARABLE_ITEMS = [
    ("orders", "订单数据"),
    ("books", "图书资料"),
    ("supplier_rules", "供应商规则"),
    ("operation_logs", "操作日志"),
    ("courier_companies", "快递公司记录"),
]

SETTINGS_KEYS = type("SettingsKeys", (), {
    "WECHAT_ROOT": "import.wechat_root",
    "TAOBAO_ACCOUNT": "procurement.taobao_account",
    "TAOBAO_PASSWORD": "procurement.taobao_password",
})()

# 免运费阈值
FREE_SHIPPING_THRESHOLD = 59.0
DEFAULT_SHIPPING_FEE = 6.0
FREE_SHIPPING_EXCLUDED_REGIONS = ["新疆", "西藏", "新疆维吾尔自治区", "西藏自治区"]

# Excel命名空间
EXCEL_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
