# -*- coding: utf-8 -*-
"""
多平台对接 — 订单导入适配器
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_reader import (
    read_csv_rows,
    read_order_rows_from_file,
    read_table_file,
    read_xlsx_sheets,
)
from .utils import (
    clean_date_text,
    normalize_settlement_status,
    now_str,
    pick_value,
    safe_text,
    to_float,
    to_int,
)


class PlatformAdapter:
    """平台导入适配器基类"""
    platform_name: str = "未知"

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        """将平台原始行数据统一为系统格式"""
        raise NotImplementedError

    def fetch_orders(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """从平台API拉取订单（预留，暂不实现）"""
        raise NotImplementedError

    def sync_inventory(self, sku: str, quantity: int) -> bool:
        """同步库存到平台（预留）"""
        return False

    def update_tracking(self, order_no: str, courier: str, tracking_no: str) -> bool:
        """回传物流信息到平台（预留）"""
        return False


class ZhihuAdapter(PlatformAdapter):
    """知护平台（原有逻辑）"""
    platform_name = "知护"

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        from .utils import calculate_receivable_shipping_fee, normalize_discount
        sku = pick_value(raw_row, "SKU编码(自定义)", "SKU编码", "SKU", "商品编码", "书号")
        quantity = max(to_int(pick_value(raw_row, "商品数量", "数量"), 1), 1)
        list_price = to_float(pick_value(raw_row, "定价", "价格"), 0.0)
        discount = normalize_discount(pick_value(raw_row, "折扣"), 1.0)
        book_amount = to_float(pick_value(raw_row, "应收书款"), round(list_price * discount * quantity, 2))
        recipient_address = pick_value(raw_row, "收件人地址", "地址")
        shipping_fee = calculate_receivable_shipping_fee(
            book_amount, recipient_address,
            pick_value(raw_row, "应收运费", "邮费", "运费") or 6.0,
        )
        receivable_amount = to_float(pick_value(raw_row, "应收金额"), round(book_amount + shipping_fee, 2))

        return {
            "order_no": pick_value(raw_row, "订单号", "订单编号"),
            "order_time": clean_date_text(pick_value(raw_row, "订单下单时间", "下单时间", "订单时间")),
            "platform_source": "知护",
            "platform_order_id": pick_value(raw_row, "订单号"),
            "shop_name": "知护",
            "sku": sku,
            "product_name": pick_value(raw_row, "商品名称", "书名", "商品名"),
            "quantity": quantity,
            "list_price": list_price,
            "discount": discount,
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "recipient_name": pick_value(raw_row, "收件人姓名", "收货人"),
            "recipient_phone": pick_value(raw_row, "收件人手机", "手机"),
            "recipient_address": recipient_address,
            "remark": pick_value(raw_row, "备注"),
            "courier_company": pick_value(raw_row, "快递公司"),
            "tracking_no": pick_value(raw_row, "单号", "物流单号"),
            "settlement_status": normalize_settlement_status(pick_value(raw_row, "结算状态"), "未结算"),
            "invoice_status": pick_value(raw_row, "发票状态") or "未开票",
            "procurement_cost": to_float(pick_value(raw_row, "采购成本"), 0.0),
            "procurement_date": clean_date_text(pick_value(raw_row, "采购日期")),
            "procurement_order_no": pick_value(raw_row, "采购订单号"),
            "procurement_remark": pick_value(raw_row, "采购备注"),
        }


class TaobaoAdapter(PlatformAdapter):
    """淘宝/天猫订单导入适配器"""
    platform_name = "淘宝"

    # 淘宝导出表格表头别名映射
    HEADER_MAP = {
        "订单编号": "订单号",
        "订单创建时间": "订单下单时间",
        "买家会员名": "buyer_name",
        "收货人姓名": "收件人姓名",
        "收货地址 ": "收件人地址",
        "联系手机": "收件人手机",
        "联系电话": "收件人手机",
        "宝贝标题": "商品名称",
        "宝贝种类": "商品数量",
        "商品单价": "定价",
        "买家实际支付金额": "receivable_amount",
        "物流单号": "tracking_no",
        "物流公司": "快递公司",
        "订单备注": "备注",
        "商家编码": "SKU编码(自定义)",
    }

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        from .utils import normalize_discount
        order_no = pick_value(raw_row, "订单编号", "订单号")
        sku = pick_value(raw_row, "商家编码", "SKU编码", "SKU编码(自定义)")
        quantity = max(to_int(pick_value(raw_row, "宝贝种类", "商品数量", "数量"), 1), 1)
        list_price = to_float(pick_value(raw_row, "商品单价", "定价", "价格"), 0.0)
        # 淘宝折扣 = 实付 / (单价*数量)
        actual_payment = to_float(pick_value(raw_row, "买家实际支付金额", "实付金额"), 0.0)
        book_amount = actual_payment if actual_payment > 0 else round(list_price * quantity, 2)
        shipping_fee = to_float(pick_value(raw_row, "邮费", "运费"), 0.0)
        receivable_amount = actual_payment if actual_payment > 0 else book_amount + shipping_fee

        return {
            "order_no": order_no,
            "order_time": clean_date_text(pick_value(raw_row, "订单创建时间", "订单下单时间", "下单时间")),
            "platform_source": "淘宝",
            "platform_order_id": order_no,
            "shop_name": pick_value(raw_row, "店铺名称", "店铺") or "淘宝",
            "sku": sku,
            "product_name": pick_value(raw_row, "宝贝标题", "商品名称", "商品标题"),
            "quantity": quantity,
            "list_price": list_price,
            "discount": normalize_discount(pick_value(raw_row, "折扣"), 1.0),
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "recipient_name": pick_value(raw_row, "收货人姓名", "收件人姓名"),
            "recipient_phone": pick_value(raw_row, "联系手机", "联系电话", "收件人手机"),
            "recipient_address": pick_value(raw_row, "收货地址", "收件人地址"),
            "remark": pick_value(raw_row, "订单备注", "备注"),
            "courier_company": pick_value(raw_row, "物流公司", "快递公司"),
            "tracking_no": pick_value(raw_row, "物流单号", "单号"),
            "settlement_status": "未结算",
            "invoice_status": "未开票",
            "procurement_cost": 0.0,
            "procurement_date": "",
            "procurement_order_no": "",
            "procurement_remark": "",
        }


class PinduoduoAdapter(PlatformAdapter):
    """拼多多订单导入适配器"""
    platform_name = "拼多多"

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        from .utils import normalize_discount
        order_no = pick_value(raw_row, "订单编号", "订单号")
        sku = pick_value(raw_row, "商家编码", "SKU编码", "商品编码", "SKU编码(自定义)")
        quantity = max(to_int(pick_value(raw_row, "商品数量", "数量", "购买数量"), 1), 1)
        list_price = to_float(pick_value(raw_row, "商品单价", "定价", "价格"), 0.0)
        book_amount = to_float(pick_value(raw_row, "商品总金额", "应收书款"), 0.0)
        shipping_fee = to_float(pick_value(raw_row, "邮费", "运费"), 0.0)
        receivable_amount = to_float(pick_value(raw_row, "实付金额", "应收金额"), book_amount + shipping_fee)

        return {
            "order_no": order_no,
            "order_time": clean_date_text(pick_value(raw_row, "下单时间", "订单创建时间", "订单下单时间")),
            "platform_source": "拼多多",
            "platform_order_id": order_no,
            "shop_name": pick_value(raw_row, "店铺名称") or "拼多多",
            "sku": sku,
            "product_name": pick_value(raw_row, "商品名称", "宝贝标题"),
            "quantity": quantity,
            "list_price": list_price,
            "discount": normalize_discount(pick_value(raw_row, "折扣"), 1.0),
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "recipient_name": pick_value(raw_row, "收货人姓名", "收件人姓名"),
            "recipient_phone": pick_value(raw_row, "收货人手机", "手机号", "联系电话"),
            "recipient_address": pick_value(raw_row, "收货地址", "收件人地址"),
            "remark": pick_value(raw_row, "备注", "订单备注"),
            "courier_company": pick_value(raw_row, "快递公司", "物流公司"),
            "tracking_no": pick_value(raw_row, "物流单号", "运单号"),
            "settlement_status": "未结算",
            "invoice_status": "未开票",
            "procurement_cost": 0.0,
            "procurement_date": "",
            "procurement_order_no": "",
            "procurement_remark": "",
        }


class DouyinAdapter(PlatformAdapter):
    """抖音电商订单导入适配器"""
    platform_name = "抖音"

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        from .utils import normalize_discount
        order_no = pick_value(raw_row, "订单编号", "订单号", "子订单编号")
        sku = pick_value(raw_row, "商家编码", "SKU编码", "商品编码", "SKU编码(自定义)")
        quantity = max(to_int(pick_value(raw_row, "商品数量", "数量"), 1), 1)
        list_price = to_float(pick_value(raw_row, "商品单价", "定价", "价格"), 0.0)
        book_amount = to_float(pick_value(raw_row, "商品总金额", "应收书款", "商品实付"), 0.0)
        shipping_fee = to_float(pick_value(raw_row, "邮费", "运费"), 0.0)
        receivable_amount = to_float(pick_value(raw_row, "实付金额", "应收金额", "订单实付"), book_amount + shipping_fee)

        return {
            "order_no": order_no,
            "order_time": clean_date_text(pick_value(raw_row, "下单时间", "订单创建时间", "订单下单时间")),
            "platform_source": "抖音",
            "platform_order_id": order_no,
            "shop_name": pick_value(raw_row, "店铺名称") or "抖音",
            "sku": sku,
            "product_name": pick_value(raw_row, "商品名称", "商品标题"),
            "quantity": quantity,
            "list_price": list_price,
            "discount": normalize_discount(pick_value(raw_row, "折扣"), 1.0),
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "recipient_name": pick_value(raw_row, "收货人姓名", "收件人姓名"),
            "recipient_phone": pick_value(raw_row, "收货人手机", "手机号", "联系电话"),
            "recipient_address": pick_value(raw_row, "收货地址", "收件人地址"),
            "remark": pick_value(raw_row, "备注", "订单备注"),
            "courier_company": pick_value(raw_row, "快递公司", "物流公司"),
            "tracking_no": pick_value(raw_row, "物流单号", "运单号"),
            "settlement_status": "未结算",
            "invoice_status": "未开票",
            "procurement_cost": 0.0,
            "procurement_date": "",
            "procurement_order_no": "",
            "procurement_remark": "",
        }


class JDAdapter(PlatformAdapter):
    """京东订单导入适配器"""
    platform_name = "京东"

    def normalize_row(self, raw_row: Dict[str, str]) -> Dict[str, Any]:
        from .utils import normalize_discount
        order_no = pick_value(raw_row, "订单编号", "京东订单号", "订单号")
        sku = pick_value(raw_row, "商家编码", "SKU编码", "商品编码", "SKU编码(自定义)", "商品SKU")
        quantity = max(to_int(pick_value(raw_row, "商品数量", "数量"), 1), 1)
        list_price = to_float(pick_value(raw_row, "商品单价", "定价", "京东价"), 0.0)
        book_amount = to_float(pick_value(raw_row, "商品总金额", "应收书款"), 0.0)
        shipping_fee = to_float(pick_value(raw_row, "邮费", "运费"), 0.0)
        receivable_amount = to_float(pick_value(raw_row, "实付金额", "应收金额", "订单金额"), book_amount + shipping_fee)

        return {
            "order_no": order_no,
            "order_time": clean_date_text(pick_value(raw_row, "下单时间", "订单创建时间")),
            "platform_source": "京东",
            "platform_order_id": order_no,
            "shop_name": pick_value(raw_row, "店铺名称") or "京东",
            "sku": sku,
            "product_name": pick_value(raw_row, "商品名称", "商品标题"),
            "quantity": quantity,
            "list_price": list_price,
            "discount": normalize_discount(pick_value(raw_row, "折扣"), 1.0),
            "book_amount": book_amount,
            "shipping_fee": shipping_fee,
            "receivable_amount": receivable_amount,
            "recipient_name": pick_value(raw_row, "收货人姓名", "收件人姓名"),
            "recipient_phone": pick_value(raw_row, "收货人手机", "手机号", "联系电话"),
            "recipient_address": pick_value(raw_row, "收货地址", "收件人地址"),
            "remark": pick_value(raw_row, "备注", "订单备注"),
            "courier_company": pick_value(raw_row, "快递公司", "物流公司"),
            "tracking_no": pick_value(raw_row, "物流单号", "运单号"),
            "settlement_status": "未结算",
            "invoice_status": "未开票",
            "procurement_cost": 0.0,
            "procurement_date": "",
            "procurement_order_no": "",
            "procurement_remark": "",
        }


# ---------- 适配器注册表 ----------
PLATFORM_ADAPTERS: Dict[str, type] = {
    "知护": ZhihuAdapter,
    "淘宝": TaobaoAdapter,
    "天猫": TaobaoAdapter,  # 天猫复用淘宝适配器
    "拼多多": PinduoduoAdapter,
    "抖音": DouyinAdapter,
    "京东": JDAdapter,
}


def get_adapter(platform_name: str) -> PlatformAdapter:
    """根据平台名称获取适配器实例"""
    adapter_cls = PLATFORM_ADAPTERS.get(platform_name)
    if adapter_cls is None:
        raise ValueError(f"不支持的平台：{platform_name}，支持的平台：{list(PLATFORM_ADAPTERS.keys())}")
    return adapter_cls()


def auto_detect_platform(file_path: Path) -> str:
    """根据文件名/内容自动检测平台来源"""
    name = file_path.name.lower()
    if "淘宝" in name or "taobao" in name or "天猫" in name or "tmall" in name:
        return "淘宝"
    if "拼多多" in name or "pdd" in name or "pinduoduo" in name:
        return "拼多多"
    if "抖音" in name or "douyin" in name or "tiktok" in name:
        return "抖音"
    if "京东" in name or "jd" in name:
        return "京东"
    # 默认知护
    return "知护"


def import_orders_from_file(
    file_path: Path,
    platform_name: str = "",
    username: str = "system",
) -> tuple:
    """
    从文件导入订单，自动识别平台
    返回 (normalized_rows, platform_name, sheet_names)
    """
    platform = platform_name or auto_detect_platform(file_path)
    adapter = get_adapter(platform)

    raw_rows, sheet_names = read_order_rows_from_file(file_path)
    normalized_rows = []
    for raw_row in raw_rows:
        try:
            normalized = adapter.normalize_row(raw_row)
            if normalized.get("order_no"):
                normalized_rows.append(normalized)
        except Exception:
            continue  # 跳过无法解析的行

    return normalized_rows, platform, sheet_names
