#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
账户余额查询数据模型
文件名: AccountBalanceQueryModel.py  
功能: 定义账户余额查询相关的数据模型类
接口: merchant.balanceQuery
参考文档: 3.7.3账户余额查询
作者: 系统自动生成
更新时间: 2025-08-29
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AccountBalanceQueryRequest:
    """账户余额查询请求模型"""
    sso_node_id: str = ""  # 机构ID（必须）
    account_sub_type: str = "1"  # 账户类型：0=收款账户，1=付款账户，默认1
    merchant_id: int = 0  # 商户号（必须）
    sub_node_id: Optional[str] = None  # 门店号（可选）
    store_no: Optional[str] = None  # 门店代码（可选）
    
    def to_dict(self):
        """转换为字典格式"""
        data = {
            "sso_node_id": self.sso_node_id,
            "account_sub_type": self.account_sub_type,
            "merchant_id": self.merchant_id
        }
        if self.sub_node_id:
            data["sub_node_id"] = self.sub_node_id
        if self.store_no:
            data["store_no"] = self.store_no
        return data
    
    def validate(self):
        """验证请求参数"""
        errors = []
        if not self.sso_node_id:
            errors.append("机构ID(sso_node_id)不能为空")
        if not self.merchant_id or self.merchant_id <= 0:
            errors.append("商户号(merchant_id)必须为正整数")
        if self.account_sub_type not in ['0', '1']:
            errors.append("账户类型(account_sub_type)必须是0(收款账户)或1(付款账户)")
        return len(errors) == 0, errors


@dataclass
class AccountBalanceData:
    """账户余额查询结果数据模型"""
    available_balance: Optional[int] = None  # 可用余额(分)
    frozen_balance: Optional[int] = None  # 冻结余额(分)
    amount_retained: Optional[int] = None  # 保留金额(分)
    total_balance: Optional[int] = None  # 总余额(分)
    
    def get_available_balance_yuan(self) -> float:
        """获取可用余额（元）"""
        try:
            return float(self.available_balance or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_frozen_balance_yuan(self) -> float:
        """获取冻结余额（元）"""
        try:
            return float(self.frozen_balance or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_amount_retained_yuan(self) -> float:
        """获取保留金额（元）"""
        try:
            return float(self.amount_retained or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_total_balance_yuan(self) -> float:
        """获取总余额（元）"""
        try:
            return float(self.total_balance or 0) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def is_sufficient(self, required_amount: int) -> bool:
        """判断可用余额是否充足"""
        return (self.available_balance or 0) >= required_amount
    
    def get_balance_summary(self) -> str:
        """获取余额摘要字符串"""
        return (f"总余额: {self.get_total_balance_yuan():.2f}元, "
                f"可用: {self.get_available_balance_yuan():.2f}元, "
                f"冻结: {self.get_frozen_balance_yuan():.2f}元, "
                f"保留: {self.get_amount_retained_yuan():.2f}元")


@dataclass
class AccountBalanceQueryResponse:
    """账户余额查询响应模型"""
    request_id: str  # 请求唯一ID
    code: int  # 返回码
    msg: str = ""  # 返回信息
    sub_code: Optional[str] = None  # 子错误码
    sub_msg: Optional[str] = None  # 子错误信息
    sign: Optional[str] = None  # 响应签名
    data: Optional[AccountBalanceData] = None  # 业务数据
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
    def from_dict(cls, response_dict: dict) -> 'AccountBalanceQueryResponse':
        """从字典创建响应对象"""
        # 提取响应根数据
        response_data = response_dict.get('merchant_balancequery_response', {})
        
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
            response.data = AccountBalanceData(
                available_balance=data_dict.get('available_balance'),
                frozen_balance=data_dict.get('frozen_balance'),
                amount_retained=data_dict.get('amount_retained'),
                total_balance=data_dict.get('total_balance')
            )
        
        return response


@dataclass
class MerchantInfo:
    """商户信息模型（用于批量查询）"""
    merchant_id: int  # 商户号
    merchant_name: str = ""  # 商户名称
    account_type: str = "1"  # 账户类型
    sub_node_id: Optional[str] = None  # 门店号
    store_no: Optional[str] = None  # 门店代码
    query_time: Optional[datetime] = None  # 查询时间
    total_amount: float = 0.0  # 总金额（元）
    bill_id: str = ""  # 账单ID
    
    def __post_init__(self):
        """初始化后处理"""
        if self.query_time is None:
            self.query_time = datetime.now()
    
    def get_account_type_text(self) -> str:
        """获取账户类型文本"""
        return "收款账户" if self.account_type == "0" else "付款账户"


if __name__ == '__main__':
    """测试账户余额查询数据模型"""
    print("🧪 测试账户余额查询数据模型")
    
    # 测试请求模型
    request = AccountBalanceQueryRequest(
        sso_node_id="00061990",  # 机构ID
        account_sub_type="1",
        merchant_id=1000000001234,
        sub_node_id="00061990",
        store_no="0001783"
    )
    print(f"📤 请求模型: {request.to_dict()}")
    
    # 测试参数验证
    is_valid, errors = request.validate()
    print(f"🔍 参数验证: {'✅ 有效' if is_valid else '❌ 无效'} - 错误: {errors}")
    
    # 测试响应模型
    test_response = {
        "merchant_balancequery_response": {
            "request_id": "test_request_123",
            "code": 10000,
            "success": True,
            "data": {
                "available_balance": 50000,  # 500元
                "frozen_balance": 10000,     # 100元
                "amount_retained": 5000,     # 50元
                "total_balance": 65000       # 650元
            }
        }
    }
    
    response = AccountBalanceQueryResponse.from_dict(test_response)
    print(f"📥 响应解析成功: {response.is_success()}")
    if response.data:
        print(f"📊 余额信息: {response.data.get_balance_summary()}")
        print(f"💰 总余额: {response.data.get_total_balance_yuan()}元")
        print(f"💳 可用余额: {response.data.get_available_balance_yuan()}元")
    
    # 测试商户信息
    merchant = MerchantInfo(
        merchant_id=1000000001234,
        merchant_name="测试商户",
        account_type="1"
    )
    print(f"🏪 商户信息: {merchant.merchant_name} ({merchant.get_account_type_text()})")