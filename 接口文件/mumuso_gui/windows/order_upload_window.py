#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
订单上传功能窗口
从原OrderUploadTab重构而来
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # windows/
project_root = os.path.dirname(current_dir)  # 项目根目录

sys.path.insert(0, project_root)

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# 尝试导入schedule库
try:
    import schedule
except ImportError:
    schedule = None

# 根据实际目录结构导入模块
try:
    # 从项目根目录导入
    from order_upload_demo import OrderUploadDemo
except ImportError:
    print("警告: 无法导入 OrderUploadDemo，使用模拟实现")


    class OrderUploadDemo:
        def __init__(self, logger=None):
            self.logger = logger

        def get_database_connection(self):
            print("OrderUploadDemo: 模拟数据库连接")
            return None

        def get_orders_from_database(self):
            print("OrderUploadDemo: 模拟获取订单数据")
            return []

        def get_order_by_id(self, order_id):
            print(f"OrderUploadDemo: 模拟查询订单 {order_id}")
            return None

        def upload_single_order(self, order):
            print("OrderUploadDemo: 模拟上传单个订单")
            return False

        def batch_upload_orders(self, progress_callback=None):
            print("OrderUploadDemo: 模拟批量上传订单")
            return 0, 0, []

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

        def get_app_id(self):
            return "test_app_id"

        def get_node_id(self):
            return "test_node_id"


    config_adapter = ConfigAdapter()

try:
    # 从utils目录导入BaseWindow
    from utils.base_window import BaseWindow

    print("成功导入 BaseWindow")
except ImportError:
    print("警告: 无法导入 BaseWindow，使用本地实现")
    # 提供本地BaseWindow实现
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

        def __init__(self, parent, title, size="800x600", log_queue=None):
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

                        # 测试LogHandler是否工作
                        print(f"[DEBUG] 测试LogHandler...")
                        test_message = f"[{self.logger_name}] LogHandler测试消息"
                        self.logger.info(test_message)
                        print(f"[DEBUG] 测试消息已发送: {test_message}")

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
            env_frame = ttk.LabelFrame(parent, text="🌐 环境信息", padding=10)
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

        def debug_log_system(self):
            print("\n" + "=" * 50)
            print("开始日志系统调试")
            print("=" * 50)
            print(f"1. self.log_queue 存在: {hasattr(self, 'log_queue')}")
            print(f"   self.log_queue 不为None: {getattr(self, 'log_queue', None) is not None}")
            print(f"2. self.logger 存在: {hasattr(self, 'logger')}")
            print(f"   self.logger 不为None: {getattr(self, 'logger', None) is not None}")

            if hasattr(self, 'logger') and self.logger:
                print(f"   logger handlers数量: {len(self.logger.handlers)}")
                for i, handler in enumerate(self.logger.handlers):
                    print(f"   handler[{i}]: {type(handler).__name__}")

            if hasattr(self, 'log_queue') and self.log_queue:
                print(f"3. 当前队列大小: {self.log_queue.qsize()}")
                test_message = {
                    'level': 'INFO',
                    'message': '[订单上传] 直接队列测试消息 - ' + datetime.now().strftime('%H:%M:%S'),
                    'module': '订单上传',
                    'time': datetime.now().strftime('%H:%M:%S')
                }
                self.log_queue.put(test_message)
                print(f"   直接放入队列后的大小: {self.log_queue.qsize()}")

            if hasattr(self, 'logger') and self.logger:
                print("4. 测试logger各级别日志:")
                self.logger.info("[订单上传] INFO级别测试日志")
                self.logger.warning("[订单上传] WARNING级别测试日志")
                self.logger.error("[订单上传] ERROR级别测试日志")

            print("5. 测试update_status方法:")
            self.update_status("调试测试 - 信息级别", 'info')
            self.update_status("调试测试 - 警告级别", 'warning')
            self.update_status("调试测试 - 错误级别", 'error')
            self.update_status("调试测试 - 成功级别", 'success')

            print("=" * 50)
            print("日志系统调试完成")
            print("=" * 50 + "\n")


