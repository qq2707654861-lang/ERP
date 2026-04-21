from typing import Any


def build_settings_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="系统设置")

    outer = gui.ttk.Frame(frame)
    outer.pack(fill="both", expand=True)
    ybar = gui.ttk.Scrollbar(outer, orient="vertical")
    ybar.pack(side="left", fill="y", padx=(8, 0), pady=8)
    canvas = gui.tk.Canvas(outer, highlightthickness=0, yscrollcommand=ybar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(6, 8), pady=8)
    ybar.configure(command=canvas.yview)
    content = gui.ttk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def _sync_scroll_region(_event: Any = None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _sync_canvas_width(event: Any) -> None:
        canvas.itemconfigure(canvas_window, width=event.width)

    content.bind("<Configure>", _sync_scroll_region)
    canvas.bind("<Configure>", _sync_canvas_width)

    import_panel = gui.ttk.LabelFrame(content, text="数据导入")
    import_panel.pack(fill="both", expand=True, padx=12, pady=(12, 6))

    btn_frame = gui.ttk.Frame(import_panel)
    btn_frame.pack(fill="x", pady=10, padx=10)
    gui.ttk.Button(btn_frame, text="导入订单文件", command=gui.import_orders_file).pack(side="left", padx=5)
    gui.ttk.Button(btn_frame, text="导入图书资料", command=gui.import_books_file).pack(side="left", padx=5)
    gui.ttk.Button(btn_frame, text="导入供应商规则", command=gui.import_supplier_file).pack(side="left", padx=5)
    gui.ttk.Button(btn_frame, text="导入当前目录示例表格.xlsx", command=gui.import_default_sample).pack(side="left", padx=5)

    auto_import_panel = gui.ttk.LabelFrame(import_panel, text="微信订单一键导入")
    auto_import_panel.pack(fill="x", padx=10, pady=(0, 10))
    root_row = gui.ttk.Frame(auto_import_panel)
    root_row.pack(fill="x", padx=8, pady=(8, 6))
    gui.ttk.Label(root_row, text="微信文件根目录 / 月目录：").pack(side="left")
    gui.ttk.Entry(root_row, textvariable=gui.wechat_root_var, width=58).pack(side="left", padx=6, fill="x", expand=True)
    gui.ttk.Button(root_row, text="选择文件夹", command=gui.select_wechat_root_dir).pack(side="left", padx=4)
    gui.ttk.Button(root_row, text="自动定位", command=gui.auto_fill_wechat_root).pack(side="left", padx=4)
    gui.ttk.Button(root_row, text="一键查找最新订单并导入", command=gui.auto_import_latest_orders).pack(side="left", padx=4)
    gui.ttk.Label(
        auto_import_panel,
        text=(
            "支持直接填写微信根目录、msg/file 目录，或当月目录。\n"
            "点击一键查找后，系统会自动找到最新订单文件，智能识别订单工作表并导入审核页面。"
        ),
        justify="left",
    ).pack(anchor="w", padx=8, pady=(0, 8))

    tips = (
        "支持文件：CSV / XLSX\n"
        "建议格式：\n"
        "- 订单：包含 订单号、下单时间、收件人、SKU、数量 等字段\n"
        "- 图书资料：包含 书号、书名、定价、折扣、邮费 等字段\n"
        "- 当前目录下的 表格.xlsx 可直接作为初始化数据源"
    )
    gui.ttk.Label(import_panel, text=tips, justify="left").pack(anchor="w", padx=10)

    gui.import_log = gui.tk.Text(import_panel, height=12, wrap="word")
    gui.import_log.pack(fill="both", expand=True, padx=10, pady=(8, 10))

    playwright_panel = gui.ttk.LabelFrame(content, text="Playwright 采购环境")
    playwright_panel.pack(fill="x", padx=12, pady=(0, 6))
    gui.ttk.Label(
        playwright_panel,
        text="用于淘宝 Cookie 登录采购助手。依赖和 Chromium 浏览器未安装时，可在这里一键检测并打开安装终端。",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(10, 6))
    status_row = gui.ttk.Frame(playwright_panel)
    status_row.pack(fill="x", padx=10, pady=(0, 8))
    gui.ttk.Label(status_row, textvariable=gui.playwright_status_var, foreground="#0a5f9c").pack(side="left")
    gui.ttk.Button(status_row, text="重新检测", command=gui.refresh_playwright_status).pack(side="left", padx=8)
    gui.ttk.Button(status_row, text="安装 Playwright 依赖", command=gui.install_playwright_package).pack(side="left", padx=4)
    gui.ttk.Button(status_row, text="安装 Chromium 浏览器", command=gui.install_playwright_browser).pack(side="left", padx=4)

    database_panel = gui.ttk.LabelFrame(content, text="数据库")
    database_panel.pack(fill="x", padx=12, pady=(0, 6))
    gui.ttk.Label(
        database_panel,
        text=f"当前数据库：{gui.db.db_path.name}",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(10, 4))
    gui.ttk.Button(database_panel, text="软件操作日志", command=gui.open_software_log_dialog).pack(anchor="w", padx=10, pady=(0, 10))

    panel = gui.ttk.LabelFrame(content, text="危险操作")
    panel.pack(fill="x", padx=12, pady=(6, 12))

    gui.settings_clear_vars = {
        key: gui.tk.BooleanVar(value=False)
        for key, _label in gui.module.SETTINGS_CLEARABLE_ITEMS
    }

    warning_text = (
        "可按项目分别勾选要清空的数据。系统登录账号会保留。\n"
        "如果勾选快递公司记录，系统会在清空后自动重置默认快递公司。此操作不可撤销。"
    )
    gui.ttk.Label(panel, text=warning_text, justify="left", foreground="#aa0000").pack(anchor="w", padx=10, pady=10)

    options_frame = gui.ttk.Frame(panel)
    options_frame.pack(fill="x", padx=10, pady=(0, 10))
    for idx, (key, label) in enumerate(gui.module.SETTINGS_CLEARABLE_ITEMS):
        gui.ttk.Checkbutton(
            options_frame,
            text=label,
            variable=gui.settings_clear_vars[key],
        ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=8, pady=4)

    button_frame = gui.ttk.Frame(panel)
    button_frame.pack(fill="x", padx=10, pady=(0, 10))
    gui.ttk.Button(button_frame, text="全选项目", command=lambda: gui.set_settings_clear_selection(True)).pack(side="left")
    gui.ttk.Button(button_frame, text="取消全选", command=lambda: gui.set_settings_clear_selection(False)).pack(side="left", padx=6)
    gui.ttk.Button(button_frame, text="清空已勾选项目", command=gui.clear_selected_data_action).pack(side="left", padx=6)
