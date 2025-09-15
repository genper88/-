#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
账户余额查询请求处理
文件名: AccountBalanceQueryRequest.py
功能: 处理账户余额查询接口请求
接口: merchant.balanceQuery
参考文档: 3.7.3账户余额查询
作者: 系统自动生成
更新时间: 2025-08-29
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from common.OpenClient import OpenClient
from request.BaseRequest import BaseRequest
from model.AccountBalanceQueryModel import (
    AccountBalanceQueryRequest, 
    AccountBalanceQueryResponse, 
    MerchantInfo
)
from config import Config


class AccountBalanceQueryAPIRequest(BaseRequest):
    """账户余额查询API请求类"""
    
    def __init__(self):
        super().__init__()
    
    def get_method(self):
        return "merchant.balanceQuery"
    
    def get_version(self):
        """返回接口版本号"""
        return "1.0"
    
    def get_request_type(self):
        """返回请求类型"""
        from common import RequestTypes
        return RequestTypes.POST_FORM


class AccountBalanceQueryRequestHandler:
    """账户余额查询请求处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化处理器
        
        Args:
            logger: 日志记录器，如果不提供则创建默认的
        """
        self.logger = logger or self._create_default_logger()
        
        # 初始化OpenClient，传入必要的参数
        try:
            self.client = OpenClient(
                app_id=Config.APP_ID,
                private_key=Config.PRIVATE_KEY,
                url=Config.API_URL
            )
        except Exception as e:
            self.logger.error(f"[账户余额查询] 初始化OpenClient失败: {str(e)}")
            self.client = None
        
        # 从配置获取基本信息
        self.config = Config.get_account_balance_query_config()
        self.default_account_type = Config.get_default_account_type()
        
        self.logger.info(f"[账户余额查询] 初始化完成 - 环境: {Config.get_env_name()}")
        self.logger.debug(f"[账户余额查询] 默认账户类型: {self.default_account_type}")
    
    def _create_default_logger(self) -> logging.Logger:
        """创建默认日志记录器"""
        logger = logging.getLogger('AccountBalanceQuery')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def query_single_balance(self, merchant_id: int, 
                           account_type: Optional[str] = None,
                           sub_node_id: Optional[str] = None, 
                           store_no: Optional[str] = None) -> AccountBalanceQueryResponse:
        """
        查询单个商户的账户余额
        
        Args:
            merchant_id: 商户号
            account_type: 账户类型，默认使用配置中的默认值
            sub_node_id: 门店号（可选）
            store_no: 门店代码（可选）
            
        Returns:
            AccountBalanceQueryResponse: 查询响应
        """
        if account_type is None:
            account_type = self.default_account_type
        
        self.logger.info(f"[账户余额查询] 开始查询单个商户余额 - 商户号: {merchant_id}, 账户类型: {account_type}")
        
        try:
            # 创建请求模型
            request_data = AccountBalanceQueryRequest(
                sso_node_id=Config.get_account_balance_node_id(),  # 从配置获取机构ID
                account_sub_type=account_type,
                merchant_id=merchant_id,
                sub_node_id=sub_node_id,
                store_no=store_no
            )
            
            # 验证请求参数
            is_valid, errors = request_data.validate()
            if not is_valid:
                error_msg = f"请求参数验证失败: {'; '.join(errors)}"
                self.logger.error(f"[账户余额查询] {error_msg}")
                return self._create_error_response("参数错误", error_msg)
            
            self.logger.debug(f"[账户余额查询] 请求参数: {request_data.to_dict()}")
            
            # 创建API请求
            api_request = AccountBalanceQueryAPIRequest()
            api_request.biz_model = request_data
            
            # 发送请求
            if not self.client:
                raise Exception("请求客户端未正确初始化")
            
            self.logger.debug(f"[账户余额查询] 发送API请求...")
            response_data = self.client.execute(api_request)
            
            self.logger.debug(f"[账户余额查询] 收到响应: {response_data}")
            
            # 解析响应
            response = AccountBalanceQueryResponse.from_dict({'merchant_balancequery_response': response_data})
            
            if response.is_success():
                balance_info = response.data.get_balance_summary() if response.data else "无余额数据"
                self.logger.info(f"[账户余额查询] 查询成功 - 商户号: {merchant_id}, {balance_info}")
            else:
                self.logger.warning(f"[账户余额查询] 查询失败 - 商户号: {merchant_id}, 错误: {response.get_error_message()}")
            
            return response
            
        except Exception as e:
            error_msg = f"查询账户余额异常: {str(e)}"
            self.logger.error(f"[账户余额查询] {error_msg}", exc_info=True)
            return self._create_error_response("系统错误", error_msg)
    
    def batch_query_balances(self, merchant_list: List[MerchantInfo]) -> Dict[int, AccountBalanceQueryResponse]:
        """
        批量查询商户账户余额
        
        Args:
            merchant_list: 商户信息列表
            
        Returns:
            Dict[int, AccountBalanceQueryResponse]: 商户号 -> 查询响应的字典
        """
        self.logger.info(f"[账户余额查询] 开始批量查询 - 商户数量: {len(merchant_list)}")
        
        results = {}
        success_count = 0
        
        for i, merchant in enumerate(merchant_list, 1):
            try:
                self.logger.debug(f"[账户余额查询] 批量查询进度: {i}/{len(merchant_list)} - 商户: {merchant.merchant_id}")
                
                response = self.query_single_balance(
                    merchant_id=merchant.merchant_id,
                    account_type=merchant.account_type,
                    sub_node_id=merchant.sub_node_id,
                    store_no=merchant.store_no
                )
                
                results[merchant.merchant_id] = response
                
                if response.is_success():
                    success_count += 1
                
                # 如果有进度回调函数，可以在这里调用
                progress = (i / len(merchant_list)) * 100
                self.logger.debug(f"[账户余额查询] 批量查询进度: {progress:.1f}%")
                
            except Exception as e:
                error_msg = f"批量查询商户 {merchant.merchant_id} 失败: {str(e)}"
                self.logger.error(f"[账户余额查询] {error_msg}")
                results[merchant.merchant_id] = self._create_error_response("查询异常", error_msg)
        
        self.logger.info(f"[账户余额查询] 批量查询完成 - 总数: {len(merchant_list)}, 成功: {success_count}, 失败: {len(merchant_list) - success_count}")
        
        return results
    
    def format_balance_result_summary(self, response: AccountBalanceQueryResponse) -> str:
        """
        格式化余额查询结果摘要
        
        Args:
            response: 查询响应
            
        Returns:
            str: 格式化的摘要字符串
        """
        if not response.is_success():
            return f"查询失败: {response.get_error_message()}"
        
        if not response.data:
            return "查询成功，但无余额数据"
        
        return response.data.get_balance_summary()
    
    def get_detailed_balance_info(self, response: AccountBalanceQueryResponse) -> List[str]:
        """
        获取详细的余额信息列表
        
        Args:
            response: 查询响应
            
        Returns:
            List[str]: 详细信息列表
        """
        info_list = []
        
        info_list.append("=" * 50)
        info_list.append("账户余额查询详细信息")
        info_list.append("=" * 50)
        
        if not response.is_success():
            info_list.append(f"❌ 查询失败")
            info_list.append(f"错误代码: {response.code}")
            info_list.append(f"错误信息: {response.get_error_message()}")
            if response.request_id:
                info_list.append(f"请求ID: {response.request_id}")
        else:
            info_list.append(f"✅ 查询成功")
            if response.request_id:
                info_list.append(f"请求ID: {response.request_id}")
            
            if response.data:
                data = response.data
                info_list.append("")
                info_list.append("💰 余额详情:")
                info_list.append(f"  总余额: {data.get_total_balance_yuan():.2f} 元 ({data.total_balance or 0} 分)")
                info_list.append(f"  可用余额: {data.get_available_balance_yuan():.2f} 元 ({data.available_balance or 0} 分)")
                info_list.append(f"  冻结余额: {data.get_frozen_balance_yuan():.2f} 元 ({data.frozen_balance or 0} 分)")
                info_list.append(f"  保留金额: {data.get_amount_retained_yuan():.2f} 元 ({data.amount_retained or 0} 分)")
                
                # 余额充足性提示
                if (data.available_balance or 0) > 100:  # 大于1元
                    info_list.append("  💚 可用余额充足")
                elif (data.available_balance or 0) > 0:
                    info_list.append("  🟡 可用余额较少")
                else:
                    info_list.append("  🔴 可用余额不足")
            else:
                info_list.append("⚠️ 查询成功，但无余额数据返回")
        
        info_list.append("=" * 50)
        info_list.append(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return info_list
    
    def _create_error_response(self, msg: str, detail: str) -> AccountBalanceQueryResponse:
        """创建错误响应"""
        return AccountBalanceQueryResponse(
            request_id=f"error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            code=50000,
            msg=msg,
            sub_msg=detail,
            success=False
        )
    
    def validate_merchant_id(self, merchant_id: str) -> bool:
        """
        验证商户号格式
        
        Args:
            merchant_id: 商户号字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            mid = int(merchant_id)
            return mid > 0
        except (ValueError, TypeError):
            return False


if __name__ == '__main__':
    """测试账户余额查询处理器"""
    print("🧪 测试账户余额查询处理器")
    
    # 创建处理器
    handler = AccountBalanceQueryRequestHandler()
    
    # 测试商户号验证
    test_merchants = ["1000000001234", "abc", "0", "-1"]
    for mid in test_merchants:
        is_valid = handler.validate_merchant_id(mid)
        status = "✅ 有效" if is_valid else "❌ 无效"
        print(f"商户号 {mid}: {status}")
    
    print("\n✅ 账户余额查询处理器测试完成")