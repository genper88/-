#!/usr/bin/env python
# -*- coding: UTF-8 -*-

class OrderUploadModel:
    """订单上传业务请求参数模型"""

    def __init__(self):
        # 交易类型：1-支付，2-退款
        self.trade_type = None
        # 商品信息
        self.goods_detail = None
        # 机构号
        self.node_id = None
        # 订单金额，单位分
        self.order_amount = None
        # 订单交易流水号
        self.order_id = None
        # 订单交易时间 (格式: yyyyMMddHHmmss)
        self.order_time = None
        # 原订单交易流水号
        self.org_order_id = None
        # 第三方支付渠道商户号
        self.pay_merchant_id = None
        # 支付类型：502-支付宝，503-微信，512-银联云闪付
        self.pay_type = None
        # 门店id
        self.store_id = None
        # 支付平台订单号
        self.trade_no = None
        # 操作员标识
        self.user_id = None
        # 交易手续费，单位分
        self.fee_amount = None
        # 分账规则来源：1-接口，不传默认为空，表示控台
        self.split_rule_source = None
        # 分账退回流水号
        self.split_refund_seq = None
        # 支付机构号
        self.pay_node_id = None
        # 订单上传模式：1-冻结充值；2-挂账充值；3-订单报备
        self.order_upload_mode = None
        # 账户类型：1-收款账户；2-付款账户
        self.account_type = None
        # 挂账充值功能标志：1-直接充值（挂账T0-商户T0），2-冻结充值（当前暂不支持）
        self.recharge_type = None
        # 支付通道：0-支付宝；1-微信；7-星POS；c-通联
        self.source = None
        # 翼码商户号
        self.merchant_id = None
        # 备注
        self.remark = None


class GoodsDetail:
    """商品详情模型"""

    def __init__(self):
        # 商品的编号
        self.goods_id = None
        # 商品名称
        self.goods_name = None
        # 商品数量
        self.quantity = None
        # 商品单价，单位为分
        self.price = None
        # 商品实际单价，单位为分
        self.real_price = None
        # 商品类目
        self.goods_category = None
        # 商品描述信息
        self.body = None
        # 商品金额手续费，单位为分
        self.goods_fee_amount = None