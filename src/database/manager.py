# -*- coding: utf-8 -*-
"""
Database manager for ERP Order Manager
Inspired by Claude Code architecture - database layer isolated
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils.helpers import now_str, to_float


class ERPOrderDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self) -> None:
        create_tables = not self.db_path.exists()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        if not create_tables:
            return

        # Create tables
        cursor = self.conn.cursor()

        # Orders table
        cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            order_no TEXT NOT NULL,
            sku TEXT,
            product_name TEXT,
            quantity INTEGER DEFAULT 1,
            list_price REAL DEFAULT 0,
            discount REAL DEFAULT 1.0,
            book_amount REAL DEFAULT 0,
            shipping_fee REAL DEFAULT 0,
            receivable_amount REAL DEFAULT 0,
            remark TEXT,
            courier_company TEXT,
            tracking_no TEXT,
            recipient_name TEXT,
            recipient_address TEXT,
            recipient_phone TEXT,
            order_status TEXT DEFAULT '审核',
            settlement_status TEXT DEFAULT '未结算',
            invoice_status TEXT DEFAULT '未开票',
            procurement_date TEXT,
            procurement_order_no TEXT,
            procurement_cost REAL DEFAULT 0,
            procurement_remark TEXT,
            profit REAL DEFAULT 0,
            updated_at TEXT
        )
        """)

        # Books table (book catalog)
        cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            default_list_price REAL DEFAULT 0,
            default_procurement_cost REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """)

        # Supplier rules
        cursor.execute("""
        CREATE TABLE supplier_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            sku_pattern TEXT,
            default_procurement_cost REAL DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)

        # Operation logs
        cursor.execute("""
        CREATE TABLE operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )
        """)

        # Courier company records (for autocomplete)
        cursor.execute("""
        CREATE TABLE courier_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            use_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)

        # Settings (key-value)
        cursor.execute("""
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
        """)

        # Insert default courier companies
        from src import constants
        for cc in constants.COURIER_COMPANY_OPTIONS:
            cursor.execute(
                "INSERT OR IGNORE INTO courier_companies (name, created_at) VALUES (?, ?)",
                (cc, now_str())
            )

        self.conn.commit()
    def _get_where_filter(
        self,
        order_status: Optional[str] = None,
        settlement_status: Optional[str] = None,
        invoice_status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[str, List[Any]]:
        conditions: List[str] = []
        params: List[Any] = []

        if order_status and order_status != "全部":
            conditions.append("order_status = ?")
            params.append(order_status)

        if settlement_status and settlement_status != "全部":
            conditions.append("settlement_status = ?")
            params.append(settlement_status)

        if invoice_status and invoice_status != "全部":
            conditions.append("invoice_status = ?")
            params.append(invoice_status)

        if keyword:
            keywords = keyword.strip().split()
            for kw in keywords:
                conditions.append(
                    "(order_no LIKE ? OR product_name LIKE ? OR recipient_name LIKE ? OR recipient_phone LIKE ?)"
                )
                kw_pattern = f"%{kw}%"
                params.extend([kw_pattern, kw_pattern, kw_pattern, kw_pattern])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params

    def list_orders(
        self,
        order_status: Optional[str] = None,
        settlement_status: Optional[str] = None,
        invoice_status: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[sqlite3.Row]:
        where_clause, params = self._get_where_filter(
            order_status, settlement_status, invoice_status, keyword
        )

        sql = f"""
        SELECT *, ROUND(receivable_amount - procurement_cost, 2) AS profit
        FROM orders
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return list(cursor.fetchall())

    def count_orders(
        self,
        order_status: Optional[str] = None,
        settlement_status: Optional[str] = None,
        invoice_status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        where_clause, params = self._get_where_filter(
            order_status, settlement_status, invoice_status, keyword
        )

        sql = f"SELECT COUNT(*) FROM orders {where_clause}"
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()[0]

    def get_order_by_id(self, order_id: int) -> Optional[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT *, ROUND(receivable_amount - procurement_cost, 2) AS profit
        FROM orders WHERE id = ?
        """, (order_id,))
        return cursor.fetchone()

    def insert_order(self, order_data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        now = now_str()

        # Calculate profit
        receivable = to_float(order_data.get("receivable_amount", 0.0), 0.0)
        procurement_cost = to_float(order_data.get("procurement_cost", 0.0), 0.0)
        profit = round(receivable - procurement_cost, 2)

        columns = [
            "created_at", "order_no", "sku", "product_name", "quantity",
            "list_price", "discount", "book_amount", "shipping_fee",
            "receivable_amount", "remark", "courier_company", "tracking_no",
            "recipient_name", "recipient_address", "recipient_phone",
            "order_status", "settlement_status", "invoice_status",
            "procurement_date", "procurement_order_no", "procurement_cost",
            "procurement_remark", "profit", "updated_at",
        ]
        placeholders = ", ".join(["?"] * len(columns))
        values = [
            now,
            order_data.get("order_no", ""),
            order_data.get("sku", ""),
            order_data.get("product_name", ""),
            order_data.get("quantity", 1),
            order_data.get("list_price", 0.0),
            order_data.get("discount", 1.0),
            order_data.get("book_amount", 0.0),
            order_data.get("shipping_fee", 6.0),
            order_data.get("receivable_amount", 0.0),
            order_data.get("remark", ""),
            order_data.get("courier_company", ""),
            order_data.get("tracking_no", ""),
            order_data.get("recipient_name", ""),
            order_data.get("recipient_address", ""),
            order_data.get("recipient_phone", ""),
            order_data.get("order_status", "审核"),
            order_data.get("settlement_status", "未结算"),
            order_data.get("invoice_status", "未开票"),
            order_data.get("procurement_date", ""),
            order_data.get("procurement_order_no", ""),
            procurement_cost,
            order_data.get("procurement_remark", ""),
            profit,
            now,
        ]

        sql = f"INSERT INTO orders ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        self.conn.commit()
        return cursor.lastrowid

    def update_order(self, order_id: int, data: Dict[str, Any]) -> bool:
        from src.utils.status import normalize_order_status

        cursor = self.conn.cursor()
        now = now_str()

        # Recalculate profit if receivable or procurement changed
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        updated_data = dict(data)
        if 'receivable_amount' in updated_data or 'procurement_cost' in updated_data:
            receivable = to_float(
                updated_data.get('receivable_amount', order['receivable_amount']), 0.0
            )
            procurement = to_float(
                updated_data.get('procurement_cost', order['procurement_cost']), 0.0
            )
            updated_data['profit'] = round(receivable - procurement, 2)

        updated_data['updated_at'] = now

        set_clause = ", ".join([f"{k} = ?" for k in updated_data.keys()])
        sql = f"UPDATE orders SET {set_clause} WHERE id = ?"
        params = list(updated_data.values()) + [order_id]

        cursor.execute(sql, params)
        self.conn.commit()
        return True

    def delete_order(self, order_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_statistics(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(receivable_amount), SUM(procurement_cost), SUM(ROUND(receivable_amount - procurement_cost, 2)) FROM orders WHERE settlement_status = '已结算'")
        row = cursor.fetchone()
        total_receivable = row[0] or 0.0
        total_procurement = row[1] or 0.0
        total_profit = row[2] or 0.0

        cursor.execute("SELECT COUNT(*) FROM orders WHERE settlement_status = '未结算'")
        unpaid_count = cursor.fetchone()[0]

        return {
            "total_orders": total_orders,
            "total_receivable": round(total_receivable, 2),
            "total_procurement": round(total_procurement, 2),
            "total_profit": round(total_profit, 2),
            "unpaid_count": unpaid_count,
        }

    def clear_all(self, table: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()
        return True

    def log_operation(self, operation: str, details: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO operation_logs (operation, details, created_at) VALUES (?, ?, ?)",
            (operation, details, now_str())
        )
        self.conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return default
        return row[0]

    def set_setting(self, key: str, value: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
        REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)
        """, (key, value, now_str()))
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()


# Backward compatibility for older imports
ZhihuOrderDB = ERPOrderDB
