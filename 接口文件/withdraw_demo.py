#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
提现申请接口演示 - GUI支持版本
文件名: withdraw_demo.py
测试环境: https://fzxt-yzt-openapi.imageco.cn
接口名: bkfunds.withdraw.apply

功能说明:
1. 支持GUI模式调用和日志系统
2. 提现业务：从账户中提取资金到指定银行卡
3. 支持测试/正式环境切换
4. 测试环境：固定商户号进行提现
5. 正式环境：从数据库获取提现信息
"""

import json
import time
import uuid
import logging
from datetime import datetime
# 尝试导入cx_Oracle，如果失败则使用模拟
try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None

from common.OpenClient import OpenClient
from model.WithdrawModel import WithdrawModel
from request.WithdrawRequest import WithdrawRequest
from config import Config
from config_adapter import config_adapter


class WithdrawDemo:
    """提现申请演示类 - GUI支持版本"""

    def __init__(self, logger=None):
        self.config = Config
        self.client = OpenClient(Config.APP_ID, Config.PRIVATE_KEY, Config.get_url())

        # 设置日志器
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('Withdraw')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

        self.logger.info(f"[提现管理] 💰 提现申请系统初始化完成")
        self.logger.info(f"[提现管理] 🌍 当前环境: {Config.get_env_name()}")

    def get_database_connection(self):
        """获取数据库连接"""
        try:
            if cx_Oracle is None:
                self.logger.warning(f"[提现管理] ⚠️ cx_Oracle未安装，使用模拟数据")
                return None
                
            user, password, dsn = Config.get_db_connection_info()
            self.logger.info(f"[提现管理] 正在连接数据库: {dsn}")
            connection = cx_Oracle.connect(user, password, dsn)
            self.logger.info(f"[提现管理] ✅ 数据库连接成功: {dsn}")
            return connection
        except Exception as e:
            self.logger.error(f"[提现管理] ❌ 数据库连接失败: {str(e)}")
            return None

    def get_withdraw_orders_from_database(self):
        """从数据库获取待提现的订单信息（正式环境）"""
        connection = self.get_database_connection()
        if not connection:
            # 如果数据库连接失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[提现管理] ⚠️ 数据库连接失败，测试环境返回模拟数据")
                return self._get_test_withdraw_orders()
            return []

        try:
            cursor = connection.cursor()

            # 根据用户提供的SQL语句查询待提现记录
            sql = """
            select BILLID, STOREID, MERCHANTNO, IS_UNPAID_FEE, WITHDRAW_AMOUNT, 
                   AVAILABLE_FEE, TRANSACTION_NO, WITHDRAW_TIME, SERVICE_FEE  
            from p_bl_draw_hd
            where AVAILABLE_FEE>=WITHDRAW_AMOUNT and IS_UNPAID_FEE='Y' and cancelsign='N' and status='003'
            """

            self.logger.info(f"[提现管理] 🔍 执行批量提现查询SQL:")
            self.logger.info(f"[提现管理] {sql}")

            cursor.execute(sql)
            rows = cursor.fetchall()

            self.logger.info(f"[提现管理] 📊 数据库查询结果: 共找到 {len(rows)} 条待提现记录")

            # 处理查询结果
            orders = []
            for i, row in enumerate(rows, 1):
                billid, storeid, merchantno, is_unpaid_fee, withdraw_amount, available_fee, transaction_no, withdraw_time, service_fee = row

                self.logger.info(f"[提现管理] 📋 处理第 {i} 条提现记录:")
                self.logger.info(f"[提现管理]    提现单据号: {billid}")
                self.logger.info(f"[提现管理]    门店ID: {storeid}")
                self.logger.info(f"[提现管理]    商户号: {merchantno}")
                self.logger.info(f"[提现管理]    费用结清标记: {is_unpaid_fee}")
                self.logger.info(f"[提现管理]    提现金额: {withdraw_amount}")
                self.logger.info(f"[提现管理]    可用余额: {available_fee}")
                self.logger.info(f"[提现管理]    交易号: {transaction_no}")
                self.logger.info(f"[提现管理]    提现时间: {withdraw_time}")
                self.logger.info(f"[提现管理]    手续费: {service_fee}")

                # 处理金额，确保转换为分
                try:
                    withdraw_amount_fen = int(float(withdraw_amount) * 100) if withdraw_amount else 0
                except (ValueError, TypeError):
                    self.logger.warning(f"[提现管理] ⚠️ 提现金额格式错误，跳过: {billid}")
                    continue

                if withdraw_amount_fen <= 0:
                    self.logger.warning(f"[提现管理] ⚠️ 提现金额为0或负数，跳过: {billid}")
                    continue

                order_data = {
                    'billid': billid,
                    'storeid': storeid,
                    'merchantno': merchantno,
                    'is_unpaid_fee': is_unpaid_fee,
                    'withdraw_amount': withdraw_amount_fen,
                    'available_fee': float(available_fee) if available_fee else 0,
                    'transaction_no': transaction_no,
                    'withdraw_time': withdraw_time,
                    'service_fee': float(service_fee) if service_fee else 0,
                    'business_type': '提现申请',
                    'withdraw_status': '待处理',
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                orders.append(order_data)

                self.logger.info(f"[提现管理]    ✅ 添加提现订单: 提现金额 {withdraw_amount_fen / 100:.2f}元")

            return orders

        except Exception as e:
            self.logger.error(f"[提现管理] ❌ 数据库查询失败: {str(e)}")
            import traceback
            self.logger.error(f"[提现管理] 错误详情: {traceback.format_exc()}")
            # 如果数据库查询失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[提现管理] ⚠️ 数据库查询失败，测试环境返回模拟数据")
                return self._get_test_withdraw_orders()
            return []
        finally:
            if connection:
                connection.close()
                self.logger.info(f"[提现管理] 🔒 数据库连接已关闭")

    def get_withdraw_order_by_billid(self, billid):
        """根据billid获取待提现的订单信息"""
        connection = self.get_database_connection()
        if not connection:
            # 如果数据库连接失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[提现管理] ⚠️ 数据库连接失败，测试环境返回模拟数据")
                return self._get_test_withdraw_orders()
            return []

        try:
            cursor = connection.cursor()

            # 根据用户提供的SQL语句查询单个提现记录
            sql = """
            select BILLID, STOREID, MERCHANTNO, IS_UNPAID_FEE, WITHDRAW_AMOUNT, 
                   AVAILABLE_FEE, TRANSACTION_NO, WITHDRAW_TIME, SERVICE_FEE  
            from p_bl_draw_hd
            where AVAILABLE_FEE>=WITHDRAW_AMOUNT and IS_UNPAID_FEE='Y' and cancelsign='N' and status='003'
            and BILLID = :billid
            """

            self.logger.info(f"[提现管理] 🔍 根据billid执行查询SQL:")
            self.logger.info(f"[提现管理] {sql}")
            self.logger.info(f"[提现管理] 🎯 查询条件: billid = {billid}")

            cursor.execute(sql, {'billid': billid})
            rows = cursor.fetchall()

            self.logger.info(f"[提现管理] 📊 数据库查询结果: 共找到 {len(rows)} 条待提现记录")

            if not rows:
                self.logger.warning(f"[提现管理] ⚠️ 未找到billid为 {billid} 的待提现记录")
                return []

            # 处理查询结果
            orders = []
            for i, row in enumerate(rows, 1):
                billid, storeid, merchantno, is_unpaid_fee, withdraw_amount, available_fee, transaction_no, withdraw_time, service_fee = row

                self.logger.info(f"[提现管理] 📋 处理第 {i} 条提现记录:")
                self.logger.info(f"[提现管理]    提现单据号: {billid}")
                self.logger.info(f"[提现管理]    门店ID: {storeid}")
                self.logger.info(f"[提现管理]    商户号: {merchantno}")
                self.logger.info(f"[提现管理]    费用结清标记: {is_unpaid_fee}")
                self.logger.info(f"[提现管理]    提现金额: {withdraw_amount}")
                self.logger.info(f"[提现管理]    可用余额: {available_fee}")
                self.logger.info(f"[提现管理]    交易号: {transaction_no}")
                self.logger.info(f"[提现管理]    提现时间: {withdraw_time}")
                self.logger.info(f"[提现管理]    手续费: {service_fee}")

                # 处理金额，确保转换为分
                try:
                    withdraw_amount_fen = int(float(withdraw_amount) * 100) if withdraw_amount else 0
                except (ValueError, TypeError):
                    self.logger.warning(f"[提现管理] ⚠️ 提现金额格式错误，跳过: {billid}")
                    continue

                if withdraw_amount_fen <= 0:
                    self.logger.warning(f"[提现管理] ⚠️ 提现金额为0或负数，跳过: {billid}")
                    continue

                order_data = {
                    'billid': billid,
                    'storeid': storeid,
                    'merchantno': merchantno,
                    'is_unpaid_fee': is_unpaid_fee,
                    'withdraw_amount': withdraw_amount_fen,
                    'available_fee': float(available_fee) if available_fee else 0,
                    'transaction_no': transaction_no,
                    'withdraw_time': withdraw_time,
                    'service_fee': float(service_fee) if service_fee else 0,
                    'business_type': '提现申请',
                    'withdraw_status': '待处理',
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                orders.append(order_data)

                self.logger.info(f"[提现管理]    ✅ 添加提现订单: 提现金额 {withdraw_amount_fen / 100:.2f}元")

            return orders

        except Exception as e:
            self.logger.error(f"[提现管理] ❌ 数据库查询失败: {str(e)}")
            import traceback
            self.logger.error(f"[提现管理] 错误详情: {traceback.format_exc()}")
            # 如果数据库查询失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[提现管理] ⚠️ 数据库查询失败，测试环境返回模拟数据")
                return self._get_test_withdraw_orders()
            return []
        finally:
            if connection:
                connection.close()
                self.logger.info(f"[提现管理] 🔒 数据库连接已关闭")

    def _get_test_withdraw_orders(self):
        """获取测试环境的模拟提现订单"""
        self.logger.info(f"[提现管理] 🧪 生成测试环境模拟数据")

        test_orders = [
            {
                'billid': f'TEST_WITHDRAW_{datetime.now().strftime("%Y%m%d%H%M%S")}_001',
                'storeid': 'TEST_STORE_001',
                'merchantno': '1000000001222',
                'is_unpaid_fee': 'Y',
                'withdraw_amount': 10000,  # 100元 = 10000分
                'available_fee': 150.00,
                'transaction_no': '',
                'withdraw_time': None,
                'service_fee': 2.00,
                'business_type': '提现申请',
                'withdraw_status': '待处理',
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

        self.logger.info(f"[提现管理] 📈 测试数据生成完成: 共 {len(test_orders)} 笔测试订单")
        for order in test_orders:
            self.logger.info(f"[提现管理]   - 订单号: {order['billid']}")
            self.logger.info(f"[提现管理]   - 商户号: {order['merchantno']}")
            self.logger.info(f"[提现管理]   - 门店ID: {order['storeid']}")
            self.logger.info(f"[提现管理]   - 提现金额: {order['withdraw_amount'] / 100:.2f}元")

        return test_orders

    def create_withdraw_request(self, order_data):
        """
        创建提现申请请求
        :param order_data: 订单数据
        :return: request对象
        """
        self.logger.info(f"[提现管理] 🔧 创建提现申请请求:")
        self.logger.info(f"[提现管理]   原订单号: {order_data['billid']}")
        self.logger.info(f"[提现管理]   商户号: {order_data['merchantno']}")
        self.logger.info(f"[提现管理]   门店ID: {order_data['storeid']}")
        self.logger.info(f"[提现管理]   提现金额: {order_data['withdraw_amount']}分 ({order_data['withdraw_amount'] / 100}元)")

        # 创建请求对象
        request = WithdrawRequest()
        # 创建业务参数模型
        model = WithdrawModel()

        # ===== 基本参数设置 =====
        # 使用配置适配器获取机构号
        model.sso_node_id = str(config_adapter.get_node_id())  # 机构号
        model.merchant_id = str(order_data['merchantno'])  # 翼码商户id
        model.store_no = str(order_data['storeid'])  # 自定义门店号
        
        # 账户类型 0-收款账户 1-付款账户
        model.account_sub_type = "1"  # 付款账户

        # ===== 提现金额 =====
        model.total_amount = int(order_data['withdraw_amount'])  # 提现金额(分)

        # ===== 其他信息 =====
        model.remark = str(f"MUMUSO提现申请-{order_data['billid']}")

        # 验证参数
        valid, errors = model.validate()
        if not valid:
            self.logger.error(f"[提现管理] ❌ 参数验证失败:")
            for error in errors:
                self.logger.error(f"[提现管理]   - {error}")
            raise ValueError(f"参数验证失败: {errors}")

        # 设置请求的业务模型
        request.biz_model = model
        self.logger.info(f"[提现管理] ✅ 提现申请请求对象创建完成")
        return request

    def execute_withdraw_request(self, request, order_data):
        """
        执行提现申请请求 - 使用OpenClient
        :param request: 提现申请请求对象
        :param order_data: 订单数据
        :return: 响应结果
        """
        try:
            model = request.biz_model

            self.logger.info(f"[提现管理] 📡 使用OpenClient发送提现申请请求:")
            self.logger.info(f"[提现管理]   接口地址: {Config.get_url()}")
            self.logger.info(f"[提现管理]   接口方法: {request.get_method()}")
            self.logger.info(f"[提现管理]   请求类型: {request.get_request_type()}")
            self.logger.info(f"[提现管理]   请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 验证业务参数
            if hasattr(request.biz_model, 'validate'):
                valid, errors = request.biz_model.validate()
                if not valid:
                    self.logger.error(f"[提现管理] ❌ 业务参数验证失败: {errors}")
                    return None

            # 打印业务参数
            self.logger.info(f"[提现管理] 🔧 业务参数:")
            biz_dict = model.to_dict()
            for key, value in biz_dict.items():
                if value is not None:
                    self.logger.info(f"[提现管理]   {key}: {value}")

            # 使用OpenClient执行请求（会自动生成签名）
            self.logger.info(f"[提现管理] 🔐 执行OpenClient请求（包含RSA2签名）...")
            response = self.client.execute(request)

            self.logger.info(f"[提现管理] 📋 提现申请响应:")
            if response:
                self.logger.info(f"[提现管理] {json.dumps(response, indent=2, ensure_ascii=False)}")
            else:
                self.logger.error(f"[提现管理] ❌ 响应为空")

            return response

        except Exception as e:
            self.logger.error(f"[提现管理] ❌ 提现申请请求异常: {str(e)}")
            import traceback
            self.logger.error(f"[提现管理] 错误详情: {traceback.format_exc()}")
            return None

    def withdraw_single_order(self, order_data):
        """对单个订单进行提现申请"""
        self.logger.info(f"[提现管理] " + "=" * 60)
        self.logger.info(f"[提现管理] 💰 开始订单提现申请: {order_data['billid']}")
        self.logger.info(f"[提现管理] " + "=" * 60)

        try:
            self.logger.info(f"[提现管理] 📄 执行提现申请...")

            # 创建提现请求
            request = self.create_withdraw_request(order_data)

            # 执行提现请求
            response = self.execute_withdraw_request(request, order_data)

            # 处理响应
            success, msg, request_id, trade_no = self._handle_withdraw_response(response)

            result = {
                'billid': order_data['billid'],
                'merchantno': order_data['merchantno'],
                'storeid': order_data['storeid'],
                'amount': order_data['withdraw_amount'],
                'success': success,
                'message': msg,
                'response': response,
                'request_id': request_id,
                'trade_no': trade_no,
                'execute_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if success:
                self.logger.info(f"[提现管理] ✅ 提现申请成功: {order_data['withdraw_amount']}分")
                # 更新数据库状态
                update_success = self.update_withdraw_status(order_data['billid'], True, request_id, trade_no)
                if update_success:
                    self.logger.info(f"[提现管理] ✅ 提现状态更新成功")
                else:
                    self.logger.error(f"[提现管理] ❌ 提现状态更新失败")
            else:
                self.logger.error(f"[提现管理] ❌ 提现申请失败: {msg}")
                # 更新数据库状态为失败
                self.update_withdraw_status(order_data['billid'], False, request_id, trade_no)

            return result

        except Exception as e:
            error_msg = f"提现异常: {str(e)}"
            self.logger.error(f"[提现管理] ❌ 提现异常: {error_msg}")

            result = {
                'billid': order_data['billid'],
                'merchantno': order_data['merchantno'],
                'storeid': order_data['storeid'],
                'amount': order_data['withdraw_amount'],
                'success': False,
                'message': error_msg,
                'response': None,
                'request_id': None,
                'trade_no': None,
                'execute_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 更新数据库状态为失败
            self.update_withdraw_status(order_data['billid'], False, None, None)
            return result

    def withdraw_single_order_by_billid(self, billid):
        """根据billid对单个订单进行提现申请"""
        self.logger.info(f"[提现管理] " + "=" * 60)
        self.logger.info(f"[提现管理] 💰 开始根据billid进行订单提现申请: {billid}")
        self.logger.info(f"[提现管理] " + "=" * 60)

        # 根据billid获取订单信息
        orders = self.get_withdraw_order_by_billid(billid)

        if not orders:
            self.logger.warning(f"[提现管理] ⚠️ 未找到billid为 {billid} 的待提现订单")
            return None

        # 使用找到的第一个订单进行提现
        order = orders[0]
        result = self.withdraw_single_order(order)

        return result

    def batch_withdraw_orders(self):
        """批量处理提现申请"""
        self.logger.info(f"[提现管理] 🚀 开始批量提现申请处理")
        self.logger.info(f"[提现管理] 🌍 当前环境: {Config.get_env_name()}")

        # 获取待提现订单
        orders = self.get_withdraw_orders_from_database()

        if not orders:
            self.logger.warning(f"[提现管理] ⚠️ 没有找到待提现的订单")
            return []

        self.logger.info(f"[提现管理] 📊 开始处理 {len(orders)} 笔待提现订单")

        all_results = []
        for i, order in enumerate(orders, 1):
            self.logger.info(f"[提现管理] 📋 处理第 {i}/{len(orders)} 笔订单: {order['billid']}")

            try:
                # 执行提现
                result = self.withdraw_single_order(order)
                all_results.append(result)

                # 间隔一下
                if i < len(orders):
                    self.logger.info(f"[提现管理] ⏱️ 等待2秒后处理下一笔订单...")
                    time.sleep(2)

            except Exception as e:
                self.logger.error(f"[提现管理] ❌ 订单处理异常: {order['billid']}, 错误: {str(e)}")

        # 汇总统计
        total_withdraws = len(all_results)
        success_withdraws = sum(1 for r in all_results if r['success'])

        self.logger.info(f"[提现管理] " + "=" * 60)
        self.logger.info(f"[提现管理] 📊 批量提现申请完成")
        self.logger.info(f"[提现管理] " + "=" * 60)
        self.logger.info(f"[提现管理] 📈 处理订单数: {len(orders)}")
        self.logger.info(f"[提现管理] 🎯 提现申请总数: {total_withdraws}")
        self.logger.info(f"[提现管理] ✅ 提现成功: {success_withdraws}")
        self.logger.info(f"[提现管理] ❌ 提现失败: {total_withdraws - success_withdraws}")
        self.logger.info(
            f"[提现管理] 📊 成功率: {(success_withdraws / total_withdraws * 100):.1f}%" if total_withdraws > 0 else "无提现申请")

        return all_results

    def _handle_withdraw_response(self, response):
        """处理提现申请响应结果"""
        self.logger.info(f"[提现管理] 📊 响应解析:")

        if not response:
            self.logger.error(f"[提现管理] ❌ 响应为空")
            return False, "响应为空", None, None

        # 根据API文档，响应的根键名可能是 bkfunds_withdraw_apply_response
        withdraw_response = response
        if 'bkfunds_withdraw_apply_response' in response:
            withdraw_response = response['bkfunds_withdraw_apply_response']

        success = withdraw_response.get('success', False)
        code = withdraw_response.get('code', 'N/A')
        msg = withdraw_response.get('msg', 'N/A')
        request_id = withdraw_response.get('request_id', 'N/A')
        sub_code = withdraw_response.get('sub_code', '')
        sub_msg = withdraw_response.get('sub_msg', '')
        
        # 获取交易流水号
        trade_no = None
        data = withdraw_response.get('data', {})
        if isinstance(data, dict):
            trade_no = data.get('trade_no')

        self.logger.info(f"[提现管理]   成功标识: {success}")
        self.logger.info(f"[提现管理]   响应码: {code}")
        self.logger.info(f"[提现管理]   响应消息: {msg}")
        self.logger.info(f"[提现管理]   请求ID: {request_id}")
        self.logger.info(f"[提现管理]   交易流水号: {trade_no}")
        if sub_code:
            self.logger.info(f"[提现管理]   子错误码: {sub_code}")
        if sub_msg:
            self.logger.info(f"[提现管理]   子错误信息: {sub_msg}")

        if success:
            return True, msg, request_id, trade_no
        else:
            error_msg = f"错误码: {code}, 消息: {msg}"
            if sub_msg:
                error_msg += f", 详细: {sub_msg}"
            return False, error_msg, request_id, trade_no

    def update_withdraw_status(self, billid, success=True, request_id=None, trade_no=None):
        """更新提现申请状态到数据库"""
        connection = self.get_database_connection()
        if not connection:
            self.logger.error(f"[提现管理] ❌ 无法获取数据库连接，无法更新提现申请状态")
            return False

        try:
            cursor = connection.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if success:
                # 提现成功，更新status为'007'
                sql = """
                UPDATE p_bl_draw_hd 
                SET status = '007',
                    WITHDRAW_TIME = TO_DATE(:withdraw_time, 'YYYY-MM-DD HH24:MI:SS'),
                    TRANSACTION_NO = :transaction_no
                WHERE billid = :billid
                """
                
                params = {
                    'billid': billid,
                    'withdraw_time': current_time,
                    'transaction_no': trade_no if trade_no else ''
                }
            else:
                # 提现失败，可以记录失败时间等信息
                sql = """
                UPDATE p_bl_draw_hd 
                SET WITHDRAW_TIME = TO_DATE(:withdraw_time, 'YYYY-MM-DD HH24:MI:SS')
                WHERE billid = :billid
                """
                
                params = {
                    'billid': billid,
                    'withdraw_time': current_time
                }

            self.logger.info(f"[提现管理] 📄 更新提现申请状态: {billid} -> {'成功' if success else '失败'}")

            cursor.execute(sql, params)
            connection.commit()
            affected_rows = cursor.rowcount

            if affected_rows > 0:
                self.logger.info(f"[提现管理] ✅ 提现申请状态更新成功，影响行数: {affected_rows}")
            else:
                self.logger.warning(f"[提现管理] ⚠️ 提现申请状态更新无影响行数: {billid}")

            cursor.close()
            return affected_rows > 0

        except Exception as e:
            self.logger.error(f"[提现管理] ❌ 提现申请状态更新失败: {str(e)}")
            import traceback
            self.logger.error(f"[提现管理] 错误详情: {traceback.format_exc()}")
            try:
                connection.rollback()
            except:
                pass
            return False
        finally:
            if connection:
                connection.close()


# ===== 4. 主函数和调用示例 =====
def run_demo():
    """运行演示程序"""
    print("💰 MUMUSO提现申请系统 - 完整版")
    print("=" * 80)
    print("🔧 集成内容:")
    print("   1. WithdrawModel - 业务参数模型")
    print("   2. WithdrawRequest - 请求类")
    print("   3. WithdrawDemo - 演示类")
    print("   4. 支持测试/正式环境")
    print("=" * 80)

    # 检查配置
    ready, msg = Config.is_config_ready()
    if not ready:
        print(f"⚠️ 配置检查失败: {msg}")
        return False

    # 创建提现申请实例
    withdraw_demo = WithdrawDemo()

    print("\n🚀 开始自动执行提现申请演示...")

    # 执行批量提现
    results = withdraw_demo.batch_withdraw_orders()

    print(f"\n🎉 提现申请演示完成!")
    return True


if __name__ == '__main__':
    print("=" * 80)
    print("💰 MUMUSO提现申请系统")
    print("=" * 80)

    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n👋 程序退出")
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")