class OrderUploadWindow(BaseWindow):
    """订单上传功能窗口"""

    def __init__(self, parent, title="📦 订单上传管理", size="900x700", log_queue=None):
        self.upload_demo = OrderUploadDemo()
        self.is_auto_running = False
        self.auto_thread = None
        self.order_data = {}  # 存储订单数据
        self.module_name = "订单上传"

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="📦 订单上传管理", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        env_frame = self.create_env_info_frame(main_frame)
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

        # 订单明细框架
        orders_frame = ttk.LabelFrame(main_frame, text="📄 待上传订单明细", padding=10)
        orders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.setup_orders_tree(orders_frame)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(buttons_frame, text="🔍 查看待上传订单",
                   command=self.show_pending_orders, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🚀 批量上传订单",
                   command=self.batch_upload_orders, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📝 测试日志功能",
                   command=self.test_logging, width=20).pack(side=tk.LEFT, padx=5)

        # 单个订单上传区域
        single_frame = ttk.Frame(parent)
        single_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(single_frame, text="单个订单上传:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_input_frame, text="订单号(xpbillid):").pack(side=tk.LEFT)
        self.single_order_var = tk.StringVar()
        ttk.Entry(single_input_frame, textvariable=self.single_order_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(single_input_frame, text="📤 上传此订单",
                   command=self.upload_single_order, width=15).pack(side=tk.LEFT, padx=5)

    def setup_auto_execution(self, parent):
        """设置自动执行"""
        # 时间设置
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(time_frame, text="每日执行时间:").pack(side=tk.LEFT)
        self.auto_hour_var = tk.StringVar(value="04")
        self.auto_minute_var = tk.StringVar(value="00")

        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.auto_hour_var,
                    width=3, format="%02.0f").pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.auto_minute_var,
                    width=3, format="%02.0f").pack(side=tk.LEFT, padx=5)

        # 自动执行控制
        auto_control_frame = ttk.Frame(parent)
        auto_control_frame.pack(fill=tk.X, pady=5)

        self.auto_status_var = tk.StringVar(value="ℹ️ 自动执行已停止")
        ttk.Label(auto_control_frame, textvariable=self.auto_status_var).pack(side=tk.LEFT)

        ttk.Button(auto_control_frame, text="▶️ 启动自动执行",
                   command=self.start_auto_execution).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(auto_control_frame, text="⏹️ 停止自动执行",
                   command=self.stop_auto_execution).pack(side=tk.RIGHT)

    def setup_orders_tree(self, parent):
        """设置订单树形表格"""
        # 创建Treeview显示订单
        columns = (
            'order_id', 'payment_method', 'amount', 'order_time', 'merchant_id', 'store_id', 'status', 'update_time')
        self.orders_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)

        # 设置列标题和宽度
        self.orders_tree.heading('order_id', text='订单号')
        self.orders_tree.heading('payment_method', text='支付方式')
        self.orders_tree.heading('amount', text='金额(元)')
        self.orders_tree.heading('order_time', text='支付时间')
        self.orders_tree.heading('merchant_id', text='商户号')
        self.orders_tree.heading('store_id', text='门店ID')
        self.orders_tree.heading('status', text='上传状态')
        self.orders_tree.heading('update_time', text='状态更新时间')

        self.orders_tree.column('order_id', width=150, minwidth=120)
        self.orders_tree.column('payment_method', width=80, minwidth=80)
        self.orders_tree.column('amount', width=80, minwidth=80)
        self.orders_tree.column('order_time', width=120, minwidth=120)
        self.orders_tree.column('merchant_id', width=120, minwidth=100)
        self.orders_tree.column('store_id', width=80, minwidth=80)
        self.orders_tree.column('status', width=100, minwidth=80)
        self.orders_tree.column('update_time', width=120, minwidth=120)

        # 添加滚动条
        orders_scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.orders_tree.yview)
        orders_scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=orders_scrollbar_y.set, xscrollcommand=orders_scrollbar_x.set)

        # 布局
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        orders_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        orders_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置不同状态的颜色
        self.orders_tree.tag_configure('pending', foreground='blue')  # 待上传
        self.orders_tree.tag_configure('uploading', foreground='orange')  # 上传中
        self.orders_tree.tag_configure('success', foreground='green')  # 成功
        self.orders_tree.tag_configure('failed', foreground='red')  # 失败

        # 双击查看详细信息
        self.orders_tree.bind('<Double-1>', self.show_order_detail)

        # 添加清空按钮
        clear_frame = ttk.Frame(parent)
        clear_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(clear_frame, text="🗑️ 清空内容", command=self.clear_orders_tree).pack(side=tk.RIGHT)

    def setup_logger(self):
        """设置日志系统"""
        super().setup_logger()
        # 重新创建upload_demo实例，传入logger
        self.upload_demo = OrderUploadDemo(logger=self.logger)

    def debug_log_system(self):
        """调试日志系统"""
        print("\n" + "=" * 50)
        print("开始日志系统调试")
        print("=" * 50)

        # 检查基本属性
        print(f"1. self.log_queue 存在: {hasattr(self, 'log_queue')}")
        print(f"   self.log_queue 不为None: {getattr(self, 'log_queue', None) is not None}")

        print(f"2. self.logger 存在: {hasattr(self, 'logger')}")
        print(f"   self.logger 不为None: {getattr(self, 'logger', None) is not None}")

        if hasattr(self, 'logger') and self.logger:
            print(f"   logger handlers数量: {len(self.logger.handlers)}")
            for i, handler in enumerate(self.logger.handlers):
                print(f"   handler[{i}]: {type(handler).__name__}")

        # 测试队列
        if hasattr(self, 'log_queue') and self.log_queue:
            print(f"3. 当前队列大小: {self.log_queue.qsize()}")

            # 直接向队列放入测试消息
            test_message = {
                'level': 'INFO',
                'message': '[订单上传] 直接队列测试消息 - ' + datetime.now().strftime('%H:%M:%S'),
                'module': '订单上传',
                'time': datetime.now().strftime('%H:%M:%S')
            }
            self.log_queue.put(test_message)
            print(f"   直接放入队列后的大小: {self.log_queue.qsize()}")

        # 测试logger
        if hasattr(self, 'logger') and self.logger:
            print("4. 测试logger各级别日志:")
            self.logger.info("[订单上传] INFO级别测试日志")
            self.logger.warning("[订单上传] WARNING级别测试日志")
            self.logger.error("[订单上传] ERROR级别测试日志")

        # 测试update_status方法
        print("5. 测试update_status方法:")
        self.update_status("调试测试 - 信息级别", 'info')
        self.update_status("调试测试 - 警告级别", 'warning')
        self.update_status("调试测试 - 错误级别", 'error')
        self.update_status("调试测试 - 成功级别", 'success')

        print("=" * 50)
        print("日志系统调试完成")
        print("=" * 50 + "\n")

    def test_database(self):
        """测试数据库连接"""

        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                connection = self.upload_demo.get_database_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM P_BL_SELL_PAYAMOUNT_HZ_dt WHERE ROWNUM <= 1")
                    result = cursor.fetchone()
                    cursor.close()
                    connection.close()
                    self.update_status("数据库连接测试成功", 'success')
                    self.show_message_box("成功", "数据库连接测试成功！", 'info')
                else:
                    self.update_status("数据库连接失败", 'error')
                    self.show_message_box("错误", "数据库连接失败！", 'error')
            except Exception as e:
                self.update_status(f"数据库测试异常: {str(e)}", 'error')
                self.show_message_box("错误", f"数据库测试异常: {str(e)}", 'error')

        self.run_in_thread(test_in_thread)

    def test_logging(self):
        """测试日志功能 - 增强调试版"""

        def test_logs():
            # 先进行系统调试
            self.debug_log_system()

            try:
                self.update_status("开始日志功能测试", 'info')
                time.sleep(1)

                # 测试不同级别的日志
                levels = ['info', 'warning', 'error', 'success']
                for level in levels:
                    message = f"这是{level}级别的测试日志"
                    self.update_status(message, level)
                    print(f"[DEBUG] 发送了{level}级别日志: {message}")
                    time.sleep(0.5)

                # 测试直接使用logger
                if hasattr(self, 'logger') and self.logger:
                    self.logger.info("[订单上传] 直接使用logger测试")
                    self.logger.warning("[订单上传] 这是warning日志")
                    self.logger.error("[订单上传] 这是error日志")

                # 再次检查队列状态
                if hasattr(self, 'log_queue') and self.log_queue:
                    print(f"[DEBUG] 测试后队列大小: {self.log_queue.qsize()}")

                self.update_status("日志功能测试完成", 'success')
                self.show_message_box("测试完成",
                                      "日志功能测试已完成\n请检查:\n1. 主界面日志显示\n2. 控制台调试信息", 'info')

            except Exception as e:
                error_msg = f"日志测试异常: {str(e)}"
                print(f"[DEBUG] {error_msg}")
                import traceback
                traceback.print_exc()
                self.update_status(error_msg, 'error')

        self.run_in_thread(test_logs)

    def clear_orders_tree(self):
        """清空订单表格内容"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        self.order_data.clear()
        self.update_status("订单表格内容已清空", 'info')

    def add_order_to_tree(self, order):
        """向订单树中添加订单"""
        order_id = order['order_id']
        payment_method = order['payment_method']
        amount = f"{order['pay_money']:.2f}"
        order_time = order['order_time']
        merchant_id = order['merchant_id']
        store_id = order['store_id']
        status = "待上传"
        update_time = datetime.now().strftime('%H:%M:%S')

        # 添加到树中
        item_id = self.orders_tree.insert('', tk.END, values=(
            order_id,
            payment_method,
            amount,
            order_time,
            merchant_id,
            store_id,
            status,
            update_time
        ), tags=('pending',))

        # 保存订单数据
        self.order_data[item_id] = {
            'order': order,
            'status': status,
            'update_time': update_time
        }

        # 自动滚动到底部
        children = self.orders_tree.get_children()
        if children:
            self.orders_tree.see(children[-1])

    def update_order_status(self, order_id, status):
        """更新订单状态"""
        # 查找对应的表格项
        for item_id in self.orders_tree.get_children():
            item_values = self.orders_tree.item(item_id, 'values')
            if item_values[0] == order_id:  # 匹配订单号
                # 更新状态和时间
                update_time = datetime.now().strftime('%H:%M:%S')
                new_values = list(item_values)
                new_values[6] = status  # 更新状态
                new_values[7] = update_time  # 更新时间

                # 确定标签
                tag = 'pending'
                if status == "待上传":
                    tag = 'pending'
                elif status == "上传中":
                    tag = 'uploading'
                elif status == "上传成功":
                    tag = 'success'
                elif status == "上传失败":
                    tag = 'failed'

                # 更新表格项
                self.orders_tree.item(item_id, values=new_values, tags=(tag,))

                # 更新保存的数据
                if item_id in self.order_data:
                    self.order_data[item_id]['status'] = status
                    self.order_data[item_id]['update_time'] = update_time
                break

    def show_pending_orders(self):
        """显示待上传订单"""

        def show_in_thread():
            self.update_status("正在查询待上传订单...", 'info')
            try:
                orders = self.upload_demo.get_orders_from_database()
                if orders:
                    # 清空现有内容
                    self.clear_orders_tree()

                    # 添加订单到表格
                    for order in orders:
                        self.add_order_to_tree(order)

                    self.update_status(f"查询完成: 找到 {len(orders)} 笔待上传订单", 'success')
                    self.show_message_box("查询结果", f"找到 {len(orders)} 笔待上传订单，已在表格中显示", 'info')
                else:
                    self.update_status("没有找到待上传的订单", 'info')
                    self.show_message_box("查询结果", "没有找到待上传的订单", 'info')
            except Exception as e:
                self.update_status(f"查询订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询订单异常: {str(e)}", 'error')

        self.run_in_thread(show_in_thread)

    def show_order_detail(self, event):
        """显示订单详细信息"""
        selection = self.orders_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        if item_id not in self.order_data:
            return

        order_data = self.order_data[item_id]['order']

        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"订单详情 - {order_data['order_id']}")
        detail_window.geometry("500x400")
        detail_window.transient(self.window)
        detail_window.grab_set()

        # 详情信息
        detail_frame = ttk.Frame(detail_window, padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(detail_frame, text="订单详细信息", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # 创建信息展示
        info_text = f"""订单号: {order_data['order_id']}
