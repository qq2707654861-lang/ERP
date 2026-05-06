# ERP 订单管理系统（Python MVP）

## 运行方式

```bash
python ERP.py
```

如需使用淘宝 Cookie 登录采购助手，建议先安装依赖：

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## 默认账号

- 管理员：`admin / admin123`
- 订单员：`order / 123456`
- 财务：`finance / 123456`

## 已实现功能

- 本地 SQLite 数据库
- 订单导入（`CSV / XLSX`）
- 图书资料库导入与维护
- 供应商运费规则导入
- 总订单表查询
- 采购 / 物流 / 结算信息维护
- 订单导出 CSV
- 利润统计概览

## 快速验证

```bash
python ERP.py --smoke-test --seed-demo 表格.xlsx
```

这会自动初始化数据库，并导入当前目录下的 `表格.xlsx` 进行验证。

## Playwright 采购环境

- 系统设置页已提供 `重新检测`、`安装 Playwright 依赖`、`安装 Chromium 浏览器` 按钮
- 审核页采购账号区域支持 `配置 Cookie 登录`
- 若已保存 Cookie，采购助手会优先尝试使用 Playwright + Chromium 打开淘宝页面
