# -*- coding: utf-8 -*-
"""
库存管理页面
"""
from typing import Any


def build_inventory_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="库存管理")

    # ---- 顶部操作栏 ----
    top = gui.ttk.Frame(frame)
    top.pack(fill="x", padx=6, pady=6)

    gui.inventory_search_var = gui.tk.StringVar()
    gui.ttk.Label(top, text="搜索SKU:").pack(side="left", padx=4)
    gui.ttk.Entry(top, textvariable=gui.inventory_search_var, width=20).pack(side="left", padx=4)
    gui.ttk.Button(top, text="刷新", command=refresh_inventory).pack(side="left", padx=4)
    gui.ttk.Button(top, text="低库存预警", command=show_low_stock_warnings).pack(side="left", padx=4)

    # ---- 入库/出库按钮 ----
    action_frame = gui.ttk.Frame(top)
    action_frame.pack(side="right", padx=4)
    gui.ttk.Button(action_frame, text="入库", command=lambda: stock_in_out_dialog("入库")).pack(side="left", padx=2)
    gui.ttk.Button(action_frame, text="出库", command=lambda: stock_in_out_dialog("出库")).pack(side="left", padx=2)
    gui.ttk.Button(action_frame, text="盘点调整", command=stock_check_dialog).pack(side="left", padx=2)

    # ---- 库存列表 ----
    columns = ("sku", "warehouse", "available", "locked", "in_transit", "min_stock", "cost_price")
    headers = ("SKU", "仓库", "可用库存", "锁定库存", "在途库存", "最低库存", "成本价")
    widths = (150, 100, 80, 80, 80, 80, 80)

    tree_frame = gui.ttk.Frame(frame)
    tree_frame.pack(fill="both", expand=True, padx=6, pady=4)

    gui.inventory_tree = gui.ttk.Treeview(tree_frame, columns=columns, show="headings", height=25)
    for col, header, width in zip(columns, headers, widths):
        gui.inventory_tree.heading(col, text=header)
        gui.inventory_tree.column(col, width=width, minwidth=50)

    scrollbar = gui.ttk.Scrollbar(tree_frame, orient="vertical", command=gui.inventory_tree.yview)
    gui.inventory_tree.configure(yscrollcommand=scrollbar.set)
    gui.inventory_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ---- 底部详情区 ----
    detail_frame = gui.ttk.LabelFrame(frame, text="库存变动记录")
    detail_frame.pack(fill="x", padx=6, pady=4)

    log_columns = ("created_at", "change_type", "change_qty", "before_qty", "after_qty", "order_no", "operator")
    log_headers = ("时间", "类型", "变动数量", "变动前", "变动后", "订单号", "操作人")
    log_widths = (140, 80, 80, 80, 80, 140, 80)

    gui.inventory_log_tree = gui.ttk.Treeview(detail_frame, columns=log_columns, show="headings", height=6)
    for col, header, width in zip(log_columns, log_headers, log_widths):
        gui.inventory_log_tree.heading(col, text=header)
        gui.inventory_log_tree.column(col, width=width, minwidth=50)
    gui.inventory_log_tree.pack(fill="both", expand=True, padx=2, pady=2)

    # 选中库存行时显示变动记录
    gui.inventory_tree.bind("<<TreeviewSelect>>", on_inventory_select)

    # 首次加载
    refresh_inventory()


def refresh_inventory():
    """刷新库存列表"""
    import sys
    sys.path.insert(0, ".")

    gui = _get_gui()
    if not gui or not hasattr(gui, "inventory_tree"):
        return

    for item in gui.inventory_tree.get_children():
        gui.inventory_tree.delete(item)

    keyword = gui.inventory_search_var.get().strip() if hasattr(gui, "inventory_search_var") else ""
    rows = gui.db.list_inventory(keyword=keyword)

    for row in rows:
        # 低库存标红
        tags = ()
        if row["available_qty"] <= row["min_stock_qty"]:
            tags = ("low_stock",)
        gui.inventory_tree.insert("", "end", values=(
            row["sku"],
            row["warehouse"],
            row["available_qty"],
            row["locked_qty"],
            row["in_transit_qty"],
            row["min_stock_qty"],
            f"{row['cost_price']:.2f}" if row["cost_price"] else "0.00",
        ), tags=tags)

    gui.inventory_tree.tag_configure("low_stock", foreground="red")


def on_inventory_select(event=None):
    """选中库存行，显示变动记录"""
    gui = _get_gui()
    if not gui or not hasattr(gui, "inventory_log_tree"):
        return

    for item in gui.inventory_log_tree.get_children():
        gui.inventory_log_tree.delete(item)

    selection = gui.inventory_tree.selection()
    if not selection:
        return

    values = gui.inventory_tree.item(selection[0], "values")
    sku = values[0] if values else ""
    if not sku:
        return

    rows = gui.db.conn.execute(
        "SELECT * FROM inventory_logs WHERE sku = ? ORDER BY created_at DESC LIMIT 50",
        (sku,),
    ).fetchall()

    for row in rows:
        gui.inventory_log_tree.insert("", "end", values=(
            row["created_at"],
            row["change_type"],
            row["change_qty"],
            row["before_qty"],
            row["after_qty"],
            row["order_no"],
            row["operator"],
        ))