支付方式: {order_data['payment_method']}
支付金额: {order_data['pay_money']:.2f}元
支付时间: {order_data['order_time']}
商户号: {order_data['merchant_id']}
门店ID: {order_data['store_id']}
业务单号: {order_data['billid']}
支付类型代码: {order_data['pay_type']}
订单金额(分): {order_data['order_amount']}"""

        text_widget = tk.Text(detail_frame, wrap=tk.WORD, height=12)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

        # 添加滚动条
        text_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=text_scrollbar.set)

        ttk.Button(detail_window, text="关闭",
                   command=detail_window.destroy).pack(pady=5)

    def upload_single_order(self):
        """上传单个订单"""
        order_id = self.single_order_var.get().strip()
        if not order_id:
            self.show_message_box("警告", "请输入订单号！", 'warning')
            return

        def upload_in_thread():
            self.update_status(f"正在上传订单: {order_id}", 'info')
            try:
                # 先查询此订单
                target_order = self.upload_demo.get_order_by_id(order_id)

                if target_order:
                    # 更新表格状态
                    self.update_order_status(order_id, "上传中")

                    success = self.upload_demo.upload_single_order(target_order)
                    if success:
                        self.update_status(f"订单 {order_id} 上传成功", 'success')
                        self.update_order_status(order_id, "上传成功")
                        self.show_message_box("成功", f"订单 {order_id} 上传成功！", 'info')
                        # 清空输入框
                        self.single_order_var.set("")
                    else:
                        self.update_status(f"订单 {order_id} 上传失败", 'error')
                        self.update_order_status(order_id, "上传失败")
                        self.show_message_box("失败", f"订单 {order_id} 上传失败！", 'error')
                else:
                    self.update_status(f"未找到订单: {order_id}", 'warning')
                    self.show_message_box("警告", f"未找到订单: {order_id}", 'warning')

            except Exception as e:
                self.update_status(f"上传订单异常: {str(e)}", 'error')
                self.update_order_status(order_id, "上传失败")
                self.show_message_box("错误", f"上传订单异常: {str(e)}", 'error')

        self.run_in_thread(upload_in_thread)

    def batch_upload_orders(self):
        """批量上传订单"""
        # 检查是否有待上传订单
        if not self.order_data:
            self.show_message_box("警告", "请先查询待上传订单！", 'warning')
            return

        result = self.show_message_box("确认", "确认要批量上传所有待处理订单吗？", 'question')
        if not result:
            return

        def upload_in_thread():
            self.update_status("开始批量上传订单...", 'info')
            self.progress_var.set(0)

            def progress_callback(current, total, message):
                progress = (current / total) * 100
                self.progress_var.set(progress)
                self.update_status(f"处理进度: {current}/{total} - {message}", 'info')

            try:
                success_count, total_count, failed_orders = self.upload_demo.batch_upload_orders(
                    progress_callback=progress_callback)

                self.progress_var.set(100)
                success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                summary = f"批量上传完成\n总订单数: {total_count}\n成功: {success_count}\n失败: {len(failed_orders)}\n成功率: {success_rate:.1f}%"

                self.update_status(f"批量上传完成: {success_count}/{total_count} 成功", 'success')
                self.show_message_box("完成", summary, 'info')

            except Exception as e:
                self.update_status(f"批量上传异常: {str(e)}", 'error')
                self.show_message_box("错误", f"批量上传异常: {str(e)}", 'error')

        self.run_in_thread(upload_in_thread)

    def start_auto_execution(self):
        """启动自动执行"""
        # 检查schedule是否可用
        if schedule is None:
            self.show_message_box("错误", "缺少schedule库，请先安装: pip install schedule", 'error')
            return

        if self.is_auto_running:
            self.show_message_box("信息", "自动执行已在运行中", 'info')
            return

        hour = int(self.auto_hour_var.get())
        minute = int(self.auto_minute_var.get())

        # 清除之前的调度
        if schedule:
            schedule.clear()

        # 设置新的调度
        if schedule:
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._auto_upload_job)

        self.is_auto_running = True
        self.auto_status_var.set(f"⏰ 自动执行已启动 - 每日 {hour:02d}:{minute:02d}")

        # 启动调度线程
        self.auto_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.auto_thread.start()

        self.update_status(f"自动执行已启动 - 每日 {hour:02d}:{minute:02d}", 'success')
        self.show_message_box("成功", f"自动执行已启动\n每日 {hour:02d}:{minute:02d} 自动批量上传订单", 'info')

    def stop_auto_execution(self):
        """停止自动执行"""
        # 检查schedule是否可用
        if schedule is None:
            return

        self.is_auto_running = False
        if schedule:
            schedule.clear()
        self.auto_status_var.set("ℹ️ 自动执行已停止")
        self.update_status("自动执行已停止", 'info')
        self.show_message_box("信息", "自动执行已停止", 'info')

    def _run_scheduler(self):
        """运行调度器"""
        # 检查schedule是否可用
        if schedule is None:
            return

        while self.is_auto_running:
            if schedule:
                schedule.run_pending()
            time.sleep(1)

    def _auto_upload_job(self):
        """自动上传任务"""
        self.update_status("自动任务开始执行", 'info')
        try:
            success_count, total_count, failed_orders = self.upload_demo.batch_upload_orders()
            if total_count > 0:
                self.update_status(f"自动任务完成: {success_count}/{total_count} 成功", 'success')
            else:
                self.update_status("自动任务完成: 没有待上传订单", 'info')
        except Exception as e:
            self.update_status(f"自动任务异常: {str(e)}", 'error')

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动执行
        if self.is_auto_running:
            self.stop_auto_execution()
        super().on_window_close()