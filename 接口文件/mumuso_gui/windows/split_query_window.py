#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账结果查询功能窗口
从原SplitQueryTab重构而来
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径 - 修复导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # windows/
project_root = os.path.dirname(current_dir)  # 项目根目录

sys.path.insert(0, project_root)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

# 尝试导入schedule库
try:
    import schedule
except ImportError:
    schedule = None

# 根据实际目录结构导入模块 - 修复导入问题
try:
    # 从项目根目录导入
    from split_query_demo import SplitQueryDemo
except ImportError:
    print("警告: 无法导入 SplitQueryDemo，使用模拟实现")


    class SplitQueryDemo:
        def __init__(self, logger=None):
            self.logger = logger

        def test_database_connection(self):
            print("SplitQueryDemo: 模拟数据库连接测试")
            return True

        def query_pending_split_records(self):
            print("SplitQueryDemo: 模拟查询待查询记录")
            return []

        def query_single_split_result(self, trade_no):
            print(f"SplitQueryDemo: 模拟查询单个结果 {trade_no}")
            return None, None

        def batch_query_split_results(self, progress_callback=None):
            print("SplitQueryDemo: 模拟批量查询")
            return 0, 0, []

        def batch_writeback_results(self, results):
            print("SplitQueryDemo: 模拟批量回写")
            return 0, 0

        def set_progress_callback(self, callback):
            pass

        def set_result_callback(self, callback):
            pass

try:
    # 从项目根目录导入配置适配器
    from config_adapter import config_adapter
except ImportError:
    print("警告: 无法导入 config_adapter，使用模拟实现")


    class ConfigAdapter:
        def get_env_name(self):
            return "开发环境"

        def get_api_url(self):
            return "http://localhost:8080"

        def get_balance_pay_query_node_id(self):
            return "test_node_id"

        def get_auto_query_interval(self):
            return 5


    config_adapter = ConfigAdapter()

try:
    # 从utils目录导入BaseWindow
    from utils.base_window import BaseWindow

    print("成功导入 BaseWindow")
