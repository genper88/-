#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
订单上传模块 - 支持动态商户号和门店ID版本
文件名: order_upload_demo.py (完整版)
支持从数据库动态获取商户号和门店ID，适配生产环境需求
"""

import json
import time
import uuid
import logging
from datetime import datetime
import cx_Oracle

from common.OpenClient import OpenClient
from model.OrderUploadModel import OrderUploadModel
from request.OrderUploadRequest import OrderUploadRequest
from config import Config
from config_adapter import config_adapter


class OrderUploadDemo:
    """订单上传演示类 - 支持动态商户号和门店ID版本"""

    def __init__(self, logger=None):
        self.config = Config
        self.client = OpenClient(Config.APP_ID, Config.PRIVATE_KEY, Config.get_url())

        # 设置日志器
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('OrderUpload')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

        # 记录配置策略
        merchant_strategy = "动态获取" if Config.should_use_dynamic_merchant_id() else "配置文件固定"
        store_strategy = "动态获取" if Config.should_use_dynamic_store_id() else "配置文件固定"

        self.logger.info(f"[订单上传] 💼 商户号策略: {merchant_strategy} (备用: {Config.get_fallback_merchant_id()})")
        self.logger.info(f"[订单上传] 🏪 门店ID策略: {store_strategy} (备用: {Config.get_fallback_store_id()})")

    def get_database_connection(self):
        """获取数据库连接"""
        try:
            user, password, dsn = Config.get_db_connection_info()
            self.logger.info(f"[订单上传] 正在连接数据库: {dsn}")
            connection = cx_Oracle.connect(user, password, dsn)
            self.logger.info(f"[订单上传] ✅ 数据库连接成功: {dsn}")
            return connection
        except Exception as e:
            self.logger.error(f"[订单上传] ❌ 数据库连接失败: {str(e)}")
            return None

    def get_orders_from_database(self):
        """从数据库获取待上传的订单（支持动态商户号和门店ID）"""
        connection = self.get_database_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor()

            # 修正后的SQL - 包含商户号和门店ID字段，按时间升序排列
            sql = """
            SELECT hd.billid, dt.xpbillid as order_id, dt.wxmoney, dt.zfbmoney, 
            dt.paytime as order_time, hd.ymshanghuhao as merchant_id, hd.storeid as store_id                   
            FROM P_BL_SELL_PAYAMOUNT_HZ_HD hd
            LEFT JOIN P_BL_SELL_PAYAMOUNT_HZ_dt dt ON hd.billid = dt.billid 
            WHERE hd.cancelsign = 'N' 
            AND dt.cancelsign = 'N'
            AND hd.status = '002'
            and dt.paytype  in('001','002')
            and dt.xpbillid not like '%from%'
            AND (dt.WXMONEY <> 0 OR dt.zfbmoney <> 0 )
            AND NVL(dt.ISUPLOAD_FZ, 'N') = 'N'
            ORDER BY dt.paytime ASC
            """

            self.logger.info(f"[订单上传] 🔍 执行查询SQL (包含动态商户号和门店ID):")
            self.logger.info(f"[订单上传] {sql}")

            cursor.execute(sql)
            rows = cursor.fetchall()

            self.logger.info(f"[订单上传] 📊 数据库查询结果: 共找到 {len(rows)} 条记录")

            orders = []
            for i, row in enumerate(rows, 1):
                billid, order_id, wxmoney, zfbmoney, paytime, db_merchant_id, db_store_id = row

                self.logger.info(f"[订单上传] 📋 处理第 {i} 条记录:")
                self.logger.info(f"[订单上传]    billid: {billid}")
                self.logger.info(f"[订单上传]    order_id: {order_id}")
                self.logger.info(f"[订单上传]    wxmoney: {wxmoney}")
                self.logger.info(f"[订单上传]    zfbmoney: {zfbmoney}")
                self.logger.info(f"[订单上传]    paytime: {paytime}")
                self.logger.info(f"[订单上传]    db_merchant_id: {db_merchant_id}")
                self.logger.info(f"[订单上传]    db_store_id: {db_store_id}")

                # 处理订单时间 - 兼容字符串和日期对象
                order_time_str = ''
                if paytime:
                    if isinstance(paytime, str):
                        order_time_str = paytime
                        self.logger.info(f"[订单上传]    时间格式: 字符串 -> {order_time_str}")
                    elif hasattr(paytime, 'strftime'):
                        order_time_str = paytime.strftime("%Y%m%d%H%M%S")
                        self.logger.info(f"[订单上传]    时间格式: 日期对象 -> {order_time_str}")
                    else:
                        order_time_str = str(paytime)
                        self.logger.info(f"[订单上传]    时间格式: 其他类型 -> {order_time_str}")

                # 处理动态商户号和门店ID
                final_merchant_id = self._process_merchant_id(db_merchant_id, billid)
                final_store_id = self._process_store_id(db_store_id, billid)

                # 根据微信和支付宝金额分别处理
                if wxmoney and float(wxmoney) > 0:
                    order_data = {
                        'billid': billid,
                        'order_id': order_id,
                        'order_amount': int(float(wxmoney) * 100),  # 转换为分
                        'pay_type': '503',  # 微信支付
                        'pay_money': float(wxmoney),
                        'order_time': order_time_str,
                        'payment_method': '微信支付',
                        'merchant_id': final_merchant_id,  # 动态商户号
                        'store_id': final_store_id  # 动态门店ID
                    }
                    orders.append(order_data)
                    self.logger.info(
                        f"[订单上传]    ✅ 添加微信支付订单: {wxmoney}元 (商户: {final_merchant_id}, 门店: {final_store_id})")

                if zfbmoney and float(zfbmoney) > 0:
                    order_data = {
                        'billid': billid,
                        'order_id': order_id,
                        'order_amount': int(float(zfbmoney) * 100),  # 转换为分
                        'pay_type': '502',  # 支付宝
                        'pay_money': float(zfbmoney),
                        'order_time': order_time_str,
                        'payment_method': '支付宝',
                        'merchant_id': final_merchant_id,  # 动态商户号
                        'store_id': final_store_id  # 动态门店ID
                    }
                    orders.append(order_data)
                    self.logger.info(
                        f"[订单上传]    ✅ 添加支付宝订单: {zfbmoney}元 (商户: {final_merchant_id}, 门店: {final_store_id})")

            cursor.close()
            self.logger.info(f"[订单上传] 📈 订单处理完成: 共生成 {len(orders)} 笔待上传订单")
            return orders

        except Exception as e:
            self.logger.error(f"[订单上传] ❌ 数据库查询失败: {str(e)}")
            import traceback
            self.logger.error(f"[订单上传] 错误详情: {traceback.format_exc()}")
            return []
        finally:
            if connection:
                connection.close()
                self.logger.info(f"[订单上传] 🔒 数据库连接已关闭")

    def _process_merchant_id(self, db_merchant_id, billid):
        """
        处理商户号：根据配置决定使用动态获取还是固定配置
        :param db_merchant_id: 数据库中的商户号
        :param billid: 业务单号（用于日志）
        :return: 最终使用的商户号
        """
        if not Config.should_use_dynamic_merchant_id():
            # 使用配置文件中的固定商户号
            final_merchant_id = Config.get_fallback_merchant_id()
            self.logger.info(f"[订单上传] 💼 使用固定商户号: {final_merchant_id} (billid: {billid})")
            return final_merchant_id

        # 使用动态商户号
        if db_merchant_id and str(db_merchant_id).strip():
            final_merchant_id = str(db_merchant_id).strip()
            self.logger.info(f"[订单上传] 💼 使用动态商户号: {final_merchant_id} (billid: {billid})")
            return final_merchant_id
        else:
            # 动态获取失败，使用备用商户号
            fallback_merchant_id = Config.get_fallback_merchant_id()
            self.logger.warning(
                f"[订单上传] ⚠️ 动态商户号为空，使用备用商户号: {fallback_merchant_id} (billid: {billid})")
            return fallback_merchant_id

    def _process_store_id(self, db_store_id, billid):
        """
        处理门店ID：根据配置决定使用动态获取还是固定配置
        :param db_store_id: 数据库中的门店ID
        :param billid: 业务单号（用于日志）
        :return: 最终使用的门店ID
        """
        if not Config.should_use_dynamic_store_id():
            # 使用配置文件中的固定门店ID
            final_store_id = Config.get_fallback_store_id()
            self.logger.info(f"[订单上传] 🏪 使用固定门店ID: {final_store_id} (billid: {billid})")
            return final_store_id

        # 使用动态门店ID
        if db_store_id and str(db_store_id).strip():
            final_store_id = str(db_store_id).strip()
            self.logger.info(f"[订单上传] 🏪 使用动态门店ID: {final_store_id} (billid: {billid})")
            return final_store_id
        else:
            # 动态获取失败，使用备用门店ID
            fallback_store_id = Config.get_fallback_store_id()
            self.logger.warning(
                f"[订单上传] ⚠️ 动态门店ID为空，使用备用门店ID: {fallback_store_id} (billid: {billid})")
            return fallback_store_id

    def update_order_upload_status(self, billid, order_id, request_no, success=True):
        """
        更新订单上传状态到数据库
        :param billid: 业务单号
        :param order_id: 订单号
        :param request_no: 接口返回的请求号
        :param success: 是否成功
        :return: 是否更新成功
        """
        connection = self.get_database_connection()
        if not connection:
            self.logger.error(f"[订单上传] ❌ 无法获取数据库连接，无法更新订单状态")
            return False

        try:
            cursor = connection.cursor()

            if success:
                # 上传成功，更新3个字段
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                sql = """
                UPDATE P_BL_SELL_PAYAMOUNT_HZ_dt 
                SET ISUPLOAD_FZ = 'Y',
                    FZ_UPLOAD_TIME = TO_DATE(:upload_time, 'YYYY-MM-DD HH24:MI:SS'),
                    FZ_BACKREQUST_NO = :request_no
                WHERE billid = :billid 
                AND xpbillid = :order_id
                """

                self.logger.info(f"[订单上传] 🔄 更新订单上传状态 - 成功:")
                self.logger.info(f"[订单上传]    SQL: {sql}")
                self.logger.info(f"[订单上传]    参数: billid={billid}, order_id={order_id}")
                self.logger.info(f"[订单上传]    参数: upload_time={current_time}, request_no={request_no}")

                cursor.execute(sql, {
                    'upload_time': current_time,
                    'request_no': request_no,
                    'billid': billid,
                    'order_id': order_id
                })

            else:
                # 上传失败，只记录失败时间（可选）
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                sql = """
                UPDATE P_BL_SELL_PAYAMOUNT_HZ_dt 
                SET ISUPLOAD_FZ = 'F',
                    FZ_UPLOAD_TIME = TO_DATE(:upload_time, 'YYYY-MM-DD HH24:MI:SS'),
                    FZ_BACKREQUST_NO = :request_no
                WHERE billid = :billid 
                AND xpbillid = :order_id
                """

                self.logger.info(f"[订单上传] 🔄 更新订单上传状态 - 失败:")
                self.logger.info(f"[订单上传]    SQL: {sql}")
                self.logger.info(f"[订单上传]    参数: billid={billid}, order_id={order_id}")
                self.logger.info(f"[订单上传]    参数: upload_time={current_time}, request_no={request_no}")

                cursor.execute(sql, {
                    'upload_time': current_time,
                    'request_no': request_no,
                    'billid': billid,
                    'order_id': order_id
                })

            # 提交事务
            connection.commit()

            affected_rows = cursor.rowcount
            self.logger.info(f"[订单上传] ✅ 数据库更新成功，影响行数: {affected_rows}")

            cursor.close()
            return affected_rows > 0

        except Exception as e:
            self.logger.error(f"[订单上传] ❌ 数据库更新失败: {str(e)}")
            import traceback
            self.logger.error(f"[订单上传] 错误详情: {traceback.format_exc()}")

            # 回滚事务
            try:
                connection.rollback()
                self.logger.info(f"[订单上传] 🔄 事务已回滚")
            except:
                pass
            return False
        finally:
            if connection:
                connection.close()

    def create_order_request(self, order_data):
        """
        根据数据库订单数据创建上传请求（支持动态商户号和门店ID）
        :param order_data: 数据库查询出的订单数据（包含动态商户号和门店ID）
        :return: request对象
        """
        self.logger.info(f"[订单上传] 🔧 创建订单请求对象:")
        self.logger.info(f"[订单上传]    订单号: {order_data['order_id']}")
        self.logger.info(f"[订单上传]    支付方式: {order_data['payment_method']}")
        self.logger.info(f"[订单上传]    动态商户号: {order_data['merchant_id']}")
        self.logger.info(f"[订单上传]    动态门店ID: {order_data['store_id']}")

        # 创建请求对象
        request = OrderUploadRequest()

        # 创建业务参数模型
        model = OrderUploadModel()

        # ===== 基本参数设置 =====
        model.trade_type = "1"  # 交易类型：1-支付，2-退款
        model.node_id = Config.NODE_ID  # 机构号
        model.merchant_id = order_data['merchant_id']  # 使用动态获取的商户号
        model.store_id = order_data['store_id']  # 使用动态获取的门店ID

        self.logger.info(f"[订单上传]    机构号: {model.node_id}")
        self.logger.info(f"[订单上传]    商户号: {model.merchant_id} (动态获取)")
        self.logger.info(f"[订单上传]    门店ID: {model.store_id} (动态获取)")

        # ===== 用户指定的参数 =====
        model.order_upload_mode = config_adapter.get_order_upload_mode_normal()  # 普通订单上传模式
        model.account_type = config_adapter.get_account_type_normal()  # 普通订单账户类型

        self.logger.info(f"[订单上传]    上传模式: {model.order_upload_mode} (普通订单)")
        self.logger.info(f"[订单上传]    账户类型: {model.account_type}")

        # ===== 订单信息（从数据库获取）=====
        model.order_id = order_data['order_id']
        model.order_time = order_data['order_time']
        model.order_amount = order_data['order_amount']  # 已经转换为分

        self.logger.info(f"[订单上传]    订单金额: {model.order_amount}分 ({model.order_amount / 100}元)")
        self.logger.info(f"[订单上传]    订单时间: {model.order_time}")

        # ===== 支付相关信息（根据数据库字段动态设置）=====
        model.pay_type = order_data['pay_type']  # 503-微信，502-支付宝
        model.pay_merchant_id = Config.PAY_MERCHANT_ID  # 第三方支付渠道商户号

        self.logger.info(f"[订单上传]    支付类型: {model.pay_type}")
        self.logger.info(f"[订单上传]    支付商户号: {model.pay_merchant_id}")

        # 生成支付平台订单号
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if order_data['pay_type'] == '503':  # 微信
            model.trade_no = f"WX{timestamp}{str(uuid.uuid4())[:6].upper()}"
        else:  # 支付宝
            model.trade_no = f"ALI{timestamp}{str(uuid.uuid4())[:6].upper()}"

        self.logger.info(f"[订单上传]    支付平台订单号: {model.trade_no}")

        # ===== 其他信息 =====
        model.user_id = Config.DEFAULT_USER_ID  # 操作员ID
        model.fee_amount = Config.DEFAULT_FEE_AMOUNT  # 交易手续费
        model.split_rule_source = Config.SPLIT_RULE_SOURCE  # 分账规则来源：1-接口
        model.remark = f"MUMUSO门店订单 - {order_data['payment_method']} - billid:{order_data['billid']} - 商户:{order_data['merchant_id']} - 门店:{order_data['store_id']}"

        self.logger.info(f"[订单上传]    操作员ID: {model.user_id}")
        self.logger.info(f"[订单上传]    手续费: {model.fee_amount}")
        self.logger.info(f"[订单上传]    分账规则来源: {model.split_rule_source}")
        self.logger.info(f"[订单上传]    备注: {model.remark}")

        # 设置请求的业务模型
        request.biz_model = model

        self.logger.info(f"[订单上传] ✅ 订单请求对象创建完成")
        return request

    def upload_single_order(self, order_data):
        """
        上传单个订单
        :param order_data: 订单数据
        :return: 是否成功
        """
        order_id = order_data['order_id']
        merchant_id = order_data['merchant_id']
        store_id = order_data['store_id']
        self.logger.info(f"[订单上传] {'=' * 80}")
        self.logger.info(f"[订单上传] 🚀 开始上传订单: {order_id} (商户: {merchant_id}, 门店: {store_id})")
        self.logger.info(f"[订单上传] {'=' * 80}")

        try:
            # 创建订单请求
            request = self.create_order_request(order_data)
            model = request.biz_model

            # 打印订单信息
            self._print_order_info(model, order_data)

            # 执行请求
            self.logger.info(f"[订单上传] 📡 发送API请求...")
            self.logger.info(f"[订单上传]    接口地址: {Config.get_url()}")
            self.logger.info(f"[订单上传]    请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            response = self.client.execute(request)

            # 处理响应
            success, request_no = self._handle_response(response, model, order_data)

            # 更新数据库状态
            if success:
                self.logger.info(f"[订单上传] 💾 更新数据库状态...")
                db_update_success = self.update_order_upload_status(
                    order_data['billid'],
                    order_data['order_id'],
                    request_no,
                    success=True
                )

                if db_update_success:
                    self.logger.info(f"[订单上传] ✅ 数据库状态更新成功")
                    return True
                else:
                    self.logger.warning(f"[订单上传] ⚠️ 订单上传成功但数据库状态更新失败")
                    return False
            else:
                self.logger.info(f"[订单上传] 💾 记录失败状态到数据库...")
                self.update_order_upload_status(
                    order_data['billid'],
                    order_data['order_id'],
                    request_no or "FAILED",
                    success=False
                )
                return False

        except Exception as e:
            self.logger.error(f"[订单上传] ❌ 订单上传异常: {str(e)}")
            import traceback
            self.logger.error(f"[订单上传] 错误详情: {traceback.format_exc()}")

            # 记录异常到数据库
            self.update_order_upload_status(
                order_data['billid'],
                order_data['order_id'],
                f"EXCEPTION: {str(e)[:100]}",
                success=False
            )
            return False

    def batch_upload_orders(self, progress_callback=None):
        """批量上传订单"""
        self.logger.info(f"[订单上传] 🚀 开始批量上传订单...")
        self.logger.info(f"[订单上传] {'=' * 80}")

        # 从数据库获取订单
        self.logger.info(f"[订单上传] 📋 从数据库获取待上传订单...")
        orders = self.get_orders_from_database()

        if not orders:
            self.logger.warning(f"[订单上传] ⚠️ 没有找到待上传的订单")
            return 0, 0, []

        total_orders = len(orders)
        self.logger.info(f"[订单上传] 📊 共找到 {total_orders} 笔待上传订单")

        # 统计商户号和门店ID分布
        merchant_stats = {}
        store_stats = {}
        for order in orders:
            merchant_id = order['merchant_id']
            store_id = order['store_id']

            if merchant_id not in merchant_stats:
                merchant_stats[merchant_id] = 0
            merchant_stats[merchant_id] += 1

            if store_id not in store_stats:
                store_stats[store_id] = 0
            store_stats[store_id] += 1

        self.logger.info(f"[订单上传] 💼 商户号分布统计:")
        for merchant_id, count in merchant_stats.items():
            self.logger.info(f"[订单上传]    商户 {merchant_id}: {count} 笔订单")

        self.logger.info(f"[订单上传] 🏪 门店ID分布统计:")
        for store_id, count in store_stats.items():
            self.logger.info(f"[订单上传]    门店 {store_id}: {count} 笔订单")

        self.logger.info(f"[订单上传] {'=' * 80}")

        success_count = 0
        failed_orders = []
        start_time = datetime.now()

        for i, order_data in enumerate(orders, 1):
            self.logger.info(f"[订单上传] 📤 处理第 {i}/{total_orders} 笔订单")
            self.logger.info(f"[订单上传]    订单号: {order_data['order_id']}")
            self.logger.info(f"[订单上传]    业务单号: {order_data['billid']}")
            self.logger.info(f"[订单上传]    支付方式: {order_data['payment_method']}")
            self.logger.info(f"[订单上传]    订单金额: {order_data['order_amount'] / 100}元")
            self.logger.info(f"[订单上传]    动态商户号: {order_data['merchant_id']}")
            self.logger.info(f"[订单上传]    动态门店ID: {order_data['store_id']}")
            self.logger.info(f"[订单上传] {'-' * 80}")

            # 更新进度
            if progress_callback:
                progress_callback(i, total_orders, f"处理订单: {order_data['order_id']}")

            order_start_time = datetime.now()
            success = self.upload_single_order(order_data)
            order_end_time = datetime.now()

            processing_time = (order_end_time - order_start_time).total_seconds()

            if success:
                success_count += 1
                self.logger.info(f"[订单上传] ✅ 第 {i} 笔订单处理成功 (耗时: {processing_time:.2f}秒)")
            else:
                failed_orders.append(order_data)
                self.logger.error(f"[订单上传] ❌ 第 {i} 笔订单处理失败 (耗时: {processing_time:.2f}秒)")

            # 间隔一下避免请求过快
            if i < len(orders):  # 不是最后一笔
                self.logger.info(f"[订单上传] ⏱️ 等待1秒后处理下一笔订单...")
                time.sleep(1)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 打印汇总结果
        self.logger.info(f"[订单上传] {'=' * 80}")
        self.logger.info(f"[订单上传] 📊 批量上传结果汇总")
        self.logger.info(f"[订单上传] {'=' * 80}")
        self.logger.info(f"[订单上传] 📈 处理订单总数: {len(orders)} 笔")
        self.logger.info(f"[订单上传] ✅ 成功上传: {success_count} 笔")
        self.logger.info(f"[订单上传] ❌ 上传失败: {len(failed_orders)} 笔")
        self.logger.info(f"[订单上传] 📊 成功率: {success_count / len(orders) * 100:.1f}%")
        self.logger.info(f"[订单上传] ⏱️ 总耗时: {total_time:.2f}秒")
        self.logger.info(f"[订单上传] ⚡ 平均每笔耗时: {total_time / len(orders):.2f}秒")
        self.logger.info(f"[订单上传] 🕐 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"[订单上传] 🕐 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if failed_orders:
            self.logger.warning(f"[订单上传] ❌ 失败订单详情:")
            self.logger.warning(f"[订单上传] {'-' * 80}")
            for i, order in enumerate(failed_orders, 1):
                self.logger.warning(f"[订单上传] {i:2d}. 订单号: {order['order_id']}")
                self.logger.warning(f"[订单上传]      业务单号: {order['billid']}")
                self.logger.warning(f"[订单上传]      支付方式: {order['payment_method']}")
                self.logger.warning(f"[订单上传]      订单金额: {order['order_amount'] / 100}元")
                self.logger.warning(f"[订单上传]      商户号: {order['merchant_id']}")
                self.logger.warning(f"[订单上传]      门店ID: {order['store_id']}")

        self.logger.info(f"[订单上传] {'=' * 80}")
        return success_count, len(orders), failed_orders

    def _print_order_info(self, model, order_data):
        """打印订单详细信息"""
        self.logger.info(f"[订单上传] {'=' * 80}")
        self.logger.info(f"[订单上传] 📦 MUMUSO订单上传信息 (动态商户号+门店ID版)")
        self.logger.info(f"[订单上传] {'=' * 80}")
        self.logger.info(f"[订单上传] 🌐 环境: {Config.get_env_name()}")
        self.logger.info(f"[订单上传] 🏪 门店ID: {model.store_id} (动态获取)")
        self.logger.info(f"[订单上传] 🏢 商户号: {model.merchant_id} (动态获取)")
        self.logger.info(f"[订单上传] 🔢 订单号: {model.order_id}")
        self.logger.info(f"[订单上传] 📊 业务单号: {order_data['billid']}")
        self.logger.info(f"[订单上传] 💰 订单金额: {model.order_amount}分 ({model.order_amount / 100}元)")
        self.logger.info(f"[订单上传] 💳 支付方式: {order_data['payment_method']} ({model.pay_type})")
        self.logger.info(f"[订单上传] 🆔 支付平台订单号: {model.trade_no}")
        self.logger.info(f"[订单上传] 🕐 订单时间: {model.order_time}")
        self.logger.info(f"[订单上传] ⚙️ 上传模式: {model.order_upload_mode}")
        self.logger.info(f"[订单上传] 💼 账户类型: {model.account_type}")
        self.logger.info(f"[订单上传] 👤 操作员: {model.user_id}")
        self.logger.info(f"[订单上传] 💸 手续费: {model.fee_amount}")
        self.logger.info(f"[订单上传] 📝 备注: {model.remark}")
        self.logger.info(f"[订单上传] {'=' * 80}")

    def _handle_response(self, response, model, order_data):
        """
        处理响应结果
        :return: (是否成功, 请求号)
        """
        self.logger.info(f"[订单上传] 📋 API响应结果:")
        self.logger.info(f"[订单上传] {'-' * 60}")

        if response:
            response_str = json.dumps(response, indent=2, ensure_ascii=False)
            self.logger.info(f"[订单上传] 响应内容: {response_str}")
        else:
            self.logger.error(f"[订单上传] ❌ 响应为空")
            return False, None

        if response and isinstance(response, dict):
            success = response.get('success')
            code = response.get('code', 'N/A')
            msg = response.get('msg', 'N/A')
            sub_code = response.get('sub_code', '')
            sub_msg = response.get('sub_msg', '')

            # 尝试获取请求号 - 可能在不同字段中
            request_no = (response.get('request_no') or
                          response.get('request_id') or
                          response.get('out_request_no') or
                          response.get('trace_id') or
                          'NO_REQUEST_NO')

            self.logger.info(f"[订单上传] 📊 响应解析:")
            self.logger.info(f"[订单上传]    成功标识: {success}")
            self.logger.info(f"[订单上传]    响应码: {code}")
            self.logger.info(f"[订单上传]    响应消息: {msg}")
            self.logger.info(f"[订单上传]    请求号: {request_no}")
            if sub_code:
                self.logger.info(f"[订单上传]    子错误码: {sub_code}")
            if sub_msg:
                self.logger.info(f"[订单上传]    子错误信息: {sub_msg}")

            if success is True:
                self.logger.info(f"[订单上传] 🎉 订单上传成功!")
                self.logger.info(f"[订单上传] ✅ 订单号: {model.order_id}")
                self.logger.info(f"[订单上传] 📊 业务单号: {order_data['billid']}")
                self.logger.info(f"[订单上传] 💰 订单金额: {model.order_amount / 100}元")
                self.logger.info(f"[订单上传] 💳 支付方式: {order_data['payment_method']}")
                self.logger.info(f"[订单上传] 🏢 商户号: {model.merchant_id} (动态)")
                self.logger.info(f"[订单上传] 🏪 门店ID: {model.store_id} (动态)")
                self.logger.info(f"[订单上传] 🆔 请求号: {request_no}")
                self.logger.info(f"[订单上传] 📞 银账通系统将处理订单并发送状态通知...")
                return True, request_no
            else:
                self.logger.error(f"[订单上传] 💥 订单上传失败!")
                self.logger.error(f"[订单上传] ❌ 订单号: {model.order_id}")
                self.logger.error(f"[订单上传] 📊 业务单号: {order_data['billid']}")
                self.logger.error(f"[订单上传] 🏢 商户号: {model.merchant_id} (动态)")
                self.logger.error(f"[订单上传] 🏪 门店ID: {model.store_id} (动态)")
                self.logger.error(f"[订单上传] 🔴 错误码: {code}")
                self.logger.error(f"[订单上传] 🔴 错误信息: {msg}")
                if sub_code:
                    self.logger.error(f"[订单上传] 🔴 子错误码: {sub_code}")
                if sub_msg:
                    self.logger.error(f"[订单上传] 🔴 子错误信息: {sub_msg}")
                return False, request_no
        else:
            self.logger.error(f"[订单上传] ❌ 响应格式异常")
            self.logger.error(f"[订单上传]    响应类型: {type(response)}")
            self.logger.error(f"[订单上传]    响应内容: {response}")
            return False, "INVALID_RESPONSE"

    # 其他方法保持不变...
    def get_order_by_id(self, order_id):
        """根据订单ID获取单个订单信息"""
        orders = self.get_orders_from_database()
        for order in orders:
            if order['order_id'] == order_id:
                return order
        return None

    def get_order_statistics(self):
        """获取订单统计信息"""
        try:
            orders = self.get_orders_from_database()
            if not orders:
                return {
                    'total': 0,
                    'wx_count': 0,
                    'alipay_count': 0,
                    'total_amount': 0,
                    'wx_amount': 0,
                    'alipay_amount': 0
                }

            wx_orders = [o for o in orders if o['payment_method'] == '微信支付']
            alipay_orders = [o for o in orders if o['payment_method'] == '支付宝']

            total_amount = sum(o['order_amount'] for o in orders) / 100
            wx_amount = sum(o['order_amount'] for o in wx_orders) / 100
            alipay_amount = sum(o['order_amount'] for o in alipay_orders) / 100

            stats = {
                'total': len(orders),
                'wx_count': len(wx_orders),
                'alipay_count': len(alipay_orders),
                'total_amount': total_amount,
                'wx_amount': wx_amount,
                'alipay_amount': alipay_amount
            }

            self.logger.info(f"[订单上传] 订单统计 - 总计: {stats['total']}笔, "
                             f"微信: {stats['wx_count']}笔, 支付宝: {stats['alipay_count']}笔, "
                             f"总金额: {stats['total_amount']:.2f}元")

            return stats

        except Exception as e:
            self.logger.error(f"[订单上传] 获取订单统计失败: {str(e)}")
            return None


# 为了向后兼容，保留原有的函数接口
def test_database_connection():
    """测试数据库连接"""
    demo = OrderUploadDemo()
    connection = demo.get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM P_BL_SELL_PAYAMOUNT_HZ_dt WHERE ROWNUM <= 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            demo.logger.error(f"[订单上传] 数据库查询测试失败: {str(e)}")
            connection.close()
            return False
    return False


def main():
    """命令行模式主函数（向后兼容）"""
    demo = OrderUploadDemo()
    demo.logger.info("[订单上传] MUMUSO订单上传系统启动 (支持动态商户号+门店ID)")

    # 检查配置
    ready, msg = Config.is_config_ready()
    if not ready:
        demo.logger.error(f"[订单上传] 配置检查失败: {msg}")
        return False

    while True:
        print("\n请选择操作:")
        print("1. 测试数据库连接")
        print("2. 查看待上传订单")
        print("3. 批量上传订单")
        print("4. 退出")

        try:
            choice = input("\n请输入选项 (1-4): ").strip()

            if choice == '1':
                success = test_database_connection()
                print("✅ 数据库连接成功" if success else "❌ 数据库连接失败")

            elif choice == '2':
                stats = demo.get_order_statistics()
                if stats:
                    print(f"📊 待上传订单统计:")
                    print(f"   总计: {stats['total']} 笔")
                    print(f"   微信支付: {stats['wx_count']} 笔 ({stats['wx_amount']:.2f}元)")
                    print(f"   支付宝: {stats['alipay_count']} 笔 ({stats['alipay_amount']:.2f}元)")
                    print(f"   总金额: {stats['total_amount']:.2f}元")

            elif choice == '3':
                confirm = input("\n⚠️ 确认要批量上传订单吗？(y/N): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    success_count, total_count, failed_orders = demo.batch_upload_orders()
                    print(f"\n📊 批量上传完成:")
                    print(f"   成功: {success_count}/{total_count}")
                    print(f"   失败: {len(failed_orders)}")

            elif choice == '4':
                print("👋 退出系统")
                break
            else:
                print("❌ 无效选项")

        except KeyboardInterrupt:
            print("\n👋 用户中断")
            break
        except Exception as e:
            demo.logger.error(f"[订单上传] 操作异常: {str(e)}")


if __name__ == '__main__':
    main()