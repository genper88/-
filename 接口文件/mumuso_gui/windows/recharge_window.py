#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
挂账充值功能窗口
从原RechargeAfterSplitTab重构而来
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# 尝试导入schedule库
try:
    import schedule
except ImportError:
    schedule = None

# 导入业务模块和基础类
from recharge_after_split_demo import RechargeAfterSplitDemo
from config_adapter import config_adapter
from utils.base_window import BaseWindow


class RechargeAfterSplitWindow(BaseWindow):
    """挂账充值功能窗口"""

    def __init__(self, parent, title="💳 挂账充值管理", size="800x600", log_queue=None):
        self.recharge_demo = RechargeAfterSplitDemo()
        self.is_auto_running = False
        self.auto_thread = None
        self.query_results = {}
        self.module_name = "挂账充值"

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="💳 挂账充值管理", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        additional_info = "处理对象: 已订单备案且未挂账充值的订单 (FZ_UPLOADRESULT_CONFIRM='Y' 且 ISRECHARGE_FZ='N')"
        env_frame = self.create_env_info_frame(main_frame, additional_info)
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

        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="📄 充值结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_result_tree(result_frame)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(buttons_frame, text="🔍 查看待充值订单",
                   command=self.show_pending_recharge, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="💳 批量挂账充值",
                   command=self.batch_recharge_orders, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20).pack(side=tk.LEFT, padx=5)

        # 单个充值区域
        single_frame = ttk.Frame(parent)
        single_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(single_frame, text="单个订单充值:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_input_frame, text="订单号(xpbillid):").pack(side=tk.LEFT)
        self.single_order_var = tk.StringVar()
        ttk.Entry(single_input_frame, textvariable=self.single_order_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(single_input_frame, text="💳 充值此订单",
                   command=self.recharge_single_order, width=15).pack(side=tk.LEFT, padx=5)

    def setup_auto_execution(self, parent):
        """设置自动执行"""
        # 时间设置
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(time_frame, text="每日执行时间:").pack(side=tk.LEFT)
        self.auto_hour_var = tk.StringVar(value="05")
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

    def setup_result_tree(self, parent):
        """设置结果树形表格"""
        # 创建Treeview显示结果
        columns = ('recharge_id', 'status', 'amount', 'account', 'recharge_time')
        self.result_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)

        # 设置列标题和宽度
        self.result_tree.heading('recharge_id', text='充值ID')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('amount', text='金额(元)')
        self.result_tree.heading('account', text='账户')
        self.result_tree.heading('recharge_time', text='充值时间')

        self.result_tree.column('recharge_id', width=200, minwidth=150)
        self.result_tree.column('status', width=100, minwidth=80)
        self.result_tree.column('amount', width=100, minwidth=80)
        self.result_tree.column('account', width=100, minwidth=80)
        self.result_tree.column('recharge_time', width=150, minwidth=120)

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
        self.result_tree.tag_configure('processing', foreground='orange')  # 处理中
        self.result_tree.tag_configure('pending', foreground='blue')  # 待处理

        # 双击查看详细信息
        self.result_tree.bind('<Double-1>', self.show_detail_info)

    def setup_logger(self):
        """设置日志系统"""
        super().setup_logger()
        # 重新创建recharge_demo实例，传入logger
        self.recharge_demo = RechargeAfterSplitDemo(logger=self.logger)

    def test_database(self):
        """测试数据库连接"""

        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                connection = self.recharge_demo.get_database_connection()
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

    def show_pending_recharge(self):
        """显示待充值订单"""

        def show_in_thread():
            self.update_status("正在查询待充值订单...", 'info')
            try:
                stats = self.recharge_demo.get_recharge_statistics()
                if stats and stats['total'] > 0:
                    message = f"找到 {stats['total']} 笔待充值订单\n"
                    message += f"微信支付: {stats['wx_count']} 笔 ({stats['wx_amount']:.2f}元)\n"
                    message += f"支付宝: {stats['alipay_count']} 笔 ({stats['alipay_amount']:.2f}元)\n"
                    message += f"总金额: {stats['total_amount']:.2f}元"

                    self.update_status(f"查询完成: 找到 {stats['total']} 笔待充值订单", 'success')
                    self.show_message_box("查询结果", message, 'info')
                else:
                    self.update_status("没有找到待充值的订单", 'info')
                    self.show_message_box("查询结果", "没有找到待充值的订单", 'info')
            except Exception as e:
                self.update_status(f"查询订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询订单异常: {str(e)}", 'error')

        self.run_in_thread(show_in_thread)

    def recharge_single_order(self):
        """充值单个订单"""
        order_id = self.single_order_var.get().strip()
        if not order_id:
            self.show_message_box("警告", "请输入订单号！", 'warning')
            return

        def recharge_in_thread():
            self.update_status(f"正在充值订单: {order_id}", 'info')
            try:
                # 先查询此订单
                target_order = self.recharge_demo.get_recharge_by_id(order_id)

                if target_order:
                    success = self.recharge_demo.recharge_single_order(target_order)
                    if success:
                        self.update_status(f"订单 {order_id} 充值成功", 'success')
                        self.show_message_box("成功", f"订单 {order_id} 充值成功！", 'info')
                        # 清空输入框
                        self.single_order_var.set("")
                    else:
                        self.update_status(f"订单 {order_id} 充值失败", 'error')
                        self.show_message_box("失败", f"订单 {order_id} 充值失败！", 'error')
                else:
                    self.update_status(f"未找到订单: {order_id}", 'warning')
                    self.show_message_box("警告", f"未找到订单: {order_id} 或订单不符合充值条件", 'warning')

            except Exception as e:
                self.update_status(f"充值订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"充值订单异常: {str(e)}", 'error')

        self.run_in_thread(recharge_in_thread)

    def batch_recharge_orders(self):
        """批量充值订单"""
        result = self.show_message_box("确认", "确认要批量充值所有待处理订单吗？", 'question')
        if not result:
            return

        def recharge_in_thread():
            self.update_status("开始批量挂账充值...", 'info')
            self.progress_var.set(0)

            def progress_callback(current, total, message):
                progress = (current / total) * 100
                self.progress_var.set(progress)
                self.update_status(f"处理进度: {current}/{total} - {message}", 'info')

            try:
                success_count, total_count, failed_orders = self.recharge_demo.batch_recharge_orders(
                    progress_callback=progress_callback)

                self.progress_var.set(100)
                success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                summary = f"批量充值完成\n总订单数: {total_count}\n成功: {success_count}\n失败: {len(failed_orders)}\n成功率: {success_rate:.1f}%"

                self.update_status(f"批量充值完成: {success_count}/{total_count} 成功", 'success')
                self.show_message_box("完成", summary, 'info')

            except Exception as e:
                self.update_status(f"批量充值异常: {str(e)}", 'error')
                self.show_message_box("错误", f"批量充值异常: {str(e)}", 'error')

        self.run_in_thread(recharge_in_thread)

    def start_auto_execution(self):
        """启动自动执行"""
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
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._auto_recharge_job)

        self.is_auto_running = True
        self.auto_status_var.set(f"⏰ 自动执行已启动 - 每日 {hour:02d}:{minute:02d}")

        # 启动调度线程
        self.auto_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.auto_thread.start()

        self.update_status(f"自动执行已启动 - 每日 {hour:02d}:{minute:02d}", 'success')
        self.show_message_box("成功", f"自动执行已启动\n每日 {hour:02d}:{minute:02d} 自动批量挂账充值", 'info')

    def stop_auto_execution(self):
        """停止自动执行"""
        self.is_auto_running = False
        if schedule:
            schedule.clear()
        self.auto_status_var.set("ℹ️ 自动执行已停止")
        self.update_status("自动执行已停止", 'info')
        self.show_message_box("信息", "自动执行已停止", 'info')

    def _run_scheduler(self):
        """运行调度器"""
        while self.is_auto_running:
            if schedule:
                schedule.run_pending()
            time.sleep(1)

    def _auto_recharge_job(self):
        """自动充值任务"""
        self.update_status("自动任务开始执行", 'info')
        try:
            success_count, total_count, failed_orders = self.recharge_demo.batch_recharge_orders()
            if total_count > 0:
                self.update_status(f"自动任务完成: {success_count}/{total_count} 成功", 'success')
            else:
                self.update_status("自动任务完成: 没有待充值订单", 'info')
        except Exception as e:
            self.update_status(f"自动任务异常: {str(e)}", 'error')

    def add_result_to_tree(self, result):
        """向结果树中添加结果"""
        recharge_id = result['recharge_id']
        status = result['status']
        amount = f"{result['amount']:.2f}"
        account = result['account']
        recharge_time = result['recharge_time']

        # 添加到树中
        item_id = self.result_tree.insert('', tk.END, values=(
            recharge_id,
            status,
            amount,
            account,
            recharge_time
        ), tags=(status,))

    def show_detail_info(self, event):
        """显示详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        if item_id not in self.query_results:
            return

        result_data = self.query_results[item_id]

        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"充值结果详情 - {result_data['recharge_id']}")
        detail_window.geometry("500x400")
        detail_window.transient(self.window)
        detail_window.grab_set()

        # 详情信息
        detail_frame = ttk.Frame(detail_window, padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(detail_frame, text="充值结果详细信息", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # 创建信息展示
        info_text = f"""充值ID: {result_data['recharge_id']}
状态: {result_data['status']}
金额: {result_data['amount']:.2f}元
账户: {result_data['account']}
充值时间: {result_data['recharge_time']}"""

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

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动执行
        if self.is_auto_running:
            self.stop_auto_execution()
        super().on_window_close()