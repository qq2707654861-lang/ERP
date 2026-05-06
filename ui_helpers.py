from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def create_notebook_tab(gui: Any, title: str) -> Any:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text=title)
    return frame


def build_date_filter_input(gui: Any, parent: Any, label: str, target_var: Any) -> None:
    gui.ttk.Label(parent, text=label).pack(side="left", padx=(10, 0))
    date_frame = gui.ttk.Frame(parent)
    date_frame.pack(side="left", padx=5)
    gui.ttk.Entry(date_frame, textvariable=target_var, width=12).pack(side="left")
    gui.ttk.Button(
        date_frame,
        text="选日期",
        command=lambda var=target_var: gui.open_date_picker(var, gui.root),
    ).pack(side="left", padx=4)


def build_order_filter_bar(
    gui: Any,
    parent: Any,
    search_var: Any,
    start_date_var: Any,
    end_date_var: Any,
    query_command: Callable[[], Any],
    refresh_command: Optional[Callable[[], Any]] = None,
    extra_filters: Optional[List[Dict[str, Any]]] = None,
    extra_buttons: Optional[List[Dict[str, Any]]] = None,
) -> None:
    gui.ttk.Label(parent, text="订单号/收件人：").pack(side="left")
    gui.ttk.Entry(parent, textvariable=search_var, width=30).pack(side="left", padx=5)
    build_date_filter_input(gui, parent, "起始日期：", start_date_var)
    build_date_filter_input(gui, parent, "结束日期：", end_date_var)

    for filter_config in extra_filters or []:
        gui.ttk.Label(parent, text=f"{_text(filter_config.get('label'))}：").pack(side="left", padx=(10, 0))
        gui.ttk.Combobox(
            parent,
            textvariable=filter_config["variable"],
            values=filter_config["values"],
            width=_to_int(filter_config.get("width"), 10),
            state="readonly",
        ).pack(side="left", padx=5)

    gui.ttk.Button(parent, text="查询", command=query_command).pack(side="left", padx=4)
    gui.ttk.Button(parent, text="刷新", command=refresh_command or query_command).pack(side="left", padx=4)

    for button_config in extra_buttons or []:
        gui.ttk.Button(
            parent,
            text=_text(button_config.get("text")),
            command=button_config["command"],
        ).pack(side="left", padx=button_config.get("padx", 6))


def build_page_summary(gui: Any, parent: Any, page_title: str, count_var: Any) -> None:
    summary = gui.ttk.Frame(parent)
    summary.pack(fill="x", pady=(0, 6))
    gui.ttk.Label(summary, text=f"当前页面：{page_title}", font=("Microsoft YaHei", 10, "bold")).pack(side="left")
    gui.ttk.Label(summary, text="订单数：").pack(side="left", padx=(16, 0))
    gui.ttk.Label(summary, textvariable=count_var).pack(side="left")


def create_bound_order_tree(gui: Any, parent: Any, height: int = 12, on_select: Optional[Callable[[Any], None]] = None) -> Any:
    table_frame = gui.ttk.Frame(parent)
    table_frame.pack(fill="x")
    tree = gui.create_order_tree(table_frame, height=height)
    if on_select is not None:
        tree.bind("<<TreeviewSelect>>", on_select)
    tree.bind("<Double-1>", lambda _event, current_tree=tree: gui.on_tree_order_double_click(current_tree))
    return tree


def build_export_columns_section(gui: Any, parent: Any, scope: str) -> None:
    export_columns_frame = gui.ttk.LabelFrame(parent, text="导出列设置")
    export_columns_frame.pack(fill="x", pady=(8, 0))
    gui.build_export_column_selector(export_columns_frame, scope)


def add_tree_selection_buttons(
    gui: Any,
    parent: Any,
    tree: Any,
    select_all_text: str = "一键全选",
    clear_text: str = "取消全选",
) -> None:
    gui.ttk.Button(
        parent,
        text=select_all_text,
        command=lambda current_tree=tree: gui.check_all_tree_items(current_tree),
    ).pack(side="left")
    gui.ttk.Button(
        parent,
        text=clear_text,
        command=lambda current_tree=tree: gui.clear_tree_checked_items(current_tree),
    ).pack(side="left", padx=6)


