# -*- coding: utf-8 -*-
"""
财务管理页面
"""
from typing import Any


def build_finance_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="财务管理")

    # ---- 顶部汇总区 ----
    summary_frame = gui.ttk.LabelFrame(frame, text="财务汇总")
    summary_frame.pack(fill="x", padx=6, pady=6)

    gui.finance_vars = {
        "income": gui.tk.StringVar(value="0.00"),
        "expense": gui.tk.StringVar(value="0.00"),
        "commission": gui.tk.StringVar(value="0.00"),
        "refund": gui.tk.StringVar(value="0.00"),
        "net_profit": gui.tk.StringVar(value="0.00"),
    }
    labels = [
        ("收入", "income", "#2e7d32"),
        ("支出", "expense", "#c62828"),
        ("佣金", "commission", "#e65100"),
        ("退款", "refund", "#6a1b9a"),
        ("净利润", "net_profit", "#1565c0"),
    ]
    for idx, (title, key, color) in enumerate(labels):
        card = gui.ttk.LabelFrame(summary_frame, text=title)
        card.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")
        lbl = gui.ttk.Label(card, textvariable=gui.finance_vars[key], font=("Microsoft YaHei", 14, "bold"))
        lbl.pack(padx=16, pady=8)

    # ---- 筛选栏 ----
    filter_frame = gui.ttk.Frame(frame)
    filter_frame.pack(fill="x", padx=6, pady=4)

    gui.finance_platform_var = gui.tk.StringVar(value="全部")
    gui.finance_type_var = gui.tk.StringVar(value="全部")
    gui.finance_start_date_var = gui.tk.StringVar()
    gui.finance_end_date_var = gui.tk.StringVar()

    gui.ttk.Label(filter_frame, text="平台:").pack(side="left", padx=4)
    gui.ttk.Combobox(
        filter_frame, textvariable=gui.finance_platform_var,
        values=["全部", "知护", "淘宝", "天猫", "京东", "拼多多", "抖音", "快手", "闲鱼"],
        width=8, state="readonly",
    ).pack(side="left", padx=4)

    gui.ttk.Label(filter_frame, text="类型:").pack(side="left", padx=4)
    gui.ttk.Combobox(
        filter_frame, textvariable=gui.finance_type_var,
        values=["全部", "收入", "支出", "佣金", "退款"],
        width=8, state="readonly",
    ).pack(side="left", padx=4)

    gui.ttk.Label(filter_frame, text="起始日期:").pack(side="left", padx=4)
    gui.ttk.Entry(filter_frame, textvariable=gui.finance_start_date_var, width=12).pack(side="left", padx=4)
    gui.ttk.Label(filter_frame, text="截止日期:").pack(side="left", padx=4)
    gui.ttk.Entry(filter_frame, textvariable=gui.finance_end_date_var, width=12).pack(side="left", padx=4)

    gui.ttk.Button(filter_frame, text="查询", command=refresh_finance).pack(side="left", padx=8)

    # ---- 操作按钮 ----
    btn_frame = gui.ttk.Frame(frame)
    btn_frame.pack(fill="x", padx=6, pady=2)
    gui.ttk.Button(btn_frame, text="记录收入", command=lambda: add_record_dialog("收入")).pack(side="left", padx=4)
    gui.ttk.Button(btn_frame, text="记录支出", command=lambda: add_record_dialog("支出")).pack(side="left", padx=4)
    gui.ttk.Button(btn_frame, text="记录佣金", command=lambda: add_record_dialog("佣金")).pack(side="left", padx=4)
    gui.ttk.Button(btn_frame, text="刷新", command=refresh_finance).pack(side="left", padx=4)

    # ---- 财务记录列表 ----
    tree_frame = gui.ttk.Frame(frame)
    tree_frame.pack(fill="both", expand=True, padx=6, pady=4)

    columns = ("created_at", "order_no", "platform_source", "type", "category", "amount", "payment_method", "remark")
    headers = ("时间", "订单号", "平台", "类型", "分类", "金额", "支付方式", "备注")
    widths = (140, 140, 80, 60, 80, 90, 100, 150)

    gui.finance_tree = gui.ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
    for col, header, width in zip(columns, headers, widths):
        gui.finance_tree.heading(col, text=header)
        gui.finance_tree.column(col, width=width, minwidth=40)

    scrollbar = gui.ttk.Scrollbar(tree_frame, orient="vertical", command=gui.finance_tree.yview)
    gui.finance_tree.configure(yscrollcommand=scrollbar.set)
    gui.finance_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 颜色标记
    gui.finance_tree.tag_configure("income", foreground="#2e7d32")
    gui.finance_tree.tag_configure("expense", foreground="#c62828")
    gui.finance_tree.tag_configure("commission", foreground="#e65100")
    gui.finance_tree.tag_configure("refund", foreground="#6a1b9a")

    # 首次加载
    refresh_finance()


