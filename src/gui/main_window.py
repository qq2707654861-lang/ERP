# -*- coding: utf-8 -*-
"""
Main GUI Window for ERP Order Manager
Inspired by Claude Code architecture - GUI layer isolated
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from src.database.manager import ERPOrderDB
from src import constants


class OrderManagerGUI:
    def __init__(self, root: tk.Tk, db: ERPOrderDB):
        self.root = root
        self.db = db
        self.root.title(constants.APP_TITLE)
        self.root.geometry("1400x900")

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        from src.gui.tabs.orders_tab import OrdersTab
        from src.gui.tabs.stats_tab import StatsTab
        from src.gui.tabs.settings_tab import SettingsTab

        self.orders_tab = OrdersTab(self.notebook, self.db)
        self.stats_tab = StatsTab(self.notebook, self.db)
        self.settings_tab = SettingsTab(self.notebook, self.db)

        self.notebook.add(self.orders_tab.frame, text="订单管理")
        self.notebook.add(self.stats_tab.frame, text="利润统计")
        self.notebook.add(self.settings_tab.frame, text="设置")

    def refresh_all(self):
        self.orders_tab.refresh_table()
        self.stats_tab.refresh_stats()
