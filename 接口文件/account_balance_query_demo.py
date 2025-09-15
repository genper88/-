#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
账户余额查询演示 - 适配完整配置系统版
文件名: account_balance_query_demo.py
功能: 演示如何使用账户余额查询功能，支持真实数据库操作和API调用
接口: merchant.balanceQuery
参考文档: 3.7.3账户余额查询
作者: 系统自动生成
更新时间: 2025-01-XX
"""

import logging
import sys
import os
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
import threading
import time
import json
import requests
import hashlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config_adapter import config_adapter
except ImportError:
    # 如果没有config_adapter，创建一个临时适配器
    class TempConfigAdapter:
        @staticmethod
        def get_env_name():
            return "测试环境"

        @staticmethod
        def get_api_url():
            return "https://fzxt-yzt-openapi.imageco.cn"

        @staticmethod
        def get_app_id():
            return "20211012897445821048422400"

        @staticmethod
        def get_account_balance_node_id():
            return "00061783"

        @staticmethod
        def get_account_balance_auto_interval():
            return 10

        @staticmethod
        def get_db_connection_info():
            return "mmserp", "mu89so7mu", "47.102.84.152:1521/mmserp"

        @staticmethod
        def get_private_key():
            return "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE_KEY-----"


    config_adapter = TempConfigAdapter()


class AccountBalanceQueryResponse:
    """账户余额查询响应类"""

    def __init__(self, request_id: str, code: int, msg: str = "",
                 sub_msg: str = "", success: bool = False, data: Dict = None):
        self.request_id = request_id
        self.code = code
        self.msg = msg
        self.sub_msg = sub_msg
        self.success = success
        self.data = data or {}

    def is_success(self) -> bool:
        """判断请求是否成功"""
        return self.success and self.code == 10000

    def get_error_message(self) -> str:
        """获取错误消息"""
        if self.is_success():
            return ""
        return f"[{self.code}] {self.msg} {self.sub_msg}".strip()

    def get_total_balance_yuan(self) -> float:
        """获取总余额（元）"""
        return self.data.get('total_balance', 0) / 100.0

    def get_available_balance_yuan(self) -> float:
        """获取可用余额（元）"""
        return self.data.get('available_balance', 0) / 100.0

    def get_frozen_balance_yuan(self) -> float:
        """获取冻结余额（元）"""
        return self.data.get('frozen_balance', 0) / 100.0

    def get_balance_summary(self) -> str:
        """获取余额摘要"""
        if not self.is_success():
            return f"查询失败: {self.get_error_message()}"

        return (f"总余额: {self.get_total_balance_yuan():.2f}元, "
                f"可用: {self.get_available_balance_yuan():.2f}元, "
                f"冻结: {self.get_frozen_balance_yuan():.2f}元")


class MerchantInfo:
    """商户信息类"""

    def __init__(self, merchant_id: int, store_no: str = "",
                 bill_id: str = "", total_amount: float = 0,
                 merchant_name: str = ""):
        self.merchant_id = merchant_id
        self.store_no = store_no
        self.bill_id = bill_id
        self.total_amount = total_amount
        self.merchant_name = merchant_name


class DatabaseManager:
    """数据库管理类 - 真实数据库连接"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.connection = None

    def connect(self):
        """连接数据库"""
        try:
            # 导入Oracle数据库驱动
            import cx_Oracle

            # 从配置适配器获取数据库连接信息
            user, password, dsn = config_adapter.get_db_connection_info()

            # 建立连接
            self.connection = cx_Oracle.connect(
                user=user,
                password=password,
                dsn=dsn,
                encoding="UTF-8"
            )

            self.logger.info(f"[数据库] 数据库连接成功 - {user}@{dsn}")
            return True

        except ImportError:
            self.logger.error("[数据库] cx_Oracle模块未安装，请运行: pip install cx_Oracle")
            return False
        except Exception as e:
            self.logger.error(f"[数据库] 连接失败: {str(e)}")
            return False

    def get_pending_merchants(self) -> List[MerchantInfo]:
        """获取待查询余额的商户列表"""
        try:
            if not self.connection:
                if not self.connect():
                    return []

            cursor = self.connection.cursor()

            # 修正后的SQL查询 - 使用正确的字段名
            sql = """
            SELECT hd.ymshanghuhao as merchant_id, 
                   hd.storeid as store_no, 
                   hd.billid, 
                   hd.totalamount
            FROM P_BL_SELL_PAYAMOUNT_HZ_hd hd 
            WHERE hd.allresult_check_sign='Y' 
            AND hd.BALANCE_MONEY_SIGN='N'
            AND ROWNUM <= 100
            ORDER BY hd.uptime DESC
            """

            cursor.execute(sql)
            results = cursor.fetchall()

            merchants = []
            for row in results:
                merchant_id, store_no, bill_id, total_amount = row
                merchants.append(MerchantInfo(
                    merchant_id=int(merchant_id) if merchant_id else 0,
                    store_no=store_no or "",
                    bill_id=bill_id or "",
                    total_amount=float(total_amount) / 100.0 if total_amount else 0.0,  # 转换为元
                    merchant_name=""  # 移除无效的字段
                ))

            cursor.close()
            self.logger.info(f"[数据库] 查询到 {len(merchants)} 个待处理商户")
            return merchants

        except Exception as e:
            self.logger.error(f"[数据库] 查询待处理商户失败: {str(e)}")
            return []

    def update_balance_sign(self, merchant_id: int, bill_id: str) -> bool:
        """更新余额标志位"""
        try:
            if not self.connection:
                if not self.connect():
                    return False

            cursor = self.connection.cursor()

            # 真实更新SQL
            sql = """
            UPDATE P_BL_SELL_PAYAMOUNT_HZ_hd 
            SET BALANCE_MONEY_SIGN='Y',
                BALANCE_CHECK_TIME=SYSDATE
            WHERE ymshanghuhao=:merchant_id 
            AND billid=:bill_id
            """

            cursor.execute(sql, {
                'merchant_id': merchant_id,
                'bill_id': bill_id
            })

            # 提交事务
            self.connection.commit()

            # 检查影响行数
            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                self.logger.info(f"[数据库] 更新商户 {merchant_id} 账单 {bill_id} 余额标志位成功")
                return True
            else:
                self.logger.warning(f"[数据库] 商户 {merchant_id} 账单 {bill_id} 未找到记录")
                return False

        except Exception as e:
            self.logger.error(f"[数据库] 更新余额标志位失败: {str(e)}")
            # 回滚事务
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            return False

    def send_wechat_message(self, merchant_id: int, message: str) -> bool:
        """发送企业微信消息"""
        try:
            if not self.connection:
                if not self.connect():
                    return False

            cursor = self.connection.cursor()

            # 获取下一个序列号
            max_series_sql = "SELECT NVL(MAX(series), 0) + 1 FROM d_qiye_sendmsg"
            cursor.execute(max_series_sql)
            next_series = cursor.fetchone()[0]

            # 插入消息SQL
            sql = """
            INSERT INTO d_qiye_sendmsg (SERIES, STAFFID, MSG, TYPEID, AGENTID)
            VALUES (:series, :staff_id, :message, '002', '3091828666')
            """

            # 根据商户ID查找对应的员工ID
            staff_id = f"GP"

            cursor.execute(sql, {
                'series': next_series,
                'staff_id': staff_id,
                'message': message
            })

            # 提交事务
            self.connection.commit()
            cursor.close()

            self.logger.info(f"[数据库] 发送企业微信消息成功 - 商户: {merchant_id}, 序列号: {next_series}")
            return True

        except Exception as e:
            self.logger.error(f"[数据库] 发送企业微信消息失败: {str(e)}")
            # 回滚事务
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("[数据库] 连接已关闭")
            except Exception as e:
                self.logger.error(f"[数据库] 关闭连接失败: {str(e)}")


