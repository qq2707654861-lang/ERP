# -*- coding: utf-8 -*-
"""
数据库管理 — 建表、迁移、CRUD
新增：platform_source/shop_name字段、库存表、财务记录表
"""
from __future__ import annotations

import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from .config import (
    APP_RUNTIME_LOG_PATH,
    BASE_DIR,
    COURIER_COMPANY_OPTIONS,
    DB_PATH,
    EXCEL_NS,
    LEGACY_ORDER_STATUS_MAP,
    LEGACY_SETTLEMENT_STATUS_MAP,
    ORDER_EXPORT_COLUMN_KEYS,
    ORDER_GRID_COLUMNS,
    SETTINGS_CLEARABLE_ITEMS,
    SETTINGS_KEYS,
    SMART_ORDER_HEADER_ALIASES,
    SMART_ORDER_REQUIRED_HEADERS,
)
from .utils import (
    clean_date_text,
    col_to_num,
    excel_col_name,
    normalize_discount,
    normalize_header_text,
    normalize_settlement_status,
    now_str,
    pick_value,
    safe_text,
    to_float,
    to_int,
)


def append_runtime_log(message: str, exc_info: Any = None) -> None:
    lines = [f"[{now_str()}] {safe_text(message)}"]
    if exc_info:
        lines.append("".join(traceback.format_exception(*exc_info)).rstrip())
    try:
        with open(APP_RUNTIME_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines) + "\n\n")
    except Exception:
        pass


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.init_db()

    # ==================== 建表 ====================
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
                platform_source TEXT DEFAULT '知护',
                platform_order_id TEXT DEFAULT '',
                shop_name TEXT DEFAULT '',
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
                actual_payment REAL DEFAULT 0,
                platform_commission REAL DEFAULT 0,
                refund_status TEXT DEFAULT '',
                refund_amount REAL DEFAULT 0,
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
                weight REAL DEFAULT 0,
                package_count INTEGER DEFAULT 1,
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

            -- ========== 新增：库存表 ==========
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                warehouse TEXT DEFAULT '默认仓库',
                available_qty INTEGER DEFAULT 0,
                locked_qty INTEGER DEFAULT 0,
                in_transit_qty INTEGER DEFAULT 0,
                min_stock_qty INTEGER DEFAULT 5,
                cost_price REAL DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(sku, warehouse)
            );

            -- ========== 新增：库存变动日志 ==========
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                warehouse TEXT DEFAULT '默认仓库',
                change_type TEXT NOT NULL,
                change_qty INTEGER NOT NULL,
                before_qty INTEGER DEFAULT 0,
                after_qty INTEGER DEFAULT 0,
                order_no TEXT DEFAULT '',
                operator TEXT DEFAULT '',
                remark TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            -- ========== 新增：财务记录 ==========
            CREATE TABLE IF NOT EXISTS finance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT DEFAULT '',
                platform_source TEXT DEFAULT '',
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT DEFAULT '',
                settlement_date TEXT DEFAULT '',
                remark TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status);
            CREATE INDEX IF NOT EXISTS idx_orders_settlement_status ON orders(settlement_status);
            CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
            CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);
            CREATE INDEX IF NOT EXISTS idx_finance_records_order_no ON finance_records(order_no);
            """
        )
        self.conn.commit()
        # 先迁移旧表字段，再创建依赖新字段的索引
        self.ensure_orders_schema()
        self.ensure_procurement_products_schema()
        self.normalize_existing_order_statuses()
        self._create_new_indexes()
        self.seed_default_users()
        self.seed_default_courier_companies()
        self._migrate_plain_passwords()

    # ==================== 动态索引 ====================
    def _create_new_indexes(self) -> None:
        """创建依赖新字段的索引（迁移后执行）"""
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(orders)").fetchall()}
        if "platform_source" in columns:
            try:
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_platform_source ON orders(platform_source)")
            except Exception:
                pass
        if "shop_name" in columns:
            try:
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_shop_name ON orders(shop_name)")
            except Exception:
                pass
        self.conn.commit()

    # ==================== 数据迁移 ====================
    def ensure_orders_schema(self) -> None:
        """确保 orders 表包含新字段（兼容旧数据库）"""
        columns = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        new_columns = {
            "order_status_updated_at": "TEXT DEFAULT ''",
            "platform_source": "TEXT DEFAULT '知护'",
            "platform_order_id": "TEXT DEFAULT ''",
            "shop_name": "TEXT DEFAULT ''",
            "actual_payment": "REAL DEFAULT 0",
            "platform_commission": "REAL DEFAULT 0",
            "refund_status": "TEXT DEFAULT ''",
            "refund_amount": "REAL DEFAULT 0",
            "weight": "REAL DEFAULT 0",
            "package_count": "INTEGER DEFAULT 1",
        }
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                self.conn.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
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

    # ==================== 种子数据 ====================
    def seed_default_users(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        if count == 0:
            users = [
                ("admin", self._hash_password("admin123"), "管理员", now_str()),
                ("order", self._hash_password("123456"), "订单员", now_str()),
                ("finance", self._hash_password("123456"), "财务", now_str()),
            ]
            cur.executemany(
                "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                users,
            )
            self.conn.commit()

    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希（兼容旧明文密码）"""
        import hashlib
        return "sha256:" + hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        """验证密码（兼容旧明文和新的sha256哈希）"""
        if not stored:
            return False
        if stored.startswith("sha256:"):
            import hashlib
            return stored == "sha256:" + hashlib.sha256(password.encode("utf-8")).hexdigest()
        # 旧版明文密码
        return password == stored

    def _migrate_plain_passwords(self) -> None:
        """将旧明文密码迁移为哈希"""
        rows = self.conn.execute("SELECT id, password FROM users WHERE password NOT LIKE 'sha256:%'").fetchall()
        for row in rows:
            hashed = self._hash_password(row["password"])
            self.conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, row["id"]))
        if rows:
            self.conn.commit()

    def seed_default_courier_companies(self) -> None:
        now = now_str()
        self.conn.executemany(
            """
            INSERT INTO courier_companies (name, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET updated_at = excluded.updated_at
            """,
            [(name, now, now) for name in COURIER_COMPANY_OPTIONS],
        )
        self.conn.commit()

    # ==================== 用户 ====================
    def verify_user(self, username: str, password: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT role, password FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        if not self._verify_password(password, row["password"]):
            return None
        # 首次登录自动迁移旧明文密码
        if not row["password"].startswith("sha256:"):
            self._migrate_plain_passwords()
        return row["role"]

    # ==================== 设置 ====================
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

    # ==================== 日志 ====================
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

    # ==================== 快递公司 ====================
    def remember_courier_company(self, name: str) -> None:
        company = safe_text(name)
        if not company:
            return
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO courier_companies (name, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (company, now, now),
        )
        self.conn.commit()

    # ==================== 图书资料 ====================
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
                name = excluded.name, price = excluded.price, publisher = excluded.publisher,
                discount = excluded.discount, shipping_fee = excluded.shipping_fee,
                supplier = excluded.supplier, updated_at = excluded.updated_at
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

    def import_books_from_file(self, file_path: Path, username: str = "system") -> str:
        from .file_reader import read_table_file, get_sheet_rows
        sheets = read_table_file(file_path)
        rows = get_sheet_rows(sheets, "知护网图书资料库")
        count = 0
        for row in rows:
            sku = pick_value(row, "书号", "SKU", "SKU编码", "商品编码", "书号")
            if not sku:
                continue
            self.upsert_book({
                "sku": sku,
                "name": pick_value(row, "书名", "商品名称", "名称"),
                "price": pick_value(row, "定价", "价格", "售价"),
                "publisher": pick_value(row, "出版社"),
                "discount": pick_value(row, "折扣"),
                "shipping_fee": pick_value(row, "邮费", "运费"),
                "supplier": pick_value(row, "供应商"),
            }, username=username)
            count += 1
        self.log(username, "导入图书资料", f"{file_path.name}，共 {count} 条")
        return f"图书资料导入完成：{count} 条"

    # ==================== 供应商规则 ====================
    def import_supplier_rules_from_file(self, file_path: Path, username: str = "system") -> str:
        from .file_reader import read_table_file, get_sheet_rows
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
                    discount_note = excluded.discount_note, shipping_note = excluded.shipping_note,
                    special_area = excluded.special_area, extra_rule = excluded.extra_rule,
                    updated_at = excluded.updated_at
                """,
                (
                    supplier_name,
                    pick_value(row, "折扣"),
                    pick_value(row, "邮费", "运费说明"),
                    pick_value(row, "地区", "特殊地区"),
                    pick_value(row, "首重1kg 续重1kg", "规则说明"),
                    now, now,
                ),
            )
            count += 1
        self.conn.commit()
        self.log(username, "导入供应商规则", f"{file_path.name}，共 {count} 条")
        return f"供应商规则导入完成：{count} 条"

    # ==================== 采购商品 ====================
    def list_procurement_products(self, keyword: str = "") -> List[sqlite3.Row]:
        sql = "SELECT * FROM procurement_products"
        params: List[Any] = []
        if keyword:
            sql += " WHERE product_name LIKE ? OR isbn LIKE ? OR shop LIKE ? OR item_id LIKE ?"
            like = f"%{keyword}%"
            params.extend([like, like, like, like])
        sql += " ORDER BY use_count DESC, updated_at DESC"
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
                product_name = excluded.product_name, isbn = excluded.isbn,
                price = excluded.price, shop = excluded.shop, updated_at = excluded.updated_at
            """,
            (
                safe_text(data.get("product_name")),
                safe_text(data.get("isbn")),
                to_float(data.get("price"), 0.0),
                safe_text(data.get("shop")),
                item_id,
                max(to_int(data.get("use_count"), 0), 0),
                safe_text(data.get("last_used_at")),
                now, now,
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
            SET use_count = IFNULL(use_count, 0) + 1, last_used_at = ?, updated_at = ?
            WHERE item_id = ?
            """,
            (now, now, item_value),
        )
        self.conn.commit()

    # ==================== 库存管理（新增） ====================
    def get_inventory(self, sku: str, warehouse: str = "默认仓库") -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM inventory WHERE sku = ? AND warehouse = ?",
            (sku, warehouse),
        ).fetchone()

    def list_inventory(self, keyword: str = "", warehouse: str = "") -> List[sqlite3.Row]:
        sql = "SELECT * FROM inventory"
        conditions: List[str] = []
        params: List[Any] = []
        if keyword:
            conditions.append("sku LIKE ?")
            params.append(f"%{keyword}%")
        if warehouse:
            conditions.append("warehouse = ?")
            params.append(warehouse)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY updated_at DESC"
        return list(self.conn.execute(sql, params))

    def upsert_inventory(self, data: Dict[str, Any], operator: str = "system") -> None:
        sku = safe_text(data.get("sku"))
        if not sku:
            return
        warehouse = safe_text(data.get("warehouse", "默认仓库")) or "默认仓库"
        available_qty = to_int(data.get("available_qty"), 0)
        locked_qty = to_int(data.get("locked_qty"), 0)
        in_transit_qty = to_int(data.get("in_transit_qty"), 0)
        min_stock_qty = to_int(data.get("min_stock_qty"), 5)
        cost_price = to_float(data.get("cost_price"), 0.0)
        now = now_str()
        self.conn.execute(
            """
            INSERT INTO inventory (sku, warehouse, available_qty, locked_qty, in_transit_qty, min_stock_qty, cost_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku, warehouse) DO UPDATE SET
                available_qty = excluded.available_qty, locked_qty = excluded.locked_qty,
                in_transit_qty = excluded.in_transit_qty, min_stock_qty = excluded.min_stock_qty,
                cost_price = excluded.cost_price, updated_at = excluded.updated_at
            """,
            (sku, warehouse, available_qty, locked_qty, in_transit_qty, min_stock_qty, cost_price, now),
        )
        self.conn.commit()

    def adjust_inventory(
        self,
        sku: str,
        change_type: str,
        change_qty: int,
        warehouse: str = "默认仓库",
        order_no: str = "",
        operator: str = "system",
        remark: str = "",
    ) -> None:
        """库存变动，自动记录日志"""
        inv = self.get_inventory(sku, warehouse)
        before_qty = int(inv["available_qty"]) if inv else 0

        if change_type == "入库":
            after_qty = before_qty + change_qty
        elif change_type == "出库":
            after_qty = max(before_qty - change_qty, 0)
        elif change_type == "锁定":
            after_qty = before_qty  # available不变，locked变
        elif change_type == "盘点调整":
            after_qty = change_qty
        else:
            after_qty = before_qty + change_qty

        now = now_str()
        self.conn.execute(
            """
            INSERT INTO inventory (sku, warehouse, available_qty, locked_qty, in_transit_qty, min_stock_qty, cost_price, updated_at)
            VALUES (?, ?, ?, 0, 0, 5, 0, ?)
            ON CONFLICT(sku, warehouse) DO UPDATE SET
                available_qty = ?, updated_at = ?
            """,
            (sku, warehouse, after_qty, now, after_qty, now),
        )

        self.conn.execute(
            """
            INSERT INTO inventory_logs (sku, warehouse, change_type, change_qty, before_qty, after_qty, order_no, operator, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sku, warehouse, change_type, change_qty, before_qty, after_qty, order_no, operator, remark, now),
        )
        self.conn.commit()

    def get_low_stock_warnings(self) -> List[sqlite3.Row]:
        """获取低于最低库存的SKU"""
        return list(self.conn.execute(
            """
            SELECT i.*, b.name as book_name
            FROM inventory i
            LEFT JOIN books b ON i.sku = b.sku
            WHERE i.available_qty <= i.min_stock_qty
            ORDER BY i.available_qty ASC
            """
        ))

    # ==================== 财务记录（新增） ====================
    def add_finance_record(self, data: Dict[str, Any], username: str = "system") -> None:
        self.conn.execute(
            """
            INSERT INTO finance_records (order_no, platform_source, type, category, amount, payment_method, settlement_date, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                safe_text(data.get("order_no")),
                safe_text(data.get("platform_source", "知护")),
                safe_text(data.get("type")),
                safe_text(data.get("category")),
                to_float(data.get("amount"), 0.0),
                safe_text(data.get("payment_method")),
                clean_date_text(data.get("settlement_date")),
                safe_text(data.get("remark")),
                now_str(),
            ),
        )
        self.conn.commit()

    def list_finance_records(
        self,
        order_no: str = "",
        platform_source: str = "",
        record_type: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> List[sqlite3.Row]:
        conditions: List[str] = []
        params: List[Any] = []
        if order_no:
            conditions.append("order_no = ?")
            params.append(order_no)
        if platform_source:
            conditions.append("platform_source = ?")
            params.append(platform_source)
        if record_type:
            conditions.append("type = ?")
            params.append(record_type)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date + " 23:59:59")
        sql = "SELECT * FROM finance_records"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC"
        return list(self.conn.execute(sql, params))

    def get_finance_summary(
        self,
        platform_source: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> Dict[str, float]:
        """财务汇总：收入/支出/佣金/退款"""
        conditions: List[str] = []
        params: List[Any] = []
        if platform_source:
            conditions.append("platform_source = ?")
            params.append(platform_source)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date + " 23:59:59")
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = self.conn.execute(
            f"SELECT type, SUM(amount) as total FROM finance_records{where} GROUP BY type",
            params,
        ).fetchall()
        result = {"收入": 0.0, "支出": 0.0, "佣金": 0.0, "退款": 0.0}
        for row in rows:
            result[row["type"]] = float(row["total"] or 0)
        result["净利润"] = result["收入"] - result["支出"] - result["佣金"] - result["退款"]
        return result

    # ==================== 订单 ====================
    def get_order_by_no(self, order_no: str) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()

    def list_orders(self, **kwargs) -> List[sqlite3.Row]:
        """兼容旧接口，支持多平台筛选"""
        conditions: List[str] = []
        params: List[Any] = []
        keyword = kwargs.get("keyword", "")
        order_status = kwargs.get("order_status", "")
        settlement_status = kwargs.get("settlement_status", "")
        invoice_status = kwargs.get("invoice_status", "")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        platform_source = kwargs.get("platform_source", "")
        shop_name = kwargs.get("shop_name", "")

        if keyword:
            conditions.append("(order_no LIKE ? OR product_name LIKE ? OR sku LIKE ? OR recipient_name LIKE ?)")
            key = f"%{keyword}%"
            params.extend([key, key, key, key])
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
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date + " 23:59:59")
        if platform_source and platform_source != "全部":
            conditions.append("platform_source = ?")
            params.append(platform_source)
        if shop_name and shop_name != "全部":
            conditions.append("shop_name = ?")
            params.append(shop_name)

        sql = "SELECT * FROM orders"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC"
        return list(self.conn.execute(sql, params))

    def get_dashboard_stats(self) -> Dict[str, Any]:
        total_orders = self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = self.conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = '审核'").fetchone()[0]
        shipping = self.conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = '发货'").fetchone()[0]
        total_revenue = self.conn.execute("SELECT IFNULL(SUM(receivable_amount), 0) FROM orders").fetchone()[0]
        total_profit = self.conn.execute(
            "SELECT IFNULL(SUM(receivable_amount - procurement_cost), 0) FROM orders"
        ).fetchone()[0]
        unsettled = self.conn.execute(
            "SELECT COUNT(*) FROM orders WHERE settlement_status = '未结算'"
        ).fetchone()[0]
        # 按平台统计
        platform_stats = {}
        for row in self.conn.execute(
            "SELECT platform_source, COUNT(*) as cnt, IFNULL(SUM(receivable_amount),0) as rev FROM orders GROUP BY platform_source"
        ).fetchall():
            platform_stats[row["platform_source"] or "未知"] = {
                "count": row["cnt"],
                "revenue": row["rev"],
            }
        return {
            "total_orders": total_orders,
            "pending_orders": pending,
            "shipping_orders": shipping,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "unsettled_orders": unsettled,
            "platform_stats": platform_stats,
        }

    # ==================== 清空数据 ====================
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

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
