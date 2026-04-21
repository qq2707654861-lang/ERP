# -*- coding: utf-8 -*-
"""
知护图书订单管理系统 - 重构后，Claude Code 架构启发
入口文件
"""
import argparse
import tkinter as tk
import sys
from pathlib import Path

from src.database.manager import ZhihuOrderDB
from src.gui.main_window import OrderManagerGUI
from src.utils.helpers import append_runtime_log
from src import constants


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "zhihu_order_manager.db"
APP_RUNTIME_LOG_PATH = BASE_DIR / "software_runtime.log"


def run_gui():
    db = ZhihuOrderDB(DB_PATH)
    root = tk.Tk()
    root.title(constants.APP_TITLE)
    app = OrderManagerGUI(root, db)
    root.mainloop()
    db.close()


def smoke_test(seed_demo=None):
    """Smoke test to verify the application works without GUI"""
    print("=== 知护图书订单管理系统 - 烟雾测试 ===")
    print(f"Base directory: {BASE_DIR}")
    print(f"Database path: {DB_PATH}")

    db = ZhihuOrderDB(DB_PATH)
    stats = db.get_statistics()
    print(f"\n当前统计:")
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  已结算总利润: {stats['total_profit']:.2f} 元")
    print(f"  未结算订单: {stats['unpaid_count']}")

    db.log_operation("smoke_test", "Smoke test completed")
    db.close()
    print("\n✅ 烟雾测试通过，应用正常运行")
    return 0


def main():
    parser = argparse.ArgumentParser(description=constants.APP_TITLE)
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test without GUI to verify installation"
    )
    parser.add_argument(
        "--seed-demo",
        type=str,
        help="Seed demo data from Excel file"
    )
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(smoke_test(args.seed_demo))

    run_gui()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        append_runtime_log(f"Unhandled exception: {e}", exc_info=sys.exc_info())
        raise