class ApiClient:
    """API客户端类 - 真实API调用"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.base_url = config_adapter.get_api_url()
        self.app_id = config_adapter.get_app_id()
        self.node_id = config_adapter.get_account_balance_node_id()

        # 加载私钥
        self.private_key = self._load_private_key()

    def _load_private_key(self):
        """加载RSA私钥"""
        try:
            # 从配置适配器获取私钥
            private_key_content = config_adapter.get_private_key()

            if not private_key_content or "-----BEGIN" not in private_key_content:
                self.logger.error("[API] 私钥配置无效或为空")
                return None

            private_key = RSA.import_key(private_key_content)
            self.logger.info("[API] 私钥加载成功")
            return private_key

        except Exception as e:
            self.logger.error(f"[API] 加载私钥失败: {str(e)}")
            return None

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成RSA2签名"""
        try:
            if not self.private_key:
                self.logger.error("[API] 私钥未加载，无法生成签名")
                return ""

            # 移除sign参数
            sign_params = {k: v for k, v in params.items() if k != 'sign'}

            # 按字典序排序
            sorted_params = sorted(sign_params.items())

            # 构建签名字符串
            sign_string = '&'.join([f'{k}={v}' for k, v in sorted_params])

            # 使用私钥进行RSA2签名
            signer = PKCS1_v1_5.new(self.private_key)
            digest = SHA256.new(sign_string.encode('utf-8'))
            signature = signer.sign(digest)

            # Base64编码
            sign = base64.b64encode(signature).decode('utf-8')

            self.logger.debug(f"[API] 签名字符串: {sign_string}")
            return sign

        except Exception as e:
            self.logger.error(f"[API] 生成签名失败: {str(e)}")
            return ""

    def query_balance(self, merchant_id: int, account_type: str = "1",
                      store_no: str = "") -> AccountBalanceQueryResponse:
        """查询商户余额"""
        try:
            # 构建业务参数
            biz_content = {
                "account_sub_type": account_type,
                "merchant_id": str(merchant_id),
                "sso_node_id": self.node_id,
                "store_no": store_no
            }

            # 构建公共参数
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params = {
                "app_id": self.app_id,
                "method": "merchant.balanceQuery",
                "format": "json",
                "charset": "UTF-8",
                "sign_type": "RSA2",
                "timestamp": timestamp,
                "version": "1.0",
                "biz_content": json.dumps(biz_content, ensure_ascii=False)
            }

            # 生成签名
            params["sign"] = self._generate_sign(params)

            if not params["sign"]:
                return AccountBalanceQueryResponse(
                    request_id="error",
                    code=50000,
                    msg="签名生成失败",
                    success=False
                )

            self.logger.info(f"[API] 查询商户余额 - 商户ID: {merchant_id}, 账户类型: {account_type}")
            self.logger.debug(f"[API] 请求参数: {json.dumps(params, ensure_ascii=False, indent=2)}")

            # 发送请求
            response = requests.post(
                self.base_url,
                data=params,
                timeout=30,
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            )

            self.logger.debug(f"[API] 响应状态码: {response.status_code}")
            self.logger.debug(f"[API] 响应内容: {response.text}")

            if response.status_code == 200:
                result = response.json()

                # 解析响应
                if "merchant_balanceQuery_response" in result:
                    resp_data = result["merchant_balanceQuery_response"]
                    return AccountBalanceQueryResponse(
                        request_id=resp_data.get("request_id", ""),
                        code=int(resp_data.get("code", 50000)),
                        msg=resp_data.get("msg", ""),
                        sub_msg=resp_data.get("sub_msg", ""),
                        success=resp_data.get("success", False),
                        data=resp_data.get("data", {})
                    )
                else:
                    return AccountBalanceQueryResponse(
                        request_id="error",
                        code=50000,
                        msg="响应格式错误",
                        sub_msg=f"未找到merchant_balanceQuery_response节点: {result}",
                        success=False
                    )
            else:
                return AccountBalanceQueryResponse(
                    request_id="error",
                    code=response.status_code,
                    msg=f"HTTP错误: {response.status_code}",
                    sub_msg=response.text,
                    success=False
                )

        except requests.exceptions.Timeout:
            return AccountBalanceQueryResponse(
                request_id="error",
                code=50001,
                msg="请求超时",
                success=False
            )
        except requests.exceptions.RequestException as e:
            return AccountBalanceQueryResponse(
                request_id="error",
                code=50002,
                msg="网络请求异常",
                sub_msg=str(e),
                success=False
            )
        except json.JSONDecodeError as e:
            return AccountBalanceQueryResponse(
                request_id="error",
                code=50003,
                msg="响应JSON解析失败",
                sub_msg=str(e),
                success=False
            )
        except Exception as e:
            self.logger.error(f"[API] 查询余额异常: {str(e)}", exc_info=True)
            return AccountBalanceQueryResponse(
                request_id="error",
                code=50000,
                msg="查询异常",
                sub_msg=str(e),
                success=False
            )


