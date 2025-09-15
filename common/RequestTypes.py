# coding: utf-8
from common.RequestType import RequestType

# 创建 OpenClient 需要的各种请求类型实例
GET = RequestType()
POST_JSON = RequestType()
POST_FORM = RequestType()
POST_UPLOAD = RequestType()