def show_low_stock_warnings():
    """显示低库存预警"""
    gui = _get_gui()
    if not gui:
        return
    rows = gui.db.get_low_stock_warnings()
    if not rows:
        gui.messagebox.showinfo("库存预警", "所有商品库存充足，无预警")
        return
    lines = []
    for row in rows:
        name = row["book_name"] if "book_name" in row.keys() else row["sku"]
        lines.append(f"{name}({row['sku']}): 可用{row['available_qty']}，最低{row['min_stock_qty']}")
    gui.messagebox.showwarning("库存预警", "以下商品库存不足：\n\n" + "\n".join(lines))


def stock_in_out_dialog(action_type):
    """入库/出库对话框"""
    gui = _get_gui()
    if not gui:
        return
    dialog = gui.tk.Toplevel(gui.root)
    dialog.title(f"{'入库' if action_type == '入库' else '出库'}操作")
    dialog.geometry("400x300")
    dialog.transient(gui.root)
    dialog.grab_set()

    vars_dict = {
        "sku": gui.tk.StringVar(),
        "qty": gui.tk.StringVar(value="1"),
        "warehouse": gui.tk.StringVar(value="默认仓库"),
        "cost_price": gui.tk.StringVar(value="0"),
        "remark": gui.tk.StringVar(),
    }

    fields = [
        ("SKU/书号", "sku"),
        ("数量", "qty"),
        ("仓库", "warehouse"),
        ("成本价", "cost_price"),
        ("备注", "remark"),
    ]

    for idx, (label, key) in enumerate(fields):
        gui.ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="e", padx=10, pady=8)
        gui.ttk.Entry(dialog, textvariable=vars_dict[key], width=30).grid(row=idx, column=1, sticky="w", padx=10, pady=8)

    def do_action():
        from core.utils import to_float, to_int, safe_text
        sku = safe_text(vars_dict["sku"].get())
        qty = to_int(vars_dict["qty"].get(), 0)
        warehouse = safe_text(vars_dict["warehouse"].get()) or "默认仓库"
        cost_price = to_float(vars_dict["cost_price"].get(), 0.0)
        remark = safe_text(vars_dict["remark"].get())

        if not sku or qty <= 0:
            gui.messagebox.showwarning("提示", "SKU和数量不能为空")
            return

        try:
            if action_type == "入库":
                gui.db.adjust_inventory(sku, "入库", qty, warehouse, operator=gui.current_user, remark=remark)
                if cost_price > 0:
                    inv = gui.db.get_inventory(sku, warehouse)
                    if inv:
                        gui.db.conn.execute(
                            "UPDATE inventory SET cost_price = ? WHERE sku = ? AND warehouse = ?",
                            (cost_price, sku, warehouse),
                        )
                        gui.db.conn.commit()
                gui.db.log(gui.current_user, "入库", f"SKU {sku} +{qty} 仓库 {warehouse}")
            else:
                inv = gui.db.get_inventory(sku, warehouse)
                available = int(inv["available_qty"]) if inv else 0
                if available < qty:
                    gui.messagebox.showwarning("库存不足", f"{sku} 可用库存 {available}，不足 {qty}")
                    return
                gui.db.adjust_inventory(sku, "出库", qty, warehouse, operator=gui.current_user, remark=remark)
                gui.db.log(gui.current_user, "出库", f"SKU {sku} -{qty} 仓库 {warehouse}")

            gui.messagebox.showinfo("成功", f"{action_type}完成：{sku} {'+' if action_type == '入库' else '-'}{qty}")
            dialog.destroy()
            refresh_inventory()
        except Exception as e:
            gui.messagebox.showerror("操作失败", str(e))

    gui.ttk.Button(dialog, text="确认", command=do_action).grid(row=len(fields), column=0, columnspan=2, pady=16)


def stock_check_dialog():
    """盘点调整对话框"""
    gui = _get_gui()
    if not gui:
        return
    dialog = gui.tk.Toplevel(gui.root)
    dialog.title("盘点调整")
    dialog.geometry("400x200")
    dialog.transient(gui.root)
    dialog.grab_set()

    sku_var = gui.tk.StringVar()
    qty_var = gui.tk.StringVar()
    warehouse_var = gui.tk.StringVar(value="默认仓库")

    fields = [("SKU/书号", sku_var), ("实际库存数量", qty_var), ("仓库", warehouse_var)]
    for idx, (label, var) in enumerate(fields):
        gui.ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="e", padx=10, pady=8)
        gui.ttk.Entry(dialog, textvariable=var, width=30).grid(row=idx, column=1, sticky="w", padx=10, pady=8)

    def do_check():
        from core.utils import safe_text, to_int
        sku = safe_text(sku_var.get())
        qty = to_int(qty_var.get(), 0)
        warehouse = safe_text(warehouse_var.get()) or "默认仓库"
        if not sku:
            gui.messagebox.showwarning("提示", "SKU不能为空")
            return
        gui.db.adjust_inventory(sku, "盘点调整", qty, warehouse, operator=gui.current_user, remark="盘点")
        gui.db.log(gui.current_user, "盘点调整", f"SKU {sku} -> {qty}")
        gui.messagebox.showinfo("成功", f"盘点完成：{sku} -> {qty}")
        dialog.destroy()
        refresh_inventory()

    gui.ttk.Button(dialog, text="确认盘点", command=do_check).grid(row=len(fields), column=0, columnspan=2, pady=16)


def _get_gui():
    """获取全局GUI实例"""
    # 通过hack获取GUI（因为build函数只传gui参数，其他回调需要访问）
    import __main__
    if hasattr(__main__, "_gui_instance"):
        return __main__._gui_instance
    return None
