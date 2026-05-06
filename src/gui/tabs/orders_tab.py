# -*- coding: utf-8 -*-
"""
Orders management tab
Inspired by Claude Code architecture - each tab in separate file
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from src.database.manager import ERPOrderDB
from src import constants
from src.parsers.order_parser import (
    read_xlsx_raw_sheets,
    find_best_order_sheet,
    parse_smart_order_rows,
    is_valid_order_xlsx,
)


class OrdersTab:
    def __init__(self, parent: ttk.Notebook, db: ERPOrderDB):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        # Toolbar frame
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="导入Excel订单", command=self.import_excel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="刷新列表", command=self.refresh_table).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出全部", command=self.export_excel).pack(side=tk.LEFT, padx=2)

        # Filter frame
        filter_frame = ttk.LabelFrame(self.frame, text="筛选")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Order status filter
        ttk.Label(filter_frame, text="订单状态:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.order_status_var = tk.StringVar(value="全部")
        status_combo = ttk.Combobox(
            filter_frame, textvariable=self.order_status_var,
            values=constants.ORDER_STATUS_FILTER_OPTIONS,
            state="readonly", width=10
        )
        status_combo.grid(row=0, column=1, padx=5, pady=2)

        # Settlement status filter
        ttk.Label(filter_frame, text="结算状态:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.settlement_status_var = tk.StringVar(value="全部")
        settlement_combo = ttk.Combobox(
            filter_frame, textvariable=self.settlement_status_var,
            values=constants.SETTLEMENT_STATUS_FILTER_OPTIONS,
            state="readonly", width=10
        )
        settlement_combo.grid(row=0, column=3, padx=5, pady=2)

        # Keyword filter
        ttk.Label(filter_frame, text="关键词:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(filter_frame, textvariable=self.keyword_var, width=20)
        keyword_entry.grid(row=0, column=5, padx=5, pady=2)

        ttk.Button(filter_frame, text="筛选", command=self.refresh_table).grid(row=0, column=6, padx=5, pady=2)
        ttk.Button(filter_frame, text="清空", command=self.clear_filters).grid(row=0, column=7, padx=5, pady=2)

        # Table frame
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview
        columns = [col[0] for col in constants.ORDER_TREE_COLUMNS]
        col_widths = [col[2] for col in constants.ORDER_TREE_COLUMNS]

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        for i, (col, title, width) in enumerate(constants.ORDER_TREE_COLUMNS):
            self.tree.heading(i, text=title)
            self.tree.column(i, width=width, stretch=tk.NO if i != 4 else tk.YES)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Double click to edit
        self.tree.bind("<Double-1>", self.on_double_click)

    def clear_filters(self):
        self.order_status_var.set("全部")
        self.settlement_status_var.set("全部")
        self.keyword_var.set("")
        self.refresh_table()

    def refresh_table(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get filters
        order_status = self.order_status_var.get() if self.order_status_var.get() != "全部" else None
        settlement_status = self.settlement_status_var.get() if self.settlement_status_var.get() != "全部" else None
        keyword = self.keyword_var.get() or None

        # Count and fetch
        total_count = self.db.count_orders(order_status, settlement_status, None, keyword)
        orders = self.db.list_orders(order_status, settlement_status, None, keyword, limit=500)

        for order in orders:
            values = [
                order[col] if col != "checked" else ""
                for col in constants.ORDER_TREE_COLUMNS
            ]
            self.tree.insert("", tk.END, values=values, iid=order["id"])

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            title="选择订单Excel文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        from pathlib import Path
        path = Path(file_path)

        try:
            sheets = read_xlsx_raw_sheets(path)
            analysis = find_best_order_sheet(sheets)
            if analysis["missing_headers_count"] > 0:
                missing = ", ".join(analysis["missing_headers"])
                if not messagebox.askyesno(
                    "表头不完整",
                    f"缺少必填表头: {missing}\n\n是否继续导入?"
                ):
                    return

            orders = parse_smart_order_rows(analysis)
            if not orders:
                messagebox.showwarning("警告", "没有解析到有效订单")
                return

            # Insert into database
            inserted = 0
            for order in orders:
                self.db.insert_order(order)
                inserted += 1

            self.db.log_operation("import_excel", f"Inserted {inserted} orders from {file_path}")
            self.refresh_table()
            messagebox.showinfo("完成", f"成功导入 {inserted} 个订单")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_excel(self):
        pass  # TODO: Implement export

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        # Open edit dialog
        pass  # TODO: Implement edit dialog

    def get_selected_ids(self):
        return [int(iid) for iid in self.tree.selection()]
