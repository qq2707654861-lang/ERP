from typing import Any


def build_status_tab(gui: Any, status: str) -> None:
    frame = gui._create_notebook_tab(status)
    top = gui.ttk.Frame(frame)
    top.pack(fill="x", pady=6)
    search_var = gui.tk.StringVar()
    start_date_var = gui.tk.StringVar()
    end_date_var = gui.tk.StringVar()
    count_var = gui.tk.StringVar(value="0")
    gui._build_order_filter_bar(
        top,
        search_var,
        start_date_var,
        end_date_var,
        query_command=lambda: gui.refresh_status_tab(status),
    )
    gui._build_page_summary(frame, status, count_var)
    tree = gui._create_bound_order_tree(frame, height=12)

    if status == "发货":
        gui._build_export_columns_section(frame, "status_shipment")

    action_frame = gui.ttk.Frame(frame)
    action_frame.pack(fill="x", pady=8)
    gui._build_status_action_bar(action_frame, status, tree)

    if status == "审核":
        account_frame = gui.ttk.LabelFrame(frame, text="采购淘宝账号设置")
        account_frame.pack(fill="x", padx=10, pady=(0, 6))
        gui.ttk.Label(account_frame, text="账号：").pack(side="left", padx=(8, 4), pady=8)
        gui.ttk.Entry(account_frame, textvariable=gui.taobao_account_var, width=24).pack(side="left", padx=4)
        gui.ttk.Label(account_frame, text="密码：").pack(side="left", padx=(12, 4))
        gui.ttk.Entry(account_frame, textvariable=gui.taobao_password_var, width=24, show="*").pack(side="left", padx=4)
        gui.ttk.Button(account_frame, text="保存账号", command=gui.save_procurement_account_settings).pack(side="left", padx=8)
        gui.ttk.Button(account_frame, text="一键获取登录态", command=gui.bootstrap_taobao_login_state).pack(side="left", padx=6)
        gui.ttk.Button(account_frame, text="检测有效性", command=gui.check_taobao_login_state_validity_async).pack(side="left", padx=4)
        gui.ttk.Button(account_frame, text="清除登录态", command=gui.clear_taobao_login_state).pack(side="left", padx=4)
        gui.ttk.Label(account_frame, textvariable=gui.taobao_login_state_status_var, foreground="#0a7f2e").pack(side="left", padx=8)
        gui.ttk.Label(account_frame, textvariable=gui.taobao_login_state_validity_var, foreground="#0a5f9c").pack(side="left", padx=8)
        gui.ttk.Label(
            account_frame,
            text="登录态保存在本机 Playwright 配置目录中，不读取也不明文保存 Cookie。",
            foreground="#666666",
        ).pack(side="left", padx=10)

        product_frame = gui.ttk.LabelFrame(frame, text="采购商品库")
        product_frame.pack(fill="x", padx=10, pady=(0, 6))
        columns = ("商品名称", "书号/ISBN", "价格", "店铺", "商品ID")
        gui.procurement_product_tree = gui.ttk.Treeview(product_frame, columns=columns, show="headings", height=6)
        for col in columns:
            gui.procurement_product_tree.heading(col, text=col)
            gui.procurement_product_tree.column(col, width=110 if col != "商品名称" else 220, anchor="center")
        product_ybar = gui.ttk.Scrollbar(product_frame, orient="vertical", command=gui.procurement_product_tree.yview)
        gui.procurement_product_tree.configure(yscrollcommand=product_ybar.set)
        gui.procurement_product_tree.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        product_ybar.pack(side="right", fill="y", pady=4)
        gui._load_procurement_products()

    gui.status_tab_contexts[status] = {
        "tree": tree,
        "search_var": search_var,
        "start_date_var": start_date_var,
        "end_date_var": end_date_var,
        "count_var": count_var,
    }
