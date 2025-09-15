#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账申请请求类
文件位置: request/SplitAccountRequest.py
接口名: bkfunds.balance.pay.apply
"""

from common import RequestTypes  # 现在从 common 目录导入
from request.BaseRequest import BaseRequest


class SplitAccountRequest(BaseRequest):
    """分账申请请求类"""

    def __init__(self):
        super().__init__()

    def get_method(self):
        """
        返回分账申请接口方法名
        :return: 接口方法名
        """
        return "bkfunds.balance.pay.apply"

    def get_version(self):
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