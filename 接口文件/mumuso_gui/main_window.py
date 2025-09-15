#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
MUMUSO分账系统主窗口 - 简化版
文件名: main_window.py
功能：
1. 简洁的主界面，只显示功能按钮和日志
2. 通过按钮唤醒各个功能模块的独立窗口
3. 统一的日志显示和状态管理
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue

# 导入配置适配器
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_adapter import config_adapter

# 导入组件
from components.log_viewer import LogViewer
from components.window_manager import setup_window_manager


class MainApplication:
    """主应用程序"""

    def __init__(self):
        self.root = tk.Tk()
        self.log_queue = queue.Queue()
        self.window_manager = None
        self.setup_window()
        self.setup_ui()
        self.setup_window_manager()

    def setup_window(self):
        """设置主窗口"""
        self.root.title("MUMUSO分账管理系统 v2.0 - 模块化版本")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)

        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # 设置主题样式
        style = ttk.Style()
        style.theme_use('clam')  # 使用现代主题

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """设置用户界面"""
        # 创建主菜单
        self.create_menu()

        # 创建主要内容区域
        self.create_main_content()

        # 创建状态栏
        self.create_status_bar()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出日志", command=self.export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        # 窗口菜单
        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="窗口", menu=window_menu)
        window_menu.add_command(label="显示所有窗口", command=self.show_all_windows)
        window_menu.add_command(label="隐藏所有窗口", command=self.hide_all_windows)
        window_menu.add_separator()
        window_menu.add_command(label="窗口状态", command=self.show_window_status)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_main_content(self):
        """创建主要内容区域"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="MUMUSO分账管理系统",
                                font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        self.create_env_info_frame(main_frame)

        # 功能按钮区域
        self.create_function_buttons(main_frame)

        # 日志显示区域
        self.create_log_area(main_frame)

    def create_env_info_frame(self, parent):
        """创建环境信息框架"""
        env_frame = ttk.LabelFrame(parent, text="🌐 系统环境信息", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 15))

        # 环境信息
        env_info = f"当前环境: {config_adapter.get_env_name()} | API地址: {config_adapter.get_api_url()}"
        ttk.Label(env_frame, text=env_info).pack(anchor=tk.W)

        # 配置信息
        config_info = f"APP_ID: {config_adapter.get_app_id()} | 机构号: {config_adapter.get_node_id()}"
        ttk.Label(env_frame, text=config_info, foreground='blue').pack(anchor=tk.W)

    def create_function_buttons(self, parent):
        """创建功能按钮区域"""
        buttons_frame = ttk.LabelFrame(parent, text="🎯 功能模块", padding=15)
        buttons_frame.pack(fill=tk.X, pady=(0, 15))

        # 创建按钮网格
        button_config = [
            ("📦 订单上传管理", "order_upload", "管理订单批量上传", "#4CAF50"),
            ("💳 挂账充值管理", "recharge_after_split", "处理挂账充值业务", "#FF9800"),
            ("📊 分账管理", "split_account", "执行分账申请操作", "#2196F3"),
            ("🔍 分账结果查询", "split_query", "查询分账处理结果", "#9C27B0"),
            ("💰 账户余额查询", "balance_query", "查询账户余额信息", "#00BCD4"),
            ("💰 提现管理", "withdraw", "执行提现申请操作", "#FF5722"),
           # ("📱 短信服务管理", "sms", "阿里云短信服务管理", "#E91E63"),
            ("🔧 系统配置管理", "config_management", "管理系统配置参数", "#607D8B")
        ]

        # 创建按钮网格 (2行4列)
        for i, (text, window_name, desc, color) in enumerate(button_config):
            row = i // 4
            col = i % 4

            # 创建按钮框架
            btn_frame = ttk.Frame(buttons_frame)
            btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            # 配置列权重
            buttons_frame.grid_columnconfigure(col, weight=1)

            # 创建按钮
            btn = ttk.Button(btn_frame, text=text,
                             command=lambda wn=window_name: self.show_function_window(wn),
                             width=20)
            btn.pack(fill=tk.X)

            # 添加描述标签
            desc_label = ttk.Label(btn_frame, text=desc, font=('Arial', 8),
                                   foreground='gray')
            desc_label.pack(pady=(2, 0))

    def create_log_area(self, parent):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="📄 系统日志监控", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 创建日志查看器
        self.log_viewer = LogViewer(log_frame, self.log_queue, height=12)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_text = tk.StringVar()
        self.status_text.set(f"系统就绪 | 当前环境: {config_adapter.get_env_name()}")

        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)

        # 时间显示
        self.time_label = ttk.Label(self.status_bar, text="")
        self.time_label.pack(side=tk.RIGHT, padx=5)
        self.update_time()

    def setup_window_manager(self):
        """设置窗口管理器"""
        print(f"[DEBUG] === MainApplication.setup_window_manager() ===")
        print(f"[DEBUG] self.log_queue: {self.log_queue is not None}")
        print(f"[DEBUG] log_queue大小: {self.log_queue.qsize() if self.log_queue else 'None'}")

        from components.window_manager import setup_window_manager
        self.window_manager = setup_window_manager(self.root, self.log_queue)

        print(f"[DEBUG] window_manager创建完成")
        if self.window_manager:
            print(f"[DEBUG] window_manager.log_queue: {self.window_manager.log_queue is not None}")
            print(f"[DEBUG] 开始注册窗口...")

            # 注册所有功能窗口 - 确保这里被调用
            self.register_all_windows()

            print(f"[DEBUG] setup_window_manager完成")
        else:
            print(f"[DEBUG] window_manager创建失败")

    def register_all_windows(self):
        """注册所有功能窗口"""
        print(f"[DEBUG] === 开始注册所有功能窗口 ===")
        print(f"[DEBUG] window_manager: {self.window_manager}")
        print(
            f"[DEBUG] window_manager.log_queue: {self.window_manager.log_queue is not None if self.window_manager else 'window_manager为None'}")

        try:
            print(f"[DEBUG] 开始导入窗口类...")

            # 窗口配置信息
            window_configs = [
                ("order_upload", "windows.order_upload_window", "OrderUploadWindow", "📦 订单上传管理", "900x900"),
                ("recharge_after_split", "windows.recharge_window", "RechargeAfterSplitWindow", "💳 挂账充值管理",
                 "900x900"),
                ("split_account", "windows.split_account_window", "SplitAccountWindow", "📊 分账管理", "900x900"),
                ("split_query", "windows.split_query_window", "SplitQueryWindow", "🔍 分账结果查询", "900x900"),
                ("balance_query", "windows.balance_query_window", "AccountBalanceQueryWindow", "💰 账户余额查询",
                 "900x1000"),
                ("withdraw", "windows.withdraw_window", "WithdrawWindow", "💰 提现管理", "900x900"),
               # ("sms", "windows.sms_window", "SmsWindow", "📱 短信服务管理", "700x600"),
                ("config_management", "windows.config_window", "ConfigManagementWindow", "🔧 系统配置管理", "900x900")
            ]

            successful_registrations = 0
            failed_imports = []

            for window_name, module_path, class_name, title, size in window_configs:
                try:
                    print(f"[DEBUG] 尝试导入 {window_name}: {module_path}.{class_name}")

                    # 动态导入模块和类
                    module = __import__(module_path, fromlist=[class_name])
                    window_class = getattr(module, class_name)

                    print(f"[DEBUG] 成功导入 {class_name}")

                    # 注册窗口
                    self.window_manager.register_window(window_name, window_class, title, size)
                    print(f"[DEBUG] {window_name} 窗口注册成功")
                    successful_registrations += 1

                except ImportError as e:
                    error_msg = f"导入 {module_path}.{class_name} 失败: {str(e)}"
                    print(f"[DEBUG] {error_msg}")
                    failed_imports.append((window_name, module_path, class_name, str(e)))

                except AttributeError as e:
                    error_msg = f"在模块 {module_path} 中找不到类 {class_name}: {str(e)}"
                    print(f"[DEBUG] {error_msg}")
                    failed_imports.append((window_name, module_path, class_name, str(e)))

                except Exception as e:
                    error_msg = f"注册 {window_name} 窗口时发生错误: {str(e)}"
                    print(f"[DEBUG] {error_msg}")
                    failed_imports.append((window_name, module_path, class_name, str(e)))

            # 检查注册结果
            print(f"[DEBUG] 检查窗口注册状态...")
            if hasattr(self.window_manager, 'windows'):
                registered_windows = list(self.window_manager.windows.keys())
                print(f"[DEBUG] 已注册的窗口: {registered_windows}")
                print(f"[DEBUG] 成功注册窗口数: {successful_registrations}/{len(window_configs)}")
            else:
                print(f"[DEBUG] window_manager没有windows属性")

            # 报告失败的导入
            if failed_imports:
                print(f"[DEBUG] === 导入失败的窗口 ===")
                for window_name, module_path, class_name, error in failed_imports:
                    print(f"[DEBUG] {window_name}: {module_path}.{class_name} - {error}")

                # 给出具体的文件路径建议
                print(f"[DEBUG] === 文件检查建议 ===")
                print(f"[DEBUG] 请检查以下文件是否存在：")
                for window_name, module_path, class_name, error in failed_imports:
                    file_path = module_path.replace('.', '/') + '.py'
                    print(f"[DEBUG] - {file_path} (应包含 {class_name} 类)")

            if successful_registrations > 0:
                self.log_info(f"成功注册 {successful_registrations}/{len(window_configs)} 个功能窗口")

            if failed_imports:
                error_summary = f"有 {len(failed_imports)} 个窗口导入失败"
                self.log_error(error_summary)

                # 显示友好的错误提示
                from tkinter import messagebox
                failed_names = [item[0] for item in failed_imports]
                messagebox.showwarning(
                    "部分模块加载失败",
                    f"以下功能模块加载失败，请检查对应文件：\n\n" +
                    "\n".join([f"• {name}" for name in failed_names]) +
                    f"\n\n请查看控制台了解详细错误信息。"
                )

            print(f"[DEBUG] === 功能窗口注册完成 ===")

        except Exception as e:
            error_msg = f"注册功能窗口失败: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            import traceback
            traceback.print_exc()
            self.log_error(error_msg)

    def show_function_window(self, window_name):
        """显示功能窗口"""
        if self.window_manager:
            try:
                self.window_manager.show_window(window_name)
                self.log_info(f"打开功能窗口: {window_name}")
            except Exception as e:
                self.log_error(f"打开窗口失败: {str(e)}")
                messagebox.showerror("错误", f"打开功能窗口失败: {str(e)}")
        else:
            messagebox.showerror("错误", "窗口管理器未初始化")

    def show_all_windows(self):
        """显示所有窗口"""
        if self.window_manager:
            windows = ["order_upload", "recharge_after_split", "split_account",
                       "split_query", "balance_query", "withdraw", "config_management"]
            for window_name in windows:
                self.window_manager.show_window(window_name)
            self.log_info("显示所有功能窗口")

    def hide_all_windows(self):
        """隐藏所有窗口"""
        if self.window_manager:
            self.window_manager.hide_all_windows()
            self.log_info("隐藏所有功能窗口")

    def show_window_status(self):
        """显示窗口状态"""
        if self.window_manager:
            status = self.window_manager.get_all_windows_status()
            status_text = "窗口状态信息:\n\n"
            for window_name, info in status.items():
                status_text += f"• {info['title']}: "
                status_text += f"{'已初始化' if info['initialized'] else '未初始化'}, "
                status_text += f"{'可见' if info['visible'] else '隐藏'}\n"

            messagebox.showinfo("窗口状态", status_text)

    def export_logs(self):
        """导出日志（菜单功能）"""
        if hasattr(self, 'log_viewer'):
            self.log_viewer.export_logs()
        else:
            messagebox.showinfo("信息", "日志组件未初始化")

    def show_about(self):
        """显示关于对话框"""
        about_text = """MUMUSO分账管理系统 v2.0 - 模块化版本