class AccountBalanceQueryDemo:
    """账户余额查询演示类 - 完整配置系统版"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化演示类

        Args:
            logger: 日志记录器
        """
        # 首先初始化基本属性，避免__del__方法出错
        self.auto_query_running = False
        self.auto_query_thread = None
        self.progress_callback = None
        self.result_callback = None
        self.api_client = None
        self.db_manager = None
        self.logger = None

        try:
            self.logger = logger or self._create_logger()

            # 从配置适配器获取自动查询间隔
            self.auto_query_interval = config_adapter.get_account_balance_auto_interval()

            # 初始化API客户端和数据库管理器
            self.api_client = ApiClient(self.logger)
            self.db_manager = DatabaseManager(self.logger)

            self.logger.info(f"[账户余额查询] 初始化完成 - 环境: {config_adapter.get_env_name()}")
            self.logger.info(f"[账户余额查询] API地址: {config_adapter.get_api_url()}")
            self.logger.info(f"[账户余额查询] 机构号: {config_adapter.get_account_balance_node_id()}")

        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"[账户余额查询] 初始化失败: {str(e)}")
            else:
                print(f"[账户余额查询] 初始化失败: {str(e)}")
            raise  # 重新抛出异常，让调用者知道初始化失败

    def _create_logger(self) -> logging.Logger:
        """创建日志记录器"""
        logger = logging.getLogger('AccountBalanceQueryDemo')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self.progress_callback = callback

    def set_result_callback(self, callback: Callable):
        """设置结果回调函数"""
        self.result_callback = callback

    def test_database_connection(self) -> bool:
        """测试数据库连接"""
        self.logger.info("[账户余额查询] 测试数据库连接...")
        return self.db_manager.connect()

    def query_single_merchant_balance(self, merchant_id: int,
                                      account_type: str = "1",
                                      store_no: str = "") -> AccountBalanceQueryResponse:
        """
        查询单个商户余额

        Args:
            merchant_id: 商户号
            account_type: 账户类型 0=收款账户 1=付款账户
            store_no: 门店号

        Returns:
            AccountBalanceQueryResponse: 查询响应
        """
        self.logger.info(f"[账户余额查询] 开始查询商户余额 - 商户号: {merchant_id}")

        try:
            if self.progress_callback:
                self.progress_callback("开始查询商户余额...", 10)

            # 执行查询
            response = self.api_client.query_balance(
                merchant_id=merchant_id,
                account_type=account_type,
                store_no=store_no
            )

            if self.progress_callback:
                self.progress_callback("查询完成", 100)

            # 调用结果回调
            if self.result_callback:
                self.result_callback('single_result', {
                    'merchant_id': merchant_id,
                    'result': response
                })

            return response

        except Exception as e:
            error_msg = f"查询商户余额异常: {str(e)}"
            self.logger.error(f"[账户余额查询] {error_msg}", exc_info=True)

            # 创建错误响应
            error_response = AccountBalanceQueryResponse(
                request_id=f"error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                code=50000,
                msg="查询异常",
                sub_msg=error_msg,
                success=False
            )

            if self.result_callback:
                self.result_callback('single_result', {
                    'merchant_id': merchant_id,
                    'result': error_response
                })

            return error_response

    def batch_query_from_database(self) -> Dict[int, AccountBalanceQueryResponse]:
        """
        从数据库批量查询商户余额并处理业务逻辑

        Returns:
            dict: 商户号 -> 查询结果的字典
        """
        self.logger.info("[账户余额查询] 开始从数据库批量查询商户余额")

        try:
            if self.progress_callback:
                self.progress_callback("正在从数据库获取商户列表...", 10)

            # 从数据库获取待处理商户
            merchant_list = self.db_manager.get_pending_merchants()

            if not merchant_list:
                self.logger.warning("[账户余额查询] 未找到需要查询的商户")
                if self.result_callback:
                    self.result_callback('batch_complete', {
                        'total_count': 0,
                        'success_count': 0,
                        'sufficient_count': 0,
                        'insufficient_count': 0,
                        'results': {}
                    })
                return {}

            self.logger.info(f"[账户余额查询] 找到 {len(merchant_list)} 个商户需要查询")

            if self.progress_callback:
                self.progress_callback(f"开始批量查询 {len(merchant_list)} 个商户...", 20)

            # 执行批量查询
            results = {}
            success_count = 0
            sufficient_count = 0
            insufficient_count = 0

            for i, merchant_info in enumerate(merchant_list):
                try:
                    # 更新进度
                    progress = 20 + (i + 1) * 60 / len(merchant_list)
                    if self.progress_callback:
                        self.progress_callback(f"查询商户 {merchant_info.merchant_id}...", progress)

                    # 查询余额（批量查询固定为付款账户）
                    response = self.api_client.query_balance(
                        merchant_id=merchant_info.merchant_id,
                        account_type="1",  # 付款账户
                        store_no=merchant_info.store_no
                    )

                    results[merchant_info.merchant_id] = response

                    if response.is_success():
                        success_count += 1

                        # 检查余额是否足够
                        total_balance = response.get_total_balance_yuan()
                        required_amount = merchant_info.total_amount

                        if total_balance >= required_amount:
                            # 余额充足，更新标志位
                            update_success = self.db_manager.update_balance_sign(
                                merchant_info.merchant_id,
                                merchant_info.bill_id
                            )

                            if update_success:
                                sufficient_count += 1
                                self.logger.info(
                                    f"[账户余额查询] 商户 {merchant_info.merchant_id} 余额充足({total_balance:.2f}元>={required_amount:.2f}元)，已更新标志位")
                            else:
                                self.logger.error(f"[账户余额查询] 商户 {merchant_info.merchant_id} 更新标志位失败")
                        else:
                            # 余额不足，发送通知
                            insufficient_count += 1
                            message = (f"你好，我是小木木，现在友情提醒你，"
                                       f"商户 {merchant_info.merchant_id} 账户余额不足，"
                                       f"当前余额: {total_balance:.2f}元，"
                                       f"需要金额: {required_amount:.2f}元，"
                                       f"请及时充值。"
                                       f"时间戳：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                            self.db_manager.send_wechat_message(
                                merchant_info.merchant_id,
                                message
                            )

                            self.logger.warning(
                                f"[账户余额查询] 商户 {merchant_info.merchant_id} 余额不足({total_balance:.2f}元<{required_amount:.2f}元)，已发送通知")
                    else:
                        self.logger.error(
                            f"[账户余额查询] 商户 {merchant_info.merchant_id} 查询失败: {response.get_error_message()}")

                    # 添加小延迟避免频繁调用
                    time.sleep(0.2)

                except Exception as e:
                    self.logger.error(f"[账户余额查询] 处理商户 {merchant_info.merchant_id} 时异常: {str(e)}")

                    # 创建错误响应
                    error_response = AccountBalanceQueryResponse(
                        request_id=f"error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        code=50000,
                        msg="处理异常",
                        sub_msg=str(e),
                        success=False
                    )
                    results[merchant_info.merchant_id] = error_response

            self.logger.info(
                f"[账户余额查询] 批量查询完成 - 总数: {len(results)}, 成功: {success_count}, 余额充足: {sufficient_count}, 余额不足: {insufficient_count}")

            if self.progress_callback:
                self.progress_callback("批量查询完成", 100)

            if self.result_callback:
                self.result_callback('batch_complete', {
                    'total_count': len(results),
                    'success_count': success_count,
                    'sufficient_count': sufficient_count,
                    'insufficient_count': insufficient_count,
                    'results': results
                })

            return results

        except Exception as e:
            error_msg = f"批量查询异常: {str(e)}"
            self.logger.error(f"[账户余额查询] {error_msg}", exc_info=True)

            if self.result_callback:
                self.result_callback('batch_error', {
                    'error': error_msg
                })

            return {}

    def start_auto_query(self):
        """启动自动查询"""
        if self.auto_query_running:
            self.logger.warning("[账户余额查询] 自动查询已在运行中")
            return

        self.auto_query_running = True
        self.auto_query_thread = threading.Thread(target=self._auto_query_worker, daemon=True)
        self.auto_query_thread.start()

        self.logger.info(f"[账户余额查询] 自动查询已启动 - 间隔: {self.auto_query_interval} 分钟")

        if self.result_callback:
            self.result_callback('auto_status', {
                'status': 'started',
                'interval': self.auto_query_interval
            })

    def stop_auto_query(self):
        """停止自动查询"""
        self.auto_query_running = False
        if self.auto_query_thread:
            self.auto_query_thread.join(timeout=5)

        self.logger.info("[账户余额查询] 自动查询已停止")

        if self.result_callback:
            self.result_callback('auto_status', {
                'status': 'stopped'
            })

    def _auto_query_worker(self):
        """自动查询工作线程"""
        self.logger.info("[账户余额查询] 自动查询工作线程已启动")

        while self.auto_query_running:
            try:
                # 执行批量查询
                results = self.batch_query_from_database()

                if self.result_callback:
                    self.result_callback('auto_query_result', {
                        'results_count': len(results),
                        'timestamp': datetime.now()
                    })

                # 等待下次查询
                for _ in range(self.auto_query_interval * 60):  # 转换为秒
                    if not self.auto_query_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"[账户余额查询] 自动查询异常: {str(e)}", exc_info=True)
                time.sleep(60)  # 异常时等待1分钟后重试

        self.logger.info("[账户余额查询] 自动查询工作线程已退出")

    def __del__(self):
        """析构函数"""
        try:
            # 停止自动查询
            if hasattr(self, 'auto_query_running') and self.auto_query_running:
                self.stop_auto_query()

            # 关闭数据库连接
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
        except Exception as e:
            # 在析构函数中不要抛出异常
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.error(f"[账户余额查询] 析构函数异常: {str(e)}")
            except:
                pass


