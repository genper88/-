#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from common import RequestTypes
from request.BaseRequest import BaseRequest


class OrderUploadRequest(BaseRequest):
    """订单上传请求"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        """返回接口名"""
        return 'bkfunds.order.upload'

    def get_version(self):
        """返回接口版本号"""
        return '1.0'

    def get_request_type(self):
        """返回请求类型"""
        return RequestTypes.POST_JSON