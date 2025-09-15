#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
账户余额查询功能窗口 - 完整配置系统适配版
从原AccountBalanceQueryTab重构而来
支持真实API调用和数据库操作，完美适配现有配置系统
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

# 导入业务模块和基础类
try:
    from account_balance_query_demo import AccountBalanceQueryDemo
except ImportError as e:
    print(f"警告: 无法导入 AccountBalanceQueryDemo: {str(e)}")
    AccountBalanceQueryDemo = None

try:
    from config_adapter import config_adapter
except ImportError as e:
    print(f"警告: 无法导入 config_adapter: {str(e)}")
    config_adapter = None

from utils.base_window import BaseWindow


class AccountBalanceQueryWindow(BaseWindow):
    """账户余额查询功能窗口 - 完整配置系统版"""

    def __init__(self, parent, title="💰 账户余额查询", size="900x1000", log_queue=None):
        self.balance_query_demo = None
        self.demo_init_error = None
        self.is_auto_running = False
        self.auto_thread = None
        self.query_results = {}  # 结果显示数据
        self.module_name = "账户余额查询"

        # UI控件变量
        self.single_merchant_var = tk.StringVar()  # 初始化为StringVar
        self.store_no_var = tk.StringVar()  # 添加门店编号变量并初始化
        self.account_type_var = tk.StringVar(value="1")  # 初始化为StringVar
        self.auto_interval_var = tk.StringVar(value="10")  # 初始化为StringVar
        self.auto_status_var = tk.StringVar(value="⏹️ 自动查询已停止")  # 初始化为StringVar
        self.result_tree = None
        self.query_button = None  # 查询按钮引用

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="💰 账户余额查询", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        additional_info = self._get_env_info()
        env_frame = self.create_env_info_frame(main_frame, additional_info)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 如果有初始化错误，显示错误信息
        if self.demo_init_error:
            self._show_init_error(main_frame)

        # 控制面板框架
        control_frame = self.create_control_frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.setup_control_panel(control_frame)

        # 自动查询设置
        auto_frame = ttk.LabelFrame(main_frame, text="⏰ 自动查询设置", padding=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))

        self.setup_auto_query(auto_frame)

        # 状态信息框架
        status_frame = self.create_status_frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="📄 查询结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_result_tree(result_frame)

    def _get_env_info(self) -> str:
        """获取环境信息"""
        try:
            if config_adapter:
                env_name = config_adapter.get_env_name()
                api_url = config_adapter.get_api_url()
                node_id = config_adapter.get_account_balance_node_id()
                interval = config_adapter.get_account_balance_auto_interval()
                return f"环境: {env_name} | API: {api_url} | 机构号: {node_id} | 查询间隔: {interval}分钟"
            else:
                return "配置系统未就绪"
        except Exception as e:
            return f"配置获取失败: {str(e)}"

    def _show_init_error(self, parent):
        """显示初始化错误信息"""
        error_frame = ttk.LabelFrame(parent, text="⚠️ 初始化错误", padding=10)
        error_frame.pack(fill=tk.X, pady=(0, 10))

        error_text = tk.Text(error_frame, height=4, bg='#ffeeee', fg='red', wrap=tk.WORD)
        error_text.pack(fill=tk.X)

        error_msg = f"账户余额查询模块初始化失败:\n{self.demo_init_error}\n\n请检查配置设置或联系管理员。"
        error_text.insert(tk.END, error_msg)
        error_text.config(state=tk.DISABLED)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        # 根据初始化状态禁用/启用按钮
        button_state = 'normal' if self.balance_query_demo else 'disabled'

        ttk.Button(buttons_frame, text="🔍 查看待查询记录",
                   command=self.show_pending_records, width=20, state=button_state).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🚀 批量查询余额",
                   command=self.batch_query_results, width=20, state=button_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20, state=button_state).pack(side=tk.LEFT, padx=5)

        # 单个查询区域
        single_frame = ttk.Frame(parent)
        single_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(single_frame, text="单个商户查询:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_input_frame, text="商户号:").pack(side=tk.LEFT)
        merchant_entry = ttk.Entry(single_input_frame, textvariable=self.single_merchant_var, width=20)
        merchant_entry.pack(side=tk.LEFT, padx=5)
        # 设置初始状态
        merchant_entry.config(state='normal' if self.balance_query_demo else 'disabled')

        # 添加门店编号输入框
        ttk.Label(single_input_frame, text="门店编号:").pack(side=tk.LEFT, padx=(10, 0))
        store_entry = ttk.Entry(single_input_frame, textvariable=self.store_no_var, width=15)
        store_entry.pack(side=tk.LEFT, padx=5)
        # 设置初始状态
        store_entry.config(state='normal' if self.balance_query_demo else 'disabled')

        ttk.Label(single_input_frame, text="账户类型:").pack(side=tk.LEFT, padx=(10, 0))
        account_type_combo = ttk.Combobox(single_input_frame, textvariable=self.account_type_var,
                                          values=["0", "1"], width=5, state="readonly" if self.balance_query_demo else "disabled")
        account_type_combo.pack(side=tk.LEFT, padx=5)
        # 设置初始状态
        account_type_combo.config(state='readonly' if self.balance_query_demo else 'disabled')

        ttk.Label(single_input_frame, text="(0=收款账户, 1=付款账户)").pack(side=tk.LEFT, padx=5)

        # 确保查询按钮状态正确设置
        query_btn = ttk.Button(single_input_frame, text="🔍 查询余额",
                               command=self.query_single_result, width=15)
        query_btn.pack(side=tk.LEFT, padx=10)
        
        # 设置初始状态
        query_btn.config(state='normal' if self.balance_query_demo else 'disabled')
        
        # 保存查询按钮引用以便后续更新
        self.query_button = query_btn

    def setup_auto_query(self, parent):
        """设置自动查询"""
        # 间隔设置
        interval_frame = ttk.Frame(parent)
        interval_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(interval_frame, text="查询间隔(分钟):").pack(side=tk.LEFT)

        # 从配置获取默认间隔
        default_interval = "10"
        try:
            if config_adapter:
                default_interval = str(config_adapter.get_account_balance_auto_interval())
        except:
            pass

        self.auto_interval_var = tk.StringVar(value=default_interval)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=5, to=60, textvariable=self.auto_interval_var, width=5)
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        # 设置初始状态
        interval_spinbox.config(state='normal' if self.balance_query_demo else 'disabled')

        ttk.Label(interval_frame, text="分钟一次").pack(side=tk.LEFT, padx=5)

        # 自动查询控制
        auto_control_frame = ttk.Frame(parent)
        auto_control_frame.pack(fill=tk.X, pady=5)

        self.auto_status_var = tk.StringVar(value="⏹️ 自动查询已停止")
        ttk.Label(auto_control_frame, textvariable=self.auto_status_var).pack(side=tk.LEFT)

        # 根据初始化状态禁用/启用按钮
        button_state = 'normal' if self.balance_query_demo else 'disabled'

        start_btn = ttk.Button(auto_control_frame, text="▶️ 启动自动查询",
                               command=self.start_auto_query, state=button_state)
        start_btn.pack(side=tk.RIGHT, padx=(5, 0))

        stop_btn = ttk.Button(auto_control_frame, text="⏹️ 停止自动查询",
                              command=self.stop_auto_query, state=button_state)
        stop_btn.pack(side=tk.RIGHT)

    def setup_result_tree(self, parent):
        """设置结果树形表格"""
        # 创建Treeview显示结果
        columns = (
            'merchant_id', 'account_type', 'total_balance', 'available_balance', 'frozen_balance', 'query_time',
            'status')
        self.result_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        # 设置列标题和宽度
        self.result_tree.heading('merchant_id', text='商户号')
        self.result_tree.heading('account_type', text='账户类型')
        self.result_tree.heading('total_balance', text='总余额(元)')
        self.result_tree.heading('available_balance', text='可用余额(元)')
        self.result_tree.heading('frozen_balance', text='冻结余额(元)')
        self.result_tree.heading('query_time', text='查询时间')
        self.result_tree.heading('status', text='查询状态')

        self.result_tree.column('merchant_id', width=150, minwidth=120)
        self.result_tree.column('account_type', width=80, minwidth=60)
        self.result_tree.column('total_balance', width=100, minwidth=80)
        self.result_tree.column('available_balance', width=100, minwidth=80)
        self.result_tree.column('frozen_balance', width=100, minwidth=80)
        self.result_tree.column('query_time', width=120, minwidth=100)
        self.result_tree.column('status', width=100, minwidth=80)

        # 添加滚动条
        result_scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=result_scrollbar_y.set, xscrollcommand=result_scrollbar_x.set)

        # 布局
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        result_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置不同状态的颜色
        self.result_tree.tag_configure('success', foreground='green')  # 成功
        self.result_tree.tag_configure('failed', foreground='red')  # 失败
        self.result_tree.tag_configure('warning', foreground='orange')  # 警告
        self.result_tree.tag_configure('insufficient', foreground='purple')  # 余额不足

        # 双击查看详细信息
        self.result_tree.bind('<Double-1>', self.show_detail_info)

    def setup_logger(self):
        """设置日志系统"""
        super().setup_logger()

        # 尝试创建balance_query_demo实例
        try:
            if AccountBalanceQueryDemo:
                self.balance_query_demo = AccountBalanceQueryDemo(logger=self.logger)

                # 设置回调函数
                self.balance_query_demo.set_progress_callback(self.on_progress_update)
                self.balance_query_demo.set_result_callback(self.on_result_update)

                self.logger.info("[账户余额查询] 业务模块初始化成功")
            else:
                raise ImportError("AccountBalanceQueryDemo类未找到")

        except Exception as e:
            self.demo_init_error = str(e)
            self.logger.error(f"[账户余额查询] 业务模块初始化失败: {str(e)}")
            self.balance_query_demo = None

        # 更新界面控件状态
        self._update_ui_state()
        
        # 特别处理查询按钮状态
        self._enable_query_button()

    def _update_ui_state(self):
        """更新界面控件状态"""
        # 如果窗口尚未创建或没有业务模块，直接返回
        if not self.window:
            return

        # 获取控件状态
        control_state = 'normal' if self.balance_query_demo else 'disabled'

        try:
            # 遍历所有控件并更新状态
            def update_widget_state(widget):
                if isinstance(widget, ttk.Entry):
                    widget.config(state=control_state)
                elif isinstance(widget, ttk.Combobox):
                    widget.config(state='readonly' if self.balance_query_demo else 'disabled')
                elif isinstance(widget, ttk.Button):
                    # 特殊处理查询按钮，确保文本正确
                    widget.config(state=control_state)
                elif isinstance(widget, ttk.Spinbox):
                    widget.config(state=control_state)
                # 递归处理子控件
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        update_widget_state(child)

            # 更新所有控件
            for child in self.window.winfo_children():
                update_widget_state(child)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"[账户余额查询] 更新界面控件状态失败: {str(e)}")

    def _enable_query_button(self):
        """特殊处理查询按钮，确保它在有业务模块时总是可用"""
        try:
            def find_and_enable_query_button(widget):
                if isinstance(widget, ttk.Button) and widget.cget('text') == "🔍 查询余额":
                    widget.config(state='normal' if self.balance_query_demo else 'disabled')
                elif hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        find_and_enable_query_button(child)
            
            if self.window:  # 确保窗口已创建
                find_and_enable_query_button(self.window)
        except Exception as e:
            if self.logger:
                self.logger.error(f"[账户余额查询] 启用查询按钮失败: {str(e)}")

    def on_progress_update(self, message, progress):
        """进度更新回调"""
        self.update_status(message, 'info')
        self.progress_var.set(progress)

    def on_result_update(self, result_type, data):
        """结果更新回调"""
        if result_type == 'single_result':
            # 兼容现有的add_result_to_tree方法签名
            self.add_result_to_tree(data['merchant_id'], data['result'])
        elif result_type == 'batch_complete':
            success_count = data['success_count']
            total_count = data['total_count']
            sufficient_count = data.get('sufficient_count', 0)
            insufficient_count = data.get('insufficient_count', 0)

            summary = f"批量查询完成: 成功 {success_count}/{total_count}"
            if sufficient_count > 0:
                summary += f", 余额充足(已回写) {sufficient_count} 个"
            if insufficient_count > 0:
                summary += f", 余额不足(已通知) {insufficient_count} 个"

            self.update_status(summary, 'success')

            # 批量查询的结果也添加到树中
            results = data.get('results', {})
            for merchant_id, result in results.items():
                self.add_result_to_tree(merchant_id, result)  # 兼容现有方法

        elif result_type == 'auto_status':
            if data['status'] == 'started':
                self.auto_status_var.set(f"⏰ 自动查询已启动 - 每{data['interval']}分钟一次")
            elif data['status'] == 'stopped':
                self.auto_status_var.set("⏹️ 自动查询已停止")
        elif result_type == 'auto_query_result':
            self.update_status(f"自动查询完成: 查询了 {data['results_count']} 个商户", 'info')

    def test_database(self):
        """测试数据库连接"""
        if not self.balance_query_demo:
            self.show_message_box("错误", "业务模块未初始化，无法测试数据库连接", 'error')
            return

        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                if self.balance_query_demo:
                    db_ok = self.balance_query_demo.test_database_connection()
                    if db_ok:
                        self.update_status("数据库连接测试成功", 'success')
                        self.show_message_box("成功", "数据库连接测试成功！", 'info')
                    else:
                        self.update_status("数据库连接失败", 'error')
                        self.show_message_box("错误", "数据库连接失败！", 'error')
            except Exception as e:
                self.update_status(f"数据库测试异常: {str(e)}", 'error')
                self.show_message_box("错误", f"数据库测试异常: {str(e)}", 'error')

        self.run_in_thread(test_in_thread)

    def show_pending_records(self):
        """显示待查询记录"""
        if not self.balance_query_demo:
            self.show_message_box("错误", "业务模块未初始化，无法查询记录", 'error')
            return

        def show_in_thread():
            self.update_status("正在查询待处理记录...", 'info')
            try:
                if self.balance_query_demo and self.balance_query_demo.db_manager:
                    # 获取待处理商户列表
                    merchants = self.balance_query_demo.db_manager.get_pending_merchants()

                    if merchants:
                        total_count = len(merchants)
                        message = f"找到 {total_count} 个待查询商户\n\n"
                        message += "商户示例:\n"
                        for i, merchant in enumerate(merchants[:5], 1):  # 显示前5个
                            message += f"{i}. 商户号: {merchant.merchant_id}, 门店: {merchant.store_no}, 金额: {merchant.total_amount:.2f}元\n"

                        if total_count > 5:
                            message += f"... 等 {total_count} 个商户"

                        self.update_status(f"查询完成: 找到 {total_count} 个待查询商户", 'success')
                        self.show_message_box("查询结果", message, 'info')
                    else:
                        self.update_status("没有找到待查询的商户", 'info')
                        self.show_message_box("查询结果", "没有找到待查询的商户", 'info')
            except Exception as e:
                self.update_status(f"查询记录异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询记录异常: {str(e)}", 'error')

        self.run_in_thread(show_in_thread)

    def query_single_result(self):
        """查询单个结果"""
        if not self.balance_query_demo:
            self.show_message_box("错误", "业务模块未初始化，无法执行查询", 'error')
            return

        merchant_id_str = self.single_merchant_var.get().strip()
        if not merchant_id_str:
            self.show_message_box("警告", "请输入商户号！", 'warning')
            return

        try:
            merchant_id = int(merchant_id_str)
        except ValueError:
            self.show_message_box("警告", "商户号必须是数字！", 'warning')
            return

        # 获取门店编号
        store_no = self.store_no_var.get().strip()
        account_type = self.account_type_var.get()

        def query_in_thread():
            self.update_status(f"正在查询商户余额: {merchant_id}", 'info')
            try:
                # 传递门店编号参数
                if self.balance_query_demo:
                    response = self.balance_query_demo.query_single_merchant_balance(
                        merchant_id=merchant_id,
                        account_type=account_type,
                        store_no=store_no
                    )

                    if response.is_success():
                        summary = response.get_balance_summary()
                        self.update_status(f"查询成功: {merchant_id}", 'success')

                        # 清空输入框
                        self.single_merchant_var.set("")
                        self.store_no_var.set("")  # 清空门店编号

                        self.show_message_box("成功", f"查询成功！\n{summary}", 'info')
                    else:
                        self.update_status(f"查询失败: {merchant_id}", 'error')
                        self.show_message_box("失败", f"查询失败: {response.get_error_message()}", 'error')

            except Exception as e:
                self.update_status(f"查询异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询异常: {str(e)}", 'error')

        self.run_in_thread(query_in_thread)

    def batch_query_results(self):
        """批量查询结果"""
        if not self.balance_query_demo:
            self.show_message_box("错误", "业务模块未初始化，无法执行批量查询", 'error')
            return

        result = self.show_message_box("确认",
                                       "确认要批量查询所有待处理商户余额吗？\n\n注意：批量查询会检查余额并更新数据库状态",
                                       'question')
        if not result:
            return

        def query_in_thread():
            self.update_status("开始批量查询商户余额...", 'info')
            self.progress_var.set(0)

            try:
                # 执行批量查询
                if self.balance_query_demo:
                    results = self.balance_query_demo.batch_query_from_database()

                    if results:
                        success_count = sum(1 for r in results.values() if r.is_success())
                        total_count = len(results)

                        self.progress_var.set(100)
                        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0

                        summary = f"批量查询完成\n总记录数: {total_count}\n成功: {success_count}\n失败: {total_count - success_count}\n成功率: {success_rate:.1f}%"

                        self.update_status(f"批量查询完成: {success_count}/{total_count} 成功", 'success')
                        self.show_message_box("完成", summary, 'info')
                    else:
                        self.update_status("没有找到需要查询的商户", 'info')
                        self.show_message_box("信息", "没有找到需要查询的商户", 'info')

            except Exception as e:
                self.update_status(f"批量查询异常: {str(e)}", 'error')
                self.show_message_box("错误", f"批量查询异常: {str(e)}", 'error')

        self.run_in_thread(query_in_thread)

    def add_result_to_tree(self, merchant_id, result):
        """向结果树中添加查询结果"""
        # 确保result_tree已初始化
        if not self.result_tree:
            return
            
        try:
            if result.is_success():
                account_type_text = "收款账户" if self.account_type_var.get() == "0" else "付款账户"
                total_balance = f"{result.get_total_balance_yuan():.2f}"
                available_balance = f"{result.get_available_balance_yuan():.2f}"
                frozen_balance = f"{result.get_frozen_balance_yuan():.2f}"
                status = "查询成功"
                tag = 'success'
            else:
                account_type_text = "未知"
                total_balance = "0.00"
                available_balance = "0.00"
                frozen_balance = "0.00"
                status = "查询失败"
                tag = 'failed'

            query_time = datetime.now().strftime('%H:%M:%S')

            # 添加到树中
            item_id = self.result_tree.insert('', tk.END, values=(
                merchant_id,
                account_type_text,
                total_balance,
                available_balance,
                frozen_balance,
                query_time,
                status
            ), tags=(tag,))

            # 保存结果数据以便查看详情
            self.query_results[item_id] = {
                'merchant_id': merchant_id,
                'result': result,
                'timestamp': datetime.now()
            }

            # 自动滚动到底部
            children = self.result_tree.get_children()
            if children:
                self.result_tree.see(children[-1])

        except Exception as e:
            if self.logger:
                self.logger.error(f"[账户余额查询] 添加结果到树失败: {str(e)}")

    def start_auto_query(self):
        """启动自动查询"""
        if not self.balance_query_demo:
            self.show_message_box("错误", "业务模块未初始化，无法启动自动查询", 'error')
            return

        if self.is_auto_running:
            self.show_message_box("信息", "自动查询已在运行中", 'info')
            return

        try:
            interval = int(self.auto_interval_var.get())
            if interval < 5:
                self.show_message_box("警告", "查询间隔不能少于5分钟！", 'warning')
                return
        except ValueError:
            self.show_message_box("警告", "查询间隔必须是数字！", 'warning')
            return

        if self.balance_query_demo:
            self.balance_query_demo.auto_query_interval = interval
            self.balance_query_demo.start_auto_query()
            self.is_auto_running = True

        self.update_status(f"自动查询已启动 - 每{interval}分钟一次", 'success')
        self.show_message_box("成功", f"自动查询已启动\n每{interval}分钟自动查询账户余额", 'info')

    def stop_auto_query(self):
        """停止自动查询"""
        if not self.balance_query_demo:
            self.show_message_box("信息", "业务模块未初始化", 'info')
            return

        if not self.is_auto_running:
            self.show_message_box("信息", "自动查询未运行", 'info')
            return

        if self.balance_query_demo:
            self.balance_query_demo.stop_auto_query()
            self.is_auto_running = False

        self.update_status("自动查询已停止", 'info')
        self.show_message_box("信息", "自动查询已停止", 'info')

    def show_detail_info(self, event):
        """显示详细信息"""
        # 确保result_tree已初始化
        if not self.result_tree:
            return
            
        selection = self.result_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        if item_id not in self.query_results:
            return

        result_data = self.query_results[item_id]
        result = result_data['result']

        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"账户余额详情 - {result_data['merchant_id']}")
        detail_window.geometry("600x500")
        detail_window.transient(self.window)
        detail_window.grab_set()

        # 详情信息
        detail_frame = ttk.Frame(detail_window, padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(detail_frame, text="账户余额详细信息", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # 创建信息展示
        if result.is_success():
            info_text = f"""商户号: {result_data['merchant_id']}
查询状态: 成功
查询时间: {result_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

=== 余额信息 ===
总余额: {result.get_total_balance_yuan():.2f}元
可用余额: {result.get_available_balance_yuan():.2f}元
冻结余额: {result.get_frozen_balance_yuan():.2f}元

=== 原始响应数据 ===
请求ID: {result.request_id}
响应码: {result.code}
响应消息: {result.msg}

原始数据: {result.data}"""
        else:
            info_text = f"""商户号: {result_data['merchant_id']}
查询状态: 失败
查询时间: {result_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

=== 错误信息 ===
错误码: {result.code}
错误消息: {result.msg}
详细信息: {result.sub_msg}

请求ID: {result.request_id}"""

        text_widget = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(detail_window, text="关闭",
                   command=detail_window.destroy).pack(pady=5)

    def show_window(self):
        """显示窗口"""
        # 先调用父类方法
        if self.window is None:
            self.create_window()
        else:
            self.window.deiconify()  # 还原窗口
            self.window.lift()  # 提升到前台
            self.window.focus_force()  # 强制获取焦点
            self.is_visible = True
            
        # 窗口显示后再次更新控件状态
        if self.window:  # 确保窗口已创建
            # 延迟一小段时间再更新UI状态，确保窗口完全初始化
            self.window.after(100, self._update_ui_state)

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动查询
        if self.is_auto_running and self.balance_query_demo:
            self.stop_auto_query()
        super().on_window_close()