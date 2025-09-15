#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
提现申请业务参数模型
文件位置: model/WithdrawModel.py
接口名: bkfunds.withdraw.apply
"""


class WithdrawModel:
    """提现申请业务参数模型"""

    def __init__(self):
        # ===== 基本参数 =====
        self.sso_node_id = None  # 机构id，必传
        self.merchant_id = None  # 翼码商户id，必传
        self.store_no = None  # 自定义门店号，必传
        self.account_sub_type = None  # 账户类型 0-收款账户 1-付款账户，必传
        
        # ===== 提现信息 =====
        self.total_amount = None  # 提现金额(分)，必传
        self.retained = None  # 是否提现留存金额 1是 0否 (默认是)，可选
        
        # ===== 银行卡信息 =====
        self.card_type = None  # 结算卡标识 0-提现卡 1-费用卡 2-其他卡，可选
        self.bank_card_no = None  # 银行卡号，可选
        self.bank_cert_name = None  # 银行账户户名，可选
        self.bank_id = None  # 银行id，可选
        self.bank_name = None  # 银行名称，可选
        
        # ===== 其他信息 =====
        self.remark = None  # 备注信息，可选

    def to_dict(self):
        """转换为字典格式，方便调试"""
        return {
            'sso_node_id': self.sso_node_id,
            'merchant_id': self.merchant_id,
            'store_no': self.store_no,
            'account_sub_type': self.account_sub_type,
            'total_amount': self.total_amount,
            'retained': self.retained,
            'card_type': self.card_type,
            'bank_card_no': self.bank_card_no,
            'bank_cert_name': self.bank_cert_name,
            'bank_id': self.bank_id,
            'bank_name': self.bank_name,
            'remark': self.remark
        }

    def validate(self):
        """
        验证必要参数
        :return: (是否有效, 错误列表)
        """
        errors = []

        # 检查必传参数
        if not self.sso_node_id:
            errors.append("机构号(sso_node_id)不能为空")

        # merchant_id和store_no二选一必传
        if not self.merchant_id and not self.store_no:
            errors.append("翼码商户ID(merchant_id)和自定义门店号(store_no)必须至少传一个")

        if not self.account_sub_type:
            errors.append("账户类型(account_sub_type)不能为空")

        if not self.total_amount or self.total_amount <= 0:
            errors.append("提现金额(total_amount)必须大于0")

        # 检查账户类型的有效性
        if self.account_sub_type not in ['0', '1']:
            errors.append("账户类型(account_sub_type)必须是0或1")

        # 检查card_type的有效性
        if self.card_type and self.card_type not in ['0', '1', '2']:
            errors.append("结算卡标识(card_type)必须是0、1或2")

        return len(errors) == 0, errors

    def __str__(self):
        """字符串表示"""
        return f"Withdraw(merchant_id={self.merchant_id}, store_no={self.store_no}, amount={self.total_amount})"