#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账申请业务参数模型
文件位置: model/SplitAccountModel.py
接口名: bkfunds.balance.pay.apply
"""


class SplitAccountModel:
    """分账申请业务参数模型"""

    def __init__(self):
        # ===== 基本参数 =====
        self.node_id = None  # 机构号，必传
        self.platform_no = None  # 平台请求流水号，必传，唯一标识

        # ===== 分账金额 =====
        self.total_amount = None  # 分账金额(分)，必传

        # ===== 付款方信息（从哪个账户扣钱）=====
        self.payer_store_no = None  # 付款方门店号，可选
        self.payer_merchant_id = None  # 付款方翼码商户号，必传
        self.payer_type = None  # 付款方账户类型，必传
        # 0-收款账户；1-待结算账户；2-挂账充值账户

        # ===== 收款方信息（分给哪个商户）=====
        self.payee_store_no = None  # 收款方门店号，可选
        self.payee_merchant_id = None  # 收款方翼码商户号，必传
        self.payee_type = None  # 收款方账户类型，必传
        # 0-收款账户；1-待结算账户；2-挂账充值账户

        # ===== 其他信息 =====
        self.arrive_time = None  # 到账时间，可选
        # T0-当天到账；T1-次日到账；默认T0

        self.remark = None  # 备注信息，可选

    def to_dict(self):
        """转换为字典格式，方便调试"""
        return {
            'node_id': self.node_id,
            'platform_no': self.platform_no,
            'total_amount': self.total_amount,
            'payer_store_no': self.payer_store_no,
            'payer_merchant_id': self.payer_merchant_id,
            'payer_type': self.payer_type,
            'payee_store_no': self.payee_store_no,
            'payee_merchant_id': self.payee_merchant_id,
            'payee_type': self.payee_type,
            'arrive_time': self.arrive_time,
            'remark': self.remark
        }

    def validate(self):
        """
        验证必要参数
        :return: (是否有效, 错误列表)
        """
        errors = []

        # 检查必传参数
        if not self.node_id:
            errors.append("机构号(node_id)不能为空")

        if not self.platform_no:
            errors.append("平台流水号(platform_no)不能为空")

        if not self.total_amount or self.total_amount <= 0:
            errors.append("分账金额(total_amount)必须大于0")

        if not self.payer_merchant_id:
            errors.append("付款方商户号(payer_merchant_id)不能为空")

        if not self.payee_merchant_id:
            errors.append("收款方商户号(payee_merchant_id)不能为空")

        if self.payer_type not in ['0', '1', '2']:
            errors.append("付款方账户类型(payer_type)必须是0、1或2")

        if self.payee_type not in ['0', '1', '2']:
            errors.append("收款方账户类型(payee_type)必须是0、1或2")

        # 检查可选参数的有效性
        if self.arrive_time and self.arrive_time not in ['T0', 'T1']:
            errors.append("到账时间(arrive_time)必须是T0或T1")

        return len(errors) == 0, errors

    def __str__(self):
        """字符串表示"""
        return f"SplitAccount(platform_no={self.platform_no}, amount={self.total_amount}, " \
               f"payer={self.payer_merchant_id}, payee={self.payee_merchant_id})"