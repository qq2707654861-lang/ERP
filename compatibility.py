# -*- coding: utf-8 -*-
"""
兼容适配器 — 让旧GUI（ERP.py里的OrderManagerGUI）
能直接使用新 core.db.DatabaseManager，无需修改GUI代码

用法：
    旧GUI原来用 from ERP import DatabaseManager
    现在改为 from compatibility import DatabaseManager
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config import (
    APP_RUNTIME_LOG_PATH,
    APP_TITLE,
    COURIER_COMPANY_OPTIONS,
    DB_PATH,
    LEGACY_ORDER_STATUS_MAP,
    LEGACY_SETTLEMENT_STATUS_MAP,
    ORDER_EXPORT_COLUMN_KEYS,
    ORDER_GRID_COLUMNS,
    ORDER_STATUS_FLOW,
    SETTINGS_CLEARABLE_ITEMS,
    SETTINGS_KEYS,
    SMART_ORDER_HEADER_ALIASES,
    SMART_ORDER_REQUIRED_HEADERS,
)
from core.utils import (
    can_transition_order_status,
    clean_date_text,
    get_allowed_order_status_options,
    get_audit_required_field_errors,
    get_delivery_required_field_errors,
    get_next_order_status,
    get_status_transition_text,
    normalize_discount,
    normalize_order_status,
    normalize_settlement_status,
    now_str,
    safe_text,
    to_float,
    to_int,
)
from core.file_reader import (
    read_csv_rows,
    read_order_rows_from_file,
    read_table_file,
    read_xlsx_raw_sheets,
    read_xlsx_sheets,
    get_sheet_rows,
    is_valid_order_xlsx,
    find_best_order_sheet,
    build_rows_from_order_analysis,
)


# 旧GUI需要的模块级常量（直接从config导出）
WECHAT_ROOT_SETTING_KEY = SETTINGS_KEYS.WECHAT_ROOT
TAOBAO_ACCOUNT_SETTING_KEY = SETTINGS_KEYS.TAOBAO_ACCOUNT
TAOBAO_PASSWORD_SETTING_KEY = SETTINGS_KEYS.TAOBAO_PASSWORD


class DatabaseManager:
    """
    兼容旧GUI的DatabaseManager
    内部使用 core.db.DatabaseManager，但暴露旧接口
    """

    def __init__(self, db_path: Path = DB_PATH):
        from core.db import DatabaseManager as NewDB
        self._new_db = NewDB(db_path)
        # 兼容属性
        self.conn = self._new_db.conn
        self.db_path = self._new_db.db_path

    # ========== 直接代理旧接口 ==========
    def init_db(self) -> None:
        self._new_db.init_db()

    def seed_default_users(self) -> None:
        self._new_db.seed_default_users()

    def seed_default_courier_companies(self) -> None:
        self._new_db.seed_default_courier_companies()

    def ensure_orders_schema(self) -> None:
        self._new_db.ensure_orders_schema()

    def ensure_procurement_products_schema(self) -> None:
        self._new_db.ensure_procurement_products_schema()

    def normalize_existing_order_statuses(self) -> None:
        self._new_db.normalize_existing_order_statuses()

    def verify_user(self, username: str, password: str) -> Optional[str]:
        return self._new_db.verify_user(username, password)

    def get_app_setting(self, setting_key: str, default: str = "") -> str:
        return self._new_db.get_app_setting(setting_key, default)

    def set_app_setting(self, setting_key: str, setting_value: str) -> None:
        self._new_db.set_app_setting(setting_key, setting_value)

    def log(self, username: str, action: str, detail: str = "") -> None:
        self._new_db.log(username, action, detail)

    def list_operation_logs(self, limit: Optional[int] = None) -> List[sqlite3.Row]:
        return self._new_db.list_operation_logs(limit)

    def remember_courier_company(self, name: str) -> None:
        self._new_db.remember_courier_company(name)

    def upsert_book(self, data: Dict[str, Any], username: str = "system") -> None:
        self._new_db.upsert_book(data, username)

    def list_books(self, keyword: str = "") -> List[sqlite3.Row]:
        return self._new_db.list_books(keyword)

    def get_book_by_sku(self, sku: str) -> Optional[sqlite3.Row]:
        return self._new_db.get_book_by_sku(sku)

    def import_books_from_file(self, file_path: Path, username: str = "system") -> str:
        return self._new_db.import_books_from_file(file_path, username)

    def import_supplier_rules_from_file(self, file_path: Path, username: str = "system") -> str:
        return self._new_db.import_supplier_rules_from_file(file_path, username)

    def list_procurement_products(self, keyword: str = "") -> List[sqlite3.Row]:
        return self._new_db.list_procurement_products(keyword)

    def upsert_procurement_product(self, data: Dict[str, Any]) -> None:
        self._new_db.upsert_procurement_product(data)

    def mark_procurement_product_used(self, item_id: str) -> None:
        self._new_db.mark_procurement_product_used(item_id)

    def get_order_by_no(self, order_no: str) -> Optional[sqlite3.Row]:
        return self._new_db.get_order_by_no(order_no)

    def clear_business_data(self, selected_items: List[str], username: str) -> None:
        self._new_db.clear_business_data(selected_items, username)

    def list_courier_companies(self) -> List[str]:
        rows = self.conn.execute("SELECT name FROM courier_companies ORDER BY name ASC").fetchall()
        return [safe_text(row[0]) for row in rows if safe_text(row[0])]

    # ========== 旧接口需兼容实现 ==========

    def _prepare_order_data(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """兼容旧 _prepare_order_data（从原始文件复制核心逻辑，加入平台字段）"""
        from core.utils import calculate_receivable_shipping_fee

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
            book_amount, recipient_address,
            pick_value(row, "应收运费", "邮费", "运费") or book_shipping_fee,
        )
        receivable_amount = to_float(pick_value(row, "应收金额"), round(book_amount + shipping_fee, 2))
        procurement_cost = to_float(pick_value(row, "采购成本"), 0.0)

        # 检测平台来源
        platform_source = safe_text(row.get("platform_source", "知护")) or "知护"
        shop_name = safe_text(row.get("shop_name", "")) or platform_source

        return {
            "order_no": order_no,
            "order_time": order_time,
            "order_date": order_date,
            "platform_source": platform_source,
            "platform_order_id": pick_value(row, "订单号"),
            "shop_name": shop_name,
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
        """兼容旧 upsert_order，加上平台字段和自动财务记录"""
        now = now_str()
        values = (
            data.get("order_no", ""),
            data.get("order_time", ""),
            data.get("order_date", ""),
            data.get("platform_source", "知护"),
            data.get("platform_order_id", ""),
            data.get("shop_name", "知护"),
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
            data.get("actual_payment", 0.0),
            data.get("platform_commission", 0.0),
            data.get("refund_status", ""),
            data.get("refund_amount", 0.0),
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
        self.conn.execute(
            """
            INSERT INTO orders (
                order_no, order_time, order_date, platform_source, platform_order_id,
                shop_name, shipping_method, recipient_name, recipient_phone, recipient_address,
                product_name, sku, quantity, list_price, discount, book_amount,
                shipping_fee, receivable_amount, actual_payment, platform_commission,
                refund_status, refund_amount, remark, courier_company, tracking_no,
                settlement_status, invoice_status, procurement_date, procurement_order_no,
                procurement_cost, procurement_remark, order_status, order_status_updated_at,
                created_at, updated_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(order_no) DO UPDATE SET
                order_time=excluded.order_time, order_date=excluded.order_date,
                platform_source=excluded.platform_source, shop_name=excluded.shop_name,
                shipping_method=excluded.shipping_method, recipient_name=excluded.recipient_name,
                recipient_phone=excluded.recipient_phone, recipient_address=excluded.recipient_address,
                product_name=excluded.product_name, sku=excluded.sku, quantity=excluded.quantity,
                list_price=excluded.list_price, discount=excluded.discount, book_amount=excluded.book_amount,
                shipping_fee=excluded.shipping_fee, receivable_amount=excluded.receivable_amount,
                actual_payment=excluded.actual_payment, platform_commission=excluded.platform_commission,
                remark=excluded.remark, courier_company=excluded.courier_company,
                tracking_no=excluded.tracking_no, settlement_status=excluded.settlement_status,
                invoice_status=excluded.invoice_status, procurement_date=excluded.procurement_date,
                procurement_order_no=excluded.procurement_order_no,
                procurement_cost=excluded.procurement_cost, procurement_remark=excluded.procurement_remark,
                order_status=excluded.order_status, order_status_updated_at=excluded.order_status_updated_at,
                updated_at=excluded.updated_at
            """,
            values,
        )
        self.conn.commit()
        self.remember_courier_company(data.get("courier_company", ""))

        # 自动生成财务记录
        order_no = data.get("order_no", "")
        receivable = to_float(data.get("receivable_amount"), 0.0)
        cost = to_float(data.get("procurement_cost"), 0.0)
        platform_source = data.get("platform_source", "知护")
        commission = to_float(data.get("platform_commission"), 0.0)

        if receivable > 0:
            self._new_db.add_finance_record({
                "order_no": order_no,
                "platform_source": platform_source,
                "type": "收入",
                "category": "书款",
                "amount": receivable,
                "remark": "订单导入自动记录",
            }, username)
        if cost > 0:
            self._new_db.add_finance_record({
                "order_no": order_no,
                "platform_source": platform_source,
                "type": "支出",
                "category": "采购",
                "amount": cost,
                "remark": "订单导入自动记录",
            }, username)
        if commission > 0:
            self._new_db.add_finance_record({
                "order_no": order_no,
                "platform_source": platform_source,
                "type": "佣金",
                "category": "平台佣金",
                "amount": commission,
                "remark": "订单导入自动记录",
            }, username)

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

    def list_orders(self, **kwargs) -> List[sqlite3.Row]:
        """兼容旧 list_orders，支持多平台筛选"""
        rows = self._new_db.list_orders(**kwargs)
        # 旧GUI依赖 profit 字段（计算列），补上
        result = []
        for row in rows:
            # sqlite3.Row不支持直接添加字段，用dict包裹
            d = dict(row)
            if "profit" not in d:
                d["profit"] = round(to_float(d.get("receivable_amount", 0)) - to_float(d.get("procurement_cost", 0)), 2)
            # 转回sqlite3.Row的dict-like对象
            result.append(RowProxy(d))
        return result

    def get_order(self, order_id: int) -> Optional[Any]:
        row = self.conn.execute(
            "SELECT *, ROUND(receivable_amount - procurement_cost, 2) AS profit FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        return row

    def update_order_details(self, order_id: int, data: Dict[str, Any], username: str) -> None:
        """兼容旧 update_order_details"""
        current_row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
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
            UPDATE orders SET
                recipient_name=?, recipient_address=?, remark=?, courier_company=?,
                tracking_no=?, settlement_status=?, invoice_status=?, procurement_date=?,
                procurement_order_no=?, procurement_cost=?, procurement_remark=?,
                order_status=?, order_status_updated_at=?, updated_at=?
            WHERE id=?
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
                next_status, status_updated_at, now_str(), order_id,
            ),
        )
        self.conn.commit()
        self.remember_courier_company(data.get("courier_company", current_row["courier_company"]))
        self.log(username, "订单状态变更", f"订单号={current_row['order_no']}：{current_status} -> {next_status}")
        self.log(username, "更新订单", f"ID={order_id}")

    def export_orders_to_excel(self, file_path: Path, **kwargs) -> int:
        from core.utils import excel_col_name
        from xml.sax.saxutils import escape as xml_escape
        import zipfile

        rows = self.list_orders(**kwargs)
        column_defs = [
            (key, title)
            for key, title, _width in ORDER_GRID_COLUMNS
            if not kwargs.get("selected_columns") or key in (kwargs.get("selected_columns") or [])
        ]
        headers = [title for _key, title in column_defs]
        float_cols = {"list_price", "discount", "book_amount", "shipping_fee", "receivable_amount", "procurement_cost", "profit"}
        excel_rows = []
        for row in rows:
            cell = []
            for key, _title in column_defs:
                if key == "created_at":
                    cell.append(safe_text(row["created_at"])[:10])
                elif key in float_cols:
                    cell.append(f"{to_float(row[key]):.2f}")
                else:
                    cell.append(safe_text(row[key]))
            excel_rows.append(cell)

        # 写xlsx
        from core.file_reader import _build_rows_from_headers_by_col
        def build_sheet_xml():
            sheet_rows = []
            all_rows = [headers] + excel_rows
            for ri, rv in enumerate(all_rows, 1):
                cells = []
                for ci, v in enumerate(rv, 1):
                    ref = f"{excel_col_name(ci)}{ri}"
                    cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(safe_text(v))}</t></is></c>')
                sheet_rows.append(f"<row r=\"{ri}\">{''.join(cells)}</row>")
            return (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f"<sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
            )

        created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
            zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
            zf.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="总订单" sheetId="1" r:id="rId1"/></sheets></workbook>')
            zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml())

        return len(rows)

    def export_rows_to_excel(self, file_path: Path, rows: List, sheet_name: str = "总订单", selected_columns: Optional[List[str]] = None) -> int:
        """兼容旧导出"""
        return self.export_orders_to_excel(file_path, selected_columns=selected_columns)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self._new_db.get_dashboard_stats()

    def get_profit_summary_text(self) -> str:
        stats = self._new_db.get_dashboard_stats()
        lines = [
            f"总订单数：{stats['total_orders']}",
            f"待审核：{stats['pending_orders']}",
            f"发货中：{stats['shipping_orders']}",
            f"应收金额合计：{stats['total_revenue']:.2f}",
            f"粗算毛利：{stats['total_profit']:.2f}",
            f"未结算：{stats['unsettled_orders']}",
            "",
            "平台分布：",
        ]
        for platform, pstat in stats.get("platform_stats", {}).items():
            lines.append(f"  - {platform}：{pstat['count']}单，¥{pstat['revenue']:.2f}")
        lines.append("")
        lines.append("最近操作日志：")
        logs = self.list_operation_logs(limit=10)
        for row in logs:
            lines.append(f"- [{row['created_at']}] {row['username']}：{row['action']}（{row['detail']}）")
        return "\n".join(lines)

    # ========== 新增接口暴露给旧GUI ==========
    def list_inventory(self, keyword: str = "", warehouse: str = "") -> List[sqlite3.Row]:
        return self._new_db.list_inventory(keyword, warehouse)

    def get_low_stock_warnings(self) -> List[sqlite3.Row]:
        return self._new_db.get_low_stock_warnings()

    def adjust_inventory(self, sku: str, change_type: str, change_qty: int, warehouse: str = "默认仓库", **kwargs) -> None:
        self._new_db.adjust_inventory(sku, change_type, change_qty, warehouse, **kwargs)

    def get_finance_summary(self, **kwargs) -> Dict[str, float]:
        return self._new_db.get_finance_summary(**kwargs)

    def list_finance_records(self, **kwargs) -> List[sqlite3.Row]:
        return self._new_db.list_finance_records(**kwargs)

    def close(self) -> None:
        self._new_db.close()


class RowProxy:
    """sqlite3.Row 的dict代理，用于兼容旧GUI的 profit 计算列"""
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> list:
        return list(self._data.keys())

    def values(self) -> list:
        return list(self._data.values())

    def items(self) -> list:
        return list(self._data.items())

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


def pick_value(row: Dict[str, Any], *aliases: str) -> str:
    return safe_text(row.get(aliases[0], "")) if len(aliases) == 1 else safe_text(
        next((row.get(a) for a in aliases if row.get(a)), "")
    )
