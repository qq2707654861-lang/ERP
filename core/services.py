# -*- coding: utf-8 -*-
"""
业务服务层 — 订单服务、库存服务、财务服务
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ORDER_STATUS_FLOW
from .db import DatabaseManager
from .platforms import auto_detect_platform, get_adapter, import_orders_from_file
from .utils import (
    can_transition_order_status,
    get_allowed_order_status_options,
    get_next_order_status,
    normalize_order_status,
    now_str,
    safe_text,
    to_float,
)


class OrderService:
    """订单业务逻辑"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def import_orders(
        self,
        file_path: Path,
        platform_name: str = "",
        username: str = "system",
    ) -> str:
        """导入订单文件，自动识别平台"""
        normalized_rows, platform, sheet_names = import_orders_from_file(
            file_path, platform_name, username
        )
        count = 0
        skipped = 0
        for row in normalized_rows:
            order_no = row.get("order_no", "")
            if not order_no:
                skipped += 1
                continue
            existing = self.db.get_order_by_no(order_no)
            if existing:
                skipped += 1
                continue
            now = now_str()
            self.db.conn.execute(
                """
                INSERT INTO orders (
                    order_no, order_time, order_date, platform_source, platform_order_id,
                    shop_name, shipping_method, recipient_name, recipient_phone, recipient_address,
                    product_name, sku, quantity, list_price, discount, book_amount,
                    shipping_fee, receivable_amount, remark, courier_company, tracking_no,
                    settlement_status, invoice_status, procurement_date, procurement_order_no,
                    procurement_cost, procurement_remark, order_status, order_status_updated_at,
                    created_at, updated_at
                ) VALUES (
                    :order_no, :order_time, :order_date, :platform_source, :platform_order_id,
                    :shop_name, :shipping_method, :recipient_name, :recipient_phone, :recipient_address,
                    :product_name, :sku, :quantity, :list_price, :discount, :book_amount,
                    :shipping_fee, :receivable_amount, :remark, :courier_company, :tracking_no,
                    :settlement_status, :invoice_status, :procurement_date, :procurement_order_no,
                    :procurement_cost, :procurement_remark, '审核', :updated_at,
                    :updated_at, :updated_at
                )
                """,
                {
                    **row,
                    "order_date": row.get("order_time", "")[:10] if row.get("order_time") else "",
                    "shipping_method": row.get("shipping_method", ""),
                    "order_status_updated_at": now,
                    "updated_at": now,
                },
            )
            count += 1
            # 自动扣库存
            sku = row.get("sku", "")
            qty = int(row.get("quantity", 1))
            if sku and qty > 0:
                self.db.adjust_inventory(
                    sku, "出库", qty, order_no=order_no, operator=username, remark="订单导入自动扣减"
                )
        self.db.conn.commit()
        self.db.log(username, f"导入{platform}订单", f"{file_path.name}，导入 {count} 条，跳过 {skipped} 条")
        return f"{platform}订单导入完成：导入 {count} 条，跳过 {skipped} 条"

    def update_order_status(
        self,
        order_id: int,
        target_status: str,
        username: str = "system",
    ) -> str:
        """更新订单状态（带校验）"""
        row = self.db.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            raise ValueError("订单不存在")
        current = normalize_order_status(row["order_status"])
        if not can_transition_order_status(current, target_status):
            raise ValueError(f"不允许从 {current} 转到 {target_status}")
        now = now_str()
        self.db.conn.execute(
            "UPDATE orders SET order_status = ?, order_status_updated_at = ?, updated_at = ? WHERE id = ?",
            (target_status, now, now, order_id),
        )
        self.db.conn.commit()
        self.db.log(username, "更新订单状态", f"订单 {row['order_no']}：{current} → {target_status}")
        return f"订单状态已更新：{current} → {target_status}"

    def batch_update_status(
        self,
        order_ids: List[int],
        target_status: str,
        username: str = "system",
    ) -> str:
        """批量更新订单状态"""
        success = 0
        failed = 0
        for oid in order_ids:
            try:
                self.update_order_status(oid, target_status, username)
                success += 1
            except ValueError:
                failed += 1
        return f"批量更新完成：成功 {success}，失败 {failed}"


