# -*- coding: utf-8 -*-
"""
Constants for Zhihu Order Manager
Inspired by Claude Code architecture - all constants in one place
"""

APP_TITLE = "知护图书订单管理系统"

# Order grid columns
ORDER_GRID_COLUMNS = [
    ("created_at", "导入时间", 100),
    ("order_no", "订单号", 180),
    ("sku", "SKU编码(自定义)", 140),
    ("product_name", "商品名称", 280),
    ("quantity", "商品数量", 80),
    ("list_price", "定价", 80),
    ("discount", "折扣", 80),
    ("book_amount", "应收书款", 90),
    ("shipping_fee", "应收运费", 90),
    ("receivable_amount", "应收金额", 90),
    ("remark", "备注", 120),
    ("courier_company", "快递公司", 100),
    ("tracking_no", "单号", 130),
    ("recipient_name", "收货人", 90),
    ("recipient_address", "地址", 260),
    ("recipient_phone", "收件人手机", 120),
    ("settlement_status", "结算状态", 100),
    ("invoice_status", "发票状态", 100),
    ("procurement_date", "采购日期", 100),
    ("procurement_order_no", "采购订单号", 130),
    ("procurement_cost", "采购成本", 90),
    ("procurement_remark", "采购备注", 120),
    ("profit", "利润", 90),
]
ORDER_EXPORT_COLUMN_KEYS = [key for key, _title, _width in ORDER_GRID_COLUMNS]
ORDER_TREE_COLUMNS = [("checked", "勾选", 50), *ORDER_GRID_COLUMNS]

# Order status workflow
ORDER_STATUS_FLOW = ["审核", "配货", "发货", "已完成"]
ORDER_STATUS_FILTER_OPTIONS = ["全部", *ORDER_STATUS_FLOW]
SETTLEMENT_STATUS_FILTER_OPTIONS = ["全部", "未结算", "已结算"]
INVOICE_STATUS_FILTER_OPTIONS = ["全部", "未开票", "已开票", "未开", "已开", "作废"]
ORDER_STATUS_EDIT_OPTIONS = ORDER_STATUS_FLOW[:]
SETTLEMENT_STATUS_EDIT_OPTIONS = ["未结算", "已结算"]
INVOICE_STATUS_EDIT_OPTIONS = ["未开票", "已开票", "未开", "已开", "作废"]

# Legacy mapping for imported data
LEGACY_ORDER_STATUS_MAP = {
    "待处理": "审核",
    "已发货": "已完成",
}
LEGACY_SETTLEMENT_STATUS_MAP = {
    "未结账": "未结算",
    "已结账": "已结算",
}

# Default courier company options
COURIER_COMPANY_OPTIONS = [
    "申通快递", "圆通快递", "中通快递", "韵达快递",
    "顺丰快递", "极兔快递", "中国邮政", "京东快递", "德邦快递"
]

# Status tab batch button text
STATUS_TAB_BATCH_BUTTON_TEXT = {
    "审核": "批量审核订单",
    "配货": "批量确认配货并进入发货",
    "发货": "一键勾选全部并批量确认发货",
}

# Clearable settings items
SETTINGS_CLEARABLE_ITEMS = [
    ("orders", "订单数据"),
    ("books", "图书资料"),
    ("supplier_rules", "供应商规则"),
    ("operation_logs", "操作日志"),
    ("courier_companies", "快递公司记录"),
]

# Smart order detection
WECHAT_ROOT_SETTING_KEY = "import.wechat_root"
TAOBAO_ACCOUNT_SETTING_KEY = "procurement.taobao_account"
TAOBAO_PASSWORD_SETTING_KEY = "procurement.taobao_password"
LATEST_ORDER_FILENAME_KEYWORDS = ("百华图书", "百华")
SMART_ORDER_REQUIRED_HEADERS = [
    "订单号",
    "订单下单时间",
    "收件人姓名",
    "收件人地址",
    "收件人手机",
    "商品名称",
    "SKU编码(自定义)",
    "商品数量",
]
SMART_ORDER_HEADER_ALIASES = {
    "订单号": ["订单号"],
    "订单下单时间": ["订单下单时间", "下单时间", "下单日期", "订单时间"],
    "收件人姓名": ["收件人姓名", "收货人姓名", "收件人", "收货人"],
    "收件人地址": [
        "收件人地址",
        "收货地址",
        "收件地址",
        "详细地址",
        "地址",
        "收件人详细地址",
        "收货详细地址",
        "收货地址(省市区)",
        "收货地址（省市区）",
        "省市区地址",
        "收件地址详情",
    ],
    "收件人手机": ["收件人手机", "收货人手机", "收件人电话", "收货人电话", "手机号", "手机号码", "联系电话", "手机"],
    "商品名称": ["商品名称", "商品", "宝贝名称", "商品标题", "书名", "商品名"],
    "SKU编码(自定义)": ["SKU编码(自定义)", "SKU编码（自定义）", "SKU编码", "商家编码", "商品编码", "SKU", "书号"],
    "商品数量": ["商品数量", "数量", "购买数量"],
}

# Excel namespaces
EXCEL_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