def main():
    """主函数 - 演示基本用法"""
    print("🚀 账户余额查询演示 - 完整配置系统版")
    print("=" * 60)

    try:
        # 创建演示实例
        demo = AccountBalanceQueryDemo()

        print(f"当前环境: {config_adapter.get_env_name()}")
        print(f"API地址: {config_adapter.get_api_url()}")
        print(f"机构号: {config_adapter.get_account_balance_node_id()}")
        print()

        # 测试数据库连接
        print("🔧 测试数据库连接...")
        if demo.test_database_connection():
            print("✅ 数据库连接成功!")
        else:
            print("❌ 数据库连接失败!")
            return

        print()

        # 测试单个查询
        print("📝 测试单个商户余额查询...")

        # 从数据库获取一个待查询的商户进行测试
        merchants = demo.db_manager.get_pending_merchants()
        if merchants:
            test_merchant = merchants[0]
            print(f"使用商户 {test_merchant.merchant_id} 进行测试")

            response = demo.query_single_merchant_balance(
                merchant_id=test_merchant.merchant_id,
                account_type="1",  # 付款账户
                store_no=test_merchant.store_no
            )

            if response.is_success():
                print("✅ 查询成功!")
                print(f"余额信息: {response.get_balance_summary()}")
            else:
                print(f"❌ 查询失败: {response.get_error_message()}")
        else:
            print("⚠️  没有找到待查询的商户")

        print()

        # 测试批量查询
        print("📋 测试批量商户余额查询...")
        batch_results = demo.batch_query_from_database()

        print(f"批量查询完成，共查询 {len(batch_results)} 个商户")
        for merchant_id, result in batch_results.items():
            status = "✅ 成功" if result.is_success() else "❌ 失败"
            print(f"  商户 {merchant_id}: {status}")
            if result.is_success():
                print(f"    {result.get_balance_summary()}")
            else:
                print(f"    错误: {result.get_error_message()}")

        print("\n🎉 演示完成!")

    except Exception as e:
        print(f"❌ 演示运行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()