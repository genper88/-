#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
余额支付查询数据模型
文件名: SplitQueryModel.py  
功能: 定义余额支付/退款查询相关的数据模型类
接口: bkfunds.balance.pay.query
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class BalancePayQueryRequest:
    """余额支付查询请求模型"""
    node_id: Optional[str] = None  # 机构号（可选）
    trade_no: str = ""  # 银行流水号（必须）
    
    def to_dict(self):
        """转换为字典格式"""
        data = {
            "trade_no": self.trade_no
        }
        if self.node_id:
            data["node_id"] = self.node_id
        return data
    
    def validate(self):
        """验证请求参数"""
        errors = []
        if not self.trade_no or not self.trade_no.strip():
            errors.append("银行流水号(trade_no)不能为空")
        return len(errors) == 0, errors


@dataclass
class BalancePayQueryData:
    """余额支付查询结果数据模型"""
    trade_time: Optional[str] = None  # 交易时间
    node_id: Optional[str] = None  # 平台号
    node_name: Optional[str] = None  # 平台名称
    platform_no: Optional[str] = None  # 平台流水号
    ym_trade_no: Optional[str] = None  # 翼码流水号
    trade_no: Optional[str] = None  # 银行流水号
    total_amount: Optional[str] = None  # 交易金额(分)
    fee: Optional[str] = None  # 手续费
    trade_type: Optional[str] = None  # 交易类型, p=支付, r=退款
    payer_merchant_id: Optional[str] = None  # 付款方平台商户号
    payer_cloud_merchant_id: Optional[str] = None  # 付款方渠道商户号
    payer_store_no: Optional[str] = None  # 付款方自定义门店号
    payer_type: Optional[str] = None  # 付款方账户类型 0-收款账户 1-付款账户
    payee_merchant_id: Optional[str] = None  # 收款方平台商户号
    payee_cloud_merchant_id: Optional[str] = None  # 收款方渠道商户号
    payee_store_no: Optional[str] = None  # 收款方自定义门店号
    payee_type: Optional[str] = None  # 收款方账户类型 0-收款账户 1-付款账户
    arrive_time: Optional[str] = None  # 到账时间 T0 当天到账 T1 次日到账
    real_amount: Optional[str] = None  # 实际到账金额(分)
    status: Optional[str] = None  # 状态: 0=失败, 1=成功, 2=已退款, 9=处理中, n=待发送申请
    status_desc: Optional[str] = None  # 状态描述
    finish_time: Optional[str] = None  # 完成时间
    before_amount: Optional[str] = None  # 交易前账户余额(分)
    
    def get_status_text(self) -> str:
        """获取状态描述文本"""
        status_map = {
            "0": "失败",
            "1": "成功",
            "2": "已退款",
            "9": "处理中",
            "n": "待发送申请"
        }
        return status_map.get(self.status or "", f"未知状态({self.status})")
    
    def get_trade_type_text(self) -> str:
        """获取交易类型描述"""
        type_map = {
            "p": "支付",
            "r": "退款"
        }
        return type_map.get(self.trade_type or "", self.trade_type or "未知")
    
    def get_total_amount_yuan(self) -> float:
        """获取交易金额（元）"""
        try:
            return float(self.total_amount or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_real_amount_yuan(self) -> float:
        """获取实际到账金额（元）"""
        try:
            return float(self.real_amount or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_before_amount_yuan(self) -> float:
        """获取交易前余额（元）"""
        try:
            return float(self.before_amount or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def is_success(self) -> bool:
        """判断交易是否成功"""
        return self.status == "1"


@dataclass
class BalancePayQueryResponse:
    """余额支付查询响应模型"""
    request_id: str  # 请求唯一ID
    code: int  # 返回码
    msg: str = ""  # 返回信息
    sub_code: Optional[str] = None  # 子错误码
    sub_msg: Optional[str] = None  # 子错误信息
    sign: Optional[str] = None  # 响应签名
    data: Optional[BalancePayQueryData] = None  # 业务数据
    success: bool = False  # 是否成功
    
    def is_success(self) -> bool:
        """判断查询是否成功"""
        return self.code == 10000 and self.success
    
    def get_error_message(self) -> str:
        """获取错误信息"""
        if self.is_success():
            return ""
        
        if self.sub_msg:
            return f"{self.msg}: {self.sub_msg}"
        return self.msg or "未知错误"
    
    @classmethod
    def from_dict(cls, response_dict: dict) -> 'BalancePayQueryResponse':
        """从字典创建响应对象"""
        # 提取响应根数据
        response_data = response_dict.get('bkfunds_balance_pay_query_response', {})
        
        # 创建基本响应对象
        response = cls(
            request_id=response_data.get('request_id', ''),
            code=response_data.get('code', 0),
            msg=response_data.get('msg', ''),
            sub_code=response_data.get('sub_code'),
            sub_msg=response_data.get('sub_msg'),
            sign=response_data.get('sign'),
            success=response_data.get('success', False)
        )
        
        # 处理业务数据
        data_dict = response_data.get('data')
        if data_dict:
            response.data = BalancePayQueryData(
                trade_time=data_dict.get('trade_time'),
                node_id=data_dict.get('node_id'),
                node_name=data_dict.get('node_name'),
                platform_no=data_dict.get('platform_no'),
                ym_trade_no=data_dict.get('ym_trade_no'),
                trade_no=data_dict.get('trade_no'),
                total_amount=data_dict.get('total_amount'),
                fee=data_dict.get('fee'),
                trade_type=data_dict.get('trade_type'),
                payer_merchant_id=data_dict.get('payer_merchant_id'),
                payer_cloud_merchant_id=data_dict.get('payer_cloud_merchant_id'),
                payer_store_no=data_dict.get('payer_store_no'),
                payer_type=data_dict.get('payer_type'),
                payee_merchant_id=data_dict.get('payee_merchant_id'),
                payee_cloud_merchant_id=data_dict.get('payee_cloud_merchant_id'),
                payee_store_no=data_dict.get('payee_store_no'),
                payee_type=data_dict.get('payee_type'),
                arrive_time=data_dict.get('arrive_time'),
                real_amount=data_dict.get('real_amount'),
                status=data_dict.get('status'),
                status_desc=data_dict.get('status_desc'),
                finish_time=data_dict.get('finish_time'),
                before_amount=data_dict.get('before_amount')
            )
        
        return response


@dataclass
class DatabaseQueryResult:
    """数据库查询结果模型（用于查询银行流水号）"""
    billid: str  # 账单ID
    xpbillid: str  # 销售单号
    trade_no: Optional[str] = None  # 银行流水号
    query_time: Optional[datetime] = None  # 查询时间
    
    def __post_init__(self):
        """初始化后处理"""
        if self.query_time is None:
            self.query_time = datetime.now()
    
    def has_trade_no(self) -> bool:
        """判断是否有银行流水号"""
        return self.trade_no is not None and self.trade_no.strip() != ''
    
    def get_trade_no(self) -> str:
        """获取银行流水号"""
        if self.has_trade_no() and self.trade_no:
            return self.trade_no.strip()
        return ""


if __name__ == '__main__':
    """测试余额支付查询数据模型"""
    print("🧪 测试余额支付查询数据模型")
    
    # 测试请求模型
    request = BalancePayQueryRequest(
        node_id="00061967",
        trade_no="2025062413594476280"
    )
    print(f"📤 请求模型: {request.to_dict()}")
    
    # 测试参数验证
    is_valid, errors = request.validate()
    valid_text = "✅ 有效" if is_valid else "❌ 无效"
    print(f"🔍 参数验证: {valid_text} - 错误: {errors}")
    
    # 测试响应模型
    test_response = {
        "bkfunds_balance_pay_query_response": {
            "request_id": "openapi_c7ee5fe4348e4d0a990d192366032ea9",
            "code": 10000,
            "success": True,
            "data": {
                "trade_time": "2025-06-24 13:59:45",
                "node_id": "00061967",
                "node_name": "18823657777",
                "platform_no": "111",
                "ym_trade_no": "2025062413594476280",
                "trade_no": "2025062413594476280",
                "total_amount": "10",
                "fee": "0",
                "trade_type": "p",
                "status": "1",
                "status_desc": "交易成功",
                "finish_time": "2025-06-24 13:59:45",
                "real_amount": "10",
                "before_amount": "99919834"
            }
        }
    }
    
    response = BalancePayQueryResponse.from_dict(test_response)
    print(f"📥 响应解析成功: {response.is_success()}")
    if response.data:
        print(f"📊 交易状态: {response.data.get_status_text()}")
        print(f"💰 交易金额: {response.data.get_total_amount_yuan()}元")
        print(f"💳 交易类型: {response.data.get_trade_type_text()}")
    
    # 测试数据库查询结果
    db_result = DatabaseQueryResult(
        billid="BILL001",
        xpbillid="XP2025010110000001",
        trade_no="2025062413594476280"
    )
    print(f"🗄️ 数据库结果: {db_result.get_trade_no()}")
    
    print("✅ 数据模型测试完成")