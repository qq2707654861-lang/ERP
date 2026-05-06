# -*- coding: utf-8 -*-
"""
订单Excel解析
Inspired by Claude Code architecture - focused module for parsing
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import zipfile
from xml.etree import ElementTree as ET

from src.utils.helpers import (
    col_to_num,
    excel_date_to_text,
    pick_value,
    normalize_header_text,
    clean_date_text,
    to_float,
    to_int,
    safe_text,
    calculate_receivable_shipping_fee,
)

# Constants (imported from constants module)
from src import constants

EXCEL_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def get_order_header_alias_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for canonical, aliases in constants.SMART_ORDER_HEADER_ALIASES.items():
        for alias in aliases:
            normalized = normalize_header_text(alias)
            if normalized:
                mapping[normalized] = canonical
        mapping[normalize_header_text(canonical)] = canonical
    return mapping


def find_best_order_sheet(sheets: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Score sheets by how many required headers they have
    required = set(constants.SMART_ORDER_REQUIRED_HEADERS)
    best_sheet = None
    best_score = 0
    best_mapping = None
    best_col_mapping = None
    missing = None

    for sheet in sheets:
        if not sheet["rows"] or len(sheet["rows"]) < 2:
            continue

        header_row = sheet["rows"][0]
        found_required = 0
        current_mapping = get_order_header_alias_mapping()
        col_mapping: Dict[str, int] = {}
        missing_required: List[str] = []

        for col_idx, cell in enumerate(header_row):
            cell_text = safe_text(cell.get("v", ""))
            if not cell_text:
                continue
            normalized = normalize_header_text(cell_text)
            if normalized in current_mapping:
                canonical = current_mapping[normalized]
                col_mapping[canonical] = col_idx
                if canonical in required:
                    found_required += 1

        for req in required:
            if req not in col_mapping:
                missing_required.append(req)

        score = found_required / len(required)
        if score > best_score:
            best_score = score
            best_sheet = sheet
            best_mapping = current_mapping
            best_col_mapping = col_mapping
            missing = missing_required

    return {
        "sheet": best_sheet,
        "mapping": best_mapping,
        "col_mapping": best_col_mapping,
        "missing_headers": missing,
        "score": best_score,
        "missing_headers_count": len(missing) if missing else 0,
    }


def read_xlsx_raw_sheets(file_path: Path) -> List[Dict[str, Any]]:
    sheets: List[Dict[str, Any]] = []

    with zipfile.ZipFile(file_path, "r") as zf:
        # Read shared strings
        shared_strings: Dict[int, str] = {}
        if "xl/sharedStrings.xml" in zf.namelist():
            ss_tree = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_tree.findall(EXCEL_NS["a"] + "si"):
                t_elements = si.findall(EXCEL_NS["a"] + "t")
                text_parts = [t.text for t in t_elements if t.text]
                shared_strings[len(shared_strings)] = "".join(text_parts)

        # Get sheet list
        workbook_rels = ET.fromstring(zf.read("_rels/.rels"))
        workbook_path = None
        for relationship in workbook_rels.findall("Relationship"):
            if relationship.attrib.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument":
                workbook_path = relationship.attrib.get("Target")
                break

        if not workbook_path:
            return sheets

        workbook_xml = zf.read("xl/" + workbook_path.split("/")[-1])
        workbook_tree = ET.fromstring(workbook_xml)
        sheets_element = workbook_tree.find(EXCEL_NS["a"] + "sheets")
        if sheets_element is None:
            return sheets

        sheet_idx = 0
        for sheet_element in sheets_element.findall(EXCEL_NS["a"] + "sheet"):
            sheet_name = sheet_element.attrib.get("name", f"Sheet{sheet_idx + 1}")
            sheet_id = sheet_element.attrib.get("sheetId", str(sheet_idx + 1))
            sheet_idx += 1

            # Find the relationship for this sheet
            sheet_rels_path = f"xl/worksheets/_rels/sheet{sheet_id}.xml.rels"
            sheet_data_path = f"xl/worksheets/sheet{sheet_id}.xml"

            if sheet_data_path not in zf.namelist():
                continue

            sheet_tree = ET.fromstring(zf.read(sheet_data_path))
            rows: List[Dict[str, Any]] = []

            for row in sheet_tree.findall(EXCEL_NS["a"] + "row"):
                row_data: Dict[str, Any] = {}
                for cell in row.findall(EXCEL_NS["a"] + "c"):
                    cell_value = None
                    cell_v = cell.find(EXCEL_NS["a"] + "v")
                    if cell_v is not None and cell_v.text:
                        if "t" in cell.attrib and cell.attrib["t"] == "s":
                            # shared string
                            idx = int(cell_v.text)
                            cell_value = shared_strings.get(idx, cell_v.text)
                        else:
                            cell_value = cell_v.text
                    row_data[cell.attrib.get("r", "")] = {"r": cell.attrib.get("r", ""), "v": cell_value}
                rows.append(row_data)

            sheets.append({
                "name": sheet_name,
                "id": sheet_id,
                "rows": rows,
            })

    return sheets


def parse_smart_order_rows(
    analysis: Dict[str, Any],
    default_shipping_fee: float = 6.0
) -> List[Dict[str, Any]]:
    sheet = analysis["sheet"]
    col_mapping = analysis["col_mapping"]
    if not sheet or not col_mapping:
        return []

    orders: List[Dict[str, Any]] = []
    # Skip header row (first row)
    for row in sheet["rows"][1:]:
        order: Dict[str, Any] = {}
        for canonical, col_idx in col_mapping.items():
            # row is list of cells, get by position
            if col_idx >= len(row):
                order[canonical] = None
                continue
            cell = list(row.values())[col_idx]
            cell_v = cell.get("v")
            if canonical == "订单下单时间":
                order["created_at"] = clean_date_text(cell_v)
            elif canonical == "订单号":
                order["order_no"] = safe_text(cell_v)
            elif canonical == "SKU编码(自定义)":
                order["sku"] = safe_text(cell_v)
            elif canonical == "商品名称":
                order["product_name"] = safe_text(cell_v)
            elif canonical == "商品数量":
                order["quantity"] = to_int(cell_v, 1)
            elif canonical == "定价":
                order["list_price"] = to_float(cell_v, 0.0)
            elif canonical == "折扣":
                order["discount"] = to_float(cell_v, 1.0)
            elif canonical == "应收书款":
                order["book_amount"] = to_float(cell_v, 0.0)
            elif canonical == "应收运费":
                order["shipping_fee"] = to_float(cell_v, calculate_receivable_shipping_fee(
                    order.get("book_amount", 0),
                    order.get("recipient_address", ""),
                    default_shipping_fee
                ))
            elif canonical == "收件人姓名":
                order["recipient_name"] = safe_text(cell_v)
            elif canonical == "收件人地址":
                order["recipient_address"] = safe_text(cell_v)
            elif canonical == "收件人手机":
                order["recipient_phone"] = safe_text(cell_v)
            elif canonical == "快递公司":
                order["courier_company"] = safe_text(cell_v)
            elif canonical == "单号":
                order["tracking_no"] = safe_text(cell_v)
            elif canonical == "结算状态":
                from src.utils.status import normalize_settlement_status
                order["settlement_status"] = normalize_settlement_status(cell_v)
            elif canonical == "发票状态":
                order["invoice_status"] = safe_text(cell_v)
            else:
                order[canonical] = safe_text(cell_v)

        # Calculate receivable amount if not present
        if "receivable_amount" not in order or not order["receivable_amount"]:
            book_amount = to_float(order.get("book_amount", 0.0), 0.0)
            shipping_fee = to_float(order.get("shipping_fee", 0.0), 0.0)
            order["receivable_amount"] = round(book_amount + shipping_fee, 2)

        if "created_at" not in order or not order["created_at"]:
            from src.utils.helpers import today_str
            order["created_at"] = today_str()

        orders.append(order)

    return orders


def is_valid_order_xlsx(file_path: Path) -> bool:
    try:
        analysis = find_best_order_sheet(read_xlsx_raw_sheets(file_path))
        return not analysis["missing_headers"]
    except Exception:
        return False
