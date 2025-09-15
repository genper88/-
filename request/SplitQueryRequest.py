#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
余额支付查询请求类
文件名: SplitQueryRequest.py
功能: 封装余额支付/退款查询的API请求逻辑
接口: bkfunds.balance.pay.query
"""

import json
import logging
from datetime import datetime
from typing import Optional

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.OpenClient import OpenClient
from common import RequestTypes
from request.BaseRequest import BaseRequest
from model.SplitQueryModel import BalancePayQueryRequest, BalancePayQueryResponse
from config import Config


class BalancePayQueryAPIRequest(BaseRequest):
    """余额支付查询请求类 - 继承BaseRequest"""

    def __init__(self):
        super().__init__()

    def get_method(self):
        """返回接口方法名"""
        return "bkfunds.balance.pay.query"

    def get_version(self):
        """返回接口版本号"""
        return "1.0"

    def get_request_type(self):
        """返回请求类型"""
        return RequestTypes.POST_FORM

    def validate_request(self):
        """验证请求参数"""
        if not self.biz_model:
            return False, ["业务参数模型(biz_model)不能为空"]

        if hasattr(self.biz_model, 'validate'):
            return self.biz_model.validate()

        return True, []

    def __str__(self):
        """字符串表示"""
        return f"BalancePayQueryAPIRequest(method={self.get_method()}, model={self.biz_model})"


class BalancePayQueryRequestHandler:
    """余额支付查询请求处理类"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化请求处理器"""
        self.logger = logger or logging.getLogger(__name__)

        # 初始化OpenClient，传入必要的参数
        try:
            self.open_client = OpenClient(
                app_id=Config.APP_ID,
                private_key=Config.PRIVATE_KEY,
                url=Config.API_URL
            )
        except Exception as e:
            self.logger.error(f"[余额支付查询] 初始化OpenClient失败: {str(e)}")
            self.open_client = None

        # 接口相关配置
        self.node_id = Config.get_split_query_node_id()  # 使用同一个机构号配置

        self.logger.info(f"[余额支付查询] 初始化完成，当前环境: {Config.get_env_name()}")
        self.logger.info(f"[余额支付查询] 机构号: {self.node_id}")
        self.logger.info(f"[余额支付查询] API地址: {Config.get_url()}")

    def query_balance_pay_result(self, trade_no: str, node_id: Optional[str] = None) -> BalancePayQueryResponse:
        """
        查询余额支付结果

        Args:
            trade_no: 银行流水号
            node_id: 机构号（可选，默认使用配置中的机构号）

        Returns:
            BalancePayQueryResponse: 查询结果响应
        """
        try:
            self.logger.info(f"[余额支付查询] 开始查询交易结果, 流水号: {trade_no}")

            # 创建请求模型
            request_model = BalancePayQueryRequest(
                node_id=node_id or self.node_id,
                trade_no=trade_no
            )

            # 验证请求参数
            is_valid, errors = request_model.validate()
            if not is_valid:
                raise Exception(f"请求参数验证失败: {', '.join(errors)}")

            # 创建请求对象
            request = BalancePayQueryAPIRequest()
            request.biz_model = request_model

            # 验证请求对象
            is_valid, errors = request.validate_request()
            if not is_valid:
                raise Exception(f"请求对象验证失败: {', '.join(errors)}")

            # 构建业务请求参数
            biz_content = request_model.to_dict()
            self.logger.debug(f"[余额支付查询] 业务参数: {json.dumps(biz_content, ensure_ascii=False, indent=2)}")

            # 发送请求
            if not self.open_client:
                raise Exception("请求客户端未正确初始化")

            response_data = self.open_client.execute(request)

            # 解析响应
            response = BalancePayQueryResponse.from_dict({'bkfunds_balance_pay_query_response': response_data})

            # 记录日志
            if response.is_success():
                self.logger.info(f"[余额支付查询] 查询成功, 流水号: {trade_no}")
                if response.data:
                    self.logger.info(f"[余额支付查询] 交易状态: {response.data.get_status_text()}")
                    self.logger.info(f"[余额支付查询] 交易类型: {response.data.get_trade_type_text()}")
                    self.logger.info(f"[余额支付查询] 交易金额: {response.data.get_total_amount_yuan()}元")
                    self.logger.info(f"[余额支付查询] 实际到账: {response.data.get_real_amount_yuan()}元")
                    self.logger.info(f"[余额支付查询] 交易时间: {response.data.trade_time}")
                    self.logger.info(f"[余额支付查询] 完成时间: {response.data.finish_time}")
            else:
                self.logger.error(f"[余额支付查询] 查询失败, 流水号: {trade_no}")
                self.logger.error(f"[余额支付查询] 错误信息: {response.get_error_message()}")

            return response

        except Exception as e:
            self.logger.error(f"[余额支付查询] 请求异常, 流水号: {trade_no}, 错误: {str(e)}")
            # 返回失败响应
            return BalancePayQueryResponse(
                request_id="",
                code=0,
                msg=f"请求异常: {str(e)}",
                success=False
            )

    def batch_query_balance_pay_results(self, trade_nos: list) -> dict:
        """
        批量查询余额支付结果

        Args:
            trade_nos: 银行流水号列表

        Returns:
            dict: 查询结果字典，key为流水号，value为查询结果
        """
        self.logger.info(f"[余额支付查询] 开始批量查询, 数量: {len(trade_nos)}")

        results = {}
        success_count = 0
        fail_count = 0

        for i, trade_no in enumerate(trade_nos, 1):
            try:
                self.logger.info(f"[余额支付查询] 批量查询进度: {i}/{len(trade_nos)} - {trade_no}")

                result = self.query_balance_pay_result(trade_no)
                results[trade_no] = result

                if result.is_success():
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                self.logger.error(f"[余额支付查询] 批量查询异常, 流水号: {trade_no}, 错误: {str(e)}")
                results[trade_no] = BalancePayQueryResponse(
                    request_id="",
                    code=0,
                    msg=f"查询异常: {str(e)}",
                    success=False
                )
                fail_count += 1

        self.logger.info(f"[余额支付查询] 批量查询完成, 总数: {len(trade_nos)}, "
                         f"成功: {success_count}, 失败: {fail_count}")

        return results

    def validate_trade_no(self, trade_no: str) -> bool:
        """
        验证银行流水号格式

        Args:
            trade_no: 银行流水号

        Returns:
            bool: 是否有效
        """
        if not trade_no or not trade_no.strip():
            return False

        # 简单的长度和格式检查
        trade_no = trade_no.strip()

        # 假设流水号至少10位
        if len(trade_no) < 10:
            return False

        # 可以添加更多格式验证规则
        return True

    def format_query_result_summary(self, response: BalancePayQueryResponse) -> str:
        """
        格式化查询结果摘要

        Args:
            response: 查询响应结果

        Returns:
            str: 格式化的摘要信息
        """
        if not response.is_success():
            return f"查询失败: {response.get_error_message()}"

        if not response.data:
            return "查询成功，但无业务数据"

        data = response.data
        summary_lines = [
            f"查询成功",
            f"交易状态: {data.get_status_text()}",
            f"交易类型: {data.get_trade_type_text()}",
            f"交易金额: {data.get_total_amount_yuan():.2f}元",
            f"实际到账: {data.get_real_amount_yuan():.2f}元"
        ]

        return " | ".join(summary_lines)

    def get_detailed_result_info(self, response: BalancePayQueryResponse) -> list:
        """
        获取详细的查询结果信息

        Args:
            response: 查询响应结果

        Returns:
            list: 详细信息列表
        """
        info_list = []

        if not response.is_success():
            info_list.append(f"❌ 查询失败: {response.get_error_message()}")
            return info_list

        if not response.data:
            info_list.append("✅ 查询成功，但无业务数据")
            return info_list

        data = response.data

        # 添加基本信息
        info_list.append(f"✅ 查询成功")
        info_list.append(f"📊 交易状态: {data.get_status_text()}")
        info_list.append(f"💳 交易类型: {data.get_trade_type_text()}")
        info_list.append(f"💰 交易金额: {data.get_total_amount_yuan():.2f}元")
        info_list.append(f"💸 实际到账: {data.get_real_amount_yuan():.2f}元")
        info_list.append(f"🏦 交易前余额: {data.get_before_amount_yuan():.2f}元")
        info_list.append("")

        # 添加交易详情
        info_list.append("📅 交易详情:")
        if data.trade_time:
            info_list.append(f"  交易时间: {data.trade_time}")
        if data.finish_time:
            info_list.append(f"  完成时间: {data.finish_time}")
        if data.arrive_time:
            info_list.append(f"  到账时间: {data.arrive_time}")
        if data.platform_no:
            info_list.append(f"  平台流水号: {data.platform_no}")
        if data.ym_trade_no:
            info_list.append(f"  翼码流水号: {data.ym_trade_no}")
        info_list.append("")

        # 添加账户信息
        info_list.append("📄 账户信息:")
        if data.payer_merchant_id:
            payer_type = "收款账户" if data.payer_type == "0" else "付款账户"
            info_list.append(f"  付款方: {data.payer_merchant_id} ({payer_type})")
            if data.payer_store_no:
                info_list.append(f"    门店号: {data.payer_store_no}")

        if data.payee_merchant_id:
            payee_type = "收款账户" if data.payee_type == "0" else "付款账户"
            info_list.append(f"  收款方: {data.payee_merchant_id} ({payee_type})")
            if data.payee_store_no:
                info_list.append(f"    门店号: {data.payee_store_no}")

        return info_list


if __name__ == '__main__':
    """测试余额支付查询请求"""
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🧪 测试余额支付查询请求")

    # 创建请求处理器
    query_handler = BalancePayQueryRequestHandler()

    # 测试流水号验证
    test_trade_nos = [
        "2025062413594476280",  # 有效
        "123",  # 无效（太短）
        "",  # 无效（空）
        "VALID_TRADE_NO_12345678901"  # 有效
    ]

    print("\n📝 测试流水号验证:")
    for trade_no in test_trade_nos:
        is_valid = query_handler.validate_trade_no(trade_no)
        print(f"  {trade_no}: {'✅ 有效' if is_valid else '❌ 无效'}")

    # 如果是测试环境，可以测试实际请求
    if not Config.USE_PRODUCTION:
        print(f"\n🔍 当前环境: {Config.get_env_name()}")
        print("💡 可以在此添加实际的API测试调用")

        # 示例：测试单个查询（需要真实的流水号）
        # test_trade_no = "2025062413594476280"
        # result = query_handler.query_balance_pay_result(test_trade_no)
        # print(f"查询结果: {query_handler.format_query_result_summary(result)}")

    print("✅ 余额支付查询请求测试完成")