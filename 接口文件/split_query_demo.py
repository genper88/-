#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
余额支付查询演示类
文件名: split_query_demo.py
功能: 集成数据库查询和API调用，实现完整的余额支付查询功能
接口: bkfunds.balance.pay.query
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable, Tuple
import cx_Oracle

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from request.SplitQueryRequest import BalancePayQueryRequestHandler
from model.SplitQueryModel import DatabaseQueryResult, BalancePayQueryResponse, BalancePayQueryData


class SplitQueryDemo:
    """余额支付查询演示类（保持类名不变以保证兼容性）"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化余额支付查询演示"""
        self.logger = logger or logging.getLogger(__name__)
        self.query_handler = BalancePayQueryRequestHandler(logger)

        # 数据库连接配置
        self.db_user, self.db_password, self.db_dsn = Config.get_db_connection_info()

        # 自动查询相关
        self.auto_query_running = False
        self.auto_query_thread = None
        self.auto_query_interval = Config.get_auto_query_interval()  # 分钟

        # 查询配置
        self.query_sql = Config.get_balance_pay_query_sql()
        self.batch_size = Config.BALANCE_PAY_QUERY_CONFIG.get('BATCH_QUERY_SIZE', 50)

        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.result_callback: Optional[Callable] = None

        self.logger.info(f"[余额支付查询] 初始化完成")
        self.logger.info(f"[余额支付查询] 数据库DSN: {self.db_dsn}")
        self.logger.info(f"[余额支付查询] 自动查询间隔: {self.auto_query_interval}分钟")
        self.logger.info(f"[余额支付查询] 批量查询大小: {self.batch_size}")

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self.progress_callback = callback

    def set_result_callback(self, callback: Callable):
        """设置结果回调函数"""
        self.result_callback = callback

    def _notify_progress(self, message: str, progress: int = 0):
        """通知进度更新"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def _notify_result(self, result_type: str, data: dict):
        """通知结果更新"""
        if self.result_callback:
            self.result_callback(result_type, data)

    def test_database_connection(self) -> bool:
        """测试数据库连接"""
        try:
            self.logger.info("[余额支付查询] 测试数据库连接...")

            connection = cx_Oracle.connect(
                user=self.db_user,
                password=self.db_password,
                dsn=self.db_dsn,
                encoding="UTF-8"
            )

            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()

            cursor.close()
            connection.close()

            if result:
                self.logger.info("[余额支付查询] 数据库连接测试成功")
                return True
            else:
                self.logger.error("[余额支付查询] 数据库连接测试失败：无返回结果")
                return False

        except Exception as e:
            self.logger.error(f"[余额支付查询] 数据库连接测试失败: {str(e)}")
            return False

    def query_pending_split_records(self, limit: Optional[int] = None) -> List[DatabaseQueryResult]:
        """
        查询待余额支付查询的记录

        Args:
            limit: 限制查询数量

        Returns:
            List[DatabaseQueryResult]: 查询结果列表
        """
        try:
            self.logger.info(f"[余额支付查询] 开始查询待查询记录，限制数量: {limit or '无限制'}")

            connection = cx_Oracle.connect(
                user=self.db_user,
                password=self.db_password,
                dsn=self.db_dsn,
                encoding="UTF-8"
            )

            cursor = connection.cursor()

            # 构建SQL语句
            sql = self.query_sql
            if limit:
                sql += f" AND ROWNUM <= {limit}"

            self.logger.debug(f"[余额支付查询] 执行SQL: {sql}")

            cursor.execute(sql)
            rows = cursor.fetchall()

            # 解析查询结果
            results = []
            for row in rows:
                # 修复字段索引，确保与SQL查询结果匹配
                result = DatabaseQueryResult(
                    billid=str(row[0]) if row[0] else "",
                    xpbillid=str(row[1]) if row[1] else "",
                    trade_no=str(row[2]) if row[2] else None  # 更新为银行流水号字段
                )
                results.append(result)

            cursor.close()
            connection.close()

            self.logger.info(f"[余额支付查询] 查询完成，共找到 {len(results)} 条记录")

            # 过滤有银行流水号的记录
            valid_results = [r for r in results if r.has_trade_no()]
            self.logger.info(f"[余额支付查询] 其中有银行流水号的记录: {len(valid_results)} 条")

            return valid_results

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            self.logger.error(f"[余额支付查询] 查询数据库失败: ORA-{error.code}: {error.message}")
            return []
        except Exception as e:
            self.logger.error(f"[余额支付查询] 查询数据库失败: {str(e)}")
            return []

    def query_record_by_trade_no(self, trade_no: str) -> Optional[DatabaseQueryResult]:
        """
        根据银行流水号查询数据库记录

        Args:
            trade_no: 银行流水号

        Returns:
            Optional[DatabaseQueryResult]: 查询到的记录，如果没有则返回None
        """
        try:
            self.logger.info(f"[余额支付查询] 根据流水号查询数据库记录: {trade_no}")

            connection = cx_Oracle.connect(
                user=self.db_user,
                password=self.db_password,
                dsn=self.db_dsn,
                encoding="UTF-8"
            )

            cursor = connection.cursor()

            # 构建查询SQL - 根据银行流水号查询
            query_sql = """
                SELECT billid, xpbillid, fz_requestback_no
                FROM P_BL_SELL_PAYAMOUNT_HZ_dt 
                WHERE fz_requestback_no = :trade_no
                AND ROWNUM = 1
            """

            cursor.execute(query_sql, {'trade_no': trade_no})
            row = cursor.fetchone()

            cursor.close()
            connection.close()

            if row:
                result = DatabaseQueryResult(
                    billid=str(row[0]) if row[0] else "",
                    xpbillid=str(row[1]) if row[1] else "",
                    trade_no=str(row[2]) if row[2] else None
                )
                self.logger.info(f"[余额支付查询] 找到记录: billid={result.billid}, xpbillid={result.xpbillid}")
                return result
            else:
                self.logger.warning(f"[余额支付查询] 未找到对应记录: {trade_no}")
                return None

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            self.logger.error(f"[余额支付查询] 查询记录失败: ORA-{error.code}: {error.message}")
            return None
        except Exception as e:
            self.logger.error(f"[余额支付查询] 查询记录失败: {str(e)}")
            return None

    def query_single_split_result(self, trade_no: str, node_id: Optional[str] = None, auto_writeback: bool = True) -> \
    Tuple[BalancePayQueryResponse, Optional[DatabaseQueryResult]]:
        """
        查询单个余额支付结果（保持方法名不变以保证兼容性）

        Args:
            trade_no: 银行流水号
            node_id: 机构号（可选）
            auto_writeback: 是否自动回写（默认True）

        Returns:
            Tuple[BalancePayQueryResponse, Optional[DatabaseQueryResult]]: 查询结果和数据库记录
        """
        self.logger.info(f"[余额支付查询] 查询单个交易结果: {trade_no}, 自动回写: {auto_writeback}")

        # 验证流水号格式
        if not self.query_handler.validate_trade_no(trade_no):
            self.logger.error(f"[余额支付查询] 流水号格式无效: {trade_no}")
            return BalancePayQueryResponse(
                request_id="",
                code=0,
                msg="流水号格式无效",
                success=False
            ), None

        # 首先查询数据库记录，获取billid和xpbillid
        db_record = self.query_record_by_trade_no(trade_no)

        # 调用API查询
        api_result = self.query_handler.query_balance_pay_result(trade_no, node_id)

        # 如果查询成功且需要自动回写
        if auto_writeback and api_result.is_success() and api_result.data and api_result.data.status == "1":
            self.logger.info(f"[余额支付查询] 分账成功，开始回写数据库: {trade_no}")
            success = self._writeback_split_result(trade_no, api_result.data)
            if success:
                self.logger.info(f"[余额支付查询] 回写成功: {trade_no}")
            else:
                self.logger.error(f"[余额支付查询] 回写失败: {trade_no}")

        return api_result, db_record

    def batch_query_split_results(self, progress_callback=None, auto_writeback: bool = True):
        """
        批量查询分账结果（GUI兼容方法）

        Args:
            progress_callback: 进度回调函数
            auto_writeback: 是否自动回写成功的结果（默认True）

        Returns:
            tuple: (success_count, total_count, results)
        """
        self.logger.info(f"[余额支付查询] 开始批量查询分账结果（GUI方法），自动回写: {auto_writeback}")

        try:
            # 首先查询数据库记录
            db_records = self.query_pending_split_records(self.batch_size)

            # 创建交易号到记录的映射
            trade_no_to_record = {record.get_trade_no(): record for record in db_records}

            # 提取银行流水号
            trade_nos = [record.get_trade_no() for record in db_records if record.get_trade_no()]

            if not trade_nos:
                self.logger.info("[余额支付查询] 没有有效的银行流水号")
                if progress_callback:
                    progress_callback("没有有效的银行流水号", 100)
                return 0, 0, []

            self.logger.info(f"[余额支付查询] 找到 {len(trade_nos)} 个银行流水号，开始查询API")

            # 批量查询API
            results = []
            success_count = 0
            writeback_success_count = 0
            total_count = len(trade_nos)

            for i, trade_no in enumerate(trade_nos, 1):
                try:
                    # 更新进度
                    if progress_callback:
                        progress = int((i / total_count) * 90)  # 0-90的进度，留10%给最终处理
                        progress_callback(f"查询进度: {i}/{total_count} - {trade_no}", progress)

                    # 查询单个结果
                    result = self.query_handler.query_balance_pay_result(trade_no)

                    # 获取对应的数据库记录
                    db_record = trade_no_to_record.get(trade_no)

                    result_item = {
                        'trade_no': trade_no,
                        'result': result,
                        'success': result.is_success() if hasattr(result, 'is_success') else False,
                        'billid': getattr(db_record, 'billid', 'N/A') if db_record else 'N/A',
                        'xpbillid': getattr(db_record, 'xpbillid', 'N/A') if db_record else 'N/A',
                        'writeback_success': False
                    }
                    results.append(result_item)

                    if result_item['success']:
                        success_count += 1

                        # 如果分账成功且需要自动回写，执行回写操作
                        if auto_writeback and result.data and result.data.status == "1":
                            writeback_success = self._writeback_split_result(trade_no, result.data)
                            result_item['writeback_success'] = writeback_success
                            if writeback_success:
                                writeback_success_count += 1

                    # 添加延时避免频繁请求
                    if i < total_count:
                        time.sleep(0.5)

                except Exception as e:
                    self.logger.error(f"[余额支付查询] 查询流水号 {trade_no} 失败: {str(e)}")
                    result_item = {
                        'trade_no': trade_no,
                        'result': BalancePayQueryResponse(
                            request_id="",
                            code=0,
                            msg=f"查询异常: {str(e)}",
                            success=False
                        ),
                        'success': False,
                        'billid': getattr(trade_no_to_record.get(trade_no), 'billid',
                                          'N/A') if trade_no in trade_no_to_record else 'N/A',
                        'xpbillid': getattr(trade_no_to_record.get(trade_no), 'xpbillid',
                                            'N/A') if trade_no in trade_no_to_record else 'N/A',
                        'writeback_success': False
                    }
                    results.append(result_item)

            # 最终进度更新
            if progress_callback:
                final_message = f"查询完成! 成功: {success_count}/{total_count}"
                if auto_writeback:
                    final_message += f", 回写成功: {writeback_success_count}"
                progress_callback(final_message, 100)

            self.logger.info(f"[余额支付查询] 批量查询完成: {success_count}/{total_count} 成功")
            if auto_writeback:
                self.logger.info(f"[余额支付查询] 回写完成: {writeback_success_count}/{success_count} 成功")

            return success_count, total_count, results

        except Exception as e:
            self.logger.error(f"[余额支付查询] 批量查询分账结果失败: {str(e)}")
            if progress_callback:
                progress_callback(f"查询失败: {str(e)}", 0)
            return 0, 0, []

    def batch_writeback_results(self, results: List[Dict]) -> Tuple[int, int]:
        """
        批量回写查询结果到数据库

        Args:
            results: 查询结果列表

        Returns:
            Tuple[int, int]: (成功回写数量, 总数量)
        """
        self.logger.info(f"[余额支付查询] 开始批量回写结果，共 {len(results)} 条记录")

        success_count = 0
        total_count = 0

        for result_item in results:
            if not result_item.get('success'):
                continue

            result = result_item.get('result')
            if not result or not result.data or result.data.status != "1":
                continue

            trade_no = result_item.get('trade_no')
            if not trade_no:
                continue

            total_count += 1

            try:
                if self._writeback_split_result(trade_no, result.data):
                    success_count += 1
                    result_item['writeback_success'] = True
                else:
                    result_item['writeback_success'] = False

            except Exception as e:
                self.logger.error(f"[余额支付查询] 回写记录失败 {trade_no}: {str(e)}")
                result_item['writeback_success'] = False

        self.logger.info(f"[余额支付查询] 批量回写完成: {success_count}/{total_count} 成功")
        return success_count, total_count

    def _writeback_split_result(self, trade_no: str, data: BalancePayQueryData) -> bool:
        """
        回写分账结果到数据库

        Args:
            trade_no: 银行流水号
            data: 查询结果数据

        Returns:
            bool: 回写是否成功
        """
        try:
            self.logger.info(f"[余额支付查询] 开始回写分账结果: {trade_no}")

            connection = cx_Oracle.connect(
                user=self.db_user,
                password=self.db_password,
                dsn=self.db_dsn,
                encoding="UTF-8"
            )

            cursor = connection.cursor()

            # 首先根据银行流水号查找对应的记录
            # 这里使用与原始查询相同的逻辑来匹配记录
            find_record_sql = self.query_sql + " AND ROWNUM = 1"

            cursor.execute(find_record_sql)
            record_row = cursor.fetchone()

            if not record_row:
                self.logger.warning(f"[余额支付查询] 未找到对应的数据库记录: {trade_no}")
                cursor.close()
                connection.close()
                return False

            # 获取billid和xpbillid用于更新
            billid = str(record_row[0]) if record_row[0] else ""
            xpbillid = str(record_row[1]) if record_row[1] else ""

            if not billid or not xpbillid:
                self.logger.warning(f"[余额支付查询] 记录缺少必要字段 billid={billid}, xpbillid={xpbillid}: {trade_no}")
                cursor.close()
                connection.close()
                return False

            # 执行回写SQL语句：根据billid和xpbillid更新
            writeback_sql = """
                UPDATE P_BL_SELL_PAYAMOUNT_HZ_dt 
                SET FZ_EXECUTE_RESULT = :result, 
                    EXECUTE_RESULT_CONFIRMTIME = TO_DATE(:confirm_time, 'YYYY-MM-DD HH24:MI:SS')
                WHERE billid = :billid 
                AND xpbillid = :xpbillid
            """

            # 准备参数
            result_value = "Y" if data.status == "1" else "N"  # Y表示成功，N表示失败
            confirm_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 执行更新
            cursor.execute(writeback_sql, {
                'result': result_value,
                'confirm_time': confirm_time,
                'billid': billid,
                'xpbillid': xpbillid
            })

            # 检查影响的行数
            rows_affected = cursor.rowcount

            # 提交事务
            connection.commit()

            cursor.close()
            connection.close()

            if rows_affected > 0:
                self.logger.info(
                    f"[余额支付查询] 回写分账结果成功: {trade_no} (billid={billid}, xpbillid={xpbillid}, 影响行数: {rows_affected})")
                return True
            else:
                self.logger.warning(
                    f"[余额支付查询] 回写分账结果失败，未找到对应记录: {trade_no} (billid={billid}, xpbillid={xpbillid})")
                return False

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            self.logger.error(f"[余额支付查询] 回写分账结果失败: ORA-{error.code}: {error.message}")
            return False
        except Exception as e:
            self.logger.error(f"[余额支付查询] 回写分账结果异常: {str(e)}")
            return False

    def batch_query_from_database(self) -> Dict[str, BalancePayQueryResponse]:
        """
        从数据库批量查询余额支付结果

        Returns:
            Dict[str, BalancePayQueryResponse]: 查询结果字典
        """
        self.logger.info("[余额支付查询] 开始从数据库批量查询交易结果")

        try:
            # 通知开始查询
            self._notify_progress("正在查询数据库记录...", 0)

            # 查询数据库记录
            db_records = self.query_pending_split_records(self.batch_size)

            if not db_records:
                self.logger.info("[余额支付查询] 没有找到待查询的交易记录")
                self._notify_progress("没有找到待查询的交易记录", 100)
                return {}

            # 提取银行流水号
            trade_nos = [record.get_trade_no() for record in db_records if record.get_trade_no()]

            if not trade_nos:
                self.logger.info("[余额支付查询] 没有有效的银行流水号")
                self._notify_progress("没有有效的银行流水号", 100)
                return {}

            self.logger.info(f"[余额支付查询] 找到 {len(trade_nos)} 个银行流水号，开始查询API")

            # 批量查询API
            self._notify_progress(f"正在查询 {len(trade_nos)} 个交易结果...", 10)

            results = {}
            success_count = 0
            writeback_success_count = 0
            total_count = len(trade_nos)

            for i, trade_no in enumerate(trade_nos, 1):
                try:
                    # 更新进度
                    progress = int(10 + (i / total_count) * 80)  # 10-90的进度
                    self._notify_progress(f"查询进度: {i}/{total_count} - {trade_no}", progress)

                    # 查询单个结果
                    result = self.query_handler.query_balance_pay_result(trade_no)
                    results[trade_no] = result

                    if result.is_success():
                        success_count += 1

                        # 如果分账成功，执行回写操作
                        if result.data and result.data.status == "1":
                            if self._writeback_split_result(trade_no, result.data):
                                writeback_success_count += 1

                        # 通知单个查询结果
                        self._notify_result('single_result', {
                            'seq': trade_no,
                            'result': result,
                            'index': i,
                            'total': total_count
                        })

                    # 添加延时避免频繁请求
                    if i < total_count:
                        time.sleep(0.5)

                except Exception as e:
                    self.logger.error(f"[余额支付查询] 查询流水号 {trade_no} 失败: {str(e)}")
                    results[trade_no] = BalancePayQueryResponse(
                        request_id="",
                        code=0,
                        msg=f"查询异常: {str(e)}",
                        success=False
                    )

            # 完成查询
            final_message = f"查询完成! 成功: {success_count}, 总数: {total_count}, 回写成功: {writeback_success_count}"
            self._notify_progress(final_message, 100)

            # 通知批量查询完成
            self._notify_result('batch_complete', {
                'results': results,
                'success_count': success_count,
                'total_count': total_count,
                'writeback_success_count': writeback_success_count,
                'db_records': db_records  # 添加数据库记录信息
            })

            self.logger.info(
                f"[余额支付查询] 批量查询完成，成功: {success_count}/{total_count}, 回写成功: {writeback_success_count}")

            return results

        except Exception as e:
            self.logger.error(f"[余额支付查询] 批量查询失败: {str(e)}")
            self._notify_progress(f"查询失败: {str(e)}", 0)
            return {}

    def start_auto_query(self):
        """启动自动查询"""
        if self.auto_query_running:
            self.logger.warning("[余额支付查询] 自动查询已在运行")
            return

        self.auto_query_running = True
        self.auto_query_thread = threading.Thread(target=self._auto_query_worker, daemon=True)
        self.auto_query_thread.start()

        self.logger.info(f"[余额支付查询] 自动查询已启动，间隔: {self.auto_query_interval}分钟")
        self._notify_result('auto_status', {'status': 'started', 'interval': self.auto_query_interval})

    def stop_auto_query(self):
        """停止自动查询"""
        if not self.auto_query_running:
            self.logger.warning("[余额支付查询] 自动查询未在运行")
            return

        self.auto_query_running = False

        if self.auto_query_thread:
            self.auto_query_thread.join(timeout=5)

        self.logger.info("[余额支付查询] 自动查询已停止")
        self._notify_result('auto_status', {'status': 'stopped'})

    def _auto_query_worker(self):
        """自动查询工作线程"""
        self.logger.info("[余额支付查询] 自动查询工作线程启动")

        while self.auto_query_running:
            try:
                # 执行查询（包含自动回写）
                self.logger.info("[余额支付查询] 执行定时自动查询")
                results = self.batch_query_from_database()

                # 通知自动查询结果
                self._notify_result('auto_query_result', {
                    'timestamp': datetime.now(),
                    'results_count': len(results),
                    'results': results
                })

                # 等待下次查询
                wait_seconds = self.auto_query_interval * 60
                for i in range(wait_seconds):
                    if not self.auto_query_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"[余额支付查询] 自动查询异常: {str(e)}")
                # 出错后等待较短时间再重试
                time.sleep(30)

        self.logger.info("[余额支付查询] 自动查询工作线程退出")

    def is_auto_query_running(self) -> bool:
        """检查自动查询是否在运行"""
        return self.auto_query_running

    def get_statistics(self) -> dict:
        """获取统计信息"""
        try:
            # 查询数据库统计
            db_records = self.query_pending_split_records()
            total_records = len(db_records)
            valid_records = len([r for r in db_records if r.has_trade_no()])  # 更新为银行流水号检查

            return {
                'total_records': total_records,
                'valid_records': valid_records,
                'invalid_records': total_records - valid_records,
                'auto_query_running': self.auto_query_running,
                'query_interval': self.auto_query_interval,
                'batch_size': self.batch_size,
                'environment': Config.get_env_name(),
                'last_update': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"[余额支付查询] 获取统计信息失败: {str(e)}")
            return {
                'error': str(e),
                'last_update': datetime.now()
            }


if __name__ == '__main__':
    """测试余额支付查询演示"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🧪 测试余额支付查询演示")

    # 创建演示实例
    demo = SplitQueryDemo()

    # 测试数据库连接
    print("\n🔍 测试数据库连接:")
    db_ok = demo.test_database_connection()
    print(f"数据库连接: {'✅ 成功' if db_ok else '❌ 失败'}")

    if db_ok:
        # 获取统计信息
        print("\n📊 获取统计信息:")
        stats = demo.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 测试查询数据库记录
        print(f"\n📋 查询数据库记录 (限制前5条):")
        records = demo.query_pending_split_records(5)
        for i, record in enumerate(records, 1):
            print(f"  {i}. {record.xpbillid} -> {record.get_trade_no()}")

        # 如果在测试环境，可以测试API查询
        if not Config.USE_PRODUCTION and records:
            print(f"\n🌐 测试API查询 (使用第一条记录):")
            first_record = records[0]
            if first_record.has_trade_no():
                result, db_record = demo.query_single_split_result(first_record.get_trade_no())
                print(f"查询结果: {demo.query_handler.format_query_result_summary(result)}")
                if db_record:
                    print(f"数据库记录: billid={db_record.billid}, xpbillid={db_record.xpbillid}")

    print("✅ 余额支付查询演示测试完成")