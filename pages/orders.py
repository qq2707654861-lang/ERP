from typing import Any


def build_orders_tab(gui: Any) -> None:
    frame = gui._create_notebook_tab("总订单")
    top = gui.ttk.Frame(frame)
    top.pack(fill="x", pady=6)
    gui.order_search_var = gui.tk.StringVar()
    gui.order_status_filter_var = gui.tk.StringVar(value="全部")
    gui.settlement_status_filter_var = gui.tk.StringVar(value="全部")
    gui.invoice_status_filter_var = gui.tk.StringVar(value="全部")
    gui.order_start_date_var = gui.tk.StringVar()
    gui.order_end_date_var = gui.tk.StringVar()
    gui._build_order_filter_bar(
        top,
        gui.order_search_var,
        gui.order_start_date_var,
        gui.order_end_date_var,
        query_command=gui.refresh_orders,
        extra_filters=[
            {"label": "订单状态", "variable": gui.order_status_filter_var, "values": gui.module.ORDER_STATUS_FILTER_OPTIONS},
            {"label": "结算状态", "variable": gui.settlement_status_filter_var, "values": gui.module.SETTLEMENT_STATUS_FILTER_OPTIONS},
            {"label": "发票状态", "variable": gui.invoice_status_filter_var, "values": gui.module.INVOICE_STATUS_FILTER_OPTIONS},
        ],
        extra_buttons=[
            {"text": "批量确认状态", "command": gui.batch_update_order_status, "padx": 10},
        ],
    )

    gui.order_tree = gui._create_bound_order_tree(frame, height=12, on_select=gui.on_order_selected)
    gui._build_export_columns_section(frame, "orders")

    order_action_frame = gui.ttk.Frame(frame)
    order_action_frame.pack(fill="x", pady=8)
    gui._build_orders_action_bar(order_action_frame, gui.order_tree)

    gui.edit_vars = {
        "recipient_name": gui.tk.StringVar(),
        "recipient_address": gui.tk.StringVar(),
        "remark": gui.tk.StringVar(),
        "courier_company": gui.tk.StringVar(),
        "tracking_no": gui.tk.StringVar(),
        "settlement_status": gui.tk.StringVar(),
        "invoice_status": gui.tk.StringVar(),
        "procurement_date": gui.tk.StringVar(),
        "procurement_order_no": gui.tk.StringVar(),
        "procurement_cost": gui.tk.StringVar(),
        "procurement_remark": gui.tk.StringVar(),
        "order_status": gui.tk.StringVar(),
    }
