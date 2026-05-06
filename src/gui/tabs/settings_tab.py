# -*- coding: utf-8 -*-
"""
Settings tab
Inspired by Claude Code architecture - each tab in separate file
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from src.database.manager import ERPOrderDB
from src import constants


class SettingsTab:
    def __init__(self, parent: ttk.Notebook, db: ERPOrderDB):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        # WeChat root setting
        wechat_frame = ttk.LabelFrame(self.frame, text="微信文件自动导入")
        wechat_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(wechat_frame, text="微信文件根目录:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.wechat_root_var = tk.StringVar()
        wechat_entry = ttk.Entry(wechat_frame, textvariable=self.wechat_root_var, width=60)
        wechat_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        ttk.Button(wechat_frame, text="浏览", command=self.browse_wechat_root).grid(row=0, column=2, padx=5, pady=5)

        # Clear data section
        clear_frame = ttk.LabelFrame(self.frame, text="清空数据")
        clear_frame.pack(fill=tk.X, padx=5, pady=5)

        for idx, (table, desc) in enumerate(constants.SETTINGS_CLEARABLE_ITEMS):
            btn = ttk.Button(
                clear_frame,
                text=f"清空{desc}",
                command=lambda t=table: self.confirm_clear(t)
            )
            btn.grid(row=idx, column=0, padx=5, pady=2, sticky=tk.W)

        # Save button
        save_frame = ttk.Frame(self.frame)
        save_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Button(save_frame, text="保存设置", command=self.save_settings).pack(side=tk.RIGHT, padx=5)

    def browse_wechat_root(self):
        folder = filedialog.askdirectory(title="选择微信文件根目录")
        if folder:
            self.wechat_root_var.set(folder)

    def load_settings(self):
        value = self.db.get_setting(constants.WECHAT_ROOT_SETTING_KEY, "")
        self.wechat_root_var.set(value or "")

    def save_settings(self):
        self.db.set_setting(constants.WECHAT_ROOT_SETTING_KEY, self.wechat_root_var.get())
        messagebox.showinfo("完成", "设置已保存")

    def confirm_clear(self, table: str):
        desc = next((d for t, d in constants.SETTINGS_CLEARABLE_ITEMS if t == table), table)
        if messagebox.askyesno("确认清空", f"确定要清空{desc}吗？此操作不可恢复！"):
            self.db.clear_all(table)
            messagebox.showinfo("完成", f"{desc}已清空")
