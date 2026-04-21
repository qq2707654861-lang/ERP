from typing import Any


def build_settlement_tab(gui: Any) -> None:
    frame = gui._create_notebook_tab("结算")
    top = gui.ttk.Frame(frame)
    top.pack(fill="x", pady=6)
    search_var = gui.tk.StringVar()
    start_date_var = gui.tk.StringVar()
    end_date_var = gui.tk.StringVar()
    settlement_status_var = gui.tk.StringVar(value="未结算")
    invoice_status_var = gui.tk.StringVar(value="全部")
    batch_settlement_status_var = gui.tk.StringVar(value="已结算")
    count_var = gui.tk.StringVar(value="0")
    gui._build_order_filter_bar(
        top,
        search_var,
        start_date_var,
        end_date_var,
        query_command=gui.refresh_settlement_tab,
        extra_filters=[
            {"label": "结算状态", "variable": settlement_status_var, "values": gui.module.SETTLEMENT_STATUS_FILTER_OPTIONS},
            {"label": "发票状态", "variable": invoice_status_var, "values": gui.module.INVOICE_STATUS_FILTER_OPTIONS},
        ],
    )
    gui._build_page_summary(frame, "结算", count_var)
    tree = gui._create_bound_order_tree(frame, height=12)
    gui._build_export_columns_section(frame, "settlement")

    action_frame = gui.ttk.Frame(frame)
    action_frame.pack(fill="x", pady=8)
    gui._build_settlement_action_bar(action_frame, tree, batch_settlement_status_var)

    gui.settlement_tab_context = {
        "tree": tree,
        "search_var": search_var,
        "start_date_var": start_date_var,
        "end_date_var": end_date_var,
        "settlement_status_var": settlement_status_var,
        "invoice_status_var": invoice_status_var,
        "batch_settlement_status_var": batch_settlement_status_var,
        "count_var": count_var,
        "export_scope": "settlement",
    }
