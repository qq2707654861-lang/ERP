# -*- coding: utf-8 -*-
"""
ERP 订单管理系统 v2.0 — 模块化重构版

新增功能：
- 多平台订单导入（淘宝/拼多多/抖音/京东）
- 库存管理（出入库+预警）
- 财务记录（收入/支出/佣金/利润报表）
- REST API（FastAPI，可选）
- 订单表新增：平台来源/店铺名/佣金/退款/重量等字段

运行：
    python main.py                  # 启动Tkinter GUI
    python main.py --api            # 启动REST API
    python main.py --smoke-test     # 烟雾测试
    python main.py --api --gui      # 同时启动API和GUI
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# 确保项目根目录在 sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import APP_TITLE, DB_PATH, PLATFORM_SOURCES, ORDER_STATUS_FLOW
from core.db import DatabaseManager
from core.services import OrderService, InventoryService, FinanceService


def run_smoke_test(db: DatabaseManager) -> int:
    """烟雾测试"""
    print(f"[SmokeTest] 数据库路径: {db.db_path}")
    print(f"[SmokeTest] 支持平台: {PLATFORM_SOURCES}")

    stats = db.get_dashboard_stats()
    print("[SmokeTest] 仪表盘统计：")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # 测试库存
    print("\n[SmokeTest] 库存测试：")
    inv_svc = InventoryService(db)
    db.upsert_inventory({"sku": "TEST-001", "available_qty": 100, "min_stock_qty": 5})
    inv_svc.stock_in("TEST-001", 50, operator="smoke_test", remark="测试入库")
    warnings = inv_svc.get_low_stock_warnings()
    print(f"  - 低库存预警数: {len(warnings)}")

    # 测试财务
    print("\n[SmokeTest] 财务测试：")
    fin_svc = FinanceService(db)
    fin_svc.record_income("TEST-001", 100.0, platform_source="知护", username="smoke_test")
    fin_svc.record_expense("TEST-001", 60.0, category="采购", username="smoke_test")
    fin_svc.record_commission("TEST-001", 5.0, platform_source="知护", username="smoke_test")
    summary = fin_svc.get_profit_report()
    print(f"  - 财务汇总: {summary}")

    # 测试多平台适配
    print("\n[SmokeTest] 平台适配器：")
    from core.platforms import PLATFORM_ADAPTERS, get_adapter
    for name in PLATFORM_ADAPTERS:
        adapter = get_adapter(name)
        print(f"  - {name}: {adapter.__class__.__name__}")

    print("\n[SmokeTest] PASS - 全部通过")
    return 0


def run_gui(db: DatabaseManager) -> None:
    """启动Tkinter GUI（兼容旧界面）"""
    try:
        # 优先用兼容适配器启动旧GUI
        from compatibility import DatabaseManager as CompatDB
        compat_db = CompatDB(db.db_path)
        # 旧GUI在同一目录，动态导入
        import importlib.util
        old_gui_path = BASE_DIR / "ERP.py"
        if old_gui_path.exists():
            spec = importlib.util.spec_from_file_location("ERP", str(old_gui_path))
            if not spec or not spec.loader:
                raise RuntimeError("旧GUI模块加载器不可用")
            old_module = importlib.util.module_from_spec(spec)
            # 用兼容DB替换旧模块的DatabaseManager
            old_module.DatabaseManager = CompatDB
            spec.loader.exec_module(old_module)
            gui = old_module.OrderManagerGUI(compat_db)
            if getattr(gui, "root", None):
                gui.run()
            else:
                print("旧GUI未正确初始化窗口，使用简化界面...")
                _run_simple_gui(db)
        else:
            _run_simple_gui(db)
    except Exception as e:
        print(f"旧GUI启动失败: {e}")
        print("使用简化界面...")
        _run_simple_gui(db)


def _run_simple_gui(db: DatabaseManager) -> None:
    """简化版GUI（过渡用）"""
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    root = tk.Tk()
    root.title(f"{APP_TITLE} v2.0")
    root.geometry("1200x700")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # ---- 仪表盘 ----
    dashboard_frame = ttk.Frame(notebook)
    notebook.add(dashboard_frame, text="仪表盘")
    stats = db.get_dashboard_stats()
    stats_text = (
        f"总订单数: {stats['total_orders']}\n"
        f"待审核: {stats['pending_orders']}\n"
        f"发货中: {stats['shipping_orders']}\n"
        f"总营收: ¥{stats['total_revenue']:.2f}\n"
        f"总利润: ¥{stats['total_profit']:.2f}\n"
        f"未结算: {stats['unsettled_orders']}\n\n"
        f"平台分布:\n"
    )
    for platform, pstat in stats.get("platform_stats", {}).items():
        stats_text += f"  {platform}: {pstat['count']}单 ¥{pstat['revenue']:.2f}\n"
    ttk.Label(dashboard_frame, text=stats_text, font=("Consolas", 12), justify="left").pack(padx=20, pady=20, anchor="w")

    # ---- 订单 ----
    order_frame = ttk.Frame(notebook)
    notebook.add(order_frame, text="订单管理")

    # 平台/状态筛选
    filter_frame = ttk.Frame(order_frame)
    filter_frame.pack(fill="x", padx=5, pady=3)
    ttk.Label(filter_frame, text="平台:").pack(side="left", padx=3)
    platform_var = tk.StringVar(value="全部")
    platform_combo = ttk.Combobox(filter_frame, textvariable=platform_var, values=["全部"] + PLATFORM_SOURCES, width=10, state="readonly")
    platform_combo.pack(side="left", padx=3)
    ttk.Label(filter_frame, text="状态:").pack(side="left", padx=(10, 3))
    status_var = tk.StringVar(value="全部")
    status_combo = ttk.Combobox(filter_frame, textvariable=status_var, values=["全部"] + ORDER_STATUS_FLOW, width=10, state="readonly")
    status_combo.pack(side="left", padx=3)
    order_hint_var = tk.StringVar(value="")
    ttk.Label(filter_frame, textvariable=order_hint_var).pack(side="right", padx=5)

    order_tree = ttk.Treeview(
        order_frame,
        columns=("order_no", "platform", "product", "amount", "status"),
        show="headings",
        height=20,
        selectmode="extended",
    )
    order_tree.heading("order_no", text="订单号")
    order_tree.heading("platform", text="平台")
    order_tree.heading("product", text="商品")
    order_tree.heading("amount", text="金额")
    order_tree.heading("status", text="状态")
    order_tree.column("order_no", width=150)
    order_tree.column("platform", width=80)
    order_tree.column("product", width=250)
    order_tree.column("amount", width=80)
    order_tree.column("status", width=80)
    order_tree.pack(fill="both", expand=True, padx=5, pady=3)

    order_scroll_y = ttk.Scrollbar(order_frame, orient="vertical", command=order_tree.yview)
    order_scroll_x = ttk.Scrollbar(order_frame, orient="horizontal", command=order_tree.xview)
    order_tree.configure(yscrollcommand=order_scroll_y.set, xscrollcommand=order_scroll_x.set)
    order_scroll_y.pack(side="right", fill="y")
    order_scroll_x.pack(fill="x")

    order_cache = {}

    def show_order_detail(event=None):
        selected = order_tree.selection()
        if not selected:
            return
        values = order_tree.item(selected[0], "values")
        if not values:
            return
        order_no = values[0]
        row = order_cache.get(order_no)
        if not row:
            messagebox.showwarning("提示", "未找到订单详情，请先刷新列表")
            return

        detail_win = tk.Toplevel(root)
        detail_win.title(f"订单详情 - {order_no}")
        detail_win.geometry("900x650")

        text_frame = ttk.Frame(detail_win)
        text_frame.pack(fill="both", expand=True, padx=8, pady=8)
        detail_text = tk.Text(text_frame, wrap="word")
        detail_text.pack(side="left", fill="both", expand=True)
        detail_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=detail_text.yview)
        detail_scroll.pack(side="right", fill="y")
        detail_text.configure(yscrollcommand=detail_scroll.set)

        detail_lines = []
        for key in row.keys():
            detail_lines.append(f"{key}: {row[key]}")
        detail_text.insert("1.0", "\n".join(detail_lines))
        detail_text.configure(state="disabled")

    order_tree.bind("<Double-1>", show_order_detail)

    def refresh_orders():
        order_cache.clear()
        for item in order_tree.get_children():
            order_tree.delete(item)
        platform = platform_var.get()
        status = status_var.get()
        rows = db.list_orders(
            platform_source="" if platform == "全部" else platform,
            order_status="" if status == "全部" else status,
        )
        for row in rows:
            order_cache[row["order_no"]] = row
            order_tree.insert("", "end", iid=str(row["id"]), values=(
                row["order_no"], row["platform_source"],
                row["product_name"], f"¥{row['receivable_amount']}", row["order_status"]
            ))
        order_hint_var.set(f"共{len(rows)}条")

    ttk.Button(filter_frame, text="刷新", command=refresh_orders).pack(side="left", padx=5)

    def submit_audit():
        selected = order_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择至少一条订单")
            return
        order_svc = OrderService(db)
        success = 0
        failed_msgs = []
        for item_id in selected:
            values = order_tree.item(item_id, "values")
            if not values:
                continue
            order_id = int(item_id)
            order_no = values[0]
            current_status = values[4]
            if current_status != "审核":
                failed_msgs.append(f"{order_no}: 当前状态不是审核")
                continue
            try:
                order_svc.update_order_status(order_id, "配货", username="gui")
                success += 1
            except Exception as e:
                failed_msgs.append(f"{order_no}: {e}")

        refresh_orders()
        if failed_msgs:
            messagebox.showwarning(
                "审核提交结果",
                f"成功 {success} 条，失败 {len(failed_msgs)} 条\n\n" + "\n".join(failed_msgs[:15]),
            )
        else:
            messagebox.showinfo("审核提交结果", f"已提交 {success} 条订单进入配货")

    ttk.Button(filter_frame, text="审核提交(改为配货)", command=submit_audit).pack(side="left", padx=5)
    platform_combo.bind("<<ComboboxSelected>>", lambda _e: refresh_orders())
    status_combo.bind("<<ComboboxSelected>>", lambda _e: refresh_orders())

    # 导入按钮
    def import_file():
        file_path = filedialog.askopenfilename(
            title="选择订单文件",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("All", "*.*")],
        )
        if not file_path:
            return
        from core.platforms import auto_detect_platform
        platform = auto_detect_platform(Path(file_path))
        order_svc = OrderService(db)
        try:
            result = order_svc.import_orders(Path(file_path), platform)
            messagebox.showinfo("导入成功", result)
            refresh_orders()
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    ttk.Button(filter_frame, text="导入订单", command=import_file).pack(side="left", padx=5)
    refresh_orders()

    # ---- 库存 ----
    inv_frame = ttk.Frame(notebook)
    notebook.add(inv_frame, text="库存管理")

    inv_tree = ttk.Treeview(inv_frame, columns=("sku", "warehouse", "available", "locked", "min"), show="headings", height=20)
    inv_tree.heading("sku", text="SKU")
    inv_tree.heading("warehouse", text="仓库")
    inv_tree.heading("available", text="可用")
    inv_tree.heading("locked", text="锁定")
    inv_tree.heading("min", text="最低库存")
    inv_tree.column("sku", width=150)
    inv_tree.column("warehouse", width=100)
    inv_tree.column("available", width=80)
    inv_tree.column("locked", width=80)
    inv_tree.column("min", width=80)
    inv_tree.pack(fill="both", expand=True, padx=5, pady=3)

    def refresh_inventory():
        for item in inv_tree.get_children():
            inv_tree.delete(item)
        for row in db.list_inventory():
            inv_tree.insert("", "end", values=(
                row["sku"], row["warehouse"], row["available_qty"],
                row["locked_qty"], row["min_stock_qty"],
            ))

    inv_btn_frame = ttk.Frame(inv_frame)
    inv_btn_frame.pack(fill="x", padx=5, pady=3)
    ttk.Button(inv_btn_frame, text="刷新", command=refresh_inventory).pack(side="left", padx=3)
    ttk.Button(inv_btn_frame, text="低库存预警", command=lambda: messagebox.showinfo(
        "低库存预警",
        "\n".join(f"{r['sku']}: 可用{r['available_qty']}，最低{r['min_stock_qty']}" for r in db.get_low_stock_warnings()) or "无预警"
    )).pack(side="left", padx=3)
    refresh_inventory()

    # ---- 财务 ----
    fin_frame = ttk.Frame(notebook)
    notebook.add(fin_frame, text="财务管理")

    fin_svc = FinanceService(db)
    summary = fin_svc.get_profit_report()
    fin_text = (
        f"收入: ¥{summary.get('收入', 0):.2f}\n"
        f"支出: ¥{summary.get('支出', 0):.2f}\n"
        f"佣金: ¥{summary.get('佣金', 0):.2f}\n"
        f"退款: ¥{summary.get('退款', 0):.2f}\n"
        f"净利润: ¥{summary.get('净利润', 0):.2f}"
    )
    ttk.Label(fin_frame, text=fin_text, font=("Consolas", 12), justify="left").pack(padx=20, pady=20, anchor="w")

    root.mainloop()


def run_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """启动REST API"""
    from api.server import start_api
    start_api(host=host, port=port)


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--smoke-test", action="store_true", help="烟雾测试")
    parser.add_argument("--api", action="store_true", help="启动REST API")
    parser.add_argument("--gui", action="store_true", help="启动GUI")
    parser.add_argument("--host", default="0.0.0.0", help="API监听地址")
    parser.add_argument("--port", type=int, default=8000, help="API监听端口")
    args = parser.parse_args()

    if args.smoke_test:
        # 使用临时数据库执行烟雾测试，避免污染正式业务数据
        with tempfile.TemporaryDirectory(prefix="erp_order_smoke_") as tmp_dir:
            smoke_db_path = Path(tmp_dir) / "smoke_test.db"
            smoke_db = DatabaseManager(smoke_db_path)
            try:
                return run_smoke_test(smoke_db)
            finally:
                smoke_db.close()

    db = DatabaseManager(DB_PATH)
    try:

        if args.api and not args.gui:
            # 纯API模式
            run_api(host=args.host, port=args.port)
            return 0

        if args.api and args.gui:
            # API+GUI同时启动
            import threading
            api_thread = threading.Thread(
                target=run_api, args=(args.host, args.port), daemon=True
            )
            api_thread.start()
            print(f"API 已在后台启动：http://{args.host}:{args.port}")
            run_gui(db)
            return 0

        # 默认启动GUI
        run_gui(db)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