系统特性:
• 模块化架构，功能独立
• 窗口化操作，多任务处理
• 统一日志管理
• 配置集中管理
• 美观的图形界面

功能模块:
• 📦 订单上传管理
• 💳 挂账充值管理
• 📊 分账管理
• 🔍 分账结果查询
• 💰 账户余额查询
• 🔧 系统配置管理

开发: 智能助手
版本: 2.0.0 (模块化重构版)
更新时间: 2025年1月
"""
        messagebox.showinfo("关于", about_text)

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def log_info(self, message):
        """记录信息日志"""
        self.log_queue.put({
            'level': 'INFO',
            'message': f"[主窗口] {message}",
            'module': '系统',
            'time': datetime.now().strftime('%H:%M:%S')
        })

    def log_error(self, message):
        """记录错误日志"""
        self.log_queue.put({
            'level': 'ERROR',
            'message': f"[主窗口] {message}",
            'module': '系统',
            'time': datetime.now().strftime('%H:%M:%S')
        })

    def on_closing(self):
        """关闭事件处理"""
        if messagebox.askokcancel("退出", "确定要退出MUMUSO分账管理系统吗？"):
            # 清理窗口管理器
            if self.window_manager:
                self.window_manager.cleanup()

            self.log_info("系统正常退出")
            self.root.quit()

    def run(self):
        """运行应用程序"""
        self.root.mainloop()


def main():
    """主函数"""
    # 检查配置
    ready, msg = config_adapter.is_config_ready()
    if not ready:
        # 不退出，允许用户通过GUI修改配置
        print(f"配置检查失败: {msg}")
        print("系统将使用默认配置启动，请通过配置管理界面调整配置")

    # 创建并运行应用程序
    app = MainApplication()
    app.run()


if __name__ == '__main__':
    main()