# -*- coding: utf-8 -*-
"""
Statistics tab - profit stats
Inspired by Claude Code architecture - each tab in separate file
"""
import tkinter as tk
from tkinter import ttk

from src.database.manager import ZhihuOrderDB


class StatsTab:
    def __init__(self, parent: ttk.Notebook, db: ZhihuOrderDB):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.refresh_stats()

    def setup_ui(self):
        # Stats labels frame
        stats_frame = ttk.LabelFrame(self.frame, text="总体统计")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        # Grid layout
        self.stats_labels = {}
        row = 0

        self._add_stat_row(stats_frame, row, "总订单数", "total_orders")
        row += 1
        self._add_stat_row(stats_frame, row, "已结算总应收", "total_receivable")
        row += 1
        self._add_stat_row(stats_frame, row, "已结算总成本", "total_procurement")
        row += 1
        self._add_stat_row(stats_frame, row, "已结算总利润", "total_profit")
        row += 1
        self._add_stat_row(stats_frame, row, "未结算订单数", "unpaid_count")

    def _add_stat_row(self, parent: ttk.Frame, row: int, label: str, key: str):
        ttk.Label(parent, text=f"{label}:", width=15).grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
        label_widget = ttk.Label(parent, text="-", width=20)
        label_widget.grid(row=row, column=1, padx=5, pady=3, sticky=tk.W)
        self.stats_labels[key] = label_widget

    def refresh_stats(self):
        stats = self.db.get_statistics()
        for key, label_widget in self.stats_labels.items():
            value = stats.get(key, 0)
            if isinstance(value, float):
                label_widget.config(text=f"{value:.2f} 元")
            else:
                label_widget.config(text=f"{value}")