def refresh_finance():
    """刷新财务数据"""
    gui = _get_gui()
    if not gui or not hasattr(gui, "finance_tree"):
        return

    # 更新汇总
    platform = gui.finance_platform_var.get() if hasattr(gui, "finance_platform_var") else ""
    start_date = gui.finance_start_date_var.get().strip() if hasattr(gui, "finance_start_date_var") else ""
    end_date = gui.finance_end_date_var.get().strip() if hasattr(gui, "finance_end_date_var") else ""

    p = "" if platform == "全部" else platform
    summary = gui.db.get_finance_summary(platform_source=p, start_date=start_date, end_date=end_date)

    if hasattr(gui, "finance_vars"):
        gui.finance_vars["income"].set(f"¥{summary.get('收入', 0):.2f}")
        gui.finance_vars["expense"].set(f"¥{summary.get('支出', 0):.2f}")
        gui.finance_vars["commission"].set(f"¥{summary.get('佣金', 0):.2f}")
        gui.finance_vars["refund"].set(f"¥{summary.get('退款', 0):.2f}")
        gui.finance_vars["net_profit"].set(f"¥{summary.get('净利润', 0):.2f}")

    # 更新记录列表
    for item in gui.finance_tree.get_children():
        gui.finance_tree.delete(item)

    record_type = gui.finance_type_var.get() if hasattr(gui, "finance_type_var") else ""
    rt = "" if record_type == "全部" else record_type

    rows = gui.db.list_finance_records(
        platform_source=p, record_type=rt, start_date=start_date, end_date=end_date,
    )

    for row in rows:
        tag = {"收入": "income", "支出": "expense", "佣金": "commission", "退款": "refund"}.get(row["type"], "")
        gui.finance_tree.insert("", "end", values=(
            row["created_at"],
            row["order_no"],
            row["platform_source"],
            row["type"],
            row["category"],
            f"¥{row['amount']:.2f}",
            row["payment_method"],
            row["remark"],
        ), tags=(tag,))


def add_record_dialog(record_type):
    """添加财务记录对话框"""
    gui = _get_gui()
    if not gui:
        return

    dialog = gui.tk.Toplevel(gui.root)
    dialog.title(f"记录{record_type}")
    dialog.geometry("450x350")
    dialog.transient(gui.root)
    dialog.grab_set()

    vars_dict = {
        "order_no": gui.tk.StringVar(),
        "amount": gui.tk.StringVar(),
        "platform_source": gui.tk.StringVar(value="知护"),
        "category": gui.tk.StringVar(value="书款" if record_type == "收入" else "采购"),
        "payment_method": gui.tk.StringVar(),
        "remark": gui.tk.StringVar(),
    }

    fields = [
        ("订单号", "order_no"),
        ("金额", "amount"),
        ("平台", "platform_source"),
        ("分类", "category"),
        ("支付方式", "payment_method"),
        ("备注", "remark"),
    ]

    for idx, (label, key) in enumerate(fields):
        gui.ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="e", padx=10, pady=8)
        if key == "platform_source":
            gui.ttk.Combobox(
                dialog, textvariable=vars_dict[key],
                values=["知护", "淘宝", "天猫", "京东", "拼多多", "抖音", "快手"],
                width=20, state="readonly",
            ).grid(row=idx, column=1, sticky="w", padx=10, pady=8)
        elif key == "category":
            categories = {
                "收入": ["书款", "运费", "其他"],
                "支出": ["采购", "运费", "包装", "其他"],
                "佣金": ["平台佣金", "推广佣金"],
                "退款": ["订单退款", "运费退款"],
            }
            gui.ttk.Combobox(
                dialog, textvariable=vars_dict[key],
                values=categories.get(record_type, ["其他"]),
                width=20, state="readonly",
            ).grid(row=idx, column=1, sticky="w", padx=10, pady=8)
        else:
            gui.ttk.Entry(dialog, textvariable=vars_dict[key], width=25).grid(row=idx, column=1, sticky="w", padx=10, pady=8)

    def do_save():
        from core.utils import safe_text, to_float
        order_no = safe_text(vars_dict["order_no"].get())
        amount = to_float(vars_dict["amount"].get(), 0.0)
        if amount <= 0:
            gui.messagebox.showwarning("提示", "金额必须大于0")
            return
        gui.db.add_finance_record({
            "order_no": order_no,
            "platform_source": safe_text(vars_dict["platform_source"].get()),
            "type": record_type,
            "category": safe_text(vars_dict["category"].get()),
            "amount": amount,
            "payment_method": safe_text(vars_dict["payment_method"].get()),
            "remark": safe_text(vars_dict["remark"].get()),
        }, gui.current_user)
        gui.db.log(gui.current_user, f"记录{record_type}", f"订单 {order_no} ¥{amount}")
        gui.messagebox.showinfo("成功", f"{record_type}已记录：¥{amount}")
        dialog.destroy()
        refresh_finance()

    gui.ttk.Button(dialog, text="保存", command=do_save).grid(row=len(fields), column=0, columnspan=2, pady=16)


def _get_gui():
    """获取全局GUI实例"""
    import __main__
    if hasattr(__main__, "_gui_instance"):
        return __main__._gui_instance
    return None
