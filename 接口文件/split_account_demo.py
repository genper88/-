#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账申请接口演示 - GUI支持版本
文件名: split_account_demo.py
测试环境: https://fzxt-yzt-openapi.imageco.cn
接口名: bkfunds.balance.pay.apply

功能说明:
1. 支持GUI模式调用和日志系统
2. 分账业务：从加盟商付款账号分账给加盟商收款账号和公司收款账号
3. 支持测试/正式环境切换
4. 测试环境：固定商户号进行分账
5. 正式环境：从数据库获取分账信息
6. 支持营销转账：从营销子账号转账到供应商付款账户
7. 修正：金额计算包含营销转账金额
"""

import json
import time
import uuid
import logging
from datetime import datetime
import cx_Oracle

from common.OpenClient import OpenClient
from model.SplitAccountModel import SplitAccountModel
from request.SplitAccountRequest import SplitAccountRequest
from config import Config
# 导入配置适配器
from config_adapter import config_adapter


class SplitAccountDemo:
    """分账申请演示类 - GUI支持版本"""

    def __init__(self, logger=None):
        self.config = Config
        self.client = OpenClient(Config.APP_ID, Config.PRIVATE_KEY, Config.get_url())

        # 设置日志器
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('SplitAccount')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

        self.logger.info(f"[分账管理] 💰 分账申请系统初始化完成")
        self.logger.info(f"[分账管理] 🌍 当前环境: {Config.get_env_name()}")
        # 使用配置适配器获取分账配置
        self.logger.info(f"[分账管理] 📊 分账配置: {config_adapter.get_split_config()}")

    def get_database_connection(self):
        """获取数据库连接"""
        try:
            user, password, dsn = Config.get_db_connection_info()
            self.logger.info(f"[分账管理] 正在连接数据库: {dsn}")
            connection = cx_Oracle.connect(user, password, dsn)
            self.logger.info(f"[分账管理] ✅ 数据库连接成功: {dsn}")
            return connection
        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 数据库连接失败: {str(e)}")
            return None

    def get_split_orders_from_database(self):
        """从数据库获取待分账的订单信息（正式环境）"""
        connection = self.get_database_connection()
        if not connection:
            # 如果数据库连接失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[分账管理] ⚠️ 数据库连接失败，测试环境返回模拟数据")
                return self._get_test_split_orders()
            return []

        try:
            cursor = connection.cursor()

            # 使用用户提供的完整准确SQL语句
            sql = """
            SELECT hd.billid, dt.xpbillid as order_id, dt.gs_fzmoney 公司分账金额, dt.jms_fzmoney 加盟商分账金额, 
                   hd.jms_payaccount 加盟商支付账号, hd.gs_receiveaccount 公司收款账号, hd.jms_receiveaccount 加盟商收款账号,
                   1 as PAYER_ACCOUNT_TYPE_FK, 0 as PAYEE_ACCOUNT_TYPE_SK, hd.payaccoutgsyx 公司营销子账号,
                   dt.paytype, dt.sourcemoney 营销子账号转账金额
                FROM P_BL_SELL_PAYAMOUNT_HZ_HD hd
                LEFT JOIN P_BL_SELL_PAYAMOUNT_HZ_dt dt ON hd.billid = dt.billid 
                WHERE hd.cancelsign = 'N' 
                AND dt.cancelsign = 'N'
                AND dt.IS_FZ_REQUEST = 'N'
                AND hd.status = '003'
                and dt.paytype in('099','003')
                AND (dt.gs_fzmoney <> 0 OR dt.jms_fzmoney <> 0 or dt.sourcemoney <>0 )
                AND hd.allresult_check_sign='Y'
                ORDER BY hd.billid ASC, dt.xpbillid ASC
            """

            self.logger.info(f"[分账管理] 🔍 执行批量分账查询SQL:")
            self.logger.info(f"[分账管理] {sql}")
            self.logger.info(f"[分账管理] 🎯 查询条件说明:")
            self.logger.info(f"[分账管理]   - hd.cancelsign='N': 主表未取消")
            self.logger.info(f"[分账管理]   - dt.cancelsign='N': 明细未取消")
            self.logger.info(f"[分账管理]   - dt.IS_FZ_REQUEST='N': 未分账记录")
            self.logger.info(f"[分账管理]   - hd.status='003': 主表状态为003")
            self.logger.info(f"[分账管理]   - dt.paytype in('099','003'): 支付类型为099或003")
            self.logger.info(
                f"[分账管理]   - (dt.gs_fzmoney <> 0 OR dt.jms_fzmoney <> 0 or dt.sourcemoney <>0): 分账金额或营销转账金额不为0")
            self.logger.info(f"[分账管理]   - hd.allresult_check_sign='Y': 审核通过")

            cursor.execute(sql)
            rows = cursor.fetchall()

            self.logger.info(f"[分账管理] 📊 数据库查询结果: 共找到 {len(rows)} 条待分账记录")

            # 处理查询结果
            orders = self._process_query_results(rows)
            return orders

        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 数据库查询失败: {str(e)}")
            import traceback
            self.logger.error(f"[分账管理] 错误详情: {traceback.format_exc()}")
            # 如果数据库查询失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[分账管理] ⚠️ 数据库查询失败，测试环境返回模拟数据")
                return self._get_test_split_orders()
            return []
        finally:
            if connection:
                connection.close()
                self.logger.info(f"[分账管理] 🔒 数据库连接已关闭")

    def get_split_order_by_xpbillid(self, xpbillid):
        """根据xpbillid获取待分账的订单信息"""
        connection = self.get_database_connection()
        if not connection:
            # 如果数据库连接失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[分账管理] ⚠️ 数据库连接失败，测试环境返回模拟数据")
                return self._get_test_split_orders()
            return []

        try:
            cursor = connection.cursor()

            # 使用用户提供的完整准确SQL语句（单个查询版本）
            sql = """
            SELECT hd.billid, dt.xpbillid as order_id, dt.gs_fzmoney 公司分账金额, dt.jms_fzmoney 加盟商分账金额, 
                   hd.jms_payaccount 加盟商支付账号, hd.gs_receiveaccount 公司收款账号, hd.jms_receiveaccount 加盟商收款账号,
                   1 as PAYER_ACCOUNT_TYPE_FK, 0 as PAYEE_ACCOUNT_TYPE_SK, hd.payaccoutgsyx 公司营销子账号,
                   dt.paytype, dt.sourcemoney 营销子账号转账金额
                FROM P_BL_SELL_PAYAMOUNT_HZ_HD hd
                LEFT JOIN P_BL_SELL_PAYAMOUNT_HZ_dt dt ON hd.billid = dt.billid 
                WHERE hd.cancelsign = 'N' 
                AND dt.cancelsign = 'N'
                AND dt.IS_FZ_REQUEST = 'N'
                AND hd.status = '003'
                and dt.paytype in('099','003')
                AND (dt.gs_fzmoney <> 0 OR dt.jms_fzmoney <> 0 or dt.sourcemoney <>0 )
                AND hd.allresult_check_sign='Y'
                AND dt.xpbillid = :xpbillid
                ORDER BY hd.billid ASC, dt.xpbillid ASC
            """

            self.logger.info(f"[分账管理] 🔍 根据xpbillid执行查询SQL:")
            self.logger.info(f"[分账管理] {sql}")
            self.logger.info(f"[分账管理] 🎯 查询条件: xpbillid = {xpbillid}")
            self.logger.info(f"[分账管理] 🎯 重要：只查询IS_FZ_REQUEST='N'的未分账记录，防止重复执行")

            cursor.execute(sql, {'xpbillid': xpbillid})
            rows = cursor.fetchall()

            self.logger.info(f"[分账管理] 📊 数据库查询结果: 共找到 {len(rows)} 条待分账记录")

            if not rows:
                self.logger.warning(f"[分账管理] ⚠️ 未找到xpbillid为 {xpbillid} 的未分账记录，可能已经分账完成")
                return []

            # 处理查询结果
            orders = self._process_query_results(rows)

            return orders

        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 数据库查询失败: {str(e)}")
            import traceback
            self.logger.error(f"[分账管理] 错误详情: {traceback.format_exc()}")
            # 如果数据库查询失败，在测试环境返回模拟数据作为兜底
            if not Config.USE_PRODUCTION:
                self.logger.warning(f"[分账管理] ⚠️ 数据库查询失败，测试环境返回模拟数据")
                return self._get_test_split_orders()
            return []
        finally:
            if connection:
                connection.close()
                self.logger.info(f"[分账管理] 🔒 数据库连接已关闭")

    def _process_query_results(self, rows):
        """处理数据库查询结果，转换为订单列表"""
        orders = []
        for i, row in enumerate(rows, 1):
            # 按照SQL字段顺序正确解包所有12个字段
            billid, xpbillid, gs_amount, jms_amount, jms_payaccount, gs_receiveaccount, jms_receiveaccount, payer_type, payee_type, payaccoutgsyx, paytype, sourcemoney = row

            self.logger.info(f"[分账管理] 📋 处理第 {i} 条分账记录:")
            self.logger.info(f"[分账管理]    分账单据号: {billid}")
            self.logger.info(f"[分账管理]    明细单据号: {xpbillid}")
            self.logger.info(f"[分账管理]    支付类型: {paytype}")
            self.logger.info(f"[分账管理]    加盟商支付账号: {jms_payaccount}")
            self.logger.info(f"[分账管理]    公司营销子账号: {payaccoutgsyx}")
            self.logger.info(f"[分账管理]    营销转账金额: {sourcemoney}")
            self.logger.info(f"[分账管理]    加盟商收款账号: {jms_receiveaccount}")
            self.logger.info(f"[分账管理]    公司收款账号: {gs_receiveaccount}")
            self.logger.info(f"[分账管理]    公司分账金额: {gs_amount}")
            self.logger.info(f"[分账管理]    加盟商分账金额: {jms_amount}")

            # 处理金额，确保转换为分
            try:
                gs_amount_fen = int(float(gs_amount) * 100) if gs_amount else 0
                jms_amount_fen = int(float(jms_amount) * 100) if jms_amount else 0
                marketing_transfer_amount = int(float(sourcemoney) * 100) if sourcemoney else 0
            except (ValueError, TypeError):
                self.logger.warning(f"[分账管理] ⚠️ 金额格式错误，跳过: {billid}-{xpbillid}")
                continue

            # 🔥 关键修正：根据 sourcemoney 是否为0 来确定业务模式
            if marketing_transfer_amount > 0:
                # 营销转账模式：营销子账号 -> 供应商付款账户（jms_payaccount）
                payer_merchant_id = payaccoutgsyx  # 付款方：公司营销子账号
                payee_target_merchant_id = jms_payaccount  # 收款方：供应商付款账户（jms_payaccount）
                # 营销转账模式下不处理常规分账账号
                payee_jms_merchant_id = None
                payee_gs_merchant_id = None
                self.logger.info(f"[分账管理]    📋 营销转账模式：{payaccoutgsyx} -> {jms_payaccount}")
                self.logger.info(
                    f"[分账管理]    💰 营销转账金额: {marketing_transfer_amount}分 ({marketing_transfer_amount / 100}元)")
            else:
                # 常规分账模式：加盟商付款账号分给两个收款账号
                payer_merchant_id = jms_payaccount
                payee_jms_merchant_id = jms_receiveaccount
                payee_gs_merchant_id = gs_receiveaccount
                payee_target_merchant_id = None  # 常规分账模式不使用这个字段
                self.logger.info(f"[分账管理]    📋 常规分账模式：付款方={jms_payaccount}")

                # 常规分账模式金额验证
                if gs_amount_fen <= 0 and jms_amount_fen <= 0:
                    self.logger.warning(f"[分账管理] ⚠️ 常规分账金额为0，跳过: {billid}-{xpbillid}")
                    continue

            # 🔥 修正总金额计算 - 包含营销转账金额
            if marketing_transfer_amount > 0:
                total_amount = gs_amount_fen + jms_amount_fen + marketing_transfer_amount
                self.logger.info(f"[分账管理]    💰 总金额(含营销转账): {total_amount}分 ({total_amount / 100:.2f}元)")
                self.logger.info(f"[分账管理]      - 常规分账: {gs_amount_fen + jms_amount_fen}分")
                self.logger.info(f"[分账管理]      - 营销转账: {marketing_transfer_amount}分")
            else:
                total_amount = gs_amount_fen + jms_amount_fen
                self.logger.info(f"[分账管理]    💰 总金额(常规分账): {total_amount}分 ({total_amount / 100:.2f}元)")

            order_data = {
                'billid': billid,
                'xpbillid': xpbillid,
                'payer_merchant_id': payer_merchant_id,  # 根据sourcemoney动态确定
                'payee_jms_merchant_id': payee_jms_merchant_id,
                'payee_gs_merchant_id': payee_gs_merchant_id,
                'payee_target_merchant_id': payee_target_merchant_id,  # 营销转账时的目标账号
                'gs_amount': gs_amount_fen,
                'jms_amount': jms_amount_fen,
                'total_amount': total_amount,  # 🔥 修正后的总金额
                'marketing_transfer_amount': marketing_transfer_amount,  # 营销转账金额
                'payer_type': payer_type,
                'payee_type': payee_type,
                'paytype': paytype,  # 支付类型
                'payaccoutgsyx': payaccoutgsyx,  # 🔥 确保字段保存
                'sourcemoney': sourcemoney,  # 🔥 确保字段保存
                # 新增专业显示字段
                'business_type': '营销转账' if marketing_transfer_amount > 0 else '常规分账',
                'split_status': '待处理',
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            orders.append(order_data)

            if marketing_transfer_amount > 0:
                self.logger.info(
                    f"[分账管理]    ✅ 添加营销转账订单: 转账金额 {marketing_transfer_amount / 100:.2f}元")
            else:
                self.logger.info(
                    f"[分账管理]    ✅ 添加常规分账订单: 总金额 {(gs_amount_fen + jms_amount_fen) / 100:.2f}元")

        return orders

    def _get_test_split_orders(self):
        """获取测试环境的模拟分账订单"""
        self.logger.info(f"[分账管理] 🧪 生成测试环境模拟数据")

        # 从配置适配器获取商户号
        split_config = config_adapter.get_split_config()

        test_orders = [
            {
                'billid': f'TEST_SPLIT_{datetime.now().strftime("%Y%m%d%H%M%S")}_001',
                'xpbillid': f'TEST_XP_{datetime.now().strftime("%Y%m%d%H%M%S")}_001',
                'payer_merchant_id': split_config['PAYER_MERCHANT_ID'],
                'payee_jms_merchant_id': split_config['PAYEE_JMS_MERCHANT_ID'],
                'payee_gs_merchant_id': split_config['PAYEE_GS_MERCHANT_ID'],
                'payee_target_merchant_id': None,
                'gs_amount': split_config['DEFAULT_GS_AMOUNT'],
                'jms_amount': split_config['DEFAULT_JMS_AMOUNT'],
                'total_amount': split_config['DEFAULT_GS_AMOUNT'] + split_config['DEFAULT_JMS_AMOUNT'],
                'marketing_transfer_amount': 0,
                'payer_type': str(split_config['PAYER_ACCOUNT_TYPE']),
                'payee_type': str(split_config['PAYEE_ACCOUNT_TYPE']),
                'paytype': '099',
                'payaccoutgsyx': None,
                'sourcemoney': 0,
                'business_type': '常规分账',
                'split_status': '待处理',
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

        self.logger.info(f"[分账管理] 📈 测试数据生成完成: 共 {len(test_orders)} 笔测试订单")
        for order in test_orders:
            self.logger.info(f"[分账管理]   - 订单号: {order['billid']}")
            self.logger.info(f"[分账管理]   - 明细单据号: {order['xpbillid']}")
            self.logger.info(f"[分账管理]   - 付款方: {order['payer_merchant_id']}")
            self.logger.info(f"[分账管理]   - 加盟商收款: {order['payee_jms_merchant_id']} ({order['jms_amount']}分)")
            self.logger.info(f"[分账管理]   - 公司收款: {order['payee_gs_merchant_id']} ({order['gs_amount']}分)")

        return test_orders

    def create_split_request(self, order_data, target_merchant, split_sequence, split_type='JMS'):
        """
        创建分账申请请求
        :param order_data: 订单数据
        :param target_merchant: 目标商户信息
        :param split_sequence: 分账序号
        :param split_type: 分账类型 JMS=加盟商 GS=公司 MARKETING_TO_SUPPLIER=营销转账
        :return: request对象
        """
        self.logger.info(f"[分账管理] 🔧 创建分账申请请求:")
        self.logger.info(f"[分账管理]   原订单号: {order_data['billid']}")
        self.logger.info(f"[分账管理]   明细单据号: {order_data.get('xpbillid', 'N/A')}")
        self.logger.info(f"[分账管理]   分账类型: {split_type}")
        self.logger.info(f"[分账管理]   目标商户: {target_merchant['merchant_id']} ({target_merchant['name']})")
        self.logger.info(f"[分账管理]   分账金额: {target_merchant['amount']}分 ({target_merchant['amount'] / 100}元)")

        # 创建请求对象
        request = SplitAccountRequest()
        # 创建业务参数模型
        model = SplitAccountModel()

        # ===== 基本参数设置 =====
        # 使用配置适配器获取机构号
        model.node_id = str(config_adapter.get_node_id())  # 机构号
        # 生成唯一的平台流水号
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        model.platform_no = str(f"SPLIT_{split_type}_{timestamp}_{split_sequence:03d}_{str(uuid.uuid4())[:4].upper()}")

        self.logger.info(f"[分账管理]   机构号: {model.node_id}")
        self.logger.info(f"[分账管理]   平台流水号: {model.platform_no}")

        # ===== 分账金额 =====
        model.total_amount = int(target_merchant['amount'])  # 分账金额(分)

        # ===== 付款方信息 =====
        model.payer_merchant_id = str(order_data['payer_merchant_id'])  # 付款方商户号
        # 使用订单数据中的账户类型或配置适配器获取账户类型
        model.payer_type = str(
            order_data.get('payer_type', config_adapter.get_split_config()['PAYER_ACCOUNT_TYPE']))  # 付款方账户类型

        # ===== 收款方信息（目标商户）=====
        model.payee_merchant_id = str(target_merchant['merchant_id'])  # 收款方商户号
        # 使用订单数据中的账户类型或配置适配器获取账户类型
        model.payee_type = str(
            order_data.get('payee_type', config_adapter.get_split_config()['PAYEE_ACCOUNT_TYPE']))  # 收款方账户类型

        # ===== 其他信息 =====
        model.arrive_time = str("T0")  # 到账时间：T0当天到账
        model.remark = str(
            f"MUMUSO分账申请-{order_data['billid']}-{order_data.get('xpbillid', '')}-{target_merchant['name']}-{split_type}")

        # 验证参数
        valid, errors = model.validate()
        if not valid:
            self.logger.error(f"[分账管理] ❌ 参数验证失败:")
            for error in errors:
                self.logger.error(f"[分账管理]   - {error}")
            raise ValueError(f"参数验证失败: {errors}")

        # 设置请求的业务模型
        request.biz_model = model
        self.logger.info(f"[分账管理] ✅ 分账申请请求对象创建完成")
        return request

    def execute_split_request(self, request, order_data, target_merchant, split_type):
        """
        执行分账申请请求 - 使用OpenClient
        :param request: 分账申请请求对象
        :param order_data: 订单数据
        :param target_merchant: 目标商户
        :param split_type: 分账类型
        :return: 响应结果
        """
        try:
            model = request.biz_model

            self.logger.info(f"[分账管理] 📡 使用OpenClient发送分账申请请求:")
            self.logger.info(f"[分账管理]   接口地址: {Config.get_url()}")
            self.logger.info(f"[分账管理]   接口方法: {request.get_method()}")
            self.logger.info(f"[分账管理]   请求类型: {request.get_request_type()}")
            self.logger.info(f"[分账管理]   请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 验证业务参数
            if hasattr(request.biz_model, 'validate'):
                valid, errors = request.biz_model.validate()
                if not valid:
                    self.logger.error(f"[分账管理] ❌ 业务参数验证失败: {errors}")
                    return None

            # 打印业务参数
            self.logger.info(f"[分账管理] 🔧 业务参数:")
            biz_dict = model.to_dict()
            for key, value in biz_dict.items():
                if value is not None:
                    self.logger.info(f"[分账管理]   {key}: {value}")

            # 使用OpenClient执行请求（会自动生成签名）
            self.logger.info(f"[分账管理] 🔐 执行OpenClient请求（包含RSA2签名）...")
            response = self.client.execute(request)

            self.logger.info(f"[分账管理] 📋 分账申请响应:")
            if response:
                self.logger.info(f"[分账管理] {json.dumps(response, indent=2, ensure_ascii=False)}")
            else:
                self.logger.error(f"[分账管理] ❌ 响应为空")

            return response

        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 分账申请请求异常: {str(e)}")
            import traceback
            self.logger.error(f"[分账管理] 错误详情: {traceback.format_exc()}")
            return None

    def split_single_order(self, order_data):
        """对单个订单进行分账申请"""
        self.logger.info(f"[分账管理] " + "=" * 60)
        self.logger.info(f"[分账管理] 💰 开始订单分账申请: {order_data['billid']}")
        self.logger.info(f"[分账管理] 📄 明细单据号: {order_data.get('xpbillid', 'N/A')}")
        self.logger.info(f"[分账管理] " + "=" * 60)

        results = []
        split_sequence = 1

        # 🔥 准备分账目标列表 - 根据sourcemoney确定分账策略（修正后的关键逻辑）
        split_targets = []

        if order_data.get('marketing_transfer_amount', 0) > 0:
            # 营销转账模式：营销子账号 -> 供应商付款账户（jms_payaccount）
            marketing_transfer_amount = order_data.get('marketing_transfer_amount', 0)
            split_targets.append({
                'merchant_id': order_data['payee_target_merchant_id'],  # jms_payaccount
                'name': '供应商付款账户',
                'amount': marketing_transfer_amount,
                'type': 'MARKETING_TO_SUPPLIER'
            })
            self.logger.info(
                f"[分账管理] 📊 营销转账模式：{marketing_transfer_amount}分 -> 供应商付款账户({order_data['payee_target_merchant_id']})")
            self.logger.info(f"[分账管理] 💰 付款方：营销子账号({order_data.get('payaccoutgsyx', 'N/A')})")
        else:
            # 常规分账模式：加盟商付款账号 -> 两个收款账号
            # 加盟商分账
            if order_data.get('jms_amount', 0) > 0:
                split_targets.append({
                    'merchant_id': order_data['payee_jms_merchant_id'],
                    'name': '加盟商收款账号',
                    'amount': order_data['jms_amount'],
                    'type': 'JMS'
                })

            # 公司分账
            if order_data.get('gs_amount', 0) > 0:
                split_targets.append({
                    'merchant_id': order_data['payee_gs_merchant_id'],
                    'name': '公司收款账号',
                    'amount': order_data['gs_amount'],
                    'type': 'GS'
                })

        self.logger.info(f"[分账管理] 📊 分账计划:")
        self.logger.info(f"[分账管理]   付款方: {order_data['payer_merchant_id']}")
        self.logger.info(f"[分账管理]   分账目标数: {len(split_targets)}")
        for target in split_targets:
            self.logger.info(f"[分账管理]   - {target['type']}: {target['merchant_id']} ({target['amount']}分)")

        # 执行分账
        for target in split_targets:
            try:
                self.logger.info(f"[分账管理] 📄 执行{target['type']}分账...")

                # 创建分账请求
                request = self.create_split_request(
                    order_data, target, split_sequence, target['type']
                )

                # 执行分账请求
                response = self.execute_split_request(
                    request, order_data, target, target['type']
                )

                # 处理响应
                success, msg = self._handle_split_response(response)

                result = {
                    'target_type': target['type'],
                    'target_merchant': target['merchant_id'],
                    'amount': target['amount'],
                    'success': success,
                    'message': msg,
                    'response': response,
                    'billid': order_data['billid'],
                    'xpbillid': order_data.get('xpbillid', ''),
                    'request_id': None,
                    'trade_no': None,
                    'execute_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                # 提取API返回的关键信息
                if success and response:
                    split_response = response
                    if 'bkfunds_balance_pay_apply_response' in response:
                        split_response = response['bkfunds_balance_pay_apply_response']

                    result['request_id'] = split_response.get('request_id')
                    data = split_response.get('data', {})
                    result['trade_no'] = data.get('trade_no')

                results.append(result)

                if success:
                    self.logger.info(f"[分账管理] ✅ {target['type']}分账成功: {target['amount']}分")
                else:
                    self.logger.error(f"[分账管理] ❌ {target['type']}分账失败: {msg}")

                split_sequence += 1

                # 间隔一下避免请求过快
                time.sleep(1)

            except Exception as e:
                error_msg = f"分账异常: {str(e)}"
                self.logger.error(f"[分账管理] ❌ {target['type']}分账异常: {error_msg}")

                result = {
                    'target_type': target['type'],
                    'target_merchant': target['merchant_id'],
                    'amount': target['amount'],
                    'success': False,
                    'message': error_msg,
                    'response': None,
                    'billid': order_data['billid'],
                    'xpbillid': order_data.get('xpbillid', ''),
                    'request_id': None,
                    'trade_no': None,
                    'execute_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                results.append(result)

        # 汇总结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)

        self.logger.info(f"[分账管理] 📈 订单分账完成: {order_data['billid']}")
        self.logger.info(f"[分账管理] 📄 明细单据号: {order_data.get('xpbillid', 'N/A')}")
        self.logger.info(f"[分账管理] ✅ 成功: {success_count}/{total_count}")
        self.logger.info(f"[分账管理] ❌ 失败: {total_count - success_count}/{total_count}")

        # 更新分账状态（根据billid和xpbillid）
        all_success = all(r['success'] for r in results)

        # 获取所有成功的分账结果的request_id和trade_no
        request_ids = []
        trade_nos = []
        for result in results:
            if result['success'] and result.get('request_id'):
                request_ids.append(result['request_id'])
            if result['success'] and result.get('trade_no'):
                trade_nos.append(result['trade_no'])

        # 使用第一个成功的分账结果的request_id和trade_no进行回写
        request_id = request_ids[0] if request_ids else None
        trade_no = trade_nos[0] if trade_nos else None

        self.logger.info(f"[分账管理] 📄 准备回写数据: request_id={request_id}, trade_no={trade_no}")
        self.logger.info(f"[分账管理] 📄 所有request_ids: {request_ids}")
        self.logger.info(f"[分账管理] 📄 所有trade_nos: {trade_nos}")

        update_success = self.update_split_status_by_xpbillid(
            order_data['billid'],
            order_data.get('xpbillid', ''),
            all_success,
            request_id,
            trade_no
        )

        if update_success:
            self.logger.info(f"[分账管理] ✅ 分账状态回写成功")
        else:
            self.logger.error(f"[分账管理] ❌ 分账状态回写失败")

        return results

    def split_single_order_by_xpbillid(self, xpbillid):
        """根据xpbillid对单个订单进行分账申请"""
        self.logger.info(f"[分账管理] " + "=" * 60)
        self.logger.info(f"[分账管理] 💰 开始根据xpbillid进行订单分账申请: {xpbillid}")
        self.logger.info(f"[分账管理] " + "=" * 60)

        # 根据xpbillid获取订单信息
        orders = self.get_split_order_by_xpbillid(xpbillid)

        if not orders:
            self.logger.warning(f"[分账管理] ⚠️ 未找到xpbillid为 {xpbillid} 的待分账订单")
            return []

        all_results = []
        for order in orders:
            results = self.split_single_order(order)
            all_results.extend(results)

        return all_results

    def batch_split_orders(self):
        """批量处理分账申请"""
        self.logger.info(f"[分账管理] 🚀 开始批量分账申请处理")
        self.logger.info(f"[分账管理] 🌍 当前环境: {Config.get_env_name()}")

        # 获取待分账订单
        orders = self.get_split_orders_from_database()

        if not orders:
            self.logger.warning(f"[分账管理] ⚠️ 没有找到待分账的订单")
            return []

        self.logger.info(f"[分账管理] 📊 开始处理 {len(orders)} 笔待分账订单")

        all_results = []
        for i, order in enumerate(orders, 1):
            self.logger.info(
                f"[分账管理] 📋 处理第 {i}/{len(orders)} 笔订单: {order['billid']}-{order.get('xpbillid', 'N/A')}")

            try:
                # 执行分账
                results = self.split_single_order(order)
                all_results.extend(results)

                # 间隔一下
                if i < len(orders):
                    self.logger.info(f"[分账管理] ⏱️ 等待2秒后处理下一笔订单...")
                    time.sleep(2)

            except Exception as e:
                self.logger.error(
                    f"[分账管理] ❌ 订单处理异常: {order['billid']}-{order.get('xpbillid', 'N/A')}, 错误: {str(e)}")

        # 汇总统计
        total_splits = len(all_results)
        success_splits = sum(1 for r in all_results if r['success'])

        self.logger.info(f"[分账管理] " + "=" * 60)
        self.logger.info(f"[分账管理] 📊 批量分账申请完成")
        self.logger.info(f"[分账管理] " + "=" * 60)
        self.logger.info(f"[分账管理] 📈 处理订单数: {len(orders)}")
        self.logger.info(f"[分账管理] 🎯 分账申请总数: {total_splits}")
        self.logger.info(f"[分账管理] ✅ 分账成功: {success_splits}")
        self.logger.info(f"[分账管理] ❌ 分账失败: {total_splits - success_splits}")
        self.logger.info(
            f"[分账管理] 📊 成功率: {(success_splits / total_splits * 100):.1f}%" if total_splits > 0 else "无分账申请")

        return all_results

    def _handle_split_response(self, response):
        """处理分账申请响应结果"""
        self.logger.info(f"[分账管理] 📊 响应解析:")

        if not response:
            self.logger.error(f"[分账管理] ❌ 响应为空")
            return False, "响应为空"

        # 根据API文档，响应的根键名可能是 bkfunds_balance_pay_apply_response
        split_response = response
        if 'bkfunds_balance_pay_apply_response' in response:
            split_response = response['bkfunds_balance_pay_apply_response']

        success = split_response.get('success', False)
        code = split_response.get('code', 'N/A')
        msg = split_response.get('msg', 'N/A')
        request_id = split_response.get('request_id', 'N/A')
        sub_code = split_response.get('sub_code', '')
        sub_msg = split_response.get('sub_msg', '')

        self.logger.info(f"[分账管理]   成功标识: {success}")
        self.logger.info(f"[分账管理]   响应码: {code}")
        self.logger.info(f"[分账管理]   响应消息: {msg}")
        self.logger.info(f"[分账管理]   请求ID: {request_id}")
        if sub_code:
            self.logger.info(f"[分账管理]   子错误码: {sub_code}")
        if sub_msg:
            self.logger.info(f"[分账管理]   子错误信息: {sub_msg}")

        if success:
            return True, msg
        else:
            error_msg = f"错误码: {code}, 消息: {msg}"
            if sub_msg:
                error_msg += f", 详细: {sub_msg}"
            return False, error_msg

    def update_split_status(self, billid, success=True):
        """更新分账申请状态到数据库"""
        # 不再根据环境跳过状态更新，但在测试环境添加日志说明
        if not Config.USE_PRODUCTION:
            self.logger.info(f"[分账管理] 🧪 测试环境执行状态更新（实际环境中会真正更新数据库）")

        connection = self.get_database_connection()
        if not connection:
            self.logger.error(f"[分账管理] ❌ 无法获取数据库连接，无法更新分账申请状态")
            return False

        try:
            cursor = connection.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            status_value = 'Y' if success else 'F'
            sql = """
            UPDATE P_BL_SELL_PAYAMOUNT_HZ_HD 
            SET IS_SPLIT_APPLIED = :status,
                SPLIT_APPLIED_TIME = TO_DATE(:apply_time, 'YYYY-MM-DD HH24:MI:SS')
            WHERE billid = :billid
            """

            self.logger.info(f"[分账管理] 📄 更新分账申请状态: {billid} -> {status_value}")

            cursor.execute(sql, {
                'status': status_value,
                'apply_time': current_time,
                'billid': billid
            })

            connection.commit()
            affected_rows = cursor.rowcount

            if affected_rows > 0:
                self.logger.info(f"[分账管理] ✅ 分账申请状态更新成功，影响行数: {affected_rows}")
            else:
                self.logger.warning(f"[分账管理] ⚠️ 分账申请状态更新无影响行数: {billid}")

            cursor.close()
            return affected_rows > 0

        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 分账申请状态更新失败: {str(e)}")
            try:
                connection.rollback()
            except:
                pass
            return False
        finally:
            if connection:
                connection.close()

    def update_split_status_by_xpbillid(self, billid, xpbillid, success=True, request_id=None, trade_no=None):
        """根据billid和xpbillid更新分账申请状态到数据库"""
        # 不再根据环境跳过状态更新，但在测试环境添加日志说明
        if not Config.USE_PRODUCTION:
            self.logger.info(f"[分账管理] 🧪 测试环境执行状态更新（实际环境中会真正更新数据库）")

        connection = self.get_database_connection()
        if not connection:
            self.logger.error(f"[分账管理] ❌ 无法获取数据库连接，无法更新分账申请状态")
            return False

        try:
            cursor = connection.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            status_value = 'Y' if success else 'F'

            # 修复：确保参数不为None，避免Oracle报错
            safe_request_id = str(request_id) if request_id and request_id.strip() else ''
            safe_trade_no = str(trade_no) if trade_no and trade_no.strip() else ''

            # 直接在一条SQL语句中完成所有字段的更新，包括FZ_SPLIT_RECORD和FZ_REQUESTBACK_NO
            sql = """
            UPDATE P_BL_SELL_PAYAMOUNT_HZ_dt 
            SET IS_FZ_REQUEST = :is_fz_request,
                FZ_REQUEST_TIME = TO_DATE(:fz_request_time, 'YYYY-MM-DD HH24:MI:SS'),
                IS_FZ_EXECUTE = :is_fz_execute,
                FZ_EXECUTE_OPERATIONTIME = TO_DATE(:fz_execute_time, 'YYYY-MM-DD HH24:MI:SS'),
                FZ_SPLIT_RECORD = :request_id,
                FZ_REQUESTBACK_NO = :trade_no
            WHERE billid = :billid 
              AND xpbillid = :xpbillid
              AND (IS_FZ_REQUEST IS NULL OR IS_FZ_REQUEST = 'N')
            """

            params = {
                'billid': billid,
                'xpbillid': xpbillid,
                'is_fz_request': status_value,
                'fz_request_time': current_time,
                'is_fz_execute': status_value,
                'fz_execute_time': current_time,
                'request_id': safe_request_id,
                'trade_no': safe_trade_no
            }

            self.logger.info(f"[分账管理] 📄 更新明细表分账状态: {billid}-{xpbillid} -> {status_value}")
            self.logger.info(f"[分账管理] 📄 回写参数: request_id={safe_request_id}, trade_no={safe_trade_no}")

            cursor.execute(sql, params)
            connection.commit()
            affected_rows_dt = cursor.rowcount

            if affected_rows_dt > 0:
                self.logger.info(f"[分账管理] ✅ 明细表分账申请状态更新成功，影响行数: {affected_rows_dt}")

                # 验证回写结果
                verify_sql = """
                SELECT IS_FZ_REQUEST, FZ_SPLIT_RECORD, FZ_REQUESTBACK_NO 
                FROM P_BL_SELL_PAYAMOUNT_HZ_dt 
                WHERE billid = :billid AND xpbillid = :xpbillid
                """
                cursor.execute(verify_sql, {'billid': billid, 'xpbillid': xpbillid})
                verify_result = cursor.fetchone()
                if verify_result:
                    is_fz_request, fz_split_record, fz_requestback_no = verify_result
                    self.logger.info(
                        f"[分账管理] 📄 验证回写结果: IS_FZ_REQUEST={is_fz_request}, FZ_SPLIT_RECORD={fz_split_record}, FZ_REQUESTBACK_NO={fz_requestback_no}")

                    if fz_split_record == safe_request_id and fz_requestback_no == safe_trade_no:
                        self.logger.info(f"[分账管理] ✅ FZ_SPLIT_RECORD和FZ_REQUESTBACK_NO回写成功验证通过")
                    else:
                        self.logger.warning(
                            f"[分账管理] ⚠️ 回写验证不一致，期望: request_id={safe_request_id}, trade_no={safe_trade_no}")

            else:
                self.logger.warning(f"[分账管理] ⚠️ 明细表分账申请状态更新无影响行数: {billid}-{xpbillid}")
                # 检查记录是否已经被处理
                check_sql = """
                SELECT IS_FZ_REQUEST, FZ_SPLIT_RECORD, FZ_REQUESTBACK_NO 
                FROM P_BL_SELL_PAYAMOUNT_HZ_dt 
                WHERE billid = :billid AND xpbillid = :xpbillid
                """
                cursor.execute(check_sql, {'billid': billid, 'xpbillid': xpbillid})
                check_result = cursor.fetchone()
                if check_result:
                    is_fz_request, fz_split_record, fz_requestback_no = check_result
                    self.logger.info(
                        f"[分账管理] 📄 检查现有记录状态: IS_FZ_REQUEST={is_fz_request}, FZ_SPLIT_RECORD={fz_split_record}, FZ_REQUESTBACK_NO={fz_requestback_no}")
                    if is_fz_request == 'Y':
                        self.logger.warning(f"[分账管理] ⚠️ 记录已经被处理过，IS_FZ_REQUEST=Y")

            cursor.close()
            return affected_rows_dt > 0

        except Exception as e:
            self.logger.error(f"[分账管理] ❌ 分账申请状态更新失败: {str(e)}")
            import traceback
            self.logger.error(f"[分账管理] 错误详情: {traceback.format_exc()}")
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
    print("💰 MUMUSO分账申请系统 - 完整版")
    print("=" * 80)
    print("🔧 集成内容:")
    print("   1. SplitAccountModel - 业务参数模型")
    print("   2. SplitAccountRequest - 请求类")
    print("   3. SplitAccountDemo - 演示类")
    print("   4. 支持测试/正式环境")
    print("=" * 80)

    # 检查配置
    ready, msg = Config.is_config_ready()
    if not ready:
        print(f"⚠️ 配置检查失败: {msg}")
        return False

    # 创建分账申请实例
    split_demo = SplitAccountDemo()

    print("\n🚀 开始自动执行分账申请演示...")

    # 执行批量分账
    results = split_demo.batch_split_orders()

    print(f"\n🎉 分账申请演示完成!")
    return True


if __name__ == '__main__':
    print("=" * 80)
    print("💰 MUMUSO分账申请系统")
    print("=" * 80)

    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n👋 程序退出")
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")