class InventoryService:
    """库存业务逻辑"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def stock_in(
        self,
        sku: str,
        qty: int,
        warehouse: str = "默认仓库",
        cost_price: float = 0.0,
        operator: str = "system",
        remark: str = "",
    ) -> str:
        """入库"""
        self.db.adjust_inventory(sku, "入库", qty, warehouse, operator=operator, remark=remark)
        if cost_price > 0:
            inv = self.db.get_inventory(sku, warehouse)
            if inv:
                self.db.conn.execute(
                    "UPDATE inventory SET cost_price = ? WHERE sku = ? AND warehouse = ?",
                    (cost_price, sku, warehouse),
                )
                self.db.conn.commit()
        self.db.log(operator, "入库", f"SKU {sku}，数量 {qty}，仓库 {warehouse}")
        return f"入库完成：{sku} +{qty}"

    def stock_out(
        self,
        sku: str,
        qty: int,
        warehouse: str = "默认仓库",
        order_no: str = "",
        operator: str = "system",
        remark: str = "",
    ) -> str:
        """出库"""
        inv = self.db.get_inventory(sku, warehouse)
        if not inv or inv["available_qty"] < qty:
            available = inv["available_qty"] if inv else 0
            raise ValueError(f"库存不足：{sku} 可用 {available}，需要 {qty}")
        self.db.adjust_inventory(sku, "出库", qty, warehouse, order_no=order_no, operator=operator, remark=remark)
        self.db.log(operator, "出库", f"SKU {sku}，数量 {qty}，订单 {order_no}")
        return f"出库完成：{sku} -{qty}"

    def get_low_stock_warnings(self) -> List:
        """获取低库存预警"""
        return self.db.get_low_stock_warnings()

    def stock_check(
        self,
        sku: str,
        actual_qty: int,
        warehouse: str = "默认仓库",
        operator: str = "system",
    ) -> str:
        """盘点调整"""
        inv = self.db.get_inventory(sku, warehouse)
        before = int(inv["available_qty"]) if inv else 0
        diff = actual_qty - before
        self.db.adjust_inventory(sku, "盘点调整", actual_qty, warehouse, operator=operator, remark=f"盘点：{before}→{actual_qty}")
        self.db.log(operator, "盘点调整", f"SKU {sku}，{before}→{actual_qty}，差异 {diff}")
        return f"盘点完成：{sku} {before}→{actual_qty}"


class FinanceService:
    """财务业务逻辑"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def record_income(
        self,
        order_no: str,
        amount: float,
        platform_source: str = "知护",
        payment_method: str = "",
        remark: str = "",
        username: str = "system",
    ) -> str:
        """记录收入"""
        self.db.add_finance_record({
            "order_no": order_no,
            "platform_source": platform_source,
            "type": "收入",
            "category": "书款",
            "amount": amount,
            "payment_method": payment_method,
            "remark": remark,
        })
        self.db.log(username, "记录收入", f"订单 {order_no}，金额 {amount}")
        return f"收入已记录：{order_no} ¥{amount}"

    def record_expense(
        self,
        order_no: str,
        amount: float,
        category: str = "采购",
        platform_source: str = "",
        payment_method: str = "",
        remark: str = "",
        username: str = "system",
    ) -> str:
        """记录支出"""
        self.db.add_finance_record({
            "order_no": order_no,
            "platform_source": platform_source,
            "type": "支出",
            "category": category,
            "amount": amount,
            "payment_method": payment_method,
            "remark": remark,
        })
        self.db.log(username, "记录支出", f"订单 {order_no}，{category} ¥{amount}")
        return f"支出已记录：{order_no} ¥{amount}"

    def record_commission(
        self,
        order_no: str,
        amount: float,
        platform_source: str = "",
        remark: str = "",
        username: str = "system",
    ) -> str:
        """记录平台佣金"""
        self.db.add_finance_record({
            "order_no": order_no,
            "platform_source": platform_source,
            "type": "佣金",
            "category": "平台佣金",
            "amount": amount,
            "remark": remark,
        })
        self.db.log(username, "记录佣金", f"订单 {order_no}，平台 {platform_source}，佣金 ¥{amount}")
        return f"佣金已记录：{order_no} ¥{amount}"

    def get_profit_report(
        self,
        platform_source: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> Dict[str, Any]:
        """利润报表"""
        finance_summary = self.db.get_finance_summary(platform_source, start_date, end_date)
        return finance_summary
