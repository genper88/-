#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
提现申请请求类
文件位置: request/WithdrawRequest.py
接口名: bkfunds.withdraw.apply
"""

from common import RequestTypes
from request.BaseRequest import BaseRequest


class WithdrawRequest(BaseRequest):
    """提现申请请求类"""

    def __init__(self):
        super().__init__()

    def get_method(self) -> str:
        """
        返回提现申请接口方法名
        :return: 接口方法名
        """
        return "bkfunds.withdraw.apply"

    def get_version(self) -> str:
        """
        返回接口版本号
        :return: 版本号
        """
        return "1.0"

    def get_request_type(self):
        """
        返回请求类型
        :return: RequestType实例
        """
        return RequestTypes.POST_FORM