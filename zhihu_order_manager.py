# -*- coding: utf-8 -*-
"""
知护图书订单管理系统（Python MVP）

功能说明：
1. SQLite 本地数据库保存订单、图书资料、供应商规则、操作日志
2. 支持导入 CSV / XLSX 订单、图书资料、供应商规则
3. 提供桌面 GUI（Tkinter）用于查看总订单、录入采购和物流信息、查看利润统计
4. 提供命令行烟雾测试，便于无界面环境验证程序可用性

运行：
    python zhihu_order_manager.py
验证：
    python zhihu_order_manager.py --smoke-test --seed-demo 表格.xlsx
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import re
import sqlite3
import subprocess
import sys
import threading
import traceback
import urllib.parse
import webbrowser
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

import procurement_address_helpers
import ui_helpers

APP_TITLE = "知护图书订单管理系统"


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "zhihu_order_manager.db"
DEFAULT_SAMPLE_FILE = BASE_DIR / "表格.xlsx"
APP_RUNTIME_LOG_PATH = BASE_DIR / "software_runtime.log"
EMBEDDED_BROWSER_BOOTSTRAP_CODE = (
    "import sys; import webview; "
    "title = sys.argv[1]; url = sys.argv[2]; "
    "webview.create_window(title, url=url, width=1360, height=900, resizable=True); "
    "webview.start(debug=False)"
)

EXCEL_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

ORDER_GRID_COLUMNS = [
    ("created_at", "导入时间", 100),
    ("order_no", "订单号", 180),
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
ORDER_TREE_COLUMNS = [("checked", "勾选", 50), *ORDER_GRID_COLUMNS]

ORDER_STATUS_FLOW = ["审核", "配货", "发货", "已完成"]
ORDER_STATUS_FILTER_OPTIONS = ["全部", *ORDER_STATUS_FLOW]
SETTLEMENT_STATUS_FILTER_OPTIONS = ["全部", "未结算", "已结算"]
INVOICE_STATUS_FILTER_OPTIONS = ["全部", "未开票", "已开票", "未开", "已开", "作废"]
ORDER_STATUS_EDIT_OPTIONS = ORDER_STATUS_FLOW[:]
SETTLEMENT_STATUS_EDIT_OPTIONS = ["未结算", "已结算"]
INVOICE_STATUS_EDIT_OPTIONS = ["未开票", "已开票", "未开", "已开", "作废"]
COURIER_COMPANY_OPTIONS = ["申通快递", "圆通快递", "中通快递", "韵达快递", "顺丰快递", "极兔快递", "中国邮政", "京东快递", "德邦快递"]
STATUS_TAB_BATCH_BUTTON_TEXT = {
    "审核": "批量审核订单",
    "配货": "批量确认配货并进入发货",
    "发货": "一键勾选全部并批量确认发货",
}
SETTINGS_CLEARABLE_ITEMS = [
    ("orders", "订单数据"),
    ("books", "图书资料"),
    ("supplier_rules", "供应商规则"),
    ("operation_logs", "操作日志"),
    ("courier_companies", "快递公司记录"),
]
WECHAT_ROOT_SETTING_KEY = "import.wechat_root"
TAOBAO_ACCOUNT_SETTING_KEY = "procurement.taobao_account"
TAOBAO_PASSWORD_SETTING_KEY = "procurement.taobao_password"
LATEST_ORDER_FILENAME_KEYWORDS = ("百华图书", "百华")
SMART_ORDER_REQUIRED_HEADERS = [
    "订单号",
    "订单下单时间",
    "收件人姓名",
    "收件人地址",
    "收件人手机",
    "商品名称",
    "SKU编码(自定义)",
    "商品数量",
]
SMART_ORDER_HEADER_ALIASES = {
    "订单号": ["订单号"],
    "订单下单时间": ["订单下单时间", "下单时间", "下单日期", "订单时间"],
    "收件人姓名": ["收件人姓名", "收货人姓名", "收件人", "收货人"],
    "收件人地址": [
        "收件人地址",
        "收货地址",
        "收件地址",
        "详细地址",
        "地址",
        "收件人详细地址",
        "收货详细地址",
        "收货地址(省市区)",
        "收货地址（省市区）",
        "省市区地址",
        "收件地址详情",
    ],
    "收件人手机": ["收件人手机", "收货人手机", "收件人电话", "收货人电话", "手机号", "手机号码", "联系电话", "手机"],
    "商品名称": ["商品名称", "商品", "宝贝名称", "商品标题", "书名", "商品名"],
    "SKU编码(自定义)": ["SKU编码(自定义)", "SKU编码（自定义）", "SKU编码", "商家编码", "商品编码", "SKU", "书号"],
    "商品数量": ["商品数量", "数量", "购买数量"],
}
LEGACY_ORDER_STATUS_MAP = {
    "待处理": "审核",
    "已发货": "已完成",
}
LEGACY_SETTLEMENT_STATUS_MAP = {
    "未结账": "未结算",
    "已结账": "已结算",
}


# =========================
# 通用工具函数
# =========================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def append_runtime_log(message: str, exc_info: Any = None) -> None:
    lines = [f"[{now_str()}] {safe_text(message)}"]
    if exc_info:
        lines.append("".join(traceback.format_exception(*exc_info)).rstrip())
    try:
        with open(APP_RUNTIME_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines) + "\n\n")
    except Exception:
        pass


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
    current = normalize_order_status(current_status)
    try:
        current_index = ORDER_STATUS_FLOW.index(current)
    except ValueError:
        return ORDER_STATUS_FLOW[0]
    if current_index >= len(ORDER_STATUS_FLOW) - 1:
        return current
    return ORDER_STATUS_FLOW[current_index + 1]


def get_allowed_order_status_options(current_status: Any) -> List[str]:
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


def get_audit_required_field_errors(current_row: sqlite3.Row, data: Dict[str, Any]) -> List[str]:
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


def get_delivery_required_field_errors(current_row: sqlite3.Row, data: Dict[str, Any]) -> List[str]:
    procurement_missing = get_audit_required_field_errors(current_row, data)
    courier_company = safe_text(data.get("courier_company", current_row["courier_company"]))
    tracking_no = safe_text(data.get("tracking_no", current_row["tracking_no"]))

    missing_fields = procurement_missing[:]
    if not courier_company:
        missing_fields.append("快递公司")
    if not tracking_no:
        missing_fields.append("物流单号")
    return missing_fields


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

def is_free_shipping_excluded_region(address: Any) -> bool:
    address_text = safe_text(address)
    if not address_text:
        return False
    excluded_keywords = ["新疆", "西藏", "新疆维吾尔自治区", "西藏自治区"]
    return any(keyword in address_text for keyword in excluded_keywords)


def calculate_receivable_shipping_fee(book_amount: Any, recipient_address: Any, default_shipping_fee: Any = 6.0) -> float:
    book_amount_value = to_float(book_amount, 0.0)
    shipping_fee = to_float(default_shipping_fee, 6.0)
    if book_amount_value >= 59.0 and not is_free_shipping_excluded_region(recipient_address):
        return 0.0
    return shipping_fee


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


def get_order_header_alias_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for canonical, aliases in SMART_ORDER_HEADER_ALIASES.items():
        for alias in aliases:
            normalized = normalize_header_text(alias)
            if normalized:
                mapping[normalized] = canonical
        mapping[normalize_header_text(canonical)] = canonical
    return mapping


def get_month_folder_names(target_date: Optional[datetime] = None) -> List[str]:
    target = target_date or datetime.now()
    return [
        f"{target.year}年{target.month}月",
        f"{target.year}-{target.month:02d}",
        f"{target.year}-{target.month}",
    ]


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


def find_wechat_search_dirs(wechat_root: str) -> List[Path]:
    search_root = Path(wechat_root).expanduser()
    if not search_root.is_dir():
        return []

    month_names = set(get_month_folder_names())
    candidates: Dict[str, Path] = {}

    def add_candidate(path: Path) -> None:
        if not path.is_dir():
            return
        candidates[get_path_key(path)] = path

    if search_root.name in month_names:
        add_candidate(search_root)

    try:
        if any(search_root.glob("*.xlsx")):
            add_candidate(search_root)
    except OSError:
        return sorted(candidates.values(), key=get_path_mtime, reverse=True)

    for name in month_names:
        add_candidate(search_root / name)
        add_candidate(search_root / "msg" / "file" / name)

    try:
        for child in search_root.iterdir():
            if not child.is_dir():
                continue
            for name in month_names:
                add_candidate(child / name)
                add_candidate(child / "msg" / "file" / name)
    except OSError:
        pass

    return sorted(candidates.values(), key=get_path_mtime, reverse=True)


def resolve_wechat_search_dir(wechat_root: str) -> Optional[Path]:
    candidates = find_wechat_search_dirs(wechat_root)
    return candidates[0] if candidates else None


def auto_detect_wechat_dirs() -> List[Path]:
    common_roots: List[Path] = []
    env_root = os.environ.get("XWECHAT_FILES")
    if env_root:
        common_roots.append(Path(env_root))

    for root in [
        Path("D:/xwechat_files"),
        Path("E:/xwechat_files"),
        Path("C:/xwechat_files"),
        Path.home() / "Documents" / "WeChat Files",
        Path.home() / "WeChat Files",
    ]:
        common_roots.append(root)

    candidates: Dict[str, Path] = {}
    checked: set[str] = set()
    for root in common_roots:
        normalized_root = get_path_key(root.expanduser())
        if normalized_root in checked:
            continue
        checked.add(normalized_root)
        if not root.is_dir():
            continue
        for detected in find_wechat_search_dirs(str(root)):
            candidates[get_path_key(detected)] = detected

    return sorted(candidates.values(), key=get_path_mtime, reverse=True)


def is_today_file(file_path: Path) -> bool:
    try:
        return datetime.fromtimestamp(file_path.stat().st_ctime).date() == datetime.now().date()
    except OSError:
        return False


def is_valid_order_xlsx(file_path: Path) -> bool:
    try:
        analysis = find_best_order_sheet(read_xlsx_raw_sheets(file_path))
    except Exception:
        return False
    return not analysis["missing_headers"]


def find_latest_order_file(wechat_root: str, filename_keywords: Iterable[str] = LATEST_ORDER_FILENAME_KEYWORDS) -> Optional[Path]:
    search_dir = resolve_wechat_search_dir(wechat_root)
    if search_dir is None:
        return None

    normalized_keywords = [safe_text(item) for item in filename_keywords if safe_text(item)]
    today_files: List[Path] = []
    for file_path in search_dir.glob("*.xlsx"):
        if file_path.name.startswith("~$"):
            continue
        if not is_today_file(file_path):
            continue
        today_files.append(file_path)

    if not today_files:
        return None

    keyword_candidates = [
        file_path
        for file_path in today_files
        if any(keyword in file_path.name for keyword in normalized_keywords) and is_valid_order_xlsx(file_path)
    ]
    if keyword_candidates:
        return max(keyword_candidates, key=lambda item: item.stat().st_ctime)

    valid_candidates = [file_path for file_path in today_files if is_valid_order_xlsx(file_path)]
    if not valid_candidates:
        return None

    return max(valid_candidates, key=lambda item: item.stat().st_ctime)


def get_sheet_preview_from_raw_rows(raw_rows: List[Dict[str, str]], max_rows: int = 5, max_cols: int = 12) -> str:
    preview_lines: List[str] = []
    for row_index, raw_row in enumerate(raw_rows[:max_rows], start=1):
        ordered_cols = sorted(raw_row.keys(), key=col_to_num)
        row_values = [safe_text(raw_row.get(col)) for col in ordered_cols[:max_cols] if safe_text(raw_row.get(col))]
        if row_values:
            preview_lines.append(f"第{row_index}行: {' | '.join(row_values)}")
    return " ; ".join(preview_lines) if preview_lines else "无可预览内容"


def find_order_header_row(raw_rows: List[Dict[str, str]], max_scan_rows: int = 10) -> tuple[int, set[str]]:
    alias_mapping = get_order_header_alias_mapping()
    best_row_index = 0
    best_headers: set[str] = set()
    best_score = -1

    for row_index, raw_row in enumerate(raw_rows[:max_scan_rows]):
        normalized_headers = {
            normalize_header_text(raw_row.get(col))
            for col in raw_row
            if normalize_header_text(raw_row.get(col))
        }
        matched_headers = {alias_mapping[item] for item in normalized_headers if item in alias_mapping}
        score = len(matched_headers)
        if score > best_score:
            best_score = score
            best_row_index = row_index
            best_headers = matched_headers

    return best_row_index, best_headers


def analyze_order_sheet(sheet_name: str, raw_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    if not raw_rows:
        return {
            "sheet_name": sheet_name,
            "header_row_index": 0,
            "raw_headers": [],
            "matched_headers": [],
            "missing_headers": SMART_ORDER_REQUIRED_HEADERS[:],
            "score": 0,
            "preview": "无可预览内容",
            "raw_rows": raw_rows,
        }

    header_row_index, matched_headers = find_order_header_row(raw_rows)
    header_row = raw_rows[header_row_index]
    ordered_cols = sorted(header_row.keys(), key=col_to_num)
    raw_headers = [safe_text(header_row.get(col)) for col in ordered_cols if safe_text(header_row.get(col))]
    missing_headers = [header for header in SMART_ORDER_REQUIRED_HEADERS if header not in matched_headers]
    preferred_sheet = sheet_name in {"知护订单", "知护总表格"}
    return {
        "sheet_name": sheet_name,
        "header_row_index": header_row_index,
        "raw_headers": raw_headers,
        "matched_headers": sorted(matched_headers),
        "missing_headers": missing_headers,
        "score": len(matched_headers),
        "preferred_sheet": preferred_sheet,
        "preview": get_sheet_preview_from_raw_rows(raw_rows),
        "raw_rows": raw_rows,
    }


def find_best_order_sheet(raw_sheets: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    analyses = [analyze_order_sheet(sheet_name, raw_rows) for sheet_name, raw_rows in raw_sheets.items()]
    if not analyses:
        raise RuntimeError("Excel 文件中未找到可读取的工作表")
    return max(
        analyses,
        key=lambda item: (item["score"], 1 if item.get("preferred_sheet") else 0, -len(item["missing_headers"]), len(item["raw_rows"])),
    )


def build_rows_from_headers_by_col(
    raw_rows: List[Dict[str, str]],
    headers_by_col: Dict[str, str],
    start_index: int,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for raw_row in raw_rows[start_index:]:
        item = {header: safe_text(raw_row.get(col)) for col, header in headers_by_col.items()}
        if any(safe_text(value) for value in item.values()):
            rows.append(item)
    return rows


def get_sheet_rows(sheets: Dict[str, List[Dict[str, str]]], preferred_sheet_name: str) -> List[Dict[str, str]]:
    if preferred_sheet_name in sheets:
        return sheets[preferred_sheet_name]
    return next(iter(sheets.values()), [])


def build_rows_from_order_analysis(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    alias_mapping = get_order_header_alias_mapping()
    raw_rows = analysis["raw_rows"]
    if not raw_rows:
        return []

    header_row = raw_rows[analysis["header_row_index"]]
    ordered_cols = sorted(header_row.keys(), key=col_to_num)
    headers_by_col: Dict[str, str] = {}
    for col in ordered_cols:
        header_text = safe_text(header_row.get(col))
        if not header_text:
            continue
        canonical = alias_mapping.get(normalize_header_text(header_text), header_text)
        if canonical not in headers_by_col.values():
            headers_by_col[col] = canonical
    return build_rows_from_headers_by_col(raw_rows, headers_by_col, analysis["header_row_index"] + 1)


# =========================
# 文件读取：CSV / XLSX（无第三方依赖）
# =========================
def read_csv_rows(file_path: Path) -> List[Dict[str, str]]:
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return [{safe_text(k): safe_text(v) for k, v in row.items()} for row in reader]
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"CSV 读取失败：{last_error}")


def _cell_value(cell: ET.Element, shared: List[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        is_el = cell.find("a:is", EXCEL_NS)
        if is_el is None:
            return ""
        return "".join(t.text or "" for t in is_el.findall(".//a:t", EXCEL_NS)).strip()

    value_el = cell.find("a:v", EXCEL_NS)
    value = "" if value_el is None or value_el.text is None else value_el.text
    if cell_type == "s" and value:
        idx = int(value)
        return shared[idx] if idx < len(shared) else value
    return safe_text(value)


def read_xlsx_raw_sheets(file_path: Path) -> Dict[str, List[Dict[str, str]]]:
    result: Dict[str, List[Dict[str, str]]] = {}
    with zipfile.ZipFile(file_path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib.get("Id"): rel.attrib.get("Target", "") for rel in rels}

        shared: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            shared_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in shared_xml.findall("a:si", EXCEL_NS):
                shared.append("".join(t.text or "" for t in si.findall(".//a:t", EXCEL_NS)))

        sheets = workbook.find("a:sheets", EXCEL_NS)
        if sheets is None:
            return result

        for sheet in sheets:
            name = sheet.attrib.get("name", "Sheet1")
            rid = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = rel_map.get(rid, "")
            normalized_target = target.replace("\\", "/")
            if normalized_target.startswith("/"):
                xml_path = normalized_target.lstrip("/")
            elif normalized_target.startswith("xl/"):
                xml_path = normalized_target
            else:
                xml_path = "xl/" + normalized_target.lstrip("/")
            root = ET.fromstring(zf.read(xml_path))

            raw_rows: List[Dict[str, str]] = []
            for row in root.findall(".//a:sheetData/a:row", EXCEL_NS):
                values: Dict[str, str] = {}
                for cell in row.findall("a:c", EXCEL_NS):
                    ref = cell.attrib.get("r", "")
                    col = "".join(ch for ch in ref if ch.isalpha())
                    values[col] = _cell_value(cell, shared)
                if any(safe_text(v) for v in values.values()):
                    raw_rows.append(values)

            result[name] = raw_rows
    return result


def read_xlsx_sheets(file_path: Path) -> Dict[str, List[Dict[str, str]]]:
    result: Dict[str, List[Dict[str, str]]] = {}
    for name, raw_rows in read_xlsx_raw_sheets(file_path).items():
        if not raw_rows:
            result[name] = []
            continue

        header_row = raw_rows[0]
        ordered_cols = sorted(header_row.keys(), key=col_to_num)
        headers = {col: safe_text(header_row.get(col)) for col in ordered_cols if safe_text(header_row.get(col))}
        result[name] = build_rows_from_headers_by_col(raw_rows, headers, 1)
    return result


def read_order_rows_from_file(file_path: Path) -> tuple[List[Dict[str, str]], List[str]]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return read_csv_rows(file_path), [file_path.stem]
    if suffix in {".xlsx", ".xlsm"}:
        analysis = find_best_order_sheet(read_xlsx_raw_sheets(file_path))
        if analysis["missing_headers"]:
            detected_text = "、".join(analysis["raw_headers"]) if analysis["raw_headers"] else "未识别到表头"
            raise RuntimeError(
                f"订单表缺少字段：{'、'.join(analysis['missing_headers'])}\n"
                f"识别工作表：{analysis['sheet_name']}，表头第 {analysis['header_row_index'] + 1} 行：{detected_text}"
            )
        return build_rows_from_order_analysis(analysis), [analysis["sheet_name"]]
    raise RuntimeError(f"暂不支持的文件类型：{file_path.suffix}")


def read_table_file(file_path: Path) -> Dict[str, List[Dict[str, str]]]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return {file_path.stem: read_csv_rows(file_path)}
    if suffix in {".xlsx", ".xlsm"}:
        return read_xlsx_sheets(file_path)
    raise RuntimeError(f"暂不支持的文件类型：{file_path.suffix}")


def excel_col_name(index: int) -> str:
    result = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_xlsx_rows(file_path: Path, sheet_name: str, headers: List[str], rows: List[List[Any]]) -> None:
    def build_sheet_xml() -> str:
        sheet_rows: List[str] = []
        all_rows = [headers] + rows
        for row_index, row_values in enumerate(all_rows, start=1):
            cells: List[str] = []
            for col_index, value in enumerate(row_values, start=1):
                cell_ref = f"{excel_col_name(col_index)}{row_index}"
                cell_text = xml_escape(safe_text(value))
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{cell_text}</t></is></c>'
                )
            sheet_rows.append(f"<row r=\"{row_index}\">{''.join(cells)}</row>")
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f"<sheetData>{''.join(sheet_rows)}</sheetData>"
            "</worksheet>"
        )

    workbook_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets><sheet name=\"{xml_escape(sheet_name)}\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )
    workbook_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    root_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
        'Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
        'Target="docProps/app.xml"/>'
        '</Relationships>'
    )
    content_types = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '</Types>'
    )
    created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    core_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:creator>GitHub Copilot</dc:creator>'
        '<cp:lastModifiedBy>GitHub Copilot</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        '</cp:coreProperties>'
    )
    app_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>Microsoft Excel</Application>'
        '</Properties>'
    )

    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("docProps/core.xml", core_xml)
        zf.writestr("docProps/app.xml", app_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml())


# =========================
# 数据库层
# =========================
class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                price REAL DEFAULT 0,
                publisher TEXT DEFAULT '',
                discount REAL DEFAULT 1,
                shipping_fee REAL DEFAULT 6,
                supplier TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS supplier_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT NOT NULL UNIQUE,
                discount_note TEXT DEFAULT '',
                shipping_note TEXT DEFAULT '',
                special_area TEXT DEFAULT '',
                extra_rule TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courier_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT NOT NULL UNIQUE,
                order_time TEXT DEFAULT '',
                order_date TEXT DEFAULT '',
                shipping_method TEXT DEFAULT '',
                recipient_name TEXT DEFAULT '',
                recipient_phone TEXT DEFAULT '',
                recipient_address TEXT DEFAULT '',
                product_name TEXT DEFAULT '',
                sku TEXT DEFAULT '',
                quantity INTEGER DEFAULT 1,
                list_price REAL DEFAULT 0,
                discount REAL DEFAULT 1,
                book_amount REAL DEFAULT 0,
                shipping_fee REAL DEFAULT 0,
                receivable_amount REAL DEFAULT 0,
                remark TEXT DEFAULT '',
                courier_company TEXT DEFAULT '',
                tracking_no TEXT DEFAULT '',
                settlement_status TEXT DEFAULT '未结算',
                invoice_status TEXT DEFAULT '未开票',
                procurement_date TEXT DEFAULT '',
                procurement_order_no TEXT DEFAULT '',
                procurement_cost REAL DEFAULT 0,
                procurement_remark TEXT DEFAULT '',
                order_status TEXT DEFAULT '审核',
                order_status_updated_at TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS procurement_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                isbn TEXT DEFAULT '',
                price REAL DEFAULT 0,
                shop TEXT DEFAULT '',
                item_id TEXT NOT NULL UNIQUE,
                use_count INTEGER DEFAULT 0,
                last_used_at TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()
        self.seed_default_users()
        self.seed_default_courier_companies()
        self.ensure_orders_schema()
        self.ensure_procurement_products_schema()
        self.normalize_existing_order_statuses()

    def seed_default_users(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        if count == 0:
            users = [
                ("admin", "admin123", "管理员", now_str()),
                ("order", "123456", "订单员", now_str()),
                ("finance", "123456", "财务", now_str()),
            ]
            cur.executemany(
                "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                users,
            )
            self.conn.commit()

    def seed_default_courier_companies(self) -> None:
        now = now_str()
        self.conn.executemany(
            """
            INSERT INTO courier_companies (name, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                updated_at = excluded.updated_at
            """,
            [(name, now, now) for name in COURIER_COMPANY_OPTIONS],
        )
        self.conn.commit()

    def normalize_existing_order_statuses(self) -> None:
        self.conn.execute(
            "UPDATE orders SET order_status = '审核' WHERE IFNULL(order_status, '') IN ('', '待处理')"
        )
        for legacy, normalized in LEGACY_ORDER_STATUS_MAP.items():
            if legacy == "待处理":
                continue
            self.conn.execute(
                "UPDATE orders SET order_status = ? WHERE order_status = ?",
                (normalized, legacy),
            )
        for legacy, normalized in LEGACY_SETTLEMENT_STATUS_MAP.items():
            self.conn.execute(
                "UPDATE orders SET settlement_status = ? WHERE settlement_status = ?",
                (normalized, legacy),
            )
        self.conn.execute(
            "UPDATE orders SET order_status_updated_at = updated_at WHERE IFNULL(order_status_updated_at, '') = ''"
        )
        self.conn.commit()

    def ensure_orders_schema(self) -> None:
        columns = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "order_status_updated_at" not in columns:
            self.conn.execute("ALTER TABLE orders ADD COLUMN order_status_updated_at TEXT DEFAULT ''")
            self.conn.commit()

    def ensure_procurement_products_schema(self) -> None:
        columns = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(procurement_products)").fetchall()
        }
        if "use_count" not in columns:
            self.conn.execute("ALTER TABLE procurement_products ADD COLUMN use_count INTEGER DEFAULT 0")
        if "last_used_at" not in columns:
            self.conn.execute("ALTER TABLE procurement_products ADD COLUMN last_used_at TEXT DEFAULT ''")
        self.conn.commit()

    def clear_business_data(self, selected_items: List[str], username: str) -> None:
        selected = {item for item in selected_items if item}
        if not selected:
            return

        action_map = {
            "orders": ("DELETE FROM orders", "订单数据"),
            "books": ("DELETE FROM books", "图书资料"),
            "supplier_rules": ("DELETE FROM supplier_rules", "供应商规则"),
            "operation_logs": ("DELETE FROM operation_logs", "操作日志"),
            "courier_companies": ("DELETE FROM courier_companies", "快递公司记录"),
        }

        cleared_labels: List[str] = []
        for key in [item_key for item_key, _label in SETTINGS_CLEARABLE_ITEMS]:
            if key not in selected:
                continue
            sql, label = action_map[key]
            self.conn.execute(sql)
            cleared_labels.append(label)
        self.conn.commit()

        if "courier_companies" in selected:
            self.seed_default_courier_companies()
            cleared_labels.append("默认快递公司重置")

        detail = "、".join(cleared_labels)
        self.log(username, "清空业务数据", f"已清空：{detail}")

    def log(self, username: str, action: str, detail: str = "") -> None:
        self.conn.execute(
            "INSERT INTO operation_logs (username, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (username, action, detail, now_str()),
        )
        self.conn.commit()

    def list_operation_logs(self, limit: Optional[int] = None) -> List[sqlite3.Row]:
        sql = "SELECT username, action, detail, created_at FROM operation_logs ORDER BY id DESC"
        params: List[Any] = []
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return list(self.conn.execute(sql, params))

    def verify_user(self, username: str, password: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        return row["role"] if row else None

    def remember_courier_company(self, name: str) -> None:
        company = safe_text(name)
        if not company:
            return
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO courier_companies (name, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                updated_at = excluded.updated_at
            """,
            (company, now, now),
        )
        self.conn.commit()

    def get_app_setting(self, setting_key: str, default: str = "") -> str:
        row = self.conn.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
        return safe_text(row["setting_value"]) if row else default

    def set_app_setting(self, setting_key: str, setting_value: str) -> None:
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (setting_key, safe_text(setting_value), now),
        )
        self.conn.commit()

    def list_procurement_products(self, keyword: str = "") -> List[sqlite3.Row]:
        sql = "SELECT * FROM procurement_products"
        params: List[Any] = []
        if keyword:
            sql += " WHERE product_name LIKE ? OR isbn LIKE ? OR shop LIKE ? OR item_id LIKE ?"
            like = f"%{keyword}%"
            params.extend([like, like, like, like])
        sql += " ORDER BY use_count DESC, last_used_at DESC, updated_at DESC, id DESC"
        return list(self.conn.execute(sql, params))

    def find_procurement_product_candidates(self, isbn: str = "", product_name: str = "") -> List[sqlite3.Row]:
        isbn_text = safe_text(isbn)
        product_text = safe_text(product_name)
        conditions: List[str] = []
        params: List[Any] = []
        if isbn_text:
            conditions.append("isbn = ?")
            params.append(isbn_text)
        if product_text:
            conditions.append("product_name LIKE ?")
            params.append(f"%{product_text}%")
        if not conditions:
            return []
        rank_sql = "CASE WHEN ? <> '' AND isbn = ? THEN 1 ELSE 0 END AS isbn_exact_rank"
        sql = (
            "SELECT *, "
            + rank_sql
            + " FROM procurement_products WHERE "
            + " OR ".join(conditions)
            + " ORDER BY isbn_exact_rank DESC, use_count DESC, last_used_at DESC, updated_at DESC, id DESC"
        )
        params = [isbn_text, isbn_text, *params]
        return list(self.conn.execute(sql, params))

    def upsert_procurement_product(self, data: Dict[str, Any]) -> None:
        item_id = safe_text(data.get("item_id"))
        if not item_id:
            return
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO procurement_products (product_name, isbn, price, shop, item_id, use_count, last_used_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                product_name = excluded.product_name,
                isbn = excluded.isbn,
                price = excluded.price,
                shop = excluded.shop,
                updated_at = excluded.updated_at
            """,
            (
                safe_text(data.get("product_name")),
                safe_text(data.get("isbn")),
                to_float(data.get("price"), 0.0),
                safe_text(data.get("shop")),
                item_id,
                max(to_int(data.get("use_count"), 0), 0),
                safe_text(data.get("last_used_at")),
                now,
                now,
            ),
        )
        self.conn.commit()

    def mark_procurement_product_used(self, item_id: str) -> None:
        item_value = safe_text(item_id)
        if not item_value:
            return
        now = now_str()
        self.conn.execute(
            """
            UPDATE procurement_products
            SET use_count = IFNULL(use_count, 0) + 1,
                last_used_at = ?,
                updated_at = ?
            WHERE item_id = ?
            """,
            (now, now, item_value),
        )
        self.conn.commit()

    # ---------- 图书资料 ----------
    def upsert_book(self, data: Dict[str, Any], username: str = "system") -> None:
        sku = safe_text(data.get("sku"))
        if not sku:
            return
        name = safe_text(data.get("name")) or sku
        price = to_float(data.get("price"))
        publisher = safe_text(data.get("publisher"))
        discount = normalize_discount(data.get("discount"), 1.0)
        shipping_fee = to_float(data.get("shipping_fee"), 6.0)
        supplier = safe_text(data.get("supplier"))
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO books (sku, name, price, publisher, discount, shipping_fee, supplier, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                price = excluded.price,
                publisher = excluded.publisher,
                discount = excluded.discount,
                shipping_fee = excluded.shipping_fee,
                supplier = excluded.supplier,
                updated_at = excluded.updated_at
            """,
            (sku, name, price, publisher, discount, shipping_fee, supplier, now, now),
        )
        self.conn.commit()

    def list_books(self, keyword: str = "") -> List[sqlite3.Row]:
        sql = "SELECT * FROM books"
        params: List[Any] = []
        if keyword:
            sql += " WHERE sku LIKE ? OR name LIKE ? OR publisher LIKE ?"
            key = f"%{keyword}%"
            params.extend([key, key, key])
        sql += " ORDER BY updated_at DESC, sku ASC"
        return list(self.conn.execute(sql, params))

    def get_book_by_sku(self, sku: str) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM books WHERE sku = ?", (sku,)).fetchone()

    def get_order_by_no(self, order_no: str) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()

    def import_books_from_file(self, file_path: Path, username: str = "system") -> str:
        sheets = read_table_file(file_path)
        rows = get_sheet_rows(sheets, "知护网图书资料库")

        count = 0
        for row in rows:
            sku = pick_value(row, "书号", "SKU", "SKU编码", "商品编码", "书号")
            if not sku:
                continue
            self.upsert_book(
                {
                    "sku": sku,
                    "name": pick_value(row, "书名", "商品名称", "名称"),
                    "price": pick_value(row, "定价", "价格", "售价"),
                    "publisher": pick_value(row, "出版社"),
                    "discount": pick_value(row, "折扣"),
                    "shipping_fee": pick_value(row, "邮费", "运费"),
                    "supplier": pick_value(row, "供应商"),
                },
                username=username,
            )
            count += 1
        self.log(username, "导入图书资料", f"{file_path.name}，共 {count} 条")
        return f"图书资料导入完成：{count} 条"

    # ---------- 供应商规则 ----------
    def import_supplier_rules_from_file(self, file_path: Path, username: str = "system") -> str:
        sheets = read_table_file(file_path)
        rows = get_sheet_rows(sheets, "知护供货 运费")

        count = 0
        for row in rows:
            supplier_name = pick_value(row, "供应商", "供货商")
            if not supplier_name:
                continue
            now = now_str()
            self.conn.execute(
                """
                INSERT INTO supplier_rules (supplier_name, discount_note, shipping_note, special_area, extra_rule, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(supplier_name) DO UPDATE SET
                    discount_note = excluded.discount_note,
                    shipping_note = excluded.shipping_note,
                    special_area = excluded.special_area,
                    extra_rule = excluded.extra_rule,
                    updated_at = excluded.updated_at
                """,
                (
                    supplier_name,
                    pick_value(row, "折扣"),
                    pick_value(row, "邮费", "运费说明"),
                    pick_value(row, "地区", "特殊地区"),
                    pick_value(row, "首重1kg 续重1kg", "规则说明"),
                    now,
                    now,
                ),
            )
            count += 1
        self.conn.commit()
        self.log(username, "导入供应商规则", f"{file_path.name}，共 {count} 条")
        return f"供应商规则导入完成：{count} 条"

    # ---------- 订单 ----------
    def _prepare_order_data(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        order_no = pick_value(row, "订单号", "订单编号")
        if not order_no:
            return None

        order_time = clean_date_text(pick_value(row, "订单下单时间", "下单时间", "订单时间"))
        order_date = clean_date_text(pick_value(row, "日期"))
        if not order_date and order_time:
            order_date = order_time[:10]

        sku = pick_value(row, "SKU编码(自定义)", "SKU编码", "SKU", "商品编码", "书号")
        book = self.get_book_by_sku(sku) if sku else None
        book_price = to_float(book["price"]) if book else 0.0
        book_discount = normalize_discount(book["discount"]) if book else 1.0
        book_shipping_fee = to_float(book["shipping_fee"]) if book else 6.0
        tracking_no = pick_value(row, "单号", "物流单号")
        recipient_address = pick_value(row, "收件人地址", "地址")

        quantity = max(to_int(pick_value(row, "商品数量", "数量"), 1), 1)
        list_price = to_float(pick_value(row, "定价", "价格"), book_price)
        discount = normalize_discount(pick_value(row, "折扣"), book_discount)
        book_amount = to_float(pick_value(row, "应收书款"), round(list_price * discount * quantity, 2))
        shipping_fee = calculate_receivable_shipping_fee(
            book_amount,
            recipient_address,
            pick_value(row, "应收运费", "邮费", "运费") or book_shipping_fee,
        )
        receivable_amount = to_float(pick_value(row, "应收金额"), round(book_amount + shipping_fee, 2))
        procurement_cost = to_float(pick_value(row, "采购成本"), 0.0)

        return {
            "order_no": order_no,
            "order_time": order_time,
            "order_date": order_date,
            "shipping_method": pick_value(row, "发货方式", "配送方式"),
            "recipient_name": pick_value(row, "收件人姓名", "收货人"),
            "recipient_phone": pick_value(row, "收件人手机", "手机"),
            "recipient_address": recipient_address,
            "product_name": pick_value(row, "商品名称", "书名", "商品名"),
            "sku": sku,
            "quantity": quantity,
            "list_price": list_price,
            "discount": discount,
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "remark": pick_value(row, "备注"),
            "courier_company": pick_value(row, "快递公司"),
            "tracking_no": tracking_no,
            "settlement_status": normalize_settlement_status(pick_value(row, "结算状态", "结账状态"), "未结算"),
            "invoice_status": pick_value(row, "发票状态") or "未开票",
            "procurement_date": clean_date_text(pick_value(row, "采购日期")),
            "procurement_order_no": pick_value(row, "采购订单号"),
            "procurement_cost": procurement_cost,
            "procurement_remark": pick_value(row, "采购备注"),
            "order_status": "发货" if tracking_no else "审核",
        }

    def upsert_order(self, data: Dict[str, Any], username: str = "system") -> None:
        now = now_str()
        values = (
            data.get("order_no", ""),
            data.get("order_time", ""),
            data.get("order_date", ""),
            data.get("shipping_method", ""),
            data.get("recipient_name", ""),
            data.get("recipient_phone", ""),
            data.get("recipient_address", ""),
            data.get("product_name", ""),
            data.get("sku", ""),
            data.get("quantity", 1),
            data.get("list_price", 0.0),
            data.get("discount", 1.0),
            data.get("book_amount", 0.0),
            data.get("shipping_fee", 0.0),
            data.get("receivable_amount", 0.0),
            data.get("remark", ""),
            data.get("courier_company", ""),
            data.get("tracking_no", ""),
            normalize_settlement_status(data.get("settlement_status", "未结算"), "未结算"),
            data.get("invoice_status", "未开票"),
            data.get("procurement_date", ""),
            data.get("procurement_order_no", ""),
            data.get("procurement_cost", 0.0),
            data.get("procurement_remark", ""),
            normalize_order_status(data.get("order_status", "审核")),
            now,
            now,
            now,
        )
        placeholders = ", ".join(["?"] * len(values))
        self.conn.execute(
            f"""
            INSERT INTO orders (
                order_no, order_time, order_date, shipping_method, recipient_name, recipient_phone,
                recipient_address, product_name, sku, quantity, list_price, discount, book_amount,
                shipping_fee, receivable_amount, remark, courier_company, tracking_no,
                settlement_status, invoice_status, procurement_date, procurement_order_no,
                procurement_cost, procurement_remark, order_status, order_status_updated_at, created_at, updated_at
            )
            VALUES ({placeholders})
            ON CONFLICT(order_no) DO UPDATE SET
                order_time = excluded.order_time,
                order_date = excluded.order_date,
                shipping_method = excluded.shipping_method,
                recipient_name = excluded.recipient_name,
                recipient_phone = excluded.recipient_phone,
                recipient_address = excluded.recipient_address,
                product_name = excluded.product_name,
                sku = excluded.sku,
                quantity = excluded.quantity,
                list_price = excluded.list_price,
                discount = excluded.discount,
                book_amount = excluded.book_amount,
                shipping_fee = excluded.shipping_fee,
                receivable_amount = excluded.receivable_amount,
                remark = excluded.remark,
                courier_company = excluded.courier_company,
                tracking_no = excluded.tracking_no,
                settlement_status = excluded.settlement_status,
                invoice_status = excluded.invoice_status,
                procurement_date = excluded.procurement_date,
                procurement_order_no = excluded.procurement_order_no,
                procurement_cost = excluded.procurement_cost,
                procurement_remark = excluded.procurement_remark,
                order_status = excluded.order_status,
                order_status_updated_at = excluded.order_status_updated_at,
                updated_at = excluded.updated_at
            """,
            values,
        )
        self.conn.commit()
        self.remember_courier_company(data.get("courier_company", ""))

    def import_orders_from_file(
        self,
        file_path: Path,
        username: str = "system",
        on_duplicate_order: Optional[Callable[[str], bool]] = None,
    ) -> str:
        rows, used_sheet_names = read_order_rows_from_file(file_path)
        imported = 0
        skipped = 0

        for row in rows:
            data = self._prepare_order_data(row)
            if not data:
                continue
            order_no = safe_text(data.get("order_no"))
            if order_no and self.get_order_by_no(order_no):
                should_skip = bool(on_duplicate_order(order_no)) if on_duplicate_order else False
                if should_skip:
                    skipped += 1
                    continue
            self.upsert_order(data, username=username)
            imported += 1

        self.log(username, "导入订单", f"{file_path.name}，工作表 {used_sheet_names}，导入 {imported} 条，跳过 {skipped} 条")
        return f"订单导入完成：{imported} 条，跳过重复 {skipped} 条（工作表：{', '.join(used_sheet_names)}）"

    def import_sample_workbook(self, file_path: Path, username: str = "system") -> List[str]:
        messages = []
        if file_path.exists():
            messages.append(self.import_books_from_file(file_path, username=username))
            messages.append(self.import_supplier_rules_from_file(file_path, username=username))
            messages.append(self.import_orders_from_file(file_path, username=username))
        return messages

    def list_orders(
        self,
        keyword: str = "",
        order_status: str = "",
        settlement_status: str = "",
        invoice_status: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> List[sqlite3.Row]:
        sql = (
            "SELECT *, ROUND(receivable_amount - procurement_cost, 2) AS profit "
            "FROM orders"
        )
        params: List[Any] = []
        conditions: List[str] = []
        if keyword:
            conditions.append("(order_no LIKE ? OR recipient_name LIKE ? OR procurement_order_no LIKE ? OR tracking_no LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like, like])
        if order_status and order_status != "全部":
            conditions.append("order_status = ?")
            params.append(order_status)
        if settlement_status and settlement_status != "全部":
            conditions.append("settlement_status = ?")
            params.append(settlement_status)
        if invoice_status and invoice_status != "全部":
            conditions.append("invoice_status = ?")
            params.append(invoice_status)
        if start_date:
            conditions.append("substr(created_at, 1, 10) >= ?")
            params.append(clean_date_text(start_date))
        if end_date:
            conditions.append("substr(created_at, 1, 10) <= ?")
            params.append(clean_date_text(end_date))
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC, id DESC"
        return list(self.conn.execute(sql, params))

    def get_order(self, order_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT *, ROUND(receivable_amount - procurement_cost, 2) AS profit FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    def update_order_details(self, order_id: int, data: Dict[str, Any], username: str) -> None:
        current_row = self.conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not current_row:
            raise ValueError("订单不存在，无法更新")
        current_status = normalize_order_status(current_row["order_status"])
        next_status = normalize_order_status(data.get("order_status"), current_status)
        if not can_transition_order_status(current_status, next_status):
            raise ValueError(f"订单状态仅允许按 {' -> '.join(ORDER_STATUS_FLOW)} 顺序流转")
        if current_status == "审核" and next_status == "配货":
            missing_fields = get_audit_required_field_errors(current_row, data)
            if missing_fields:
                raise ValueError(f"提交到配货前必须填写：{'、'.join(missing_fields)}")
        if current_status == "配货" and next_status == "发货":
            missing_fields = get_delivery_required_field_errors(current_row, data)
            if missing_fields:
                raise ValueError(f"提交到发货前必须填写：{'、'.join(missing_fields)}")
        status_updated_at = current_row["order_status_updated_at"] if current_status == next_status else now_str()
        self.conn.execute(
            """
            UPDATE orders
               SET recipient_name = ?,
                   recipient_address = ?,
                   remark = ?,
                   courier_company = ?,
                   tracking_no = ?,
                   settlement_status = ?,
                   invoice_status = ?,
                   procurement_date = ?,
                   procurement_order_no = ?,
                   procurement_cost = ?,
                   procurement_remark = ?,
                   order_status = ?,
                 order_status_updated_at = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                safe_text(data.get("recipient_name", current_row["recipient_name"])),
                safe_text(data.get("recipient_address", current_row["recipient_address"])),
                safe_text(data.get("remark", current_row["remark"])),
                safe_text(data.get("courier_company", current_row["courier_company"])),
                safe_text(data.get("tracking_no", current_row["tracking_no"])),
                normalize_settlement_status(data.get("settlement_status", current_row["settlement_status"]), "未结算"),
                safe_text(data.get("invoice_status", current_row["invoice_status"])) or "未开票",
                clean_date_text(data.get("procurement_date", current_row["procurement_date"])),
                safe_text(data.get("procurement_order_no", current_row["procurement_order_no"])),
                to_float(data.get("procurement_cost", current_row["procurement_cost"])),
                safe_text(data.get("procurement_remark", current_row["procurement_remark"])),
                next_status,
                status_updated_at,
                now_str(),
                order_id,
            ),
        )
        self.conn.commit()
        self.remember_courier_company(data.get("courier_company", current_row["courier_company"]))
        self.log(username, "订单状态变更", f"订单号={current_row['order_no']}：{current_status} -> {next_status}")
        self.log(username, "更新订单", f"ID={order_id}")

    def export_orders_to_excel(
        self,
        file_path: Path,
        keyword: str = "",
        order_status: str = "",
        settlement_status: str = "",
        invoice_status: str = "",
        start_date: str = "",
        end_date: str = "",
        selected_columns: Optional[List[str]] = None,
    ) -> int:
        rows = self.list_orders(
            keyword=keyword,
            order_status=order_status,
            settlement_status=settlement_status,
            invoice_status=invoice_status,
            start_date=start_date,
            end_date=end_date,
        )
        return self.export_rows_to_excel(file_path, rows, sheet_name="总订单", selected_columns=selected_columns)

    def export_rows_to_excel(
        self,
        file_path: Path,
        rows: List[sqlite3.Row],
        sheet_name: str = "总订单",
        selected_columns: Optional[List[str]] = None,
    ) -> int:
        column_defs = [
            (key, title)
            for key, title, _width in ORDER_GRID_COLUMNS
            if not selected_columns or key in selected_columns
        ]
        headers = [title for _key, title in column_defs]
        excel_rows: List[List[Any]] = []
        for row in rows:
            import_date = safe_text(row["created_at"])[:10]
            row_values = {
                "created_at": import_date,
                "order_no": safe_text(row["order_no"]),
                "sku": safe_text(row["sku"]),
                "product_name": safe_text(row["product_name"]),
                "quantity": safe_text(row["quantity"]),
                "list_price": f"{row['list_price']:.2f}",
                "discount": f"{row['discount']:.2f}",
                "book_amount": f"{row['book_amount']:.2f}",
                "shipping_fee": f"{row['shipping_fee']:.2f}",
                "receivable_amount": f"{row['receivable_amount']:.2f}",
                "remark": safe_text(row["remark"]),
                "courier_company": safe_text(row["courier_company"]),
                "tracking_no": safe_text(row["tracking_no"]),
                "recipient_name": safe_text(row["recipient_name"]),
                "recipient_address": safe_text(row["recipient_address"]),
                "recipient_phone": safe_text(row["recipient_phone"]),
                "settlement_status": safe_text(row["settlement_status"]),
                "invoice_status": safe_text(row["invoice_status"]),
                "procurement_date": safe_text(row["procurement_date"]),
                "procurement_order_no": safe_text(row["procurement_order_no"]),
                "procurement_cost": f"{row['procurement_cost']:.2f}",
                "procurement_remark": safe_text(row["procurement_remark"]),
                "profit": f"{row['profit']:.2f}",
            }
            excel_rows.append([row_values[key] for key, _title in column_defs])
        write_xlsx_rows(file_path, sheet_name, headers, excel_rows)
        return len(rows)

    def list_courier_companies(self) -> List[str]:
        rows = self.conn.execute("SELECT name FROM courier_companies ORDER BY name ASC").fetchall()
        return [safe_text(row[0]) for row in rows if safe_text(row[0])]

    # ---------- 统计 ----------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        total_orders = self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        total_books = self.conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        pending_orders = self.conn.execute("SELECT COUNT(*) FROM orders WHERE order_status != '已完成'").fetchone()[0]
        money_row = self.conn.execute(
            "SELECT IFNULL(SUM(receivable_amount), 0), IFNULL(SUM(procurement_cost), 0) FROM orders"
        ).fetchone()
        total_receivable = round(money_row[0], 2)
        total_cost = round(money_row[1], 2)
        gross_profit = round(total_receivable - total_cost, 2)
        return {
            "total_orders": total_orders,
            "total_books": total_books,
            "pending_orders": pending_orders,
            "total_receivable": total_receivable,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
        }

    def get_profit_summary_text(self) -> str:
        stats = self.get_dashboard_stats()
        lines = [
            f"总订单数：{stats['total_orders']}",
            f"图书资料数：{stats['total_books']}",
            f"待处理订单：{stats['pending_orders']}",
            f"应收金额合计：{stats['total_receivable']:.2f}",
            f"采购成本合计：{stats['total_cost']:.2f}",
            f"粗算毛利：{stats['gross_profit']:.2f}",
            "",
            "按商品统计（Top 10）：",
        ]
        top_products = self.conn.execute(
            """
            SELECT product_name,
                   COUNT(*) AS order_count,
                   ROUND(SUM(receivable_amount), 2) AS amount,
                   ROUND(SUM(procurement_cost), 2) AS cost,
                   ROUND(SUM(receivable_amount - procurement_cost), 2) AS profit
              FROM orders
          GROUP BY product_name
          ORDER BY profit DESC, order_count DESC
             LIMIT 10
            """
        ).fetchall()
        if top_products:
            for row in top_products:
                lines.append(
                    f"- {row['product_name']} | 单数 {row['order_count']} | 销售 {row['amount']:.2f} | 毛利 {row['profit']:.2f}"
                )
        else:
            lines.append("- 暂无数据")

        lines.append("")
        lines.append("最近操作日志：")
        logs = self.conn.execute(
            "SELECT username, action, detail, created_at FROM operation_logs ORDER BY id DESC LIMIT 10"
        ).fetchall()
        for row in logs:
            lines.append(f"- [{row['created_at']}] {row['username']}：{row['action']}（{row['detail']}）")
        return "\n".join(lines)

    def close(self) -> None:
        self.conn.close()


# =========================
# GUI
# =========================
class OrderManagerGUI:
    def __init__(self, db: DatabaseManager):
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog, ttk

        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.simpledialog = simpledialog
        self.db = db
        self.current_user = ""
        self.current_role = ""
        self.order_cache: Dict[int, sqlite3.Row] = {}
        self.status_tab_contexts: Dict[str, Dict[str, Any]] = {}
        self.settlement_tab_context: Dict[str, Any] = {}
        self.tree_checked_items: Dict[str, set[str]] = {}
        self.export_column_vars: Dict[str, Dict[str, Any]] = {}
        self.order_edit_window: Any = None
        self.main_courier_company_combo: Any = None
        self.main_order_status_combo: Any = None
        self.procurement_product_tree: Any = None

        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1360x860")
        self.root.report_callback_exception = self.handle_tk_exception
        self.wechat_root_var = self.tk.StringVar(value=self.db.get_app_setting(WECHAT_ROOT_SETTING_KEY, ""))
        self.taobao_account_var = self.tk.StringVar(value=self.db.get_app_setting(TAOBAO_ACCOUNT_SETTING_KEY, ""))
        self.taobao_password_var = self.tk.StringVar()
        self.taobao_login_state_status_var = self.tk.StringVar()
        self.taobao_login_state_validity_var = self.tk.StringVar(value="有效性：未检测")
        self.playwright_status_var = self.tk.StringVar(value="Playwright：检测中")
        self._taobao_login_state_task_running = False
        self._taobao_login_check_task_running = False
        self._taobao_browser_session_running = False
        self._refresh_taobao_login_state_status()
        # expose module to page builders (so builders can access module-level constants)
        import sys as _sys
        self.module = _sys.modules[__name__]
        try:
            self.root.state("zoomed")
        except Exception:  # noqa: BLE001
            pass

        if not self.login():
            self.root.destroy()
            return

        self.build_ui()
        self.refresh_all()
        self.root.after(200, self.refresh_playwright_status_async)
        self.root.after(800, self.auto_check_taobao_login_state_validity)

    def get_courier_company_options(self) -> List[str]:
        options: List[str] = []
        for name in COURIER_COMPANY_OPTIONS + self.db.list_courier_companies():
            text = safe_text(name)
            if text and text not in options:
                options.append(text)
        return options

    def refresh_courier_company_options(self) -> None:
        options = self.get_courier_company_options()
        if self.main_courier_company_combo is not None:
            self.main_courier_company_combo.configure(values=options)

    def _set_clipboard_text(self, text: Any, show_message: bool = False) -> bool:
        value = safe_text(text)
        if not value:
            if show_message:
                self.messagebox.showwarning("提示", "没有可复制的内容")
            return False
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()
        if show_message:
            self.messagebox.showinfo("复制成功", value)
        return True

    def copy_text(self, text: Any) -> None:
        self._set_clipboard_text(text, show_message=True)

    def login(self) -> bool:
        for _ in range(3):
            username = self.simpledialog.askstring("登录", "请输入用户名：", initialvalue="admin", parent=self.root)
            if username is None:
                return False
            password = self.simpledialog.askstring("登录", "请输入密码：", show="*", initialvalue="admin123", parent=self.root)
            if password is None:
                return False
            role = self.db.verify_user(username, password)
            if role:
                self.current_user = username
                self.current_role = role
                self.db.log(username, "登录系统", role)
                return True
            self.messagebox.showerror("登录失败", "用户名或密码错误。\n默认账号：admin / admin123")
        return False

    def build_ui(self) -> None:
        top = self.ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=6)
        self.user_label = self.ttk.Label(top, text=f"当前用户：{self.current_user}（{self.current_role}）", font=("Microsoft YaHei", 11, "bold"))
        self.user_label.pack(side="left")
        self.ttk.Label(top, text=f"数据库：{DB_PATH.name}").pack(side="right")

        self.notebook = self.ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # page builders are moved to separate modules (one file per page)
        import importlib.util

        def _load_builder(name: str):
            fallback = getattr(self, f"build_{name}_tab")
            path = BASE_DIR / "pages" / f"{name}.py"
            if not path.exists():
                append_runtime_log(f"页面模块缺失，已回退内置页面：{path}")
                return fallback
            try:
                spec = importlib.util.spec_from_file_location(f"zhihu_pages_{name}", str(path))
                if spec is None or spec.loader is None:
                    append_runtime_log(f"页面模块加载规格为空，已回退内置页面：{path}")
                    return fallback
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[union-attr]
                builder = getattr(module, f"build_{name}_tab", None)
                if builder is None:
                    append_runtime_log(f"页面模块缺少构建函数，已回退内置页面：{path}")
                    return fallback
                return builder
            except Exception:
                append_runtime_log(f"页面模块加载失败，已回退内置页面：{path}", sys.exc_info())
                return fallback

        _build_dashboard_tab = _load_builder("dashboard")
        _build_status_tab = _load_builder("status")
        _build_settlement_tab = _load_builder("settlement")
        _build_orders_tab = _load_builder("orders")
        _build_books_tab = _load_builder("books")
        _build_profit_tab = _load_builder("profit")
        _build_settings_tab = _load_builder("settings")

        _build_dashboard_tab(self)
        _build_status_tab(self, "审核")
        _build_status_tab(self, "配货")
        _build_status_tab(self, "发货")
        _build_settlement_tab(self)
        _build_orders_tab(self)
        _build_books_tab(self)
        _build_profit_tab(self)
        _build_settings_tab(self)

    def _create_notebook_tab(self, title: str) -> Any:
        return ui_helpers.create_notebook_tab(self, title)

    def _build_date_filter_input(self, parent: Any, label: str, target_var: Any) -> None:
        ui_helpers.build_date_filter_input(self, parent, label, target_var)

    def _build_order_filter_bar(
        self,
        parent: Any,
        search_var: Any,
        start_date_var: Any,
        end_date_var: Any,
        query_command: Callable[[], Any],
        refresh_command: Optional[Callable[[], Any]] = None,
        extra_filters: Optional[List[Dict[str, Any]]] = None,
        extra_buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        ui_helpers.build_order_filter_bar(
            self,
            parent,
            search_var,
            start_date_var,
            end_date_var,
            query_command,
            refresh_command=refresh_command,
            extra_filters=extra_filters,
            extra_buttons=extra_buttons,
        )

    def _build_page_summary(self, parent: Any, page_title: str, count_var: Any) -> None:
        ui_helpers.build_page_summary(self, parent, page_title, count_var)

    def _create_bound_order_tree(self, parent: Any, height: int = 12, on_select: Optional[Callable[[Any], None]] = None) -> Any:
        return ui_helpers.create_bound_order_tree(self, parent, height=height, on_select=on_select)

    def _build_export_columns_section(self, parent: Any, scope: str) -> None:
        ui_helpers.build_export_columns_section(self, parent, scope)

    def _add_tree_selection_buttons(
        self,
        parent: Any,
        tree: Any,
        select_all_text: str = "一键全选",
        clear_text: str = "取消全选",
    ) -> None:
        ui_helpers.add_tree_selection_buttons(self, parent, tree, select_all_text=select_all_text, clear_text=clear_text)

    def _get_status_tab_tip_text(self, status: str) -> str:
        return ui_helpers.get_status_tab_tip_text(status)

    def _build_status_action_bar(self, parent: Any, status: str, tree: Any) -> None:
        ui_helpers.build_status_action_bar(self, parent, status, tree)

    def _build_settlement_action_bar(self, parent: Any, tree: Any, batch_settlement_status_var: Any) -> None:
        ui_helpers.build_settlement_action_bar(self, parent, tree, batch_settlement_status_var)

    def _build_orders_action_bar(self, parent: Any, tree: Any) -> None:
        ui_helpers.build_orders_action_bar(self, parent, tree)

    def build_dashboard_tab(self) -> None:
        frame = self.ttk.Frame(self.notebook)
        self.notebook.add(frame, text="首页概览")

        stat_frame = self.ttk.Frame(frame)
        stat_frame.pack(fill="x", pady=10)
        self.dashboard_vars = {
            "total_orders": self.tk.StringVar(value="0"),
            "total_books": self.tk.StringVar(value="0"),
            "pending_orders": self.tk.StringVar(value="0"),
            "gross_profit": self.tk.StringVar(value="0.00"),
            "total_receivable": self.tk.StringVar(value="0.00"),
        }
        labels = [
            ("订单总数", "total_orders"),
            ("图书总数", "total_books"),
            ("待处理订单", "pending_orders"),
            ("粗算毛利", "gross_profit"),
            ("应收金额汇总", "total_receivable"),
        ]
        for idx, (title, key) in enumerate(labels):
            card = self.ttk.LabelFrame(stat_frame, text=title)
            card.grid(row=0, column=idx, padx=8, pady=4, sticky="nsew")
            self.ttk.Label(card, textvariable=self.dashboard_vars[key], font=("Microsoft YaHei", 18, "bold")).pack(padx=24, pady=14)

        btns = self.ttk.Frame(frame)
        btns.pack(fill="x", pady=6)
        self.ttk.Button(btns, text="刷新概览", command=self.refresh_dashboard).pack(side="left")
        self.ttk.Button(btns, text="一键导入示例表格", command=self.import_default_sample).pack(side="left", padx=8)

        self.dashboard_text = self.tk.Text(frame, height=28, wrap="word")
        self.dashboard_text.pack(fill="both", expand=True, padx=4, pady=6)

    def build_status_tab(self, status: str) -> None:
        frame = self._create_notebook_tab(status)
        top = self.ttk.Frame(frame)
        top.pack(fill="x", pady=6)
        search_var = self.tk.StringVar()
        start_date_var = self.tk.StringVar()
        end_date_var = self.tk.StringVar()
        count_var = self.tk.StringVar(value="0")
        self._build_order_filter_bar(
            top,
            search_var,
            start_date_var,
            end_date_var,
            query_command=lambda: self.refresh_status_tab(status),
        )
        self._build_page_summary(frame, status, count_var)
        tree = self._create_bound_order_tree(frame, height=12)

        if status == "发货":
            self._build_export_columns_section(frame, "status_shipment")

        action_frame = self.ttk.Frame(frame)
        action_frame.pack(fill="x", pady=8)
        self._build_status_action_bar(action_frame, status, tree)

        # --- 淘宝采购账号输入区，仅审核页面显示 ---
        if status == "审核":
            account_frame = self.ttk.LabelFrame(frame, text="采购淘宝账号设置")
            account_frame.pack(fill="x", padx=10, pady=(2, 0))
            self.ttk.Label(account_frame, text="账号：").pack(side="left", padx=4)
            self.ttk.Entry(account_frame, textvariable=self.taobao_account_var, width=18).pack(side="left", padx=2)
            self.ttk.Label(account_frame, text="密码：").pack(side="left", padx=4)
            self.ttk.Entry(account_frame, textvariable=self.taobao_password_var, width=18, show="*").pack(side="left", padx=2)

            # --- 采购商品库表格 ---
            product_frame = self.ttk.LabelFrame(frame, text="采购商品库（自动保存采购成功商品）")
            product_frame.pack(fill="both", expand=False, padx=10, pady=(2, 0))
            columns = ("商品名称", "书号/ISBN", "价格", "店铺", "商品ID")
            self.procurement_product_tree = self.ttk.Treeview(product_frame, columns=columns, show="headings", height=5)
            for col in columns:
                self.procurement_product_tree.heading(col, text=col)
                self.procurement_product_tree.column(col, width=110 if col!="商品名称" else 160, anchor="center")
            self.procurement_product_tree.pack(fill="x", padx=2, pady=2)
            # 加载历史商品
            self._load_procurement_products()

        self.status_tab_contexts[status] = {
            "tree": tree,
            "search_var": search_var,
            "start_date_var": start_date_var,
            "end_date_var": end_date_var,
            "count_var": count_var,
        }

    def save_procurement_account_settings(self) -> None:
        self.db.set_app_setting(TAOBAO_ACCOUNT_SETTING_KEY, safe_text(self.taobao_account_var.get()))
        self.db.set_app_setting(TAOBAO_PASSWORD_SETTING_KEY, "")
        self.db.log(self.current_user, "保存采购淘宝账号", safe_text(self.taobao_account_var.get()))
        self.messagebox.showinfo("保存成功", "采购淘宝账号已保存。密码不会写入本地数据库。")

    def _get_taobao_profile_dir(self) -> Path:
        return BASE_DIR / "playwright_taobao_profile"

    def _has_taobao_login_state(self) -> bool:
        profile_dir = self._get_taobao_profile_dir()
        if not profile_dir.exists():
            return False
        try:
            return any(profile_dir.iterdir())
        except OSError:
            return False

    def _refresh_taobao_login_state_status(self) -> None:
        has_state = self._has_taobao_login_state()
        status_text = "登录态：已保存" if has_state else "登录态：未初始化"
        if hasattr(self, "taobao_login_state_status_var"):
            self.taobao_login_state_status_var.set(status_text)
        if hasattr(self, "taobao_login_state_validity_var"):
            current_text = safe_text(self.taobao_login_state_validity_var.get())
            if not has_state:
                self.taobao_login_state_validity_var.set("有效性：未初始化")
            elif not current_text or current_text == "有效性：未初始化":
                self.taobao_login_state_validity_var.set("有效性：未检测")

    def _set_taobao_login_state_validity(self, text: str) -> None:
        if hasattr(self, "taobao_login_state_validity_var"):
            self.taobao_login_state_validity_var.set(f"有效性：{text}")

    def _start_background_task(
        self,
        target: Callable[[], Any],
        on_complete: Callable[[Any, Optional[BaseException]], None],
    ) -> None:
        def worker() -> None:
            result: Any = None
            error: Optional[BaseException] = None
            try:
                result = target()
            except Exception as exc:  # noqa: BLE001
                error = exc
                append_runtime_log("后台任务执行失败", sys.exc_info())
            try:
                self.root.after(0, lambda: on_complete(result, error))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def auto_check_taobao_login_state_validity(self) -> None:
        if self._has_taobao_login_state():
            self.check_taobao_login_state_validity_async(silent=True, trigger_source="程序启动自动检测")

    def _is_playwright_package_available(self) -> bool:
        try:
            return importlib.util.find_spec("playwright.sync_api") is not None
        except (ImportError, ModuleNotFoundError):
            return False

    def _is_embedded_browser_available(self) -> bool:
        return importlib.util.find_spec("webview") is not None

    def _is_playwright_browser_available(self) -> bool:
        if not self._is_playwright_package_available():
            return False
        try:
            executable_path = self._get_playwright_chromium_executable_path()
            return executable_path is not None and executable_path.exists()
        except Exception:
            return False

    def _get_playwright_chromium_executable_path(self) -> Optional[Path]:
        if not self._is_playwright_package_available():
            return None
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            return Path(playwright.chromium.executable_path)

    def _launch_chromium_with_profile(self, profile_dir: Path, urls: List[str]) -> subprocess.Popen[Any]:
        executable_path = self._get_playwright_chromium_executable_path()
        if executable_path is None or not executable_path.exists():
            raise FileNotFoundError("未找到 Playwright Chromium 可执行文件")
        command = [
            str(executable_path),
            f"--user-data-dir={profile_dir}",
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
            *urls,
        ]
        return subprocess.Popen(command, cwd=str(BASE_DIR))

    def refresh_playwright_status(self) -> None:
        package_ready = self._is_playwright_package_available()
        browser_ready = self._is_playwright_browser_available() if package_ready else False
        package_text = "依赖已安装" if package_ready else "未安装依赖"
        browser_text = "Chromium 已安装" if browser_ready else "Chromium 未安装"
        self.playwright_status_var.set(f"Playwright：{package_text} | {browser_text}")

    def refresh_playwright_status_async(self) -> None:
        def task() -> tuple[bool, bool]:
            package_ready = self._is_playwright_package_available()
            browser_ready = self._is_playwright_browser_available() if package_ready else False
            return (package_ready, browser_ready)

        def on_complete(result: Any, error: Optional[BaseException]) -> None:
            if error is not None:
                self.playwright_status_var.set("Playwright：检测失败")
                return
            package_ready, browser_ready = result
            package_text = "依赖已安装" if package_ready else "未安装依赖"
            browser_text = "Chromium 已安装" if browser_ready else "Chromium 未安装"
            self.playwright_status_var.set(f"Playwright：{package_text} | {browser_text}")

        self.playwright_status_var.set("Playwright：检测中")
        self._start_background_task(task, on_complete)

    def _get_python_install_command_parts(self) -> List[str]:
        executable = Path(sys.executable)
        if executable.name.lower().startswith("python"):
            return [str(executable)]
        return ["py"]

    def _launch_install_command(self, command_parts: List[str], action_name: str, success_tip: str) -> None:
        try:
            creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(command_parts, cwd=str(BASE_DIR), creationflags=creation_flags)
        except Exception:
            append_runtime_log(f"启动安装命令失败: {' '.join(command_parts)}", sys.exc_info())
            self.messagebox.showerror("启动失败", "无法打开安装终端，请手动执行安装命令。")
            return
        self.write_import_log(success_tip)
        self.db.log(self.current_user, action_name, " ".join(command_parts))
        self.messagebox.showinfo("已打开安装终端", success_tip)

    def install_playwright_package(self) -> None:
        command_parts = [*self._get_python_install_command_parts(), "-m", "pip", "install", "-U", "playwright"]
        self._launch_install_command(command_parts, "安装 Playwright 依赖", "已打开终端执行 Playwright 安装，请安装完成后点击“重新检测”。")

    def install_playwright_browser(self) -> None:
        command_parts = [*self._get_python_install_command_parts(), "-m", "playwright", "install", "chromium"]
        self._launch_install_command(command_parts, "安装 Playwright Chromium", "已打开终端执行 Chromium 浏览器安装，请安装完成后点击“重新检测”。")

    def _format_install_command(self, command_parts: List[str]) -> str:
        return " ".join([f'"{part}"' if " " in part else part for part in command_parts])

    def _launch_embedded_browser_window(self, url: str, title: str = "淘宝采购内置浏览器") -> bool:
        target_url = safe_text(url)
        if not target_url:
            return False
        if not self._is_embedded_browser_available():
            return False
        command_parts = [*self._get_python_install_command_parts(), "-c", EMBEDDED_BROWSER_BOOTSTRAP_CODE, title, target_url]
        try:
            creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(command_parts, cwd=str(BASE_DIR), creationflags=creation_flags)
        except Exception:
            append_runtime_log(f"启动内置浏览器失败: {target_url}", sys.exc_info())
            return False
        return True

    def _open_procurement_browser(
        self,
        items: List[Dict[str, Any]],
        status_var: Any = None,
        target_url: str = "",
        search_mode: str = "mall",
    ) -> None:
        browser_target = safe_text(target_url)
        if not browser_target:
            browser_target = "https://www.taobao.com/"
            if items:
                browser_target = self._build_procurement_search_url(items[0], search_mode=search_mode)
        if self._launch_embedded_browser_window(browser_target, title="淘宝自动采购浏览器"):
            if status_var is not None:
                if search_mode == "mall":
                    status_var.set("内置浏览器：已打开天猫搜索页，默认价格从低到高")
                else:
                    status_var.set("内置浏览器：已打开淘宝全站搜索页")
            return
        self._open_taobao_procurement_pages(items, search_mode=search_mode)
        if status_var is not None:
            status_var.set("内置浏览器：当前不可用，已回退外部采购助手")

    def ensure_playwright_ready(self) -> bool:
        package_ready = self._is_playwright_package_available()
        browser_ready = self._is_playwright_browser_available() if package_ready else False
        self.refresh_playwright_status_async()
        if package_ready and browser_ready:
            return True
        if not package_ready:
            install_command = self._format_install_command([*self._get_python_install_command_parts(), "-m", "pip", "install", "-U", "playwright"])
            should_install = self.messagebox.askyesno(
                "缺少 Playwright 依赖",
                f"当前未安装 Playwright，是否现在打开安装终端？\n\n安装命令：{install_command}",
            )
            if should_install:
                self.install_playwright_package()
            return False
        install_command = self._format_install_command([*self._get_python_install_command_parts(), "-m", "playwright", "install", "chromium"])
        should_install = self.messagebox.askyesno(
            "缺少 Chromium 浏览器",
            f"检测到 Playwright 已安装，但 Chromium 浏览器未安装，是否现在打开安装终端？\n\n安装命令：{install_command}",
        )
        if should_install:
            self.install_playwright_browser()
        return False

    def bootstrap_taobao_login_state(self) -> None:
        if self._taobao_login_state_task_running:
            self.messagebox.showinfo("提示", "淘宝登录态初始化正在进行中，请先完成当前浏览器登录。")
            return
        if not self.ensure_playwright_ready():
            return
        self.messagebox.showinfo(
            "初始化淘宝登录态",
            "将打开受控 Chromium 浏览器。请在打开的淘宝页面中手动完成登录，登录完成后直接关闭浏览器窗口即可。软件不会读取或明文保存 Cookie。",
        )
        profile_dir = self._get_taobao_profile_dir()
        profile_dir.mkdir(parents=True, exist_ok=True)
        self._taobao_login_state_task_running = True
        self.taobao_login_state_status_var.set("登录态：初始化中")
        self._set_taobao_login_state_validity("浏览器已打开，请登录后关闭")

        def task() -> bool:
            process = self._launch_chromium_with_profile(profile_dir, ["https://login.taobao.com/member/login.jhtml"])
            process.wait()
            return True

        def on_complete(result: Any, error: Optional[BaseException]) -> None:
            self._taobao_login_state_task_running = False
            self._refresh_taobao_login_state_status()
            if error is not None:
                self._set_taobao_login_state_validity("初始化失败")
                self.messagebox.showerror("登录态初始化失败", "无法启动淘宝登录浏览器，请查看软件日志。")
                return
            self._set_taobao_login_state_validity("浏览器已关闭，准备检测")
            self.db.log(self.current_user, "初始化淘宝登录态", str(profile_dir))
            self.messagebox.showinfo("完成", "淘宝登录态已更新。后续采购将优先复用本地登录态。")
            self.check_taobao_login_state_validity_async(silent=True, trigger_source="登录态初始化完成后自动检测")

        self._start_background_task(task, on_complete)

    def check_taobao_login_state_validity_async(self, silent: bool = False, trigger_source: str = "手动检测") -> None:
        if self._taobao_login_check_task_running:
            self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=跳过，原因=已有检测任务运行中")
            if not silent:
                self.messagebox.showinfo("提示", "正在检测淘宝登录态，请稍候。")
            return
        if self._taobao_browser_session_running:
            self._set_taobao_login_state_validity("浏览器会话使用中")
            self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=跳过，原因=采购浏览器会话使用中")
            if not silent:
                self.messagebox.showwarning("提示", "采购浏览器正在运行，请关闭后再检测登录态。")
            return
        if not self._has_taobao_login_state():
            self._refresh_taobao_login_state_status()
            self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=跳过，原因=未初始化登录态")
            if not silent:
                self.messagebox.showwarning("提示", "当前还没有淘宝登录态，请先点击“一键获取登录态”。")
            return
        if not self.ensure_playwright_ready():
            self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=跳过，原因=Playwright 环境未就绪")
            return

        self._taobao_login_check_task_running = True
        self._set_taobao_login_state_validity("检测中")
        profile_dir = self._get_taobao_profile_dir()
        self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=开始，目录={profile_dir}")

        def task() -> tuple[bool, str, str, str]:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    str(profile_dir),
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                    viewport={"width": 1280, "height": 800},
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto("https://i.taobao.com/my_taobao.htm", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    current_url = page.url.lower()
                    title = safe_text(page.title())
                    title_lower = title.lower()
                    if "login.taobao.com" in current_url or "passport" in current_url or "login" in title:
                        return (False, "已失效", current_url, title)
                    return (True, "有效", current_url, title)
                finally:
                    context.close()

        def on_complete(result: Any, error: Optional[BaseException]) -> None:
            self._taobao_login_check_task_running = False
            if error is not None:
                self._set_taobao_login_state_validity("检测失败")
                error_text = safe_text(error)
                self.db.log(self.current_user, "检测淘宝登录态", f"来源={trigger_source}，结果=检测失败，原因={error_text[:180]}")
                if not silent:
                    self.messagebox.showerror("检测失败", "无法检测淘宝登录态，请查看软件日志。")
                return
            is_valid, text, current_url, title = result
            self._set_taobao_login_state_validity(text)
            self.db.log(
                self.current_user,
                "检测淘宝登录态",
                f"来源={trigger_source}，结果={text}，URL={current_url[:180]}，标题={title[:80]}",
            )
            if not silent:
                if is_valid:
                    self.messagebox.showinfo("检测结果", "当前淘宝登录态有效，可直接复用。")
                else:
                    self.messagebox.showwarning("检测结果", "当前淘宝登录态已失效，请重新获取登录态。")

        self._start_background_task(task, on_complete)

    def clear_taobao_login_state(self) -> None:
        profile_dir = self._get_taobao_profile_dir()
        if not profile_dir.exists():
            self._refresh_taobao_login_state_status()
            self.messagebox.showinfo("提示", "当前没有可清除的淘宝登录态。")
            return
        confirmed = self.messagebox.askyesno("确认清除", "确定清除本机保存的淘宝登录态吗？下次采购需要重新登录。")
        if not confirmed:
            return
        try:
            import shutil

            shutil.rmtree(profile_dir, ignore_errors=True)
        except Exception:
            append_runtime_log("清除淘宝登录态失败", sys.exc_info())
            self.messagebox.showerror("清除失败", "无法清除淘宝登录态，请查看软件日志。")
            return
        self._refresh_taobao_login_state_status()
        self._set_taobao_login_state_validity("未初始化")
        self.db.log(self.current_user, "清除淘宝登录态", str(profile_dir))
        self.messagebox.showinfo("完成", "淘宝登录态已清除。")

    def _open_taobao_with_login_state(self, urls: List[str]) -> bool:
        if not self._has_taobao_login_state():
            return False
        if self._taobao_browser_session_running:
            self.messagebox.showinfo("提示", "淘宝采购浏览器已经在运行，请直接在已打开的窗口中继续操作。")
            return True
        if not self.ensure_playwright_ready():
            return False
        profile_dir = self._get_taobao_profile_dir()
        self._taobao_browser_session_running = True

        def task() -> bool:
            process = self._launch_chromium_with_profile(profile_dir, urls)
            process.wait()
            return True

        def on_complete(_result: Any, error: Optional[BaseException]) -> None:
            self._taobao_browser_session_running = False
            if error is not None:
                self.messagebox.showerror("启动失败", "无法启动淘宝采购浏览器，请查看软件日志。")
                return
            self.check_taobao_login_state_validity_async(silent=True, trigger_source="采购浏览器关闭后自动检测")

        self._start_background_task(task, on_complete)
        return True

    def _load_procurement_products(self) -> None:
        rows = self.db.list_procurement_products()
        if self.procurement_product_tree is None:
            return
        for item in self.procurement_product_tree.get_children():
            self.procurement_product_tree.delete(item)
        for row in rows:
            self.procurement_product_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    safe_text(row["product_name"]),
                    safe_text(row["isbn"]),
                    f"{to_float(row['price']):.2f}",
                    safe_text(row["shop"]),
                    safe_text(row["item_id"]),
                ),
            )

    def _save_procurement_product(self, name: str, isbn: str, price: Any, shop: str, item_id: str, mark_used: bool = False) -> None:
        item_value = safe_text(item_id)
        if not item_value:
            return
        self.db.upsert_procurement_product(
            {
                "product_name": name,
                "isbn": isbn,
                "price": price,
                "shop": shop,
                "item_id": item_value,
            }
        )
        if mark_used:
            self.db.mark_procurement_product_used(item_value)
        self._load_procurement_products()

    def _get_selected_order_rows(self, tree: Any) -> List[sqlite3.Row]:
        rows: List[sqlite3.Row] = []
        for item_id in self.get_tree_checked_or_selected_ids(tree):
            row = self.db.get_order(int(item_id))
            if row:
                rows.append(row)
        return rows

    def _get_procurement_candidate(self, order_row: sqlite3.Row) -> Optional[sqlite3.Row]:
        candidates = self.db.find_procurement_product_candidates(
            isbn=safe_text(order_row["sku"]),
            product_name=safe_text(order_row["product_name"]),
        )
        return candidates[0] if candidates else None

    def smart_procurement(self, tree: Any, mode: str = "manual") -> None:
        orders = self._get_selected_order_rows(tree)
        if not orders:
            self.messagebox.showwarning("提示", "请先勾选需要采购的订单。")
            return
        if safe_text(mode) == "auto":
            self.messagebox.showinfo("提示", "自动采购功能已删除，请使用“手动采购”。")
            return
        self._show_procurement_dialog(orders, auto=False, auto_open_pages=False)

    def _build_procurement_items(self, orders: List[sqlite3.Row]) -> Dict[int, Dict[str, Any]]:
        order_item_vars: Dict[int, Dict[str, Any]] = {}
        for order_row in orders:
            candidate = self._get_procurement_candidate(order_row)
            shop_var = self.tk.StringVar(value=safe_text(candidate["shop"]) if candidate else "")
            item_id_var = self.tk.StringVar(value=safe_text(candidate["item_id"]) if candidate else "")
            default_price = to_float(candidate["price"], 0.0) if candidate else round(
                to_float(order_row["book_amount"], 0.0) / max(to_int(order_row["quantity"], 1), 1),
                2,
            )
            price_var = self.tk.StringVar(value=f"{default_price:.2f}" if default_price else "")
            order_item_vars[int(order_row["id"])] = {
                "row": order_row,
                "shop_var": shop_var,
                "item_id_var": item_id_var,
                "price_var": price_var,
            }
        return order_item_vars

    def _build_procurement_dialog_header(self, dialog: Any, order_count: int) -> None:
        header = self.ttk.Frame(dialog)
        header.pack(fill="x", padx=12, pady=(12, 6))
        self.ttk.Label(header, text=f"已选择 {order_count} 条订单", font=("Microsoft YaHei", 11, "bold")).pack(side="left")
        self.ttk.Label(
            header,
            text="流程说明：打开淘宝登录页和商品页，验证码、支付密码、最终提交保留人工处理，避免异常风控。",
            foreground="#666666",
        ).pack(side="left", padx=12)

    def _build_procurement_account_section(self, dialog: Any) -> None:
        account_frame = self.ttk.LabelFrame(dialog, text="采购账号")
        account_frame.pack(fill="x", padx=12, pady=6)
        self.ttk.Label(account_frame, text="账号：").pack(side="left", padx=(8, 4), pady=8)
        self.ttk.Entry(account_frame, textvariable=self.taobao_account_var, width=22).pack(side="left", padx=4)
        self.ttk.Label(account_frame, text="密码：").pack(side="left", padx=(12, 4))
        self.ttk.Entry(account_frame, textvariable=self.taobao_password_var, width=22, show="*").pack(side="left", padx=4)
        self.ttk.Button(account_frame, text="保存账号", command=self.save_procurement_account_settings).pack(side="left", padx=8)
        self.ttk.Button(account_frame, text="一键获取登录态", command=self.bootstrap_taobao_login_state).pack(side="left", padx=6)
        self.ttk.Button(account_frame, text="检测有效性", command=self.check_taobao_login_state_validity_async).pack(side="left", padx=4)
        self.ttk.Button(account_frame, text="清除登录态", command=self.clear_taobao_login_state).pack(side="left", padx=4)
        self.ttk.Label(account_frame, textvariable=self.taobao_login_state_status_var, foreground="#0a7f2e").pack(side="left", padx=8)
        self.ttk.Label(account_frame, textvariable=self.taobao_login_state_validity_var, foreground="#0a5f9c").pack(side="left", padx=8)

    def _create_procurement_editor_inner(self, dialog: Any) -> Any:
        editor_outer = self.ttk.LabelFrame(dialog, text="本次采购商品")
        editor_outer.pack(fill="both", expand=True, padx=12, pady=6)
        canvas = self.tk.Canvas(editor_outer, highlightthickness=0)
        ybar = self.ttk.Scrollbar(editor_outer, orient="vertical", command=canvas.yview)
        inner = self.ttk.Frame(canvas)
        inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=ybar.set)
        canvas.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")
        return inner

    def _build_procurement_item_editor_section(self, dialog: Any, orders: List[sqlite3.Row]) -> Dict[int, Dict[str, Any]]:
        inner = self._create_procurement_editor_inner(dialog)
        headers = ["订单号", "书号/ISBN", "商品名称", "数量", "店铺", "商品ID", "采购价"]
        widths = [18, 18, 34, 8, 18, 18, 10]
        for index, title in enumerate(headers):
            self.ttk.Label(inner, text=title, font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=index, padx=4, pady=4, sticky="w")

        order_item_vars = self._build_procurement_items(orders)
        for row_index, order_row in enumerate(orders, start=1):
            item_vars = order_item_vars[int(order_row["id"])]
            self.ttk.Label(inner, text=safe_text(order_row["order_no"]), width=widths[0]).grid(row=row_index, column=0, padx=4, pady=3, sticky="w")
            self.ttk.Label(inner, text=safe_text(order_row["sku"]), width=widths[1]).grid(row=row_index, column=1, padx=4, pady=3, sticky="w")
            self.ttk.Label(inner, text=safe_text(order_row["product_name"]), width=widths[2]).grid(row=row_index, column=2, padx=4, pady=3, sticky="w")
            self.ttk.Label(inner, text=safe_text(order_row["quantity"]), width=widths[3]).grid(row=row_index, column=3, padx=4, pady=3, sticky="w")
            self.ttk.Entry(inner, textvariable=item_vars["shop_var"], width=widths[4]).grid(row=row_index, column=4, padx=4, pady=3, sticky="we")
            self.ttk.Entry(inner, textvariable=item_vars["item_id_var"], width=widths[5]).grid(row=row_index, column=5, padx=4, pady=3, sticky="we")
            self.ttk.Entry(inner, textvariable=item_vars["price_var"], width=widths[6]).grid(row=row_index, column=6, padx=4, pady=3, sticky="we")
        return order_item_vars

    def _get_procurement_browser_target_url(self, item_entries: List[Dict[str, Any]], search_mode: str) -> str:
        if not item_entries:
            return "https://www.taobao.com/"
        return self._build_procurement_search_url(item_entries[0], search_mode=search_mode)

    def _refresh_procurement_browser_url(self, item_entries: List[Dict[str, Any]], search_mode_var: Any, browser_url_var: Any) -> None:
        browser_url_var.set(self._get_procurement_browser_target_url(item_entries, safe_text(search_mode_var.get()) or "mall"))

    def _build_procurement_browser_section(self, dialog: Any, item_entries: List[Dict[str, Any]], auto: bool) -> Dict[str, Any]:
        browser_status_var = self.tk.StringVar(
            value="内置浏览器：自动采购会优先打开内置窗口；不可用时自动回退外部采购助手。"
            if auto
            else "内置浏览器：可按需打开首条采购页面。"
        )
        search_mode_var = self.tk.StringVar(value="mall")
        browser_url_var = self.tk.StringVar(value=self._get_procurement_browser_target_url(item_entries, search_mode_var.get()))

        browser_frame = self.ttk.LabelFrame(dialog, text="采购浏览器")
        browser_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.ttk.Label(browser_frame, text="搜索模式：").pack(side="left", padx=(8, 4), pady=8)
        self.ttk.Radiobutton(
            browser_frame,
            text="天猫优先",
            value="mall",
            variable=search_mode_var,
            command=lambda: self._refresh_procurement_browser_url(item_entries, search_mode_var, browser_url_var),
        ).pack(side="left", padx=4)
        self.ttk.Radiobutton(
            browser_frame,
            text="淘宝全站",
            value="all",
            variable=search_mode_var,
            command=lambda: self._refresh_procurement_browser_url(item_entries, search_mode_var, browser_url_var),
        ).pack(side="left", padx=(0, 8))
        self.ttk.Label(browser_frame, text="首条采购页：").pack(side="left", padx=(8, 4), pady=8)
        self.ttk.Entry(browser_frame, textvariable=browser_url_var, width=88).pack(side="left", padx=4, fill="x", expand=True)
        self.ttk.Button(
            browser_frame,
            text="打开内置浏览器",
            command=lambda: self._open_procurement_browser(
                item_entries,
                browser_status_var,
                browser_url_var.get(),
                search_mode_var.get(),
            ),
        ).pack(side="left", padx=6)
        self.ttk.Label(browser_frame, textvariable=browser_status_var, foreground="#0a5f9c").pack(side="left", padx=8)
        return {
            "browser_status_var": browser_status_var,
            "search_mode_var": search_mode_var,
        }

    def _build_procurement_result_section(self, dialog: Any, item_entries: List[Dict[str, Any]], search_mode_var: Any) -> None:
        footer = self.ttk.LabelFrame(dialog, text="采购结果回填")
        footer.pack(fill="x", padx=12, pady=(0, 12))
        procurement_order_no_var = self.tk.StringVar()
        procurement_cost_var = self.tk.StringVar()
        self.ttk.Button(
            footer,
            text="打开淘宝采购助手",
            command=lambda: self._open_taobao_procurement_pages(
                item_entries,
                search_mode=search_mode_var.get(),
            ),
        ).pack(side="left", padx=8, pady=8)
        self.ttk.Label(footer, text="采购单号：").pack(side="left", padx=(8, 4))
        self.ttk.Entry(footer, textvariable=procurement_order_no_var, width=22).pack(side="left", padx=4)
        self.ttk.Label(footer, text="采购总成本：").pack(side="left", padx=(12, 4))
        self.ttk.Entry(footer, textvariable=procurement_cost_var, width=14).pack(side="left", padx=4)
        self.ttk.Button(
            footer,
            text="仅回填采购信息",
            command=lambda: self._apply_procurement_result(
                item_entries,
                procurement_order_no_var.get(),
                procurement_cost_var.get(),
                submit_to_picking=False,
                dialog=dialog,
            ),
        ).pack(side="left", padx=8)
        self.ttk.Button(
            footer,
            text="回填并进入配货",
            command=lambda: self._apply_procurement_result(
                item_entries,
                procurement_order_no_var.get(),
                procurement_cost_var.get(),
                submit_to_picking=True,
                dialog=dialog,
            ),
        ).pack(side="left", padx=4)
        self.ttk.Button(footer, text="关闭", command=dialog.destroy).pack(side="right", padx=8)

    def _schedule_procurement_dialog_auto_action(
        self,
        item_entries: List[Dict[str, Any]],
        browser_status_var: Any,
        search_mode_var: Any,
        auto: bool,
        auto_open_pages: bool,
    ) -> None:
        if auto:
            self.root.after(
                120,
                lambda: self._open_procurement_browser(
                    item_entries,
                    browser_status_var,
                    search_mode=search_mode_var.get(),
                ),
            )
            return
        if auto_open_pages:
            self.root.after(
                120,
                lambda: self._open_taobao_procurement_pages(
                    item_entries,
                    search_mode=search_mode_var.get(),
                ),
            )

    def _show_procurement_dialog(self, orders: List[sqlite3.Row], auto: bool = True, auto_open_pages: bool = False) -> None:
        dialog = self.tk.Toplevel(self.root)
        dialog.title("自动采购" if auto else "手动采购")
        dialog.geometry("1120x720")
        dialog.transient(self.root)
        self._build_procurement_dialog_header(dialog, len(orders))
        self._build_procurement_account_section(dialog)
        order_item_vars = self._build_procurement_item_editor_section(dialog, orders)
        item_entries = list(order_item_vars.values())
        browser_context = self._build_procurement_browser_section(dialog, item_entries, auto)
        self._build_procurement_result_section(dialog, item_entries, browser_context["search_mode_var"])
        self._schedule_procurement_dialog_auto_action(
            item_entries,
            browser_context["browser_status_var"],
            browser_context["search_mode_var"],
            auto,
            auto_open_pages,
        )

    def _build_procurement_search_url(self, item: Dict[str, Any], search_mode: str = "mall") -> str:
        item_id = safe_text(item["item_id_var"].get())
        if item_id:
            return f"https://item.taobao.com/item.htm?id={urllib.parse.quote(item_id)}"
        order_row = item["row"]
        query = safe_text(order_row["sku"]) or safe_text(order_row["product_name"])
        if safe_text(order_row["product_name"]):
            query = f"{safe_text(order_row['sku'])} {safe_text(order_row['product_name'])}".strip()
        if search_mode == "mall":
            return f"https://s.taobao.com/search?q={urllib.parse.quote(query)}&tab=mall&sort=price-asc"
        return f"https://s.taobao.com/search?q={urllib.parse.quote(query)}"

    def _build_taobao_search_url(self, item: Dict[str, Any]) -> str:
        return self._build_procurement_search_url(item, search_mode="all")

    def _build_tmall_search_url(self, item: Dict[str, Any]) -> str:
        return self._build_procurement_search_url(item, search_mode="mall")

    def _open_taobao_procurement_pages(self, items: List[Dict[str, Any]], search_mode: str = "mall") -> None:
        urls = ["https://www.taobao.com/"]
        for item in items[:8]:
            urls.append(self._build_procurement_search_url(item, search_mode=search_mode))
        started_with_login_state = self._open_taobao_with_login_state(urls)
        if started_with_login_state:
            self.messagebox.showinfo(
                "淘宝采购助手已启动",
                "已使用本机保存的淘宝登录态启动采购浏览器。若登录态失效，请重新点击“一键获取登录态”。支付密码输入和最终提交仍建议人工确认。",
            )
            return

        webbrowser.open("https://login.taobao.com/member/login.jhtml")
        for url in urls[1:]:
            webbrowser.open_new_tab(url)
        self.messagebox.showinfo(
            "淘宝采购助手已启动",
            "未检测到可复用的淘宝登录态。已打开淘宝登录页和商品页/搜索页。若要复用登录态，请先点击“一键获取登录态”；验证码、支付密码和最终提交仍保留人工处理。",
        )

    def _get_order_recipient_summary(self, order_row: sqlite3.Row) -> str:
        return " , ".join(
            [
                safe_text(order_row["recipient_address"]) or "-",
                safe_text(order_row["recipient_phone"]) or "-",
                safe_text(order_row["recipient_name"]) or "-",
            ]
        )

    def _get_order_recipient_payload(self, order_row: sqlite3.Row) -> Dict[str, str]:
        recipient_name = safe_text(order_row["recipient_name"])
        recipient_phone = safe_text(order_row["recipient_phone"])
        recipient_address = safe_text(order_row["recipient_address"])
        recipient_summary = self._get_order_recipient_summary(order_row)
        return {
            "name": recipient_name,
            "phone": recipient_phone,
            "address": recipient_address,
            "summary": recipient_summary,
        }

    def _get_procurement_recipient_display_payload(self, order_row: sqlite3.Row) -> Dict[str, str]:
        recipient_payload = self._get_order_recipient_payload(order_row)
        recipient_phone_text = safe_text(recipient_payload.get("phone"))
        recipient_phone_digits = re.sub(r"\D+", "", recipient_phone_text)
        recipient_phone_suffix = recipient_phone_digits[-4:] if len(recipient_phone_digits) >= 4 else recipient_phone_text[-4:]
        recipient_phone_display = recipient_phone_digits[:11] if recipient_phone_digits else recipient_phone_text[:11]
        recipient_address_display = safe_text(recipient_payload.get("address"))
        recipient_name_display = safe_text(recipient_payload.get("name"))
        if recipient_phone_text:
            recipient_address_display = f"{recipient_address_display} {recipient_phone_text}".strip()
        if recipient_phone_suffix:
            recipient_name_display = f"{recipient_name_display} {recipient_phone_suffix}".strip()
        return {
            "address": recipient_address_display,
            "name": recipient_name_display,
            "phone": recipient_phone_display,
        }

    def _iter_playwright_frames(self, page: Any) -> List[Any]:
        frames: List[Any] = []
        try:
            frames.extend(page.frames)
        except Exception:
            frames.append(page)
        if page not in frames:
            frames.insert(0, page)
        return frames

    def _get_latest_open_playwright_page(self, context: Any, fallback_page: Any) -> Any:
        try:
            open_pages = [item for item in context.pages if not item.is_closed()]
        except Exception:
            return fallback_page
        if not open_pages:
            return fallback_page
        return open_pages[-1]

    def _click_taobao_buy_now(self, page: Any) -> bool:
        selectors = [
            'button:has-text("立即购买")',
            'button:has-text("立刻购买")',
            'a:has-text("立即购买")',
            'a:has-text("立刻购买")',
            'span:has-text("立即购买")',
            'span:has-text("立刻购买")',
            'div:has-text("立即购买")',
            'div:has-text("立刻购买")',
            'input[value*="立即购买"]',
            'input[value*="立刻购买"]',
        ]

        def try_click_in_frame(frame: Any) -> bool:
            for selector in selectors:
                try:
                    locator = frame.locator(selector).first
                    if locator.count() <= 0:
                        continue
                    try:
                        locator.scroll_into_view_if_needed(timeout=2000)
                    except Exception:
                        pass
                    try:
                        locator.click(timeout=2500)
                        return True
                    except Exception:
                        try:
                            locator.click(timeout=2500, force=True)
                            return True
                        except Exception:
                            continue
                except Exception:
                    continue
            return False

        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
        for _ in range(12):
            for frame in self._iter_playwright_frames(page):
                if try_click_in_frame(frame):
                    return True
            try:
                page.wait_for_timeout(700)
            except Exception:
                break
        return False

    def _click_second_taobao_address_edit(self, page: Any) -> bool:
        checkout_markers = ("确认订单", "确认收货地址", "使用新地址", "管理地址")
        address_edit_script = r"""
() => {
    const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
    const isVisible = (node) => {
        if (!node || !(node instanceof HTMLElement)) return false;
        const style = window.getComputedStyle(node);
        if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = node.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };
    const hasAddressLikeText = (text) => {
        if (!text || text.length < 14 || text.length > 260) return false;
        return /(\d{11}|省|市|区|县|镇|街道|路|号)/.test(text);
    };
    const findEditNode = (root) => {
        const candidates = [root, ...root.querySelectorAll('button, a, span, div, em, i')];
        for (const node of candidates) {
            if (!isVisible(node)) continue;
            const text = normalize(node.textContent || node.innerText || '');
            if (text === '编辑' || text.startsWith('编辑')) {
                return node;
            }
        }
        return null;
    };

    const rawNodes = Array.from(document.querySelectorAll('li, div, section, article, dl, dd'));
    const candidates = [];
    for (const node of rawNodes) {
        if (!isVisible(node)) continue;
        const text = normalize(node.innerText || node.textContent || '');
        if (!hasAddressLikeText(text)) continue;
        const rect = node.getBoundingClientRect();
        if (rect.width < 120 || rect.height < 24) continue;
        const editNode = findEditNode(node);
        if (!editNode) continue;
        candidates.push({
            node,
            editNode,
            text,
            top: Math.round(rect.top),
            left: Math.round(rect.left),
            area: Math.round(rect.width * rect.height),
        });
    }

    candidates.sort((a, b) => {
        if (a.top !== b.top) return a.top - b.top;
        if (a.left !== b.left) return a.left - b.left;
        return b.area - a.area;
    });

    const deduped = [];
    for (const item of candidates) {
        const duplicated = deduped.some((existing) => {
            return Math.abs(existing.top - item.top) <= 6
                && Math.abs(existing.left - item.left) <= 10
                && existing.text === item.text;
        });
        if (!duplicated) {
            deduped.push(item);
        }
    }

    if (deduped.length < 2) {
        return false;
    }

    const target = deduped[1];
    target.node.scrollIntoView({ block: 'center', inline: 'center' });
    for (const type of ['mouseenter', 'mouseover', 'mousemove']) {
        target.node.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    target.editNode.scrollIntoView({ block: 'center', inline: 'center' });
    for (const type of ['mouseenter', 'mouseover', 'mousemove']) {
        target.editNode.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    target.editNode.click();
    return true;
}
"""

        def has_checkout_markers(target_page: Any) -> bool:
            try:
                current_url = safe_text(target_page.url).lower()
            except Exception:
                current_url = ""
            if "buy.tmall.com/order/confirm_order" in current_url or "buy.taobao.com" in current_url:
                return True
            try:
                preview = safe_text(target_page.locator("body").inner_text(timeout=1500))[:500]
            except Exception:
                preview = ""
            return any(marker in preview for marker in checkout_markers)

        target_page = page
        try:
            context = page.context
        except Exception:
            context = None

        for _ in range(12):
            if context is not None:
                target_page = self._get_latest_open_playwright_page(context, target_page)
            try:
                target_page.wait_for_load_state("domcontentloaded", timeout=3000)
            except Exception:
                pass
            if has_checkout_markers(target_page):
                break
            try:
                target_page.wait_for_timeout(700)
            except Exception:
                break

        for _ in range(10):
            for frame in self._iter_playwright_frames(target_page):
                try:
                    if bool(frame.evaluate(address_edit_script)):
                        return True
                except Exception:
                    pass
                try:
                    edit_locator = frame.get_by_text("编辑", exact=True)
                    if edit_locator.count() > 1:
                        edit_locator.nth(1).click(timeout=1500)
                        return True
                except Exception:
                    pass
            try:
                target_page.wait_for_timeout(600)
            except Exception:
                break
        return False

    def _attempt_taobao_address_form_fill(self, page: Any, recipient_info: Dict[str, str]) -> Dict[str, Any]:
        return procurement_address_helpers.attempt_taobao_address_form_fill(
            page,
            recipient_info,
            iter_frames=self._iter_playwright_frames,
            get_latest_page=self._get_latest_open_playwright_page,
            append_log=append_runtime_log,
        )

    def _copy_procurement_recipient_payload(self, recipient_info: Dict[str, str], show_message: bool = False) -> bool:
        summary = procurement_address_helpers.format_recipient_summary(recipient_info)
        return self._set_clipboard_text(summary, show_message=show_message)

    def _show_procurement_address_fill_feedback(self, feedback: Dict[str, Any]) -> None:
        severity = safe_text(feedback.get("severity"))
        title = safe_text(feedback.get("title")) or "提示"
        message = safe_text(feedback.get("message"))
        if severity == "info":
            self.messagebox.showinfo(title, message)
            return
        if severity == "error":
            self.messagebox.showerror(title, message)
            return
        self.messagebox.showwarning(title, message)

    def _open_taobao_item_with_buy_now(
        self,
        url: str,
        recipient_info: Optional[Dict[str, str]] = None,
        operation: str = "purchase",
        feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        if self._taobao_browser_session_running:
            return False
        if not self.ensure_playwright_ready():
            return False

        profile_dir = self._get_taobao_profile_dir()
        has_login_state = self._has_taobao_login_state()
        self._taobao_browser_session_running = True

        def task() -> Dict[str, Any]:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = None
                if has_login_state:
                    context = playwright.chromium.launch_persistent_context(
                        str(profile_dir),
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled"],
                        viewport={"width": 1440, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                    )
                else:
                    browser = playwright.chromium.launch(
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled"],
                    )
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                    )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(1600)
                    clicked = self._click_taobao_buy_now(page)
                    address_edit_clicked = False
                    address_form_filled = False
                    address_fill_result: Dict[str, Any] = {"success": False, "address": False, "name": False, "phone": False}
                    try:
                        page.wait_for_timeout(1200)
                    except Exception:
                        pass
                    if clicked:
                        try:
                            address_edit_clicked = self._click_second_taobao_address_edit(
                                self._get_latest_open_playwright_page(context, page)
                            )
                        except Exception:
                            address_edit_clicked = False
                        if address_edit_clicked and recipient_info:
                            try:
                                page.wait_for_timeout(800)
                            except Exception:
                                pass
                            try:
                                address_fill_result = self._attempt_taobao_address_form_fill(
                                    self._get_latest_open_playwright_page(context, page),
                                    recipient_info,
                                )
                                address_form_filled = bool(address_fill_result.get("success"))
                            except Exception:
                                address_form_filled = False
                                address_fill_result = {"success": False, "address": False, "name": False, "phone": False}
                    while True:
                        try:
                            open_pages = [item for item in context.pages if not item.is_closed()]
                        except Exception:
                            open_pages = []
                        if not open_pages:
                            break
                        try:
                            open_pages[-1].wait_for_timeout(1000)
                        except Exception:
                            break
                    return {
                        "clicked": clicked,
                        "address_edit_clicked": address_edit_clicked,
                        "address_form_filled": address_form_filled,
                        "address_fill_result": address_fill_result,
                        "has_login_state": has_login_state,
                        "url": safe_text(page.url)[:180],
                    }
                finally:
                    try:
                        context.close()
                    except Exception:
                        pass
                    if browser is not None:
                        try:
                            browser.close()
                        except Exception:
                            pass

        def on_complete(result: Any, error: Optional[BaseException]) -> None:
            self._taobao_browser_session_running = False
            payload = result or {}
            feedback = procurement_address_helpers.build_feedback_plan(payload, operation=operation, error=error)
            if recipient_info and bool(feedback.get("copy_required")):
                self._copy_procurement_recipient_payload(recipient_info)
            if feedback_callback is not None:
                feedback_callback(feedback)
            self._show_procurement_address_fill_feedback(feedback)

        self._start_background_task(task, on_complete)
        return True

    def _normalize_procurement_search_text(self, text: str) -> str:
        normalized = safe_text(text)
        normalized = re.sub(r"[【】\[\]（）()《》<>，,。.!！?？:：;；/\\|+]+", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _shorten_procurement_product_name(self, product_name: str) -> str:
        normalized = self._normalize_procurement_search_text(product_name)
        if len(normalized) <= 28:
            return normalized
        parts = [part for part in normalized.split(" ") if part]
        shortened = " ".join(parts[:8]).strip()
        return shortened[:40] if shortened else normalized[:40]

    def _build_procurement_search_queries(self, order_row: sqlite3.Row, search_keyword: str = "") -> List[str]:
        sku = self._normalize_procurement_search_text(safe_text(order_row["sku"]))
        product_name = self._shorten_procurement_product_name(safe_text(order_row["product_name"]))
        manual = self._normalize_procurement_search_text(search_keyword)
        candidates = [
            manual,
            f"{sku} {product_name}".strip(),
            sku,
            product_name,
            safe_text(order_row["product_name"])[:20],
        ]
        queries: List[str] = []
        for candidate in candidates:
            normalized = self._normalize_procurement_search_text(candidate)
            if normalized and normalized not in queries:
                queries.append(normalized)
        return queries[:3]

    def _build_taobao_item_url(self, item_id: str) -> str:
        item_value = safe_text(item_id)
        if not item_value:
            return ""
        return f"https://item.taobao.com/item.htm?id={urllib.parse.quote(item_value)}"

    def _launch_procurement_for_result_item(
        self,
        order_row: sqlite3.Row,
        selected_item: Dict[str, Any],
        operation: str = "purchase",
        feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        url = safe_text(selected_item.get("url"))
        if not url:
            self.messagebox.showwarning("提示", "当前宝贝没有可打开的商品链接。")
            return
        recipient_summary = self._get_order_recipient_summary(order_row)
        recipient_display_payload = self._get_procurement_recipient_display_payload(order_row)
        self._set_clipboard_text(recipient_summary)
        if operation == "purchase":
            self._save_procurement_product(
                safe_text(selected_item.get("product_name")),
                safe_text(selected_item.get("isbn")),
                selected_item.get("price"),
                safe_text(selected_item.get("shop_name")),
                safe_text(selected_item.get("item_id")),
                mark_used=True,
            )
        if self._open_taobao_item_with_buy_now(url, recipient_display_payload, operation=operation, feedback_callback=feedback_callback):
            return
        append_runtime_log(
            "右键采购未启动可控浏览器："
            f"url={url[:180]}; "
            f"playwright_ready={self._is_playwright_package_available()}"
        )
        if self._taobao_browser_session_running:
            if operation == "address_retry":
                self.messagebox.showinfo("提示", "可控采购浏览器已经在运行，请先在当前窗口里完成或关闭后，再执行“重新填写收货信息”。")
                return
            self.messagebox.showinfo("提示", "可控采购浏览器已经在运行，请直接在已打开的浏览器窗口中继续，不再回退系统默认浏览器。")
            return
        if operation == "address_retry":
            self.messagebox.showwarning(
                "提示",
                "未能启动可控采购浏览器，因此无法重新填写收货信息。请先检查 Playwright/Chromium 环境，或直接手动粘贴剪贴板中的收货信息。",
            )
            return
        self.messagebox.showwarning(
            "提示",
            "未能启动可控采购浏览器，本次已阻止回退到系统默认浏览器，所以不会自动点击“立刻购买”。请先检查 Playwright/Chromium 环境后重试。",
        )

    def _start_procurement_for_result_item(
        self,
        order_row: sqlite3.Row,
        selected_item: Dict[str, Any],
        feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self._launch_procurement_for_result_item(order_row, selected_item, operation="purchase", feedback_callback=feedback_callback)

    def _retry_procurement_recipient_fill(
        self,
        order_row: sqlite3.Row,
        selected_item: Dict[str, Any],
        feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self._launch_procurement_for_result_item(order_row, selected_item, operation="address_retry", feedback_callback=feedback_callback)

    def _get_procurement_platform_label(self, item: Dict[str, Any]) -> str:
        source = safe_text(item.get("source")).lower()
        if source in {"local", "manual"}:
            return "本地商品库"
        url = safe_text(item.get("url")).lower()
        if "tmall.com" in url:
            return "天猫"
        if "taobao.com" in url or "item.htm?id=" in url:
            return "淘宝"
        return "淘宝"

    def _extract_taobao_item_id(self, text: str) -> str:
        source_text = safe_text(text)
        if not source_text:
            return ""
        url_match = re.search(r"[?&]id=(\d{6,})", source_text)
        if url_match:
            return safe_text(url_match.group(1))
        plain_match = re.search(r"\b(\d{6,})\b", source_text)
        if plain_match:
            return safe_text(plain_match.group(1))
        return ""

    def _get_local_procurement_search_results(self, order_row: sqlite3.Row, search_keyword: str = "") -> List[Dict[str, Any]]:
        seen_item_ids: set[str] = set()
        rows: List[sqlite3.Row] = []
        keyword = self._normalize_procurement_search_text(search_keyword)
        if keyword:
            rows.extend(self.db.list_procurement_products(keyword))
        rows.extend(
            self.db.find_procurement_product_candidates(
                isbn=safe_text(order_row["sku"]),
                product_name=safe_text(order_row["product_name"]),
            )
        )
        results: List[Dict[str, Any]] = []
        target_isbn = safe_text(order_row["sku"])
        target_name = safe_text(order_row["product_name"])
        for row in rows:
            item_id = safe_text(row["item_id"])
            if not item_id or item_id in seen_item_ids:
                continue
            seen_item_ids.add(item_id)
            results.append(
                {
                    "isbn": safe_text(row["isbn"]) or target_isbn,
                    "product_name": safe_text(row["product_name"]) or target_name,
                    "price": to_float(row["price"], 0.0),
                    "shop_name": safe_text(row["shop"]),
                    "shop_location": f"本地商品库 | 使用{to_int(row['use_count'], 0)}次",
                    "platform": "本地商品库",
                    "item_id": item_id,
                    "url": self._build_taobao_item_url(item_id),
                    "source": "local",
                }
            )
        return results

    def _wait_for_taobao_results_ready(self, page: Any) -> str:
        selectors = [
            'a[href*="item.htm?id="], a[href*="detail.tmall.com/item.htm"]',
            'a[href*="item.taobao.com/item.htm"], a[href*="h5.m.taobao.com/awp/core/detail.htm"]',
            '[class*="item"] a[href*="item.htm"]',
            '[data-index] a[href*="item.htm"]',
        ]
        body_preview = ""
        try:
            page.wait_for_load_state("networkidle", timeout=3500)
        except Exception:
            pass
        for _ in range(5):
            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        return "ready"
                except Exception:
                    continue
            try:
                body_preview = safe_text(page.locator("body").inner_text(timeout=1200))[:120]
            except Exception:
                body_preview = ""
            if any(flag in body_preview for flag in ["验证码", "请登录", "登录", "风险", "异常"]):
                return body_preview
            try:
                page.wait_for_timeout(700)
            except Exception:
                break
        return body_preview or "timeout"

    def _summarize_procurement_search_issue(self, detail: str) -> str:
        text = safe_text(detail)
        lower_text = text.lower()
        if "验证码" in text:
            return "天猫页面触发了验证码"
        if "请登录" in text or "登录" in text:
            return "天猫页面要求重新登录"
        if "风险" in text or "异常" in text:
            return "天猫页面触发了风控校验"
        if "timeout" in lower_text or "timed out" in lower_text:
            return "天猫页面加载超时"
        if "closed" in lower_text or "targetclosed" in lower_text:
            return "天猫页面会话被中断"
        return "天猫页未正常返回商品列表"

    def _extract_taobao_result_items(self, page: Any, isbn: str) -> List[Dict[str, Any]]:
        script = r"""
() => {
    const selectors = [
        'a[href*="item.taobao.com/item.htm?id="]',
        'a[href*="detail.tmall.com/item.htm?id="]',
        'a[href*="h5.m.taobao.com/awp/core/detail.htm"]',
        'a[href*="item.htm?id="]'
    ];
    const anchors = Array.from(document.querySelectorAll(selectors.join(', ')));
  const results = [];
  const seen = new Set();
  for (const anchor of anchors) {
    const href = anchor.href || '';
    const match = href.match(/[?&]id=(\d+)/);
    if (!match) continue;
    const itemId = match[1];
    if (seen.has(itemId)) continue;
    let container = anchor;
    for (let i = 0; i < 6 && container && container.parentElement; i++) {
      const text = (container.innerText || '').trim();
      if (text.length > 40) break;
      container = container.parentElement;
    }
    const text = ((container && container.innerText) || anchor.innerText || '').replace(/\s+/g, ' ').trim();
    let title = (anchor.getAttribute('title') || anchor.textContent || '').replace(/\s+/g, ' ').trim();
    if (!title && container) {
      const titleNode = container.querySelector('[title]');
      if (titleNode) title = (titleNode.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
    }
    if (!title) continue;
    const priceMatches = Array.from(text.matchAll(/(?:¥|￥)\s*([0-9]+(?:\.[0-9]+)?)/g)).map(m => Number.parseFloat(m[1])).filter(n => !Number.isNaN(n));
    const price = priceMatches.length ? Math.min(...priceMatches) : 0;
    let shopName = '';
    const shopNode = container ? container.querySelector('a[href*="shop"], a[href*="seller"], a[href*="tmall.com/shop"]') : null;
    if (shopNode) shopName = (shopNode.textContent || '').replace(/\s+/g, ' ').trim();
    let shopLocation = '';
    const locationNode = container ? container.querySelector('[class*="location"], [class*="city"], [class*="place"], [class*="from"]') : null;
    if (locationNode) shopLocation = (locationNode.textContent || '').replace(/\s+/g, ' ').trim();
    results.push({
      product_name: title,
      price,
      shop_name: shopName,
      shop_location: shopLocation,
      item_id: itemId,
      url: href,
    });
    seen.add(itemId);
  }
  return results;
}
"""
        raw_results = page.evaluate(script) or []
        results: List[Dict[str, Any]] = []
        for item in raw_results:
            normalized_item = {
                "isbn": isbn,
                "product_name": safe_text(item.get("product_name")),
                "price": to_float(item.get("price"), 0.0),
                "shop_name": safe_text(item.get("shop_name")),
                "shop_location": safe_text(item.get("shop_location")),
                "item_id": safe_text(item.get("item_id")),
                "url": safe_text(item.get("url")),
                "source": "remote",
            }
            normalized_item["platform"] = self._get_procurement_platform_label(normalized_item)
            results.append(
                normalized_item
            )
        return results

    def _fetch_taobao_search_results(
        self,
        order_row: sqlite3.Row,
        search_keyword: str = "",
        local_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        from playwright.sync_api import sync_playwright

        queries = self._build_procurement_search_queries(order_row, search_keyword)
        debug_messages: List[str] = []
        cached_local_results = list(local_results or [])
        issue_hint = ""

        with sync_playwright() as playwright:
            browser = None
            context = None
            try:
                if self._has_taobao_login_state() and not self._taobao_browser_session_running:
                    try:
                        context = playwright.chromium.launch_persistent_context(
                            str(self._get_taobao_profile_dir()),
                            headless=True,
                            args=["--disable-blink-features=AutomationControlled"],
                            viewport={"width": 1440, "height": 900},
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                        )
                    except Exception:
                        append_runtime_log("采购搜索使用淘宝登录态失败，已回退匿名上下文", sys.exc_info())
                        context = None
                if context is None:
                    browser = playwright.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                        viewport={"width": 1440, "height": 900},
                    )
                page = context.new_page()
                for query in queries:
                    try:
                        search_url = f"https://s.taobao.com/search?q={urllib.parse.quote(query)}&tab=mall&sort=price-asc"
                        page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                        page_state = self._wait_for_taobao_results_ready(page)
                        results = [
                            item
                            for item in self._extract_taobao_result_items(page, safe_text(order_row["sku"]))
                            if self._get_procurement_platform_label(item) == "天猫"
                        ]
                        if results:
                            results.sort(key=lambda item: (item.get("price", 0.0) <= 0, to_float(item.get("price"), 0.0)))
                            return {
                                "results": results,
                                "source": "tmall",
                                "message": f"已按“{query}”显示 {len(results)} 条天猫结果",
                            }
                        issue_hint = self._summarize_procurement_search_issue(page_state)
                        debug_messages.append(f"query={query}; state={page_state}; url={safe_text(page.url)[:120]}")
                    except Exception as exc:
                        issue_hint = self._summarize_procurement_search_issue(safe_text(exc))
                        debug_messages.append(f"query={query}; error={safe_text(exc)[:120]}")
            finally:
                if context is not None:
                    context.close()
                if browser is not None:
                    browser.close()

        if debug_messages:
            append_runtime_log("采购搜索未抓到天猫结果：" + " | ".join(debug_messages[:5]))
        if cached_local_results:
            reason_text = issue_hint or "天猫页未返回商品列表"
            return {
                "results": cached_local_results,
                "source": "local",
                "message": f"{reason_text}，已显示 {len(cached_local_results)} 条本地商品库候选",
                "detail": reason_text,
            }
        reason_text = issue_hint or "天猫页未渲染出商品列表"
        return {
            "results": [],
            "source": "none",
            "message": f"{reason_text}，可修改搜索词后重试，或直接打开淘宝搜索页手动选品",
            "detail": reason_text,
        }

    def open_order_procurement_dialog(self, order_row: sqlite3.Row, parent_dialog: Any = None) -> None:
        dialog = self.tk.Toplevel(parent_dialog or self.root)
        dialog.title(f"采购搜索 - {safe_text(order_row['order_no'])}")
        dialog.geometry("1180x760")
        dialog.transient(parent_dialog or self.root)

        container = self.ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        info_frame = self.ttk.LabelFrame(container, text="订单信息")
        info_frame.pack(fill="x", pady=(0, 8))
        recipient_display_payload = self._get_procurement_recipient_display_payload(order_row)
        info_items = [
            {"label": "商品名称", "value": safe_text(order_row["product_name"]), "copy": True},
            {"label": "书号/ISBN", "value": safe_text(order_row["sku"]), "copy": True},
            {"label": "订单号", "value": safe_text(order_row["order_no"]), "copy": False},
            {"label": "收件地址", "value": recipient_display_payload.get("address") or "-", "copy": True},
            {"label": "收件人姓名", "value": recipient_display_payload.get("name") or "-", "copy": True},
            {"label": "收件人电话", "value": recipient_display_payload.get("phone") or "-", "copy": True},
        ]
        for idx, item in enumerate(info_items):
            label = safe_text(item.get("label"))
            value = safe_text(item.get("value"))
            row_index = idx // 2
            column_index = (idx % 2) * 3
            self.ttk.Label(info_frame, text=label).grid(row=row_index, column=column_index, sticky="ne", padx=8, pady=6)
            value_frame = self.ttk.Frame(info_frame)
            value_frame.grid(row=row_index, column=column_index + 1, sticky="nw", padx=8, pady=6)
            self.ttk.Label(value_frame, text=value or "-", justify="left", wraplength=360).pack(side="left")
            if item.get("copy"):
                self.ttk.Button(value_frame, text="复制", width=6, command=lambda text=value: self.copy_text(text)).pack(side="left", padx=(8, 0))

        action_frame = self.ttk.Frame(container)
        action_frame.pack(fill="x", pady=(0, 8))
        search_status_var = self.tk.StringVar(value="待搜索")
        recipient_fill_status_var = self.tk.StringVar(value="地址填写状态：待开始")
        recipient_fill_failed_var = self.tk.StringVar(value="失败项：无")
        keyword_var = self.tk.StringVar(value=(self._build_procurement_search_queries(order_row) or [""])[0])
        manual_item_id_var = self.tk.StringVar()
        manual_shop_var = self.tk.StringVar()
        manual_price_var = self.tk.StringVar()
        result_state: Dict[str, Any] = {"results": [], "sort_reverse": False, "selected_url": "", "platform_filter": "全部", "searching": False}

        self.ttk.Label(action_frame, textvariable=search_status_var, foreground="#0a5f9c").pack(side="left")
        self.ttk.Label(action_frame, text="搜索词").pack(side="left", padx=(12, 4))
        keyword_entry = self.ttk.Entry(action_frame, textvariable=keyword_var, width=44)
        keyword_entry.pack(side="left", padx=(0, 6))
        search_button = self.ttk.Button(action_frame, text="搜索", command=lambda: run_search())
        search_button.pack(side="left", padx=(0, 6))
        retry_fill_button = self.ttk.Button(action_frame, text="重新填写收货信息", command=lambda: retry_selected_recipient_fill())
        retry_fill_button.pack(side="left", padx=(0, 6))

        recipient_helper_frame = self.ttk.LabelFrame(container, text="收货信息辅助")
        recipient_helper_frame.pack(fill="x", pady=(0, 8))
        self.ttk.Label(recipient_helper_frame, textvariable=recipient_fill_status_var, foreground="#0a5f9c").pack(side="left", padx=(8, 8), pady=8)
        self.ttk.Label(recipient_helper_frame, textvariable=recipient_fill_failed_var, foreground="#b34a00").pack(side="left", padx=(0, 12), pady=8)
        for copy_item in procurement_address_helpers.build_recipient_copy_items(recipient_display_payload):
            self.ttk.Button(
                recipient_helper_frame,
                text=copy_item["label"],
                command=lambda text=copy_item["value"]: self.copy_text(text),
            ).pack(side="left", padx=4, pady=8)
        self.ttk.Button(
            recipient_helper_frame,
            text="复制全部",
            command=lambda: self.copy_text(procurement_address_helpers.format_recipient_summary(recipient_display_payload)),
        ).pack(side="left", padx=4, pady=8)

        manual_frame = self.ttk.LabelFrame(container, text="手动选品回填")
        manual_frame.pack(fill="x", pady=(0, 8))
        self.ttk.Label(manual_frame, text="商品ID/链接").pack(side="left", padx=(8, 4), pady=6)
        self.ttk.Entry(manual_frame, textvariable=manual_item_id_var, width=28).pack(side="left", padx=4)
        self.ttk.Label(manual_frame, text="店铺").pack(side="left", padx=(10, 4))
        self.ttk.Entry(manual_frame, textvariable=manual_shop_var, width=18).pack(side="left", padx=4)
        self.ttk.Label(manual_frame, text="价格").pack(side="left", padx=(10, 4))
        self.ttk.Entry(manual_frame, textvariable=manual_price_var, width=10).pack(side="left", padx=4)

        result_frame = self.ttk.LabelFrame(container, text="采购搜索结果（全部）")
        result_frame.pack(fill="both", expand=True)
        columns = ("platform", "isbn", "product_name", "price", "shop_name", "shop_location", "item_id")
        headers = {
            "platform": "平台",
            "isbn": "书号/ISBN",
            "product_name": "商品名称",
            "price": "价格",
            "shop_name": "店铺名称",
            "shop_location": "店铺所在地",
            "item_id": "商品ID",
        }
        widths = {"platform": 100, "isbn": 140, "product_name": 340, "price": 90, "shop_name": 180, "shop_location": 160, "item_id": 140}
        tree = self.ttk.Treeview(result_frame, columns=columns, show="headings", height=16)
        def update_price_heading() -> None:
            if bool(result_state.get("sort_reverse")):
                tree.heading("price", text="价格 ▼", command=toggle_price_sort)
            else:
                tree.heading("price", text="价格 ▲", command=toggle_price_sort)

        def toggle_price_sort() -> None:
            result_state["sort_reverse"] = not bool(result_state.get("sort_reverse"))
            update_price_heading()
            refresh_tree()

        for col in columns:
            if col == "price":
                tree.heading(col, text=headers[col], command=toggle_price_sort)
            else:
                tree.heading(col, text=headers[col])
            tree.column(col, width=widths[col], anchor="center" if col != "product_name" else "w")
        ybar = self.ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
        xbar = self.ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, rowspan=2, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        def get_visible_results() -> List[Dict[str, Any]]:
            results = list(result_state["results"])
            platform_filter = safe_text(result_state.get("platform_filter", "全部")) or "全部"
            if platform_filter != "全部":
                results = [item for item in results if self._get_procurement_platform_label(item) == platform_filter]
            results.sort(key=lambda item: to_float(item.get("price"), 0.0), reverse=bool(result_state["sort_reverse"]))
            return results

        def refresh_tree() -> None:
            for item in tree.get_children():
                tree.delete(item)
            results = get_visible_results()
            for index, item in enumerate(results, start=1):
                iid = str(index)
                tree.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        self._get_procurement_platform_label(item),
                        safe_text(item.get("isbn")),
                        safe_text(item.get("product_name")),
                        f"{to_float(item.get('price'), 0.0):.2f}",
                        safe_text(item.get("shop_name")),
                        safe_text(item.get("shop_location")),
                        safe_text(item.get("item_id")),
                    ),
                )

        def open_selected_item() -> None:
            results = get_visible_results()
            selected_item = get_selected_result_item(results)
            if not selected_item:
                return
            recipient_fill_status_var.set("地址填写状态：正在尝试自动填写...")
            recipient_fill_failed_var.set("失败项：待检测")
            self._start_procurement_for_result_item(order_row, selected_item, feedback_callback=handle_recipient_fill_feedback)

        def get_selected_result_item(results: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
            selected = tree.selection()
            if not selected:
                self.messagebox.showwarning("提示", "请先选择一条宝贝记录。")
                return None
            current_results = results if results is not None else get_visible_results()
            index = int(selected[0]) - 1
            if index < 0 or index >= len(current_results):
                return None
            return current_results[index]

        def retry_selected_recipient_fill() -> None:
            selected_item = get_selected_result_item()
            if not selected_item:
                return
            recipient_fill_status_var.set("地址填写状态：正在重新尝试...")
            recipient_fill_failed_var.set("失败项：待检测")
            self._retry_procurement_recipient_fill(order_row, selected_item, feedback_callback=handle_recipient_fill_feedback)

        def handle_recipient_fill_feedback(feedback: Dict[str, Any]) -> None:
            if not dialog.winfo_exists():
                return
            recipient_fill_status_var.set(safe_text(feedback.get("status_text")) or "地址填写状态：未知")
            failed_text = safe_text(feedback.get("failed_fields_text")) or "无"
            recipient_fill_failed_var.set(f"失败项：{failed_text}")

        def show_tree_context_menu(event: Any) -> None:
            item_id = tree.identify_row(event.y)
            if not item_id:
                return
            tree.selection_set(item_id)
            tree.focus(item_id)
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        context_menu = self.tk.Menu(dialog, tearoff=0)
        context_menu.add_command(label="采购", command=open_selected_item)

        def remember_manual_item() -> None:
            item_id = self._extract_taobao_item_id(manual_item_id_var.get())
            if not item_id:
                self.messagebox.showwarning("提示", "请先粘贴淘宝商品ID或商品链接。")
                return
            product_name = safe_text(order_row["product_name"])
            isbn = safe_text(order_row["sku"])
            shop_name = safe_text(manual_shop_var.get())
            price_value = to_float(manual_price_var.get(), 0.0)
            item = {
                "isbn": isbn,
                "product_name": product_name,
                "price": price_value,
                "shop_name": shop_name,
                "shop_location": "手动回填 | 已记住",
                "platform": "本地商品库",
                "item_id": item_id,
                "url": self._build_taobao_item_url(item_id),
                "source": "manual",
            }
            self._save_procurement_product(product_name, isbn, price_value, shop_name, item_id, mark_used=True)
            result_state["results"] = [item, *[row for row in result_state["results"] if safe_text(row.get("item_id")) != item_id]]
            search_status_var.set("已回填商品ID并写入本地商品库，下次同ISBN会优先命中")
            refresh_tree()

        def load_item_id_from_clipboard() -> None:
            try:
                clipboard_text = self.root.clipboard_get()
            except Exception:
                self.messagebox.showwarning("提示", "剪贴板里没有可用内容。")
                return
            item_id = self._extract_taobao_item_id(clipboard_text)
            if not item_id:
                self.messagebox.showwarning("提示", "剪贴板内容里没有识别到淘宝商品ID或链接。")
                return
            manual_item_id_var.set(item_id)

        def run_search() -> None:
            if bool(result_state.get("searching")):
                return
            if not self.ensure_playwright_ready():
                search_status_var.set("未安装搜索环境")
                return
            current_keyword = safe_text(keyword_var.get())
            local_results = self._get_local_procurement_search_results(order_row, current_keyword)
            result_state["searching"] = True
            search_button.configure(state="disabled")
            if local_results:
                result_state["results"] = local_results
                search_status_var.set(f"已先显示 {len(local_results)} 条本地商品库候选，继续搜索天猫...")
                refresh_tree()
            else:
                result_state["results"] = []
                search_status_var.set("正在搜索天猫...")
                refresh_tree()

            def task() -> Dict[str, Any]:
                return self._fetch_taobao_search_results(order_row, current_keyword, local_results=local_results)

            def on_complete(result: Any, error: Optional[BaseException]) -> None:
                if not dialog.winfo_exists() or not tree.winfo_exists():
                    return
                result_state["searching"] = False
                search_button.configure(state="normal")
                if error is not None:
                    search_status_var.set("搜索失败")
                    error_text = self._summarize_procurement_search_issue(safe_text(error))
                    self.messagebox.showwarning("搜索失败", f"{error_text}，请稍后重试或直接打开淘宝搜索页。")
                    return
                payload = result or {}
                result_state["results"] = payload.get("results") or []
                if not result_state["results"]:
                    search_status_var.set(payload.get("message") or "未找到结果")
                else:
                    search_status_var.set(payload.get("message") or f"已显示 {len(result_state['results'])} 条结果")
                refresh_tree()

            self._start_background_task(task, on_complete)

        tree.bind("<Double-1>", lambda _event: open_selected_item())
        tree.bind("<Button-3>", show_tree_context_menu)
        keyword_entry.bind("<Return>", lambda _event: run_search())
        update_price_heading()
        self.ttk.Button(manual_frame, text="从剪贴板读取", command=load_item_id_from_clipboard).pack(side="left", padx=6)
        self.ttk.Button(manual_frame, text="回填商品ID并记住", command=remember_manual_item).pack(side="left", padx=6)

        tool_frame = self.ttk.Frame(container)
        tool_frame.pack(fill="x", pady=8)
        self.ttk.Button(tool_frame, text="全部", command=lambda: (result_state.update({"platform_filter": "全部"}), refresh_tree())).pack(side="left", padx=(10, 0))
        self.ttk.Button(tool_frame, text="只看本地商品库", command=lambda: (result_state.update({"platform_filter": "本地商品库"}), refresh_tree())).pack(side="left", padx=6)
        self.ttk.Button(
            tool_frame,
            text="只用ISBN",
            command=lambda: (keyword_var.set(self._normalize_procurement_search_text(safe_text(order_row["sku"]))), run_search()),
        ).pack(side="left", padx=6)
        self.ttk.Button(
            tool_frame,
            text="只用书名",
            command=lambda: (keyword_var.set(self._shorten_procurement_product_name(safe_text(order_row["product_name"]))), run_search()),
        ).pack(side="left", padx=6)
        self.ttk.Button(tool_frame, text="打开所选宝贝", command=open_selected_item).pack(side="left", padx=6)
        self.ttk.Button(
            tool_frame,
            text="打开淘宝搜索页",
            command=lambda: self._open_taobao_procurement_pages([
                {
                    "row": order_row,
                    "item_id_var": self.tk.StringVar(value=""),
                    "shop_var": self.tk.StringVar(value=""),
                    "price_var": self.tk.StringVar(value=""),
                }
            ]),
        ).pack(side="left", padx=6)
        self.ttk.Button(tool_frame, text="关闭", command=dialog.destroy).pack(side="right")

    def _apply_procurement_result(
        self,
        items: List[Dict[str, Any]],
        procurement_order_no: str,
        procurement_cost: Any,
        submit_to_picking: bool,
        dialog: Any,
    ) -> None:
        order_no_text = safe_text(procurement_order_no)
        total_cost = to_float(procurement_cost, 0.0)
        if not order_no_text:
            self.messagebox.showwarning("提示", "请先填写采购单号。")
            return
        if total_cost <= 0:
            self.messagebox.showwarning("提示", "请先填写有效的采购总成本。")
            return

        success_count = 0
        failed_orders: List[str] = []
        for item in items:
            order_row = item["row"]
            payload: Dict[str, Any] = {
                "procurement_date": today_str(),
                "procurement_order_no": order_no_text,
                "procurement_cost": total_cost,
            }
            if submit_to_picking:
                payload["order_status"] = "配货"
            try:
                self.db.update_order_details(int(order_row["id"]), payload, self.current_user)
                success_count += 1
            except ValueError as exc:
                failed_orders.append(f"{safe_text(order_row['order_no'])}: {exc}")
                continue
            self._save_procurement_product(
                safe_text(order_row["product_name"]),
                safe_text(order_row["sku"]),
                item["price_var"].get(),
                item["shop_var"].get(),
                item["item_id_var"].get(),
                mark_used=True,
            )

        self.refresh_all()
        if failed_orders:
            self.messagebox.showwarning("部分订单处理失败", "\n".join(failed_orders[:5]))
            return
        action_text = "并已提交到配货页面" if submit_to_picking else ""
        self.messagebox.showinfo("处理完成", f"已处理 {success_count} 条订单{action_text}。")
        dialog.destroy()

    def build_settlement_tab(self) -> None:
        frame = self._create_notebook_tab("结算")
        top = self.ttk.Frame(frame)
        top.pack(fill="x", pady=6)
        search_var = self.tk.StringVar()
        start_date_var = self.tk.StringVar()
        end_date_var = self.tk.StringVar()
        settlement_status_var = self.tk.StringVar(value="未结算")
        invoice_status_var = self.tk.StringVar(value="全部")
        batch_settlement_status_var = self.tk.StringVar(value="已结算")
        count_var = self.tk.StringVar(value="0")
        self._build_order_filter_bar(
            top,
            search_var,
            start_date_var,
            end_date_var,
            query_command=self.refresh_settlement_tab,
            extra_filters=[
                {"label": "结算状态", "variable": settlement_status_var, "values": SETTLEMENT_STATUS_FILTER_OPTIONS},
                {"label": "发票状态", "variable": invoice_status_var, "values": INVOICE_STATUS_FILTER_OPTIONS},
            ],
        )
        self._build_page_summary(frame, "结算", count_var)
        tree = self._create_bound_order_tree(frame, height=12)
        self._build_export_columns_section(frame, "settlement")

        action_frame = self.ttk.Frame(frame)
        action_frame.pack(fill="x", pady=8)
        self._build_settlement_action_bar(action_frame, tree, batch_settlement_status_var)

        self.settlement_tab_context = {
            "tree": tree,
            "search_var": search_var,
            "start_date_var": start_date_var,
            "end_date_var": end_date_var,
            "settlement_status_var": settlement_status_var,
            "invoice_status_var": invoice_status_var,
            "batch_settlement_status_var": batch_settlement_status_var,
            "count_var": count_var,
            "export_scope": "settlement",
        }

    def build_orders_tab(self) -> None:
        frame = self._create_notebook_tab("总订单")
        top = self.ttk.Frame(frame)
        top.pack(fill="x", pady=6)
        self.order_search_var = self.tk.StringVar()
        self.order_status_filter_var = self.tk.StringVar(value="全部")
        self.settlement_status_filter_var = self.tk.StringVar(value="全部")
        self.invoice_status_filter_var = self.tk.StringVar(value="全部")
        self.order_start_date_var = self.tk.StringVar()
        self.order_end_date_var = self.tk.StringVar()
        self._build_order_filter_bar(
            top,
            self.order_search_var,
            self.order_start_date_var,
            self.order_end_date_var,
            query_command=self.refresh_orders,
            extra_filters=[
                {"label": "订单状态", "variable": self.order_status_filter_var, "values": ORDER_STATUS_FILTER_OPTIONS},
                {"label": "结算状态", "variable": self.settlement_status_filter_var, "values": SETTLEMENT_STATUS_FILTER_OPTIONS},
                {"label": "发票状态", "variable": self.invoice_status_filter_var, "values": INVOICE_STATUS_FILTER_OPTIONS},
            ],
            extra_buttons=[
                {"text": "批量确认状态", "command": self.batch_update_order_status, "padx": 10},
            ],
        )

        self.order_tree = self._create_bound_order_tree(frame, height=12, on_select=self.on_order_selected)
        self._build_export_columns_section(frame, "orders")

        order_action_frame = self.ttk.Frame(frame)
        order_action_frame.pack(fill="x", pady=8)
        self._build_orders_action_bar(order_action_frame, self.order_tree)

        self.edit_vars = {
            "recipient_name": self.tk.StringVar(),
            "recipient_address": self.tk.StringVar(),
            "remark": self.tk.StringVar(),
            "courier_company": self.tk.StringVar(),
            "tracking_no": self.tk.StringVar(),
            "settlement_status": self.tk.StringVar(),
            "invoice_status": self.tk.StringVar(),
            "procurement_date": self.tk.StringVar(),
            "procurement_order_no": self.tk.StringVar(),
            "procurement_cost": self.tk.StringVar(),
            "procurement_remark": self.tk.StringVar(),
            "order_status": self.tk.StringVar(),
        }

    def build_export_column_selector(self, parent: Any, scope: str) -> None:
        remembered_columns = self.get_saved_export_columns(scope, mode="last")
        vars_by_key = {
            key: self.tk.BooleanVar(value=(key in remembered_columns if remembered_columns else True))
            for key in ORDER_EXPORT_COLUMN_KEYS
        }
        self.export_column_vars[scope] = vars_by_key

        button_frame = self.ttk.Frame(parent)
        button_frame.pack(fill="x", padx=8, pady=(6, 2))
        self.ttk.Button(button_frame, text="全选列", command=lambda current_scope=scope: self.set_export_column_selection(current_scope, True)).pack(side="left")
        self.ttk.Button(button_frame, text="取消全选", command=lambda current_scope=scope: self.set_export_column_selection(current_scope, False)).pack(side="left", padx=6)
        self.ttk.Button(button_frame, text="导出模板", command=lambda current_scope=scope: self.apply_export_template(current_scope)).pack(side="left", padx=6)

        options_frame = self.ttk.Frame(parent)
        options_frame.pack(fill="x", padx=8, pady=(0, 6))
        for idx, (key, title, _width) in enumerate(ORDER_GRID_COLUMNS):
            self.ttk.Checkbutton(
                options_frame,
                text=title,
                variable=vars_by_key[key],
            ).grid(row=idx // 4, column=idx % 4, sticky="w", padx=8, pady=4)

    def set_export_column_selection(self, scope: str, checked: bool) -> None:
        vars_by_key = self.export_column_vars.get(scope, {})
        for var in vars_by_key.values():
            var.set(checked)

    def apply_export_column_selection(self, scope: str, selected_columns: List[str]) -> None:
        selected = set(selected_columns)
        vars_by_key = self.export_column_vars.get(scope, {})
        for key in ORDER_EXPORT_COLUMN_KEYS:
            var = vars_by_key.get(key)
            if var is not None:
                var.set(key in selected)

    def get_selected_export_columns(self, scope: str) -> List[str]:
        vars_by_key = self.export_column_vars.get(scope, {})
        selected_columns: List[str] = []
        for key in ORDER_EXPORT_COLUMN_KEYS:
            var = vars_by_key.get(key)
            if var is not None and bool(var.get()):
                selected_columns.append(key)
        return selected_columns

    def get_export_setting_key(self, scope: str, mode: str) -> str:
        return f"export_columns.{mode}.{scope}"

    def get_saved_export_columns(self, scope: str, mode: str = "last") -> List[str]:
        raw_value = self.db.get_app_setting(self.get_export_setting_key(scope, mode), "")
        selected = [item for item in raw_value.split(",") if item in ORDER_EXPORT_COLUMN_KEYS]
        return selected

    def save_export_columns(self, scope: str, selected_columns: List[str], mode: str = "last") -> None:
        valid_columns = [item for item in selected_columns if item in ORDER_EXPORT_COLUMN_KEYS]
        self.db.set_app_setting(self.get_export_setting_key(scope, mode), ",".join(valid_columns))

    def apply_export_template(self, scope: str) -> None:
        template_columns = self.get_saved_export_columns(scope, mode="template")
        if not template_columns:
            self.messagebox.showwarning("提示", "当前页面还没有保存过导出模板")
            return
        self.apply_export_column_selection(scope, template_columns)
        self.messagebox.showinfo("导出模板", "已应用已保存的导出模板")

    def build_books_tab(self) -> None:
        frame = self.ttk.Frame(self.notebook)
        self.notebook.add(frame, text="图书资料库")

        top = self.ttk.Frame(frame)
        top.pack(fill="x", pady=6)
        self.book_search_var = self.tk.StringVar()
        self.ttk.Label(top, text="搜索：").pack(side="left")
        self.ttk.Entry(top, textvariable=self.book_search_var, width=30).pack(side="left", padx=5)
        self.ttk.Button(top, text="查询", command=self.refresh_books).pack(side="left", padx=4)
        self.ttk.Button(top, text="刷新", command=self.refresh_books).pack(side="left", padx=4)

        table_frame = self.ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True)
        columns = ("sku", "name", "price", "discount", "shipping_fee", "publisher")
        self.book_tree = self.ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        headers = {
            "sku": "SKU/书号",
            "name": "书名",
            "price": "定价",
            "discount": "折扣",
            "shipping_fee": "邮费",
            "publisher": "出版社",
        }
        widths = {"sku": 120, "name": 360, "price": 80, "discount": 80, "shipping_fee": 80, "publisher": 180}
        for col in columns:
            self.book_tree.heading(col, text=headers[col])
            self.book_tree.column(col, width=widths[col], anchor="center")
        ybar = self.ttk.Scrollbar(table_frame, orient="vertical", command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=ybar.set)
        self.book_tree.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")

        form = self.ttk.LabelFrame(frame, text="新增 / 编辑图书")
        form.pack(fill="x", pady=10)
        self.book_vars = {
            "sku": self.tk.StringVar(),
            "name": self.tk.StringVar(),
            "price": self.tk.StringVar(),
            "discount": self.tk.StringVar(value="0.65"),
            "shipping_fee": self.tk.StringVar(value="6"),
            "publisher": self.tk.StringVar(),
            "supplier": self.tk.StringVar(),
        }
        book_fields = [
            ("SKU/书号", "sku"),
            ("书名", "name"),
            ("定价", "price"),
            ("折扣", "discount"),
            ("邮费", "shipping_fee"),
            ("出版社", "publisher"),
            ("供应商", "supplier"),
        ]
        for idx, (label, key) in enumerate(book_fields):
            row = idx // 3
            col = (idx % 3) * 2
            self.ttk.Label(form, text=label).grid(row=row, column=col, sticky="e", padx=6, pady=4)
            self.ttk.Entry(form, textvariable=self.book_vars[key], width=30).grid(row=row, column=col + 1, sticky="w", padx=6, pady=4)
        self.ttk.Button(form, text="保存图书资料", command=self.save_book).grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="w")

    def build_profit_tab(self) -> None:
        frame = self.ttk.Frame(self.notebook)
        self.notebook.add(frame, text="利润统计")
        self.ttk.Button(frame, text="刷新统计", command=self.refresh_profit).pack(anchor="w", padx=6, pady=6)
        self.profit_text = self.tk.Text(frame, height=36, wrap="word")
        self.profit_text.pack(fill="both", expand=True, padx=4, pady=8)

    def build_settings_tab(self) -> None:
        frame = self.ttk.Frame(self.notebook)
        self.notebook.add(frame, text="系统设置")

        import_panel = self.ttk.LabelFrame(frame, text="数据导入")
        import_panel.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        btn_frame = self.ttk.Frame(import_panel)
        btn_frame.pack(fill="x", pady=10, padx=10)
        self.ttk.Button(btn_frame, text="导入订单文件", command=self.import_orders_file).pack(side="left", padx=5)
        self.ttk.Button(btn_frame, text="导入图书资料", command=self.import_books_file).pack(side="left", padx=5)
        self.ttk.Button(btn_frame, text="导入供应商规则", command=self.import_supplier_file).pack(side="left", padx=5)
        self.ttk.Button(btn_frame, text="导入当前目录示例表格.xlsx", command=self.import_default_sample).pack(side="left", padx=5)

        auto_import_panel = self.ttk.LabelFrame(import_panel, text="微信订单一键导入")
        auto_import_panel.pack(fill="x", padx=10, pady=(0, 10))
        root_row = self.ttk.Frame(auto_import_panel)
        root_row.pack(fill="x", padx=8, pady=(8, 6))
        self.ttk.Label(root_row, text="微信文件根目录 / 月目录：").pack(side="left")
        self.ttk.Entry(root_row, textvariable=self.wechat_root_var, width=58).pack(side="left", padx=6, fill="x", expand=True)
        self.ttk.Button(root_row, text="选择文件夹", command=self.select_wechat_root_dir).pack(side="left", padx=4)
        self.ttk.Button(root_row, text="自动定位", command=self.auto_fill_wechat_root).pack(side="left", padx=4)
        self.ttk.Button(root_row, text="一键查找最新订单并导入", command=self.auto_import_latest_orders).pack(side="left", padx=4)
        self.ttk.Label(
            auto_import_panel,
            text=(
                "支持直接填写微信根目录、msg/file 目录，或当月目录。\n"
                "点击一键查找后，系统会自动找到最新订单文件，智能识别订单工作表并导入审核页面。"
            ),
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 8))

        tips = (
            "支持文件：CSV / XLSX\n"
            "建议格式：\n"
            "- 订单：包含 订单号、下单时间、收件人、SKU、数量 等字段\n"
            "- 图书资料：包含 书号、书名、定价、折扣、邮费 等字段\n"
            "- 当前目录下的 表格.xlsx 可直接作为初始化数据源"
        )
        self.ttk.Label(import_panel, text=tips, justify="left").pack(anchor="w", padx=10)

        self.import_log = self.tk.Text(import_panel, height=12, wrap="word")
        self.import_log.pack(fill="both", expand=True, padx=10, pady=(8, 10))

        log_button_frame = self.ttk.Frame(frame)
        log_button_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.ttk.Button(log_button_frame, text="软件操作日志", command=self.open_software_log_dialog).pack(side="left")

        panel = self.ttk.LabelFrame(frame, text="危险操作")
        panel.pack(fill="x", padx=12, pady=(6, 12))

        self.settings_clear_vars = {
            key: self.tk.BooleanVar(value=False)
            for key, _label in SETTINGS_CLEARABLE_ITEMS
        }

        warning_text = (
            "可按项目分别勾选要清空的数据。系统登录账号会保留。\n"
            "如果勾选快递公司记录，系统会在清空后自动重置默认快递公司。此操作不可撤销。"
        )
        self.ttk.Label(panel, text=warning_text, justify="left", foreground="#aa0000").pack(anchor="w", padx=10, pady=10)

        options_frame = self.ttk.Frame(panel)
        options_frame.pack(fill="x", padx=10, pady=(0, 10))
        for idx, (key, label) in enumerate(SETTINGS_CLEARABLE_ITEMS):
            self.ttk.Checkbutton(
                options_frame,
                text=label,
                variable=self.settings_clear_vars[key],
            ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=8, pady=4)

        button_frame = self.ttk.Frame(panel)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.ttk.Button(button_frame, text="全选项目", command=lambda: self.set_settings_clear_selection(True)).pack(side="left")
        self.ttk.Button(button_frame, text="取消全选", command=lambda: self.set_settings_clear_selection(False)).pack(side="left", padx=6)
        self.ttk.Button(button_frame, text="清空已勾选项目", command=self.clear_selected_data_action).pack(side="left", padx=6)

    def create_order_tree(self, parent: Any, height: int = 18) -> Any:
        columns = tuple(key for key, _title, _width in ORDER_TREE_COLUMNS)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        tree = self.ttk.Treeview(parent, columns=columns, show="headings", height=height, selectmode="extended")
        self.tree_checked_items[str(tree)] = set()
        for col, title, width in ORDER_TREE_COLUMNS:
            tree.heading(col, text=title)
            anchor = "w" if col in {"product_name", "remark", "recipient_address", "procurement_remark"} else "center"
            stretch = col in {"product_name", "remark", "recipient_address", "procurement_remark"}
            tree.column(col, width=width, anchor=anchor, stretch=stretch)
        ybar = self.tk.Scrollbar(parent, orient="vertical", width=18, command=tree.yview)
        xbar = self.ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        tree.bind("<Button-1>", lambda event, current_tree=tree: self.on_order_tree_click(event, current_tree), add="+")
        tree.bind("<MouseWheel>", lambda event, current_tree=tree: self.on_order_tree_mousewheel(event, current_tree), add="+")
        return tree

    def handle_tk_exception(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        append_runtime_log("Tkinter 未处理异常", (exc_type, exc_value, exc_traceback))
        self.messagebox.showerror("程序错误", f"软件运行出现错误，已写入日志：\n{APP_RUNTIME_LOG_PATH.name}")

    def get_software_log_text(self) -> str:
        sections: List[str] = ["=== 软件操作日志 ==="]
        operation_logs = self.db.list_operation_logs()
        if operation_logs:
            for row in operation_logs:
                detail = safe_text(row["detail"])
                line = f"[{row['created_at']}] {row['username']} | {row['action']}"
                if detail:
                    line += f" | {detail}"
                sections.append(line)
        else:
            sections.append("暂无操作日志")

        sections.append("")
        sections.append("=== 运行错误日志 ===")
        if APP_RUNTIME_LOG_PATH.exists():
            try:
                sections.append(APP_RUNTIME_LOG_PATH.read_text(encoding="utf-8").strip() or "暂无运行错误日志")
            except Exception:
                sections.append("运行错误日志读取失败")
        else:
            sections.append("暂无运行错误日志")
        return "\n".join(sections)

    def open_software_log_dialog(self) -> None:
        dialog = self.tk.Toplevel(self.root)
        dialog.title("软件操作日志")
        dialog.geometry("980x720")
        dialog.transient(self.root)

        container = self.ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        text = self.tk.Text(container, wrap="word")
        ybar = self.ttk.Scrollbar(container, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=ybar.set)
        text.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")
        text.insert("1.0", self.get_software_log_text())

        button_frame = self.ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=12, pady=(0, 12))

        def refresh_log_text() -> None:
            text.delete("1.0", "end")
            text.insert("1.0", self.get_software_log_text())

        def copy_log_text() -> None:
            self.copy_text(text.get("1.0", "end").strip())

        self.ttk.Button(button_frame, text="刷新日志", command=refresh_log_text).pack(side="left")
        self.ttk.Button(button_frame, text="复制全部日志", command=copy_log_text).pack(side="left", padx=6)
        self.ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side="left", padx=6)
        self.db.log(self.current_user, "查看软件操作日志", "系统设置")

    def on_order_tree_mousewheel(self, event: Any, tree: Any) -> str:
        delta = getattr(event, "delta", 0)
        if not delta:
            return "break"
        step = -1 if delta > 0 else 1
        tree.yview_scroll(step, "units")
        return "break"

    def populate_order_tree(self, tree: Any, rows: List[sqlite3.Row]) -> None:
        checked_items = self.tree_checked_items.setdefault(str(tree), set())
        visible_ids = {str(int(row["id"])) for row in rows}
        checked_items.intersection_update(visible_ids)
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            item_id = str(int(row["id"]))
            checked_flag = "[x]" if item_id in checked_items else "[ ]"
            import_date = safe_text(row["created_at"])[:10]
            tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    checked_flag,
                    import_date,
                    row["order_no"],
                    row["sku"],
                    row["product_name"],
                    row["quantity"],
                    f"{row['list_price']:.2f}",
                    f"{row['discount']:.2f}",
                    f"{row['book_amount']:.2f}",
                    f"{row['shipping_fee']:.2f}",
                    f"{row['receivable_amount']:.2f}",
                    row["remark"],
                    row["courier_company"],
                    row["tracking_no"],
                    row["recipient_name"],
                    row["recipient_address"],
                    row["recipient_phone"],
                    row["settlement_status"],
                    row["invoice_status"],
                    row["procurement_date"],
                    row["procurement_order_no"],
                    f"{row['procurement_cost']:.2f}",
                    row["procurement_remark"],
                    f"{row['profit']:.2f}",
                ),
            )

    def on_order_tree_click(self, event: Any, tree: Any) -> Optional[str]:
        region = tree.identify("region", event.x, event.y)
        column = tree.identify_column(event.x)
        item_id = tree.identify_row(event.y)
        if region != "cell" or column != "#1" or not item_id:
            return None
        self.toggle_tree_checked_item(tree, item_id)
        return "break"

    def toggle_tree_checked_item(self, tree: Any, item_id: str) -> None:
        checked_items = self.tree_checked_items.setdefault(str(tree), set())
        if item_id in checked_items:
            checked_items.remove(item_id)
        else:
            checked_items.add(item_id)
        values = list(tree.item(item_id, "values"))
        if values:
            values[0] = "[x]" if item_id in checked_items else "[ ]"
            tree.item(item_id, values=tuple(values))

    def get_tree_checked_or_selected_ids(self, tree: Any) -> List[str]:
        checked_items = [item_id for item_id in tree.get_children() if item_id in self.tree_checked_items.setdefault(str(tree), set())]
        if checked_items:
            return checked_items
        return list(tree.selection())

    def check_all_tree_items(self, tree: Any) -> None:
        checked_items = self.tree_checked_items.setdefault(str(tree), set())
        checked_items.clear()
        for item_id in tree.get_children():
            checked_items.add(item_id)
            values = list(tree.item(item_id, "values"))
            if values:
                values[0] = "[x]"
                tree.item(item_id, values=tuple(values))

    def clear_tree_checked_items(self, tree: Any) -> None:
        checked_items = self.tree_checked_items.setdefault(str(tree), set())
        checked_items.clear()
        for item_id in tree.get_children():
            values = list(tree.item(item_id, "values"))
            if values:
                values[0] = "[ ]"
                tree.item(item_id, values=tuple(values))

    def batch_update_settlement_status(self, tree: Any = None, target_status: str = "") -> None:
        context = self.settlement_tab_context
        active_tree = tree or context.get("tree")
        if not active_tree:
            return
        selected = self.get_tree_checked_or_selected_ids(active_tree)
        if not selected:
            self.messagebox.showwarning("提示", "请先勾选或选择至少一条订单")
            return

        batch_status_var = context.get("batch_settlement_status_var")
        status = safe_text(target_status) or safe_text(batch_status_var.get() if batch_status_var is not None else "")
        if not status:
            self.messagebox.showwarning("提示", "请先选择结算状态")
            return

        success_count = 0
        failed_orders: List[str] = []
        for item_id in selected:
            order_id = int(item_id)
            row = self.db.get_order(order_id)
            order_no = safe_text(row["order_no"]) if row else str(order_id)
            try:
                self.db.update_order_details(order_id, {"settlement_status": status}, username=self.current_user)
            except ValueError as exc:
                failed_orders.append(f"{order_no}: {exc}")
                continue
            success_count += 1

        self.refresh_all()
        if failed_orders:
            detail = "\n".join(failed_orders[:5])
            if len(failed_orders) > 5:
                detail += f"\n... 另有 {len(failed_orders) - 5} 条失败"
            self.messagebox.showwarning("批量结算状态更新完成", f"成功 {success_count} 条，失败 {len(failed_orders)} 条\n{detail}")
            return

        if status == "已结算":
            self.messagebox.showinfo("批量结算完成", f"已成功结算 {success_count} 条订单")
            return
            self.messagebox.showinfo("批量修改状态完成", f"已成功更新 {success_count} 条订单为“{status}”")

    # ---------- 通用刷新 ----------
    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_orders()
        self.refresh_status_tabs()
        self.refresh_settlement_tab()
        self.refresh_books()
        self.refresh_profit()

    def refresh_dashboard(self) -> None:
        stats = self.db.get_dashboard_stats()
        self.dashboard_vars["total_orders"].set(str(stats["total_orders"]))
        self.dashboard_vars["total_books"].set(str(stats["total_books"]))
        self.dashboard_vars["pending_orders"].set(str(stats["pending_orders"]))
        self.dashboard_vars["gross_profit"].set(f"{stats['gross_profit']:.2f}")
        self.dashboard_vars["total_receivable"].set(f"{stats['total_receivable']:.2f}")
        self.dashboard_text.delete("1.0", "end")
        self.dashboard_text.insert("1.0", self.db.get_profit_summary_text())

    def refresh_orders(self) -> None:
        keyword = self.order_search_var.get().strip()
        rows = self.db.list_orders(
            keyword=keyword,
            order_status=self.order_status_filter_var.get().strip(),
            settlement_status=self.settlement_status_filter_var.get().strip(),
            invoice_status=self.invoice_status_filter_var.get().strip(),
            start_date=self.order_start_date_var.get().strip(),
            end_date=self.order_end_date_var.get().strip(),
        )
        self.order_cache = {int(row["id"]): row for row in rows}
        self.populate_order_tree(self.order_tree, rows)

    def refresh_status_tabs(self) -> None:
        for status in self.status_tab_contexts:
            self.refresh_status_tab(status)

    def refresh_status_tab(self, status: str) -> None:
        context = self.status_tab_contexts.get(status)
        if not context:
            return
        rows = self._list_status_tab_orders(context, status)
        self.populate_order_tree(context["tree"], rows)
        context["count_var"].set(str(len(rows)))

    def refresh_settlement_tab(self) -> None:
        context = self.settlement_tab_context
        if not context:
            return
        rows = self._list_settlement_orders(context)
        self.populate_order_tree(context["tree"], rows)
        context["count_var"].set(str(len(rows)))

    def refresh_books(self) -> None:
        keyword = self.book_search_var.get().strip()
        rows = self.db.list_books(keyword=keyword)
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        for row in rows:
            self.book_tree.insert(
                "",
                "end",
                values=(row["sku"], row["name"], row["price"], row["discount"], row["shipping_fee"], row["publisher"]),
            )

    def refresh_profit(self) -> None:
        self.profit_text.delete("1.0", "end")
        self.profit_text.insert("1.0", self.db.get_profit_summary_text())

    def _list_status_tab_orders(self, context: Dict[str, Any], status: str) -> List[sqlite3.Row]:
        return self.db.list_orders(
            keyword=context["search_var"].get().strip(),
            order_status=status,
            start_date=context["start_date_var"].get().strip(),
            end_date=context["end_date_var"].get().strip(),
        )

    def _list_settlement_orders(self, context: Dict[str, Any]) -> List[sqlite3.Row]:
        rows = self.db.list_orders(
            keyword=context["search_var"].get().strip(),
            settlement_status=context["settlement_status_var"].get().strip(),
            invoice_status=context["invoice_status_var"].get().strip(),
            start_date=context["start_date_var"].get().strip(),
            end_date=context["end_date_var"].get().strip(),
        )
        return [row for row in rows if normalize_order_status(row["order_status"]) in {"发货", "已完成"}]

    def _run_import_and_refresh(self, importer: Callable[[], Any], error_log_message: str) -> None:
        try:
            result = importer()
            if isinstance(result, list):
                for message in result:
                    text = safe_text(message)
                    if text:
                        self.write_import_log(text)
            else:
                text = safe_text(result)
                if text:
                    self.write_import_log(text)
            self.refresh_all()
        except Exception as exc:  # noqa: BLE001
            append_runtime_log(error_log_message, sys.exc_info())
            self.messagebox.showerror("导入失败", str(exc))

    def _choose_file(self) -> Optional[Path]:
        filename = self.filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("Excel / CSV", "*.xlsx *.csv"), ("All files", "*.*")],
        )
        return Path(filename) if filename else None

    def _choose_export_path(self, title: str, initialfile: str) -> Optional[Path]:
        filename = self.filedialog.asksaveasfilename(
            title=title,
            defaultextension=".xlsx",
            initialfile=initialfile,
            filetypes=[("Excel 文件", "*.xlsx"), ("All files", "*.*")],
        )
        return Path(filename) if filename else None

    def _prompt_and_save_export_template(self, scope: str, selected_columns: List[str]) -> None:
        self.save_export_columns(scope, selected_columns, mode="last")
        should_save_template = self.messagebox.askyesno("保存模板", "是否将本次导出列设置保存为模板？")
        if should_save_template:
            self.save_export_columns(scope, selected_columns, mode="template")

    def _finish_export(self, count: int, file_path: Path, action_name: str) -> None:
        self.messagebox.showinfo("导出成功", f"已导出 {count} 条记录到：\n{file_path}")
        self.db.log(self.current_user, action_name, str(file_path))

    # ---------- 导入 ----------
    def write_import_log(self, text: str) -> None:
        self.import_log.insert("end", f"[{now_str()}] {text}\n")
        self.import_log.see("end")

    def save_wechat_root_setting(self) -> None:
        self.db.set_app_setting(WECHAT_ROOT_SETTING_KEY, safe_text(self.wechat_root_var.get()))

    def select_wechat_root_dir(self) -> None:
        selected = self.filedialog.askdirectory(title="选择微信文件根目录")
        if not selected:
            return
        self.wechat_root_var.set(selected)
        self.save_wechat_root_setting()

    def choose_wechat_dir(self, candidates: List[Path]) -> str:
        if not candidates:
            return ""
        if len(candidates) == 1:
            only_path = str(candidates[0])
            self.messagebox.showinfo("提示", f"已自动找到微信文件目录：\n{only_path}")
            return only_path

        dialog = self.tk.Toplevel(self.root)
        dialog.title("选择微信文件目录")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        self.ttk.Label(dialog, text="请选择微信文件目录（最新在最上面）").pack(anchor="w", padx=12, pady=(10, 6))

        list_frame = self.ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=12)
        scrollbar = self.ttk.Scrollbar(list_frame, orient="vertical")
        listbox = self.tk.Listbox(list_frame, width=95, height=min(10, len(candidates)), yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for path in candidates:
            modified_time = datetime.fromtimestamp(get_path_mtime(path)).strftime("%Y-%m-%d %H:%M")
            listbox.insert("end", f"[{modified_time}] {path}")

        if candidates:
            listbox.selection_set(0)
            listbox.activate(0)

        selected_path = {"value": ""}

        def confirm_selection(_event: Any = None) -> None:
            selected_index = listbox.curselection()
            if not selected_index:
                return
            selected_path["value"] = str(candidates[selected_index[0]])
            dialog.destroy()

        button_frame = self.ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=12, pady=10)
        self.ttk.Button(button_frame, text="确定", command=confirm_selection).pack(side="left")
        self.ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=8)

        listbox.bind("<Double-Button-1>", confirm_selection)
        listbox.bind("<Return>", confirm_selection)
        self.root.wait_window(dialog)
        return selected_path["value"]

    def auto_fill_wechat_root(self) -> None:
        candidates = auto_detect_wechat_dirs()
        if not candidates:
            self.messagebox.showwarning("提示", "未自动找到微信文件目录，请手动选择。")
            return
        selected = self.choose_wechat_dir(candidates)
        if not selected:
            return
        self.wechat_root_var.set(selected)
        self.save_wechat_root_setting()

    def select_audit_tab(self) -> None:
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == "审核":
                self.notebook.select(tab_id)
                return

    def auto_import_latest_orders(self) -> None:
        wechat_root = safe_text(self.wechat_root_var.get())
        if not wechat_root:
            candidates = auto_detect_wechat_dirs()
            if not candidates:
                self.messagebox.showwarning("提示", "未自动找到微信文件目录，请先手动填写或选择目录。")
                return
            selected = self.choose_wechat_dir(candidates)
            if not selected:
                return
            wechat_root = selected
            self.wechat_root_var.set(selected)

        self.save_wechat_root_setting()
        latest_file = find_latest_order_file(wechat_root)
        if latest_file is None:
            self.messagebox.showwarning("提示", "当前目录未找到符合条件的最新订单文件。")
            return

        confirmed = self.messagebox.askyesno(
            "确认导入",
            f"已找到最新订单文件：\n{latest_file}\n\n是否立即导入并刷新审核页面？",
        )
        if not confirmed:
            return

        try:
            self.write_import_log(f"自动找到订单文件：{latest_file}")
            msg = self.db.import_orders_from_file(
                latest_file,
                username=self.current_user,
                on_duplicate_order=lambda _order_no: True,
            )
            self.write_import_log(msg)
            self.refresh_all()
            self.select_audit_tab()
            self.db.log(self.current_user, "一键导入最新订单", str(latest_file))
            self.messagebox.showinfo("导入完成", f"{msg}\n\n审核页面已刷新。")
        except Exception:
            append_runtime_log(f"一键导入最新订单失败：{latest_file}", sys.exc_info())
            self.messagebox.showerror("导入失败", traceback.format_exc())

    def import_orders_file(self) -> None:
        path = self._choose_file()
        if not path:
            return

        def ask_duplicate_order(order_no: str) -> bool:
            return self.messagebox.askyesno(
                "发现重复订单号",
                f"系统中已存在订单号：{order_no}\n\n是否跳过这条订单，不覆盖原记录？",
            )

        self._run_import_and_refresh(
            lambda: self.db.import_orders_from_file(
                path,
                username=self.current_user,
                on_duplicate_order=ask_duplicate_order,
            ),
            f"导入订单文件失败：{path}",
        )

    def import_books_file(self) -> None:
        path = self._choose_file()
        if not path:
            return
        self._run_import_and_refresh(
            lambda: self.db.import_books_from_file(path, username=self.current_user),
            f"导入图书资料失败：{path}",
        )

    def import_supplier_file(self) -> None:
        path = self._choose_file()
        if not path:
            return
        self._run_import_and_refresh(
            lambda: self.db.import_supplier_rules_from_file(path, username=self.current_user),
            f"导入供应商规则失败：{path}",
        )

    def import_default_sample(self) -> None:
        if not DEFAULT_SAMPLE_FILE.exists():
            self.messagebox.showwarning("提示", f"未找到示例文件：{DEFAULT_SAMPLE_FILE.name}")
            return
        self._run_import_and_refresh(
            lambda: self.db.import_sample_workbook(DEFAULT_SAMPLE_FILE, username=self.current_user),
            f"导入示例文件失败：{DEFAULT_SAMPLE_FILE}",
        )

    def set_settings_clear_selection(self, checked: bool) -> None:
        if not hasattr(self, "settings_clear_vars"):
            return
        for var in self.settings_clear_vars.values():
            var.set(checked)

    def clear_selected_data_action(self) -> None:
        selected_items = [key for key, var in self.settings_clear_vars.items() if bool(var.get())]
        if not selected_items:
            self.messagebox.showwarning("提示", "请先勾选要清空的项目")
            return

        selected_labels = [label for key, label in SETTINGS_CLEARABLE_ITEMS if key in selected_items]
        confirmed = self.messagebox.askyesno(
            "确认清除",
            f"确定要清除以下数据吗？\n{'、'.join(selected_labels)}\n\n此操作不可撤销。",
        )
        if not confirmed:
            return

        verify_text = self.simpledialog.askstring(
            "二次确认",
            "请输入“清空”以确认执行：",
            parent=self.root,
        )
        if safe_text(verify_text) != "清空":
            self.messagebox.showwarning("已取消", "未输入正确确认文字，操作已取消")
            return

        self.db.clear_business_data(selected_items, self.current_user)
        self.order_cache.clear()
        self.tree_checked_items.clear()
        self.refresh_all()
        self.refresh_courier_company_options()
        self.messagebox.showinfo("清除完成", f"已清空：{'、'.join(selected_labels)}")

    # ---------- 订单编辑 ----------
    def on_order_selected(self, _event: Any = None) -> None:
        selected = self.order_tree.selection()
        if not selected:
            return
        order_id = int(selected[0])
        row = self.db.get_order(order_id)
        if not row:
            return
        for key in self.edit_vars:
            if key == "procurement_date":
                self.edit_vars[key].set(safe_text(row[key]) or today_str())
            else:
                self.edit_vars[key].set(safe_text(row[key]))
        if self.main_order_status_combo is not None:
            options = get_allowed_order_status_options(row["order_status"])
            self.main_order_status_combo.configure(values=options)
            if self.edit_vars["order_status"].get() not in options:
                self.edit_vars["order_status"].set(options[0])

    def save_selected_order(self) -> None:
        selected = self.order_tree.selection()
        if not selected:
            self.messagebox.showwarning("提示", "请先选择一条订单")
            return
        order_id = int(selected[0])
        payload = {key: var.get() for key, var in self.edit_vars.items()}
        try:
            self.db.update_order_details(order_id, payload, username=self.current_user)
        except ValueError as exc:
            self.messagebox.showwarning("保存失败", str(exc))
            return
        self.refresh_courier_company_options()
        self.messagebox.showinfo("成功", "订单信息已保存")
        self.refresh_all()

    def _get_tree_source_status(self, tree: Any) -> str:
        for status, context in self.status_tab_contexts.items():
            if context.get("tree") is tree:
                return status
        if self.settlement_tab_context.get("tree") is tree:
            return "结算"
        return ""

    def _get_batch_status_feedback(self, source_status: str, success_count: int, failed_count: int = 0) -> tuple[str, str]:
        if failed_count:
            if source_status == "审核":
                return "批量审核完成", f"已审核 {success_count} 条，失败 {failed_count} 条"
            if source_status == "配货":
                return "批量确认配货完成", f"已确认配货 {success_count} 条，失败 {failed_count} 条"
            if source_status == "发货":
                return "批量确认发货完成", f"已确认发货 {success_count} 条，失败 {failed_count} 条"
            return "批量修改完成", f"成功 {success_count} 条，失败 {failed_count} 条"

        if source_status == "审核":
            return "批量审核完成", f"已审核 {success_count} 条订单，自动进入配货环节"
        if source_status == "配货":
            return "批量确认配货完成", f"已确认配货 {success_count} 条订单，自动进入发货环节"
        if source_status == "发货":
            return "批量确认发货完成", f"已确认发货 {success_count} 条订单，订单已从当前页面移除"
        return "批量确认完成", f"已成功确认 {success_count} 条订单状态"

    def _get_order_dialog_config(self, source_status: str) -> tuple[List[str], List[tuple[str, str]]]:
        if source_status == "审核":
            return (
                ["procurement_date", "procurement_order_no", "procurement_cost", "procurement_remark"],
                [
                    ("采购日期", "procurement_date"),
                    ("采购单号", "procurement_order_no"),
                    ("采购成本", "procurement_cost"),
                    ("采购备注", "procurement_remark"),
                ],
            )
        if source_status == "配货":
            return (
                ["courier_company", "tracking_no", "remark"],
                [
                    ("快递公司", "courier_company"),
                    ("物流单号", "tracking_no"),
                    ("备注", "remark"),
                ],
            )
        if not source_status:
            return ([], [])
        return (
            [
                "remark",
                "courier_company",
                "tracking_no",
                "procurement_date",
                "procurement_order_no",
                "procurement_cost",
                "procurement_remark",
                "order_status",
            ],
            [
                ("备注", "remark"),
                ("快递公司", "courier_company"),
                ("物流单号", "tracking_no"),
                ("采购日期", "procurement_date"),
                ("采购单号", "procurement_order_no"),
                ("采购成本", "procurement_cost"),
                ("采购备注", "procurement_remark"),
                ("订单状态", "order_status"),
            ],
        )

    def _apply_order_dialog_status_payload(self, payload: Dict[str, Any], source_status: str) -> None:
        if source_status == "审核":
            payload["procurement_date"] = safe_text(payload.get("procurement_date")) or today_str()
            payload["order_status"] = "配货"
        elif source_status == "配货":
            payload["order_status"] = "发货"

    def _show_order_dialog_save_error(self, source_status: str, message: str) -> None:
        if source_status == "审核":
            self.messagebox.showwarning("确认审核失败", message)
            return
        if source_status == "配货":
            self.messagebox.showwarning("确认配货失败", message)
            return
        self.messagebox.showwarning("保存失败", message)

    def _sync_order_dialog_to_main_form(self, dialog_vars: Dict[str, Any], source_status: str) -> None:
        for key, var in dialog_vars.items():
            self.edit_vars[key].set(var.get())
        if source_status == "审核":
            self.edit_vars["order_status"].set("配货")
        elif source_status == "配货":
            self.edit_vars["order_status"].set("发货")

    def _show_order_dialog_save_success(self, source_status: str) -> None:
        if source_status == "审核":
            self.messagebox.showinfo("审核完成", "订单已确认审核，自动提交到配货页面")
            return
        if source_status == "配货":
            self.messagebox.showinfo("配货完成", "订单已确认配货，自动提交到发货页面")
            return
        self.messagebox.showinfo("成功", "订单信息已保存")

    def _get_order_dialog_save_button_text(self, source_status: str) -> str:
        if source_status == "审核":
            return "确认审核"
        if source_status == "配货":
            return "确认配货"
        if source_status:
            return "保存"
        return ""

    def batch_update_order_status(self, tree: Any = None) -> None:
        active_tree = tree or self.order_tree
        selected = self.get_tree_checked_or_selected_ids(active_tree)
        if not selected:
            self.messagebox.showwarning("提示", "请先勾选或选择至少一条订单")
            return

        source_status = self._get_tree_source_status(active_tree)

        success_count = 0
        failed_orders: List[str] = []
        for item_id in selected:
            order_id = int(item_id)
            row = self.db.get_order(order_id)
            order_no = safe_text(row["order_no"]) if row else str(order_id)
            current_status = normalize_order_status(row["order_status"]) if row else ""
            target_status = get_next_order_status(current_status)
            if not row or target_status == current_status:
                failed_orders.append(f"{order_no}: 当前已是最终状态，不能继续确认")
                continue
            try:
                self.db.update_order_details(order_id, {"order_status": target_status}, username=self.current_user)
            except ValueError as exc:
                failed_orders.append(f"{order_no}: {exc}")
                continue
            success_count += 1

        self.refresh_all()
        if failed_orders:
            detail = "\n".join(failed_orders[:5])
            if len(failed_orders) > 5:
                detail += f"\n... 另有 {len(failed_orders) - 5} 条失败"
            title, summary = self._get_batch_status_feedback(source_status, success_count, len(failed_orders))
            self.messagebox.showwarning(title, f"{summary}\n{detail}")
            return
        title, summary = self._get_batch_status_feedback(source_status, success_count)
        self.messagebox.showinfo(title, summary)

    def batch_return_orders(self, tree: Any = None, target_status: str = "审核") -> None:
        active_tree = tree or self.order_tree
        selected = self.get_tree_checked_or_selected_ids(active_tree)
        if not selected:
            self.messagebox.showwarning("提示", "请先勾选或选择至少一条订单")
            return

        source_status = self._get_tree_source_status(active_tree)
        allowed_targets = {
            "配货": {"审核"},
            "发货": {"配货", "审核"},
        }
        if target_status not in allowed_targets.get(source_status, set()):
            self.messagebox.showwarning("提示", f"当前页面的订单不支持打回到{target_status}")
            return

        success_count = 0
        failed_orders: List[str] = []
        for item_id in selected:
            order_id = int(item_id)
            row = self.db.get_order(order_id)
            order_no = safe_text(row["order_no"]) if row else str(order_id)
            current_status = normalize_order_status(row["order_status"]) if row else ""
            if not row or current_status != source_status:
                failed_orders.append(f"{order_no}: 当前不是{source_status}状态，不能打回{target_status}")
                continue
            try:
                self.db.update_order_details(order_id, {"order_status": target_status}, username=self.current_user)
            except ValueError as exc:
                failed_orders.append(f"{order_no}: {exc}")
                continue
            success_count += 1

        self.refresh_all()
        if failed_orders:
            detail = "\n".join(failed_orders[:5])
            if len(failed_orders) > 5:
                detail += f"\n... 另有 {len(failed_orders) - 5} 条失败"
            self.messagebox.showwarning(
                f"批量打回{target_status}完成",
                f"已打回 {success_count} 条到{target_status}，失败 {len(failed_orders)} 条\n{detail}",
            )
            return
        self.messagebox.showinfo(f"批量打回{target_status}完成", f"已成功打回 {success_count} 条订单到{target_status}页面")

    def open_date_picker(self, target_var: Any, parent: Any) -> None:
        raw_value = safe_text(target_var.get())
        try:
            selected_date = datetime.strptime(raw_value[:10], "%Y-%m-%d") if raw_value else datetime.now()
        except ValueError:
            selected_date = datetime.now()

        dialog = self.tk.Toplevel(parent)
        dialog.title("选择日期")
        dialog.geometry("320x180")
        dialog.transient(parent)
        dialog.grab_set()

        frame = self.ttk.LabelFrame(dialog, text="采购日期")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        year_var = self.tk.StringVar(value=str(selected_date.year))
        month_var = self.tk.StringVar(value=f"{selected_date.month:02d}")
        day_var = self.tk.StringVar(value=f"{selected_date.day:02d}")

        self.ttk.Label(frame, text="年").grid(row=0, column=0, padx=8, pady=12, sticky="e")
        self.ttk.Spinbox(frame, from_=2020, to=2100, textvariable=year_var, width=8).grid(row=0, column=1, padx=8, pady=12, sticky="w")
        self.ttk.Label(frame, text="月").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        self.ttk.Spinbox(frame, from_=1, to=12, textvariable=month_var, width=8, format="%02.0f").grid(row=1, column=1, padx=8, pady=8, sticky="w")
        self.ttk.Label(frame, text="日").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        self.ttk.Spinbox(frame, from_=1, to=31, textvariable=day_var, width=8, format="%02.0f").grid(row=2, column=1, padx=8, pady=8, sticky="w")

        button_frame = self.ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=12, pady=(0, 12))

        def apply_date() -> None:
            try:
                dt = datetime(int(year_var.get()), int(month_var.get()), int(day_var.get()))
            except ValueError:
                self.messagebox.showwarning("提示", "请输入有效日期")
                return
            target_var.set(dt.strftime("%Y-%m-%d"))
            dialog.destroy()

        self.ttk.Button(button_frame, text="今天", command=lambda: target_var.set(today_str())).pack(side="left")
        self.ttk.Button(button_frame, text="确定", command=apply_date).pack(side="left", padx=8)
        self.ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="left", padx=8)

    def on_tree_order_double_click(self, tree: Any) -> None:
        selected = tree.selection()
        if not selected:
            return
        source_status = self._get_tree_source_status(tree)
        self.open_order_edit_dialog(int(selected[0]), source_status=source_status)

    def open_order_edit_dialog(self, order_id: int, source_status: str = "") -> None:
        row = self.db.get_order(order_id)
        if not row:
            self.messagebox.showwarning("提示", "未找到该订单记录")
            return

        if self.order_edit_window and self.order_edit_window.winfo_exists():
            self.order_edit_window.destroy()

        dialog = self.tk.Toplevel(self.root)
        dialog.title(f"编辑订单 - {safe_text(row['order_no'])}")
        dialog.geometry("980x760")
        dialog.transient(self.root)
        dialog.grab_set()
        self.order_edit_window = dialog

        container = self.ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        info_form = self.ttk.LabelFrame(container, text="订单全部信息")
        info_form.pack(fill="x", pady=(0, 10))

        recipient_summary = " , ".join(
            [
                safe_text(row["recipient_address"]) or "-",
                safe_text(row["recipient_phone"]) or "-",
                safe_text(row["recipient_name"]) or "-",
            ]
        )
        info_fields = [
            {"label": "导入时间", "value": safe_text(row["created_at"])[:10], "copy": None},
            {"label": "订单号", "value": safe_text(row["order_no"]), "copy": safe_text(row["order_no"])},
            {"label": "SKU编码", "value": safe_text(row["sku"]), "copy": safe_text(row["sku"])},
            {"label": "商品名称", "value": safe_text(row["product_name"]), "copy": safe_text(row["product_name"])},
            {"label": "商品数量", "value": safe_text(row["quantity"]), "copy": None},
            {"label": "定价", "value": f"{row['list_price']:.2f}", "copy": None},
            {"label": "折扣", "value": f"{row['discount']:.2f}", "copy": None},
            {"label": "应收书款", "value": f"{row['book_amount']:.2f}", "copy": None},
            {"label": "应收运费", "value": f"{row['shipping_fee']:.2f}", "copy": None},
            {"label": "应收金额", "value": f"{row['receivable_amount']:.2f}", "copy": None},
            {"label": "备注", "value": safe_text(row["remark"]), "copy": None},
            {"label": "收件信息", "value": recipient_summary, "copy": recipient_summary},
            {"label": "快递公司", "value": safe_text(row["courier_company"]), "copy": None},
            {"label": "物流单号", "value": safe_text(row["tracking_no"]), "copy": None},
            {"label": "结算状态", "value": safe_text(row["settlement_status"]), "copy": None},
            {"label": "发票状态", "value": safe_text(row["invoice_status"]), "copy": None},
            {"label": "采购日期", "value": safe_text(row["procurement_date"]) or today_str(), "copy": None},
            {"label": "采购订单号", "value": safe_text(row["procurement_order_no"]), "copy": safe_text(row["procurement_order_no"])} ,
            {"label": "采购成本", "value": f"{row['procurement_cost']:.2f}", "copy": None},
            {"label": "采购备注", "value": safe_text(row["procurement_remark"]), "copy": None},
            {"label": "订单状态", "value": safe_text(row["order_status"]), "copy": None},
            {"label": "状态更新时间", "value": safe_text(row["order_status_updated_at"]), "copy": None},
            {"label": "利润", "value": f"{row['profit']:.2f}", "copy": None},
        ]
        for idx, item in enumerate(info_fields):
            row_index = idx // 2
            col_index = (idx % 2) * 3
            self.ttk.Label(info_form, text=item["label"]).grid(row=row_index, column=col_index, sticky="ne", padx=8, pady=6)
            display = self.ttk.Label(info_form, text=item["value"] or "-", justify="left", wraplength=290)
            display.grid(row=row_index, column=col_index + 1, sticky="nw", padx=8, pady=6)
            if item["copy"]:
                self.ttk.Button(
                    info_form,
                    text="复制",
                    command=lambda text=item["copy"]: self.copy_text(text),
                ).grid(row=row_index, column=col_index + 2, sticky="w", padx=4, pady=6)

        form_title = "编辑字段" if source_status else "查看说明"
        form = self.ttk.LabelFrame(container, text=form_title)

        form.pack(fill="x", pady=6)

        editable_keys, fields = self._get_order_dialog_config(source_status)

        dialog_vars = {
            key: self.tk.StringVar(value=(safe_text(row[key]) or today_str()) if key == "procurement_date" else safe_text(row[key]))
            for key in editable_keys
        }
        if not fields:
            self.ttk.Label(
                form,
                text="总订单页面仅支持查看，不提供编辑。请到对应业务页面操作。",
                justify="left",
                foreground="#666666",
            ).pack(anchor="w", padx=10, pady=10)
        for idx, (label, key) in enumerate(fields):
            row_index = idx // 2
            col_index = (idx % 2) * 2
            self.ttk.Label(form, text=label).grid(row=row_index, column=col_index, sticky="e", padx=8, pady=8)
            if key == "courier_company":
                self.ttk.Combobox(
                    form,
                    textvariable=dialog_vars[key],
                    values=self.get_courier_company_options(),
                    width=29,
                    state="normal",
                ).grid(row=row_index, column=col_index + 1, sticky="w", padx=8, pady=8)
            elif key == "settlement_status":
                self.ttk.Combobox(
                    form,
                    textvariable=dialog_vars[key],
                    values=SETTLEMENT_STATUS_EDIT_OPTIONS,
                    width=29,
                    state="readonly",
                ).grid(row=row_index, column=col_index + 1, sticky="w", padx=8, pady=8)
            elif key == "invoice_status":
                self.ttk.Combobox(
                    form,
                    textvariable=dialog_vars[key],
                    values=INVOICE_STATUS_EDIT_OPTIONS,
                    width=29,
                    state="readonly",
                ).grid(row=row_index, column=col_index + 1, sticky="w", padx=8, pady=8)
            elif key == "order_status":
                dialog_order_status_combo = self.ttk.Combobox(
                    form,
                    textvariable=dialog_vars[key],
                    values=get_allowed_order_status_options(row["order_status"]),
                    width=29,
                    state="readonly",
                )
                dialog_order_status_combo.grid(row=row_index, column=col_index + 1, sticky="w", padx=8, pady=8)
            elif key == "procurement_date":
                date_frame = self.ttk.Frame(form)
                date_frame.grid(row=row_index, column=col_index + 1, sticky="w", padx=8, pady=8)
                self.ttk.Entry(date_frame, textvariable=dialog_vars[key], width=20).pack(side="left")
                self.ttk.Button(
                    date_frame,
                    text="选择日期",
                    command=lambda var=dialog_vars[key], parent=dialog: self.open_date_picker(var, parent),
                ).pack(side="left", padx=6)
            else:
                entry_width = 44 if key in {"remark"} else 32
                self.ttk.Entry(form, textvariable=dialog_vars[key], width=entry_width).grid(
                    row=row_index,
                    column=col_index + 1,
                    sticky="w",
                    padx=8,
                    pady=8,
                )

        button_frame = self.ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=12, pady=(0, 12))

        def save_dialog_order() -> None:
            payload = {key: var.get() for key, var in dialog_vars.items()}
            self._apply_order_dialog_status_payload(payload, source_status)
            try:
                self.db.update_order_details(order_id, payload, username=self.current_user)
            except ValueError as exc:
                self._show_order_dialog_save_error(source_status, str(exc))
                return
            self._sync_order_dialog_to_main_form(dialog_vars, source_status)
            self.refresh_courier_company_options()
            dialog.destroy()
            self.refresh_all()
            self._show_order_dialog_save_success(source_status)

        def return_to_audit() -> None:
            payload = {key: var.get() for key, var in dialog_vars.items()}
            payload["order_status"] = "审核"
            try:
                self.db.update_order_details(order_id, payload, username=self.current_user)
            except ValueError as exc:
                self.messagebox.showwarning("打回审核失败", str(exc))
                return
            self._sync_order_dialog_to_main_form(dialog_vars, "")
            self.edit_vars["order_status"].set("审核")
            self.refresh_courier_company_options()
            dialog.destroy()
            self.refresh_all()
            self.messagebox.showinfo("打回审核完成", "订单已打回审核页面")

        def return_to_status(target_status: str) -> None:
            payload = {key: var.get() for key, var in dialog_vars.items()}
            payload["order_status"] = target_status
            try:
                self.db.update_order_details(order_id, payload, username=self.current_user)
            except ValueError as exc:
                self.messagebox.showwarning(f"打回{target_status}失败", str(exc))
                return
            self._sync_order_dialog_to_main_form(dialog_vars, "")
            self.edit_vars["order_status"].set(target_status)
            self.refresh_courier_company_options()
            dialog.destroy()
            self.refresh_all()
            self.messagebox.showinfo(f"打回{target_status}完成", f"订单已打回{target_status}页面")

        save_button_text = self._get_order_dialog_save_button_text(source_status)
        if save_button_text:
            self.ttk.Button(button_frame, text=save_button_text, command=save_dialog_order).pack(side="left")
        if source_status == "配货":
            self.ttk.Button(button_frame, text="打回审核", command=return_to_audit).pack(side="left", padx=8)
        if source_status == "发货":
            self.ttk.Button(button_frame, text="打回配货", command=lambda: return_to_status("配货")).pack(side="left", padx=8)
            self.ttk.Button(button_frame, text="打回审核", command=lambda: return_to_status("审核")).pack(side="left", padx=8)
        self.ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side="left", padx=8)

    def export_orders(self) -> None:
        selected_columns = self.get_selected_export_columns("orders")
        if not selected_columns:
            self.messagebox.showwarning("提示", "请至少勾选一列后再导出")
            return
        export_path = self._choose_export_path(
            title="导出订单",
            initialfile=f"知护订单导出_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )
        if not export_path:
            return
        count = self.db.export_orders_to_excel(
            export_path,
            keyword=self.order_search_var.get().strip(),
            order_status=self.order_status_filter_var.get().strip(),
            settlement_status=self.settlement_status_filter_var.get().strip(),
            invoice_status=self.invoice_status_filter_var.get().strip(),
            start_date=self.order_start_date_var.get().strip(),
            end_date=self.order_end_date_var.get().strip(),
            selected_columns=selected_columns,
        )
        self._prompt_and_save_export_template("orders", selected_columns)
        self._finish_export(count, export_path, "导出订单")

    def export_status_tab_orders(self, status: str) -> None:
        context = self.status_tab_contexts.get(status)
        if not context:
            return
        scope = "status_shipment" if status == "发货" else ""
        selected_columns: Optional[List[str]] = None
        if scope:
            selected_columns = self.get_selected_export_columns(scope)
            if not selected_columns:
                self.messagebox.showwarning("提示", "请至少勾选一列后再导出")
                return
        # 发货页面导出默认文件名为：知护回告_当天日期
        if status == "发货":
            default_name = f"知护回告_{datetime.now().strftime('%Y%m%d')}.xlsx"
        else:
            default_name = f"知护{status}订单导出_{datetime.now().strftime('%Y%m%d')}.xlsx"
        export_path = self._choose_export_path(title=f"导出{status}页面订单", initialfile=default_name)
        if not export_path:
            return
        rows = self._list_status_tab_orders(context, status)
        count = self.db.export_rows_to_excel(export_path, rows, sheet_name=status, selected_columns=selected_columns)
        if scope and selected_columns is not None:
            self._prompt_and_save_export_template(scope, selected_columns)
        self._finish_export(count, export_path, f"导出{status}订单")

    def export_settlement_tab_orders(self) -> None:
        context = self.settlement_tab_context
        if not context:
            return
        selected_columns = self.get_selected_export_columns("settlement")
        if not selected_columns:
            self.messagebox.showwarning("提示", "请至少勾选一列后再导出")
            return
        export_path = self._choose_export_path(
            title="导出结算页面订单",
            initialfile=f"知护结算订单导出_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )
        if not export_path:
            return
        rows = self._list_settlement_orders(context)
        count = self.db.export_rows_to_excel(export_path, rows, sheet_name="结算", selected_columns=selected_columns)
        self._prompt_and_save_export_template("settlement", selected_columns)
        self._finish_export(count, export_path, "导出结算订单")

    # ---------- 图书保存 ----------
    def save_book(self) -> None:
        data = {key: var.get() for key, var in self.book_vars.items()}
        if not data.get("sku"):
            self.messagebox.showwarning("提示", "SKU/书号不能为空")
            return
        self.db.upsert_book(data, username=self.current_user)
        self.db.log(self.current_user, "保存图书资料", data.get("sku", ""))
        self.messagebox.showinfo("成功", "图书资料已保存")
        self.refresh_books()

    def run(self) -> None:
        self.root.mainloop()


# =========================
# 命令行入口
# =========================
def run_smoke_test(db: DatabaseManager, seed_file: Optional[str]) -> int:
    if seed_file:
        path = Path(seed_file)
        if path.exists():
            print("[SmokeTest] 正在导入示例文件：", path)
            for msg in db.import_sample_workbook(path, username="system"):
                print("[SmokeTest]", msg)
        else:
            print("[SmokeTest] 未找到示例文件：", path)

    stats = db.get_dashboard_stats()
    print("[SmokeTest] 统计结果：")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    rows = db.list_orders()
    if rows:
        first = rows[0]
        print("[SmokeTest] 最新订单示例：")
        print(f"  - 订单号: {first['order_no']}")
        print(f"  - 商品: {first['product_name']}")
        print(f"  - 应收金额: {first['receivable_amount']}")
        print(f"  - 粗算毛利: {first['profit']}")
    else:
        print("[SmokeTest] 当前数据库暂无订单。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--smoke-test", action="store_true", help="只做数据库初始化与数据导入验证，不启动界面")
    parser.add_argument("--seed-demo", nargs="?", const=str(DEFAULT_SAMPLE_FILE), help="导入示例 Excel 文件")
    args = parser.parse_args()

    db = DatabaseManager(DB_PATH)
    try:
        try:
            if args.smoke_test:
                return run_smoke_test(db, args.seed_demo)

            gui = OrderManagerGUI(db)
            if getattr(gui, "root", None):
                gui.run()
            return 0
        except Exception:
            append_runtime_log("程序主入口未处理异常", sys.exc_info())
            raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
