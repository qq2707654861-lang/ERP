from typing import Any


def build_dashboard_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="首页概览")

    stat_frame = gui.ttk.Frame(frame)
    stat_frame.pack(fill="x", pady=10)
    gui.dashboard_vars = {
        "total_orders": gui.tk.StringVar(value="0"),
        "total_books": gui.tk.StringVar(value="0"),
        "pending_orders": gui.tk.StringVar(value="0"),
        "gross_profit": gui.tk.StringVar(value="0.00"),
        "total_receivable": gui.tk.StringVar(value="0.00"),
    }
    labels = [
        ("订单总数", "total_orders"),
        ("图书总数", "total_books"),
        ("待处理订单", "pending_orders"),
        ("粗算毛利", "gross_profit"),
        ("应收金额汇总", "total_receivable"),
    ]
    for idx, (title, key) in enumerate(labels):
        card = gui.ttk.LabelFrame(stat_frame, text=title)
        card.grid(row=0, column=idx, padx=8, pady=4, sticky="nsew")
        gui.ttk.Label(card, textvariable=gui.dashboard_vars[key], font=("Microsoft YaHei", 18, "bold")).pack(padx=24, pady=14)

    btns = gui.ttk.Frame(frame)
    btns.pack(fill="x", pady=6)
    gui.ttk.Button(btns, text="刷新概览", command=gui.refresh_dashboard).pack(side="left")
    gui.ttk.Button(btns, text="一键导入示例表格", command=gui.import_default_sample).pack(side="left", padx=8)

    gui.dashboard_text = gui.tk.Text(frame, height=28, wrap="word")
    gui.dashboard_text.pack(fill="both", expand=True, padx=4, pady=6)