def get_status_tab_tip_text(status: str) -> str:
    if status == "审核":
        return "点击左侧勾选列选择订单；采购单号、采购成本填写完整后，批量审核才会进入配货环节。"
    if status == "配货":
        return "点击左侧勾选列选择订单；可批量确认配货进入发货，也可将订单打回审核页面。"
    if status == "发货":
        return "可一键勾选当前页全部订单；可批量确认发货，也可将订单打回配货或审核页面。"
    return "双击订单可打开编辑窗口。"


def build_status_action_bar(gui: Any, parent: Any, status: str, tree: Any) -> None:
    add_tree_selection_buttons(gui, parent, tree, select_all_text="勾选全部订单", clear_text="清空勾选")
    gui.ttk.Button(
        parent,
        text=gui.module.STATUS_TAB_BATCH_BUTTON_TEXT.get(status, f"批量确认{status}"),
        command=lambda current_tree=tree: gui.batch_update_order_status(current_tree),
    ).pack(side="left", padx=6)
    if status == "配货":
        gui.ttk.Button(
            parent,
            text="勾选订单打回审核",
            command=lambda current_tree=tree: gui.batch_return_orders(current_tree, "审核"),
        ).pack(side="left", padx=6)
    if status == "审核":
        gui.ttk.Button(
            parent,
            text="手动采购",
            command=lambda current_tree=tree: gui.smart_procurement(current_tree, mode="manual"),
        ).pack(side="left", padx=6)
    if status == "发货":
        gui.ttk.Button(
            parent,
            text="勾选订单打回配货",
            command=lambda current_tree=tree: gui.batch_return_orders(current_tree, "配货"),
        ).pack(side="left", padx=6)
        gui.ttk.Button(
            parent,
            text="勾选订单打回审核",
            command=lambda current_tree=tree: gui.batch_return_orders(current_tree, "审核"),
        ).pack(side="left", padx=6)
        gui.ttk.Button(
            parent,
            text="导出当前结果",
            command=lambda current_status=status: gui.export_status_tab_orders(current_status),
        ).pack(side="left", padx=6)
    gui.ttk.Label(parent, text=get_status_tab_tip_text(status), foreground="#666666").pack(side="left", padx=12)


def build_settlement_action_bar(gui: Any, parent: Any, tree: Any, batch_settlement_status_var: Any) -> None:
    add_tree_selection_buttons(gui, parent, tree)
    gui.ttk.Label(parent, text="结算状态：").pack(side="left", padx=(10, 0))
    gui.ttk.Combobox(
        parent,
        textvariable=batch_settlement_status_var,
        values=gui.module.SETTLEMENT_STATUS_EDIT_OPTIONS,
        width=10,
        state="readonly",
    ).pack(side="left", padx=5)
    gui.ttk.Button(
        parent,
        text="批量修改状态",
        command=lambda current_tree=tree: gui.batch_update_settlement_status(current_tree),
    ).pack(side="left", padx=6)
    gui.ttk.Button(
        parent,
        text="批量结算",
        command=lambda current_tree=tree: gui.batch_update_settlement_status(current_tree, "已结算"),
    ).pack(side="left", padx=6)
    gui.ttk.Button(parent, text="导出当前结果", command=gui.export_settlement_tab_orders).pack(side="left", padx=6)
    gui.ttk.Label(
        parent,
        text="勾选订单后可批量修改结算状态，双击订单可编辑。",
        foreground="#666666",
    ).pack(side="left", padx=12)


def build_orders_action_bar(gui: Any, parent: Any, tree: Any) -> None:
    add_tree_selection_buttons(gui, parent, tree)
    gui.ttk.Button(parent, text="导出当前结果", command=gui.export_orders).pack(side="left", padx=6)