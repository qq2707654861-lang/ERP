# -*- coding: utf-8 -*-
"""
文件读取 — CSV / XLSX，智能表头识别
从原 ERP.py 抽取，无修改核心逻辑
"""
from __future__ import annotations

import csv
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from .config import EXCEL_NS, SMART_ORDER_HEADER_ALIASES, SMART_ORDER_REQUIRED_HEADERS
from .utils import (
    col_to_num,
    normalize_header_text,
    safe_text,
)


# ---------- CSV ----------
def read_csv_rows(file_path: Path) -> List[Dict[str, str]]:
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return [{safe_text(k): safe_text(v) for k, v in row.items()} for row in reader]
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"CSV 读取失败：{last_error}")


# ---------- XLSX（无第三方依赖） ----------
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


def _build_rows_from_headers_by_col(
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


def read_xlsx_sheets(file_path: Path) -> Dict[str, List[Dict[str, str]]]:
    result: Dict[str, List[Dict[str, str]]] = {}
    for name, raw_rows in read_xlsx_raw_sheets(file_path).items():
        if not raw_rows:
            result[name] = []
            continue
        header_row = raw_rows[0]
        ordered_cols = sorted(header_row.keys(), key=col_to_num)
        headers = {col: safe_text(header_row.get(col)) for col in ordered_cols if safe_text(header_row.get(col))}
        result[name] = _build_rows_from_headers_by_col(raw_rows, headers, 1)
    return result


def get_sheet_rows(sheets: Dict[str, List[Dict[str, str]]], preferred_sheet_name: str) -> List[Dict[str, str]]:
    if preferred_sheet_name in sheets:
        return sheets[preferred_sheet_name]
    return next(iter(sheets.values()), [])


def read_table_file(file_path: Path) -> Dict[str, List[Dict[str, str]]]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return {file_path.stem: read_csv_rows(file_path)}
    if suffix in {".xlsx", ".xlsm"}:
        return read_xlsx_sheets(file_path)
    raise RuntimeError(f"暂不支持的文件类型：{file_path.suffix}")


# ---------- 智能订单识别 ----------
_ORDER_HEADER_ALIAS_MAPPING_CACHE: Optional[Dict[str, str]] = None


def get_order_header_alias_mapping() -> Dict[str, str]:
    global _ORDER_HEADER_ALIAS_MAPPING_CACHE
    if _ORDER_HEADER_ALIAS_MAPPING_CACHE is not None:
        return _ORDER_HEADER_ALIAS_MAPPING_CACHE
    mapping: Dict[str, str] = {}
    for canonical, aliases in SMART_ORDER_HEADER_ALIASES.items():
        for alias in aliases:
            normalized = normalize_header_text(alias)
            if normalized:
                mapping[normalized] = canonical
        mapping[normalize_header_text(canonical)] = canonical
    _ORDER_HEADER_ALIAS_MAPPING_CACHE = mapping
    return mapping


def find_order_header_row(raw_rows: List[Dict[str, str]], max_scan_rows: int = 10) -> tuple:
    alias_mapping = get_order_header_alias_mapping()
    best_row_index = 0
    best_headers: set = set()
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
            "sheet_name": sheet_name, "header_row_index": 0, "raw_headers": [],
            "matched_headers": [], "missing_headers": SMART_ORDER_REQUIRED_HEADERS[:],
            "score": 0, "preview": "无可预览内容", "raw_rows": raw_rows,
        }
    header_row_index, matched_headers = find_order_header_row(raw_rows)
    header_row = raw_rows[header_row_index]
    ordered_cols = sorted(header_row.keys(), key=col_to_num)
    raw_headers = [safe_text(header_row.get(col)) for col in ordered_cols if safe_text(header_row.get(col))]
    missing_headers = [h for h in SMART_ORDER_REQUIRED_HEADERS if h not in matched_headers]
    preferred_sheet = sheet_name in {"知护订单", "知护总表格"}
    return {
        "sheet_name": sheet_name, "header_row_index": header_row_index,
        "raw_headers": raw_headers, "matched_headers": sorted(matched_headers),
        "missing_headers": missing_headers, "score": len(matched_headers),
        "preferred_sheet": preferred_sheet, "raw_rows": raw_rows,
    }


def find_best_order_sheet(raw_sheets: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    analyses = [analyze_order_sheet(name, rows) for name, rows in raw_sheets.items()]
    if not analyses:
        raise RuntimeError("Excel 文件中未找到可读取的工作表")
    return max(
        analyses,
        key=lambda item: (item["score"], 1 if item.get("preferred_sheet") else 0, -len(item["missing_headers"]), len(item["raw_rows"])),
    )


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
    return _build_rows_from_headers_by_col(raw_rows, headers_by_col, analysis["header_row_index"] + 1)


def is_valid_order_xlsx(file_path: Path) -> bool:
    try:
        analysis = find_best_order_sheet(read_xlsx_raw_sheets(file_path))
    except Exception:
        return False
    return not analysis["missing_headers"]


def read_order_rows_from_file(file_path: Path) -> tuple:
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
