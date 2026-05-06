# -*- coding: utf-8 -*-
"""
REST API — FastAPI，支持外部调用和手机端
启动：uvicorn core.api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# FastAPI可选依赖
try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from .config import DB_PATH, PLATFORM_SOURCES
from .db import DatabaseManager
from .services import OrderService, InventoryService, FinanceService

if HAS_FASTAPI:
    app = FastAPI(title="知护图书ERP API", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局DB实例（生产环境应改为依赖注入）
    _db = DatabaseManager(DB_PATH)
    order_svc = OrderService(_db)
    inventory_svc = InventoryService(_db)
    finance_svc = FinanceService(_db)

    # ---------- Pydantic 模型 ----------
    class OrderImportRequest(BaseModel):
        file_path: str
        platform_name: str = ""

    class StatusUpdateRequest(BaseModel):
        order_id: int
        target_status: str
        username: str = "api"

    class InventoryInRequest(BaseModel):
        sku: str
        qty: int
        warehouse: str = "默认仓库"
        cost_price: float = 0.0
        operator: str = "api"
        remark: str = ""

    class InventoryOutRequest(BaseModel):
        sku: str
        qty: int
        warehouse: str = "默认仓库"
        order_no: str = ""
        operator: str = "api"
        remark: str = ""

    class FinanceRecordRequest(BaseModel):
        order_no: str = ""
        amount: float
        record_type: str  # income / expense / commission
        category: str = "书款"
        platform_source: str = "知护"
        payment_method: str = ""
        remark: str = ""
        username: str = "api"

    # ---------- API 路由 ----------
    @app.get("/")
    def root():
        return {"name": "知护图书ERP API", "version": "2.0.0", "platforms": PLATFORM_SOURCES}

    # --- 仪表盘 ---
    @app.get("/api/dashboard")
    def dashboard():
        return _db.get_dashboard_stats()

    # --- 订单 ---
    @app.get("/api/orders")
    def list_orders(
        keyword: str = "",
        order_status: str = "",
        platform_source: str = "",
        shop_name: str = "",
        start_date: str = "",
        end_date: str = "",
    ):
        rows = _db.list_orders(
            keyword=keyword, order_status=order_status,
            platform_source=platform_source, shop_name=shop_name,
            start_date=start_date, end_date=end_date,
        )
        return [dict(row) for row in rows]

    @app.get("/api/orders/{order_no}")
    def get_order(order_no: str):
        row = _db.get_order_by_no(order_no)
        if not row:
            raise HTTPException(status_code=404, detail="订单不存在")
        return dict(row)

    @app.post("/api/orders/import")
    def import_orders(req: OrderImportRequest):
        path = Path(req.file_path)
        if not path.exists():
            raise HTTPException(status_code=400, detail="文件不存在")
        try:
            result = order_svc.import_orders(path, req.platform_name, "api")
            return {"message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/orders/status")
    def update_status(req: StatusUpdateRequest):
        try:
            result = order_svc.update_order_status(req.order_id, req.target_status, req.username)
            return {"message": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- 库存 ---
    @app.get("/api/inventory")
    def list_inventory(keyword: str = "", warehouse: str = ""):
        rows = _db.list_inventory(keyword=keyword, warehouse=warehouse)
        return [dict(row) for row in rows]

    @app.get("/api/inventory/warnings")
    def low_stock_warnings():
        rows = inventory_svc.get_low_stock_warnings()
        return [dict(row) for row in rows]

    @app.post("/api/inventory/in")
    def stock_in(req: InventoryInRequest):
        try:
            result = inventory_svc.stock_in(req.sku, req.qty, req.warehouse, req.cost_price, req.operator, req.remark)
            return {"message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/inventory/out")
    def stock_out(req: InventoryOutRequest):
        try:
            result = inventory_svc.stock_out(req.sku, req.qty, req.warehouse, req.order_no, req.operator, req.remark)
            return {"message": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- 财务 ---
    @app.get("/api/finance/records")
    def list_finance_records(
        order_no: str = "",
        platform_source: str = "",
        record_type: str = "",
        start_date: str = "",
        end_date: str = "",
    ):
        rows = _db.list_finance_records(order_no, platform_source, record_type, start_date, end_date)
        return [dict(row) for row in rows]

    @app.get("/api/finance/summary")
    def finance_summary(platform_source: str = "", start_date: str = "", end_date: str = ""):
        return finance_svc.get_profit_report(platform_source, start_date, end_date)

    @app.post("/api/finance/record")
    def add_finance_record(req: FinanceRecordRequest):
        if req.record_type == "income":
            result = finance_svc.record_income(req.order_no, req.amount, req.platform_source, req.payment_method, req.remark, req.username)
        elif req.record_type == "expense":
            result = finance_svc.record_expense(req.order_no, req.amount, req.category, req.platform_source, req.payment_method, req.remark, req.username)
        elif req.record_type == "commission":
            result = finance_svc.record_commission(req.order_no, req.amount, req.platform_source, req.remark, req.username)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的类型：{req.record_type}")
        return {"message": result}

    # --- 图书 ---
    @app.get("/api/books")
    def list_books(keyword: str = ""):
        rows = _db.list_books(keyword=keyword)
        return [dict(row) for row in rows]

    # --- 平台 ---
    @app.get("/api/platforms")
    def list_platforms():
        return PLATFORM_SOURCES

else:
    # FastAPI未安装时提供占位
    app = None  # type: ignore
