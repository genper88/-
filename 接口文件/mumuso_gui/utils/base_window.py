#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
基础窗口类
提供所有功能窗口的通用功能
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import logging


# LogHandler类定义 - 移到前面避免引用问题
class LogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到GUI"""

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
    """基础窗口类"""

    def __init__(self, parent, title, size="800x600", log_queue=None):
        self.parent = parent
        self.log_queue = log_queue
        self.window = None
        self.title = title
        self.size = size

        # 窗口状态
        self.is_initialized = False
        self.is_visible = False

    def create_window(self):
        """创建窗口"""
        if self.window is not None:
            # 窗口已存在，直接显示
            self.show_window()
            return

        # 创建新窗口
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry(self.size)
        self.window.transient(self.parent)

        # 设置窗口最小尺寸
        min_width, min_height = self._parse_size(self.size)
        self.window.minsize(int(min_width * 0.7), int(min_height * 0.7))

        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # 设置窗口图标（如果有的话）
        try:
            self.window.iconbitmap('icon.ico')
        except Exception:
            pass

        # 初始化UI
        self.setup_ui()
        self.setup_logger()

        self.is_initialized = True
        self.is_visible = True

        # 将窗口居中显示
        self._center_window()

    def _parse_size(self, size_str):
        """解析尺寸字符串"""
        try:
            width, height = size_str.split('x')
            return int(width), int(height)
        except Exception:
            return 800, 600

    def _center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()

        # 获取窗口尺寸
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def setup_ui(self):
        """设置UI界面 - 子类需要重写"""
        pass

    def setup_logger(self):
        """设置日志系统 - 子类可以重写"""
        if not hasattr(self, 'logger_name'):
            self.logger_name = self.__class__.__name__

        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.DEBUG)

        # 添加自定义处理器（如果有log_queue的话）
        if self.log_queue and not any(isinstance(h, LogHandler) for h in self.logger.handlers):
            try:
                # 直接使用本地定义的LogHandler
                handler = LogHandler(self.log_queue)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

            except Exception as e:
                # 改进异常处理
                print(f"设置日志处理器时发生错误: {e}")
                # 添加一个基本的控制台处理器作为后备
                try:
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
                except Exception as fallback_error:
                    print(f"设置后备日志处理器也失败: {fallback_error}")

    def show_window(self):
        """显示窗口"""
        if self.window is None:
            self.create_window()
        else:
            self.window.deiconify()  # 还原窗口
            self.window.lift()  # 提升到前台
            self.window.focus_force()  # 强制获取焦点
            self.is_visible = True

    def hide_window(self):
        """隐藏窗口"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False

    def on_window_close(self):
        """窗口关闭事件处理"""
        self.hide_window()
        # 不销毁窗口，只是隐藏，这样可以保持状态

    def destroy_window(self):
        """销毁窗口"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.is_initialized = False
            self.is_visible = False

    def update_status(self, message, level='info'):
        """更新状态信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 如果窗口有状态显示控件，更新它
        if hasattr(self, 'status_var'):
            status_msg = f"[{timestamp}] {message}"
            self.status_var.set(status_msg)

        # 记录日志
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
        """创建状态框架 - 通用方法"""
        status_frame = ttk.LabelFrame(parent, text="📊 执行状态", padding=10)

        self.status_var = tk.StringVar(value="就绪状态 - 等待操作")
        ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10)).pack(anchor=tk.W)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                            mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=5)

        return status_frame

    def create_env_info_frame(self, parent, additional_info=""):
        """创建环境信息框架 - 通用方法"""
        from config_adapter import config_adapter

        env_frame = ttk.LabelFrame(parent, text="🌐 环境信息", padding=10)

        # 环境信息
        env_info = f"当前环境: {config_adapter.get_env_name()} | API地址: {config_adapter.get_api_url()}"
        ttk.Label(env_frame, text=env_info).pack(anchor=tk.W)

        # 附加信息
        if additional_info:
            ttk.Label(env_frame, text=additional_info, foreground='blue').pack(anchor=tk.W)

        return env_frame

    def create_control_frame(self, parent, title="🎮 操作控制"):
        """创建控制面板框架 - 通用方法"""
        return ttk.LabelFrame(parent, text=title, padding=10)

    def show_message_box(self, title, message, msg_type='info'):
        """显示消息框"""
        from tkinter import messagebox

        if msg_type == 'info':
            messagebox.showinfo(title, message)
        elif msg_type == 'warning':
            messagebox.showwarning(title, message)
        elif msg_type == 'error':
            messagebox.showerror(title, message)
        elif msg_type == 'question':
            return messagebox.askyesno(title, message)

    def run_in_thread(self, target_func, *args, **kwargs):
        """在线程中运行函数"""
        import threading
        thread = threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