except ImportError:
    print("警告: 无法导入 BaseWindow，使用本地实现")
    # 提供本地BaseWindow实现（与order_upload_window.py中相同的实现）
    import logging


    class LogHandler(logging.Handler):
        """简单的日志处理器"""

        def __init__(self, log_queue):
            super().__init__()
            self.log_queue = log_queue
            print(f"[DEBUG] LogHandler.__init__() - log_queue: {log_queue is not None}")

        def emit(self, record):
            try:
                print(f"[DEBUG] LogHandler.emit() 开始 - 记录: {record.getMessage()}")
                log_entry = self.format(record)
                print(f"[DEBUG] 格式化后的日志: {log_entry}")

                # 从日志消息中提取模块名
                module_name = "系统"
                if '[订单上传]' in log_entry:
                    module_name = "订单上传"
                elif '[余额查询]' in log_entry:
                    module_name = "余额查询"
                elif '[账户余额查询]' in log_entry:
                    module_name = "账户余额查询"
                elif '[分账管理]' in log_entry:
                    module_name = "分账管理"
                elif '[挂账充值]' in log_entry:
                    module_name = "挂账充值"
                elif '[分账结果查询]' in log_entry:
                    module_name = "分账结果查询"
                elif '[配置管理]' in log_entry:
                    module_name = "配置管理"

                print(f"[DEBUG] 提取的模块名: {module_name}")

                log_dict = {
                    'level': record.levelname,
                    'message': log_entry,
                    'module': module_name,
                    'time': datetime.now().strftime('%H:%M:%S')
                }

                print(f"[DEBUG] 准备放入队列的日志字典: {log_dict}")

                if self.log_queue:
                    self.log_queue.put(log_dict)
                    print(f"[DEBUG] 日志已放入队列，当前队列大小: {self.log_queue.qsize()}")
                else:
                    print(f"[DEBUG] log_queue为None，无法放入队列")

            except Exception as e:
                print(f"[DEBUG] LogHandler.emit() 发生异常: {e}")
                import traceback
                traceback.print_exc()


    class BaseWindow:
        """本地BaseWindow实现"""

        def __init__(self, parent, title, size="100x900", log_queue=None):
            self.parent = parent
            self.log_queue = log_queue
            self.window = None
            self.title = title
            self.size = size
            self.is_initialized = False
            self.is_visible = False
            print(f"[DEBUG] BaseWindow初始化 - log_queue: {log_queue is not None}")

        def create_window(self):
            if self.window is not None:
                self.show_window()
                return

            self.window = tk.Toplevel(self.parent)
            self.window.title(self.title)
            self.window.geometry(self.size)
            self.window.transient(self.parent)
            self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)

            self.setup_ui()
            self.setup_logger()

            self.is_initialized = True
            self.is_visible = True

        def setup_ui(self):
            pass

        def setup_logger(self):
            print(f"[DEBUG] BaseWindow.setup_logger() 开始 - 类名: {self.__class__.__name__}")

            if not hasattr(self, 'logger_name'):
                self.logger_name = self.__class__.__name__

            print(f"[DEBUG] logger_name: {self.logger_name}")
            print(f"[DEBUG] log_queue 是否存在: {self.log_queue is not None}")

            self.logger = logging.getLogger(self.logger_name)
            self.logger.setLevel(logging.DEBUG)

            if self.log_queue:
                print(f"[DEBUG] 开始设置LogHandler")
                existing_handlers = [h for h in self.logger.handlers if isinstance(h, LogHandler)]
                print(f"[DEBUG] 现有LogHandler数量: {len(existing_handlers)}")

                if not existing_handlers:
                    try:
                        print(f"[DEBUG] 创建新的LogHandler")
                        handler = LogHandler(self.log_queue)
                        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                        handler.setFormatter(formatter)
                        self.logger.addHandler(handler)
                        print(f"[DEBUG] LogHandler创建成功，添加到logger")

                    except Exception as e:
                        print(f"[DEBUG] 设置日志处理器时发生错误: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[DEBUG] LogHandler已存在，跳过创建")
            else:
                print(f"[DEBUG] log_queue为None，不设置LogHandler")

            print(f"[DEBUG] setup_logger完成，logger handlers: {len(self.logger.handlers)}")

        def show_window(self):
            if self.window is None:
                self.create_window()
            else:
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
                self.is_visible = True

        def hide_window(self):
            if self.window:
                self.window.withdraw()
                self.is_visible = False

        def on_window_close(self):
            self.hide_window()

        def destroy_window(self):
            if self.window:
                self.window.destroy()
                self.window = None
                self.is_initialized = False
                self.is_visible = False

        def update_status(self, message, level='info'):
            timestamp = datetime.now().strftime('%H:%M:%S')

            if hasattr(self, 'status_var'):
                status_msg = f"[{timestamp}] {message}"
                self.status_var.set(status_msg)

            if hasattr(self, 'logger'):
                log_message = f"[{getattr(self, 'module_name', self.__class__.__name__)}] {message}"
                if level == 'info':
                    self.logger.info(log_message)
                elif level == 'warning':
                    self.logger.warning(log_message)
                elif level == 'error':
                    self.logger.error(log_message)
                elif level == 'success':
                    self.logger.info(f"[{getattr(self, 'module_name', self.__class__.__name__)}] ✅ {message}")

        def create_status_frame(self, parent):
            status_frame = ttk.LabelFrame(parent, text="📊 执行状态", padding=10)
            self.status_var = tk.StringVar(value="就绪状态 - 等待操作")
            ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10)).pack(anchor=tk.W)
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                                mode='determinate', length=400)
            self.progress_bar.pack(fill=tk.X, pady=5)
            return status_frame

        def create_env_info_frame(self, parent, additional_info=""):
            env_frame = ttk.LabelFrame(parent, text="🌍 环境信息", padding=10)
            env_info = f"当前环境: {config_adapter.get_env_name()} | API地址: {config_adapter.get_api_url()}"
            ttk.Label(env_frame, text=env_info).pack(anchor=tk.W)
            if additional_info:
                ttk.Label(env_frame, text=additional_info, foreground='blue').pack(anchor=tk.W)
            return env_frame

        def create_control_frame(self, parent, title="🎮 操作控制"):
            return ttk.LabelFrame(parent, text=title, padding=10)

        def show_message_box(self, title, message, msg_type='info'):
            if msg_type == 'info':
                messagebox.showinfo(title, message)
            elif msg_type == 'warning':
                messagebox.showwarning(title, message)
            elif msg_type == 'error':
                messagebox.showerror(title, message)
            elif msg_type == 'question':
                return messagebox.askyesno(title, message)

        def run_in_thread(self, target_func, *args, **kwargs):
            thread = threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            return thread


# 添加 SplitQueryWindow类定义
class SplitQueryWindow(BaseWindow):
    """分账结果查询功能窗口"""

    def __init__(self, parent, title="🔍 分账结果查询", size="1200x900", log_queue=None):
        self.query_demo = SplitQueryDemo()
        self.is_auto_running = False
        self.auto_thread = None
        self.module_name = "分账结果查询"
        self.current_results = []  # 保存当前批量查询结果
        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="🔍 分账结果查询", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        env_frame = self.create_env_info_frame(main_frame, "分账结果查询模块")
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 控制面板框架
        control_frame = self.create_control_frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.setup_control_panel(control_frame)

        # 自动执行设置
        auto_frame = ttk.LabelFrame(main_frame, text="⏰ 自动执行设置", padding=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))

        self.setup_auto_execution(auto_frame)

        # 状态信息框架
        status_frame = self.create_status_frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # 查询结果框架
        results_frame = ttk.LabelFrame(main_frame, text="📄 查询结果", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.setup_results_tree(results_frame)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        # 单个查询区域
        single_query_frame = ttk.Frame(manual_frame)
        single_query_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_query_frame, text="银行流水号:").pack(side=tk.LEFT)
        self.trade_no_var = tk.StringVar()
        ttk.Entry(single_query_frame, textvariable=self.trade_no_var, width=30).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(single_query_frame, text="🔍 单个查询", command=self.query_single_result).pack(side=tk.LEFT,
                                                                                                 padx=(0, 10))

        # 批量操作按钮框架
        btn_frame = ttk.Frame(manual_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="📋 查询待处理记录", command=self.query_pending_records).pack(side=tk.LEFT,
                                                                                                padx=(0, 10))
        ttk.Button(btn_frame, text="🔍 批量查询结果", command=self.batch_query_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="💾 批量回写结果", command=self.batch_writeback_results).pack(side=tk.LEFT,
                                                                                                padx=(0, 10))
        ttk.Button(btn_frame, text="🔄 刷新数据", command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 10))

        # 添加自动回写选项
        options_frame = ttk.Frame(manual_frame)
        options_frame.pack(fill=tk.X, pady=5)

        self.auto_writeback_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="自动回写成功的查询结果", variable=self.auto_writeback_var).pack(
            side=tk.LEFT)

    def setup_auto_execution(self, parent):
        """设置自动执行"""
        # 自动查询设置
        auto_settings_frame = ttk.Frame(parent)
        auto_settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(auto_settings_frame, text="自动查询间隔(分钟):").pack(side=tk.LEFT)
        self.auto_interval_var = tk.StringVar(value=str(config_adapter.get_auto_query_interval()))
        ttk.Entry(auto_settings_frame, textvariable=self.auto_interval_var, width=10).pack(side=tk.LEFT, padx=(5, 10))

        self.auto_start_btn = ttk.Button(auto_settings_frame, text="▶️ 开始自动查询", command=self.start_auto_execution)
        self.auto_start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.auto_stop_btn = ttk.Button(auto_settings_frame, text="⏹️ 停止自动查询", command=self.stop_auto_execution,
                                        state='disabled')
        self.auto_stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 显示当前状态
        self.auto_status_var = tk.StringVar(value="自动查询未启动")
        ttk.Label(auto_settings_frame, textvariable=self.auto_status_var, foreground='blue').pack(side=tk.LEFT)

    def setup_results_tree(self, parent):
        """设置结果树形控件"""
        # 创建Treeview
        columns = ('billid', 'xpbillid', '交易号', '分账金额', '支付方', '接受方', '状态', '回写状态', '时间')
        self.results_tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)

        # 设置列标题和宽度
        column_info = [
            ('billid', '账单ID', 100),
            ('xpbillid', '销售单号', 120),
            ('交易号', '银行流水号', 150),
            ('分账金额', '分账金额', 80),
            ('支付方', '支付方', 120),
            ('接受方', '接受方', 120),
            ('状态', '状态', 80),
            ('回写状态', '回写状态', 80),
            ('时间', '查询时间', 150)
        ]

        for col_id, col_name, width in column_info:
            self.results_tree.heading(col_id, text=col_name)
            self.results_tree.column(col_id, width=width)

        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 布局
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def query_pending_records(self):
        """查询待处理记录"""
        self.update_status("开始查询待处理分账记录...", 'info')
        self.run_in_thread(self._query_pending_records_thread)

    def _query_pending_records_thread(self):
        """查询待处理记录线程"""
        try:
            records = self.query_demo.query_pending_split_records()
            self.window.after(0, lambda: self._on_pending_records_complete(records))
        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"查询失败: {str(e)}", 'error'))

    def _on_pending_records_complete(self, records):
        """待处理记录查询完成"""
        self.update_status(f"查询完成，找到 {len(records)} 条待处理记录", 'success')
        self.display_pending_records(records)

    def display_pending_records(self, records):
        """显示待处理记录"""
        # 清空现有数据
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # 添加待处理记录数据
        for record in records:
            values = (
                getattr(record, 'billid', 'N/A'),
                getattr(record, 'xpbillid', 'N/A'),
                getattr(record, 'trade_no', 'N/A'),
                '待查询',  # 分账金额
                '待查询',  # 支付方
                '待查询',  # 接受方
                '待查询',  # 状态
                '未回写',  # 回写状态
                getattr(record, 'query_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') if getattr(record,
                                                                                                       'query_time',
                                                                                                       None) else 'N/A'
            )
            self.results_tree.insert('', tk.END, values=values)

    def batch_query_results(self):
        """批量查询结果"""
        self.update_status("开始批量查询分账结果...", 'info')
        auto_writeback = self.auto_writeback_var.get()
        self.run_in_thread(self._batch_query_results_thread, auto_writeback)

    def _batch_query_results_thread(self, auto_writeback):
        """批量查询结果线程"""
        try:
            # 设置进度回调
            def progress_callback(message, progress):
                self.window.after(0, lambda: self._update_progress(message, progress))

            self.query_demo.set_progress_callback(progress_callback)

            success_count, total_count, results = self.query_demo.batch_query_split_results(
                progress_callback, auto_writeback
            )

            self.current_results = results  # 保存结果供后续回写使用

            self.window.after(0, lambda: self._on_batch_query_complete(success_count, total_count, results,
                                                                       auto_writeback))
        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"批量查询失败: {str(e)}", 'error'))

    def _update_progress(self, message, progress):
        """更新进度"""
        self.progress_var.set(progress)
        self.update_status(message, 'info')

    def _on_batch_query_complete(self, success_count, total_count, results, auto_writeback):
        """批量查询完成"""
        if auto_writeback:
            writeback_count = sum(1 for r in results if r.get('writeback_success', False))
            self.update_status(f"批量查询完成: {success_count}/{total_count} 成功，{writeback_count} 条已回写",
                               'success')
        else:
            self.update_status(f"批量查询完成: {success_count}/{total_count} 成功", 'success')

        self.display_batch_results(results)

    def batch_writeback_results(self):
        """批量回写结果"""
        if not self.current_results:
            self.update_status("没有可回写的查询结果，请先执行批量查询", 'warning')
            return

        if self.show_message_box("确认回写",
                                 f"确定要回写 {len(self.current_results)} 条查询结果吗？",
                                 'question'):
            self.update_status("开始批量回写查询结果...", 'info')
            self.run_in_thread(self._batch_writeback_results_thread)

    def _batch_writeback_results_thread(self):
        """批量回写结果线程"""
        try:
            success_count, total_count = self.query_demo.batch_writeback_results(self.current_results)
            self.window.after(0, lambda: self._on_batch_writeback_complete(success_count, total_count))
        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"批量回写失败: {str(e)}", 'error'))

    def _on_batch_writeback_complete(self, success_count, total_count):
        """批量回写完成"""
        self.update_status(f"批量回写完成: {success_count}/{total_count} 成功", 'success')
        # 刷新显示
        self.display_batch_results(self.current_results)

    def refresh_data(self):
        """刷新数据"""
        self.update_status("刷新数据...", 'info')
        # 清空现有数据
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_results = []
        self.update_status("数据已清空", 'info')

    def query_single_result(self):
        """单个查询结果"""
        trade_no = self.trade_no_var.get().strip()
        if not trade_no:
            self.update_status("请输入银行流水号", 'warning')
            return

        auto_writeback = self.auto_writeback_var.get()
        self.update_status(f"开始查询交易结果: {trade_no}", 'info')
        self.run_in_thread(self._query_single_result_thread, trade_no, auto_writeback)

    def _query_single_result_thread(self, trade_no, auto_writeback):
        """单个查询结果线程"""
        try:
            # 设置进度回调
            def progress_callback(message, progress):
                self.window.after(0, lambda: self._update_progress(message, progress))

            self.query_demo.set_progress_callback(progress_callback)

            # 查询单个结果，返回元组 (api_result, db_record)
            api_result, db_record = self.query_demo.query_single_split_result(trade_no, auto_writeback=auto_writeback)

            self.window.after(0,
                              lambda: self._on_single_query_complete(trade_no, api_result, db_record, auto_writeback))

        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"查询异常: {str(e)}", 'error'))

    def _on_single_query_complete(self, trade_no, api_result, db_record, auto_writeback):
        """单个查询完成"""
        if api_result.is_success():
            message = f"查询成功: {trade_no}"
            if auto_writeback and api_result.data and api_result.data.status == "1":
                message += " (已自动回写)"
            self.update_status(message, 'success')
            # 显示单个结果
            self.display_single_result(trade_no, api_result, db_record, auto_writeback)
        else:
            self.update_status(f"查询失败: {api_result.get_error_message()}", 'error')
            # 显示失败结果
            self.display_single_result(trade_no, api_result, db_record, auto_writeback)

    def display_batch_results(self, results):
        """显示批量查询结果"""
        # 清空现有数据
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # 添加批量结果数据
        for result_item in results:
            if isinstance(result_item, dict):
                trade_no = result_item.get('trade_no', 'N/A')
                billid = result_item.get('billid', 'N/A')
                xpbillid = result_item.get('xpbillid', 'N/A')
                result = result_item.get('result')
                writeback_success = result_item.get('writeback_success', False)

                if result and hasattr(result, 'data') and result.data:
                    data = result.data
                    values = (
                        billid,
                        xpbillid,
                        trade_no,
                        f"{data.get_total_amount_yuan():.2f}元" if hasattr(data,
                                                                           'get_total_amount_yuan') and data.total_amount else "N/A",
                        getattr(data, 'payer_merchant_id', None) or "N/A",
                        getattr(data, 'payee_merchant_id', None) or "N/A",
                        getattr(data, 'get_status_text', lambda: data.status if hasattr(data, 'status') else 'N/A')(),
                        "已回写" if writeback_success else "未回写",
                        getattr(data, 'finish_time', None) or getattr(data, 'trade_time',
                                                                      None) or datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                    )
                    self.results_tree.insert('', tk.END, values=values)
                else:
                    # 如果没有详细数据，显示基本状态
                    status_text = "成功" if result and result.is_success() else "失败"
                    values = (
                        billid,
                        xpbillid,
                        trade_no,
                        "N/A",  # 分账金额
                        "N/A",  # 支付方
                        "N/A",  # 接受方
                        status_text,
                        "已回写" if writeback_success else "未回写",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    self.results_tree.insert('', tk.END, values=values)

    def display_single_result(self, trade_no, api_result, db_record, auto_writeback):
        """显示单个查询结果"""
        # 清空现有数据
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # 从数据库记录获取账单信息
        billid = getattr(db_record, 'billid', 'N/A') if db_record else 'N/A'
        xpbillid = getattr(db_record, 'xpbillid', 'N/A') if db_record else 'N/A'

        # 添加单个结果数据
        if api_result and hasattr(api_result, 'data') and api_result.data:
            data = api_result.data
            writeback_status = "已回写" if auto_writeback and data.status == "1" else "未回写"

            values = (
                billid,
                xpbillid,
                trade_no,
                f"{data.get_total_amount_yuan():.2f}元" if hasattr(data,
                                                                   'get_total_amount_yuan') and data.total_amount else "N/A",
                getattr(data, 'payer_merchant_id', None) or "N/A",
                getattr(data, 'payee_merchant_id', None) or "N/A",
                getattr(data, 'get_status_text', lambda: data.status if hasattr(data, 'status') else 'N/A')(),
                writeback_status,
                getattr(data, 'finish_time', None) or getattr(data, 'trade_time', None) or datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
            )
            self.results_tree.insert('', tk.END, values=values)
        else:
            # 如果没有详细数据，显示基本状态
            status_text = "成功" if api_result and api_result.is_success() else "失败"
            values = (
                billid,
                xpbillid,
                trade_no,
                "N/A",  # 分账金额
                "N/A",  # 支付方
                "N/A",  # 接受方
                status_text,
                "未回写",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            self.results_tree.insert('', tk.END, values=values)

    def start_auto_execution(self):
        """开始自动执行"""
        if self.is_auto_running:
            return

        try:
            interval = int(self.auto_interval_var.get())
            if interval <= 0:
                raise ValueError("间隔必须大于0")
        except ValueError as e:
            self.update_status(f"自动查询间隔设置错误: {str(e)}", 'error')
            return

        self.is_auto_running = True
        self.auto_start_btn.config(state='disabled')
        self.auto_stop_btn.config(state='normal')
        self.auto_status_var.set(f"自动查询运行中 (间隔: {interval}分钟)")

        # 启动自动查询线程
        self.auto_thread = self.run_in_thread(self._auto_query_loop)

        self.update_status(f"自动查询已启动，间隔 {interval} 分钟", 'success')

    def stop_auto_execution(self):
        """停止自动执行"""
        self.is_auto_running = False
        self.auto_start_btn.config(state='normal')
        self.auto_stop_btn.config(state='disabled')
        self.auto_status_var.set("自动查询已停止")
        self.update_status("自动查询已停止", 'info')

    def _auto_query_loop(self):
        """自动查询循环"""
        try:
            interval = int(self.auto_interval_var.get())
        except ValueError:
            interval = config_adapter.get_auto_query_interval()

        while self.is_auto_running:
            if self.is_auto_running:
                try:
                    # 执行自动批量查询（包含自动回写）
                    auto_writeback = self.auto_writeback_var.get()

                    def progress_callback(message, progress):
                        self.window.after(0, lambda: self._update_progress(message, progress))

                    self.query_demo.set_progress_callback(progress_callback)
                    success_count, total_count, results = self.query_demo.batch_query_split_results(
                        progress_callback, auto_writeback
                    )

                    # 更新界面
                    self.window.after(0, lambda: self._on_auto_query_complete(success_count, total_count, results,
                                                                              auto_writeback))

                except Exception as e:
                    self.window.after(0, lambda: self.update_status(f"自动查询异常: {str(e)}", 'error'))

            # 等待指定间隔
            for _ in range(interval * 60):  # 转换为秒
                if not self.is_auto_running:
                    break
                time.sleep(1)

    def _on_auto_query_complete(self, success_count, total_count, results, auto_writeback):
        """自动查询完成"""
        if auto_writeback:
            writeback_count = sum(1 for r in results if r.get('writeback_success', False))
            self.update_status(f"自动查询完成: {success_count}/{total_count} 成功，{writeback_count} 条已回写",
                               'success')
        else:
            self.update_status(f"自动查询完成: {success_count}/{total_count} 成功", 'success')

        self.current_results = results
        self.display_batch_results(results)

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动执行
        if self.is_auto_running:
            self.stop_auto_execution()
        super().on_window_close()