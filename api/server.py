# -*- coding: utf-8 -*-
"""
API server 启动入口
启动方式：python -m api.server
"""
from __future__ import annotations

import uvicorn

from . import app, HAS_FASTAPI


def start_api(host: str = "0.0.0.0", port: int = 8000):
    if not HAS_FASTAPI:
        print("错误：需要安装 FastAPI 和 uvicorn")
        print("  pip install fastapi uvicorn")
        return
    print(f"知护图书ERP API 启动：http://{host}:{port}")
    print(f"API文档：http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api()
