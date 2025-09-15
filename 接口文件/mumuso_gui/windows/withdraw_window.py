#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
提现管理功能窗口
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import json

# 导入schedule库
SCHEDULE_AVAILABLE = False
schedule_module = None  # type: ignore

# 尝试导入schedule库
try:
    import schedule  # type: ignore
    SCHEDULE_AVAILABLE = True
    schedule_module = schedule
except ImportError:
    pass

# 导入业务模块和基础类
# 修复导入路径
from 接口文件.withdraw_demo import WithdrawDemo
from config_adapter import config_adapter
from 接口文件.mumuso_gui.utils.base_window import BaseWindow


class WithdrawWindow(BaseWindow):
    """提现管理功能窗口"""

    def __init__(self, parent, title="💰 提现管理", size="1000x700", log_queue=None):
        self.withdraw_demo = WithdrawDemo()
        self.is_auto_running = False
        self.auto_thread = None
        self.withdraw_results = []  # 提现结果数据存储
        self.module_name = "提现管理"

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="💰 提现管理", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        self.create_env_info_section(main_frame)

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

        # 提现结果显示框架
        result_frame = ttk.LabelFrame(main_frame, text="📋 提现结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.setup_result_display(result_frame)

    def create_env_info_section(self, parent):
        """创建环境信息区域"""
        env_frame = self.create_env_info_frame(parent)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 提现配置信息
        desc_info = f"机构号: {config_adapter.get_node_id()}"
        ttk.Label(env_frame, text=desc_info, foreground='blue').pack(anchor=tk.W)

        # 业务模式说明
        mode_info = "支持批量提现申请和单个提现申请两种模式"
        ttk.Label(env_frame, text=mode_info, foreground='green').pack(anchor=tk.W)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(buttons_frame, text="🔍 查看待提现订单",
                   command=self.show_pending_withdraws, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="💰 批量提现申请",
                   command=self.batch_withdraw_orders, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20).pack(side=tk.LEFT, padx=5)

        # 单个提现区域
        single_frame = ttk.Frame(parent)
        single_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(single_frame, text="单个订单提现:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_input_frame, text="订单号(Billid):").pack(side=tk.LEFT)
        self.single_order_var = tk.StringVar()
        ttk.Entry(single_input_frame, textvariable=self.single_order_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(single_input_frame, text="💰 提现此订单",
                   command=self.withdraw_single_order, width=15).pack(side=tk.LEFT, padx=5)

    def setup_auto_execution(self, parent):
        """设置自动执行"""
        # 时间设置
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(time_frame, text="每日执行时间:").pack(side=tk.LEFT)
        self.auto_hour_var = tk.StringVar(value="06")
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

    def setup_result_display(self, parent):
        """设置提现结果显示区域"""
        # 结果控制按钮
        result_control_frame = ttk.Frame(parent)
        result_control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(result_control_frame, text="🗑️ 清空结果",
                   command=self.clear_results, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_control_frame, text="📋 复制结果",
                   command=self.copy_results, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_control_frame, text="💾 导出结果",
                   command=self.export_results, width=12).pack(side=tk.LEFT)

        # 创建Treeview显示提现结果
        columns = ('billid', 'merchantno', 'storeid', 'amount', 'status', 'message', 'execute_time')
        self.result_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        # 设置列标题和宽度
        self.result_tree.heading('billid', text='提现单据号')
        self.result_tree.heading('merchantno', text='商户号')
        self.result_tree.heading('storeid', text='门店ID')
        self.result_tree.heading('amount', text='金额(元)')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('message', text='结果消息')
        self.result_tree.heading('execute_time', text='执行时间')

        self.result_tree.column('billid', width=150, minwidth=120)
        self.result_tree.column('merchantno', width=120, minwidth=100)
        self.result_tree.column('storeid', width=100, minwidth=80)
        self.result_tree.column('amount', width=100, minwidth=80)
        self.result_tree.column('status', width=80, minwidth=60)
        self.result_tree.column('message', width=200, minwidth=150)
        self.result_tree.column('execute_time', width=120, minwidth=100)

        # 添加滚动条
        result_scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=result_scrollbar_y.set, xscrollcommand=result_scrollbar_x.set)

        # 布局结果树和滚动条
        result_tree_frame = ttk.Frame(parent)
        result_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        result_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置不同状态的颜色
        self.result_tree.tag_configure('success', foreground='green')
        self.result_tree.tag_configure('failed', foreground='red')

        # 双击查看详细信息
        self.result_tree.bind('<Double-1>', self.show_result_detail)

    def setup_logger(self):
        """设置日志系统"""
        super().setup_logger()
        # 重新创建withdraw_demo实例，传入logger
        self.withdraw_demo = WithdrawDemo(logger=self.logger)

    def test_database(self):
        """测试数据库连接"""

        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                connection = self.withdraw_demo.get_database_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM p_bl_draw_hd WHERE ROWNUM <= 1")
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

    def show_pending_withdraws(self):
        """显示待提现订单"""

        def show_in_thread():
            self.update_status("正在查询待提现订单...", 'info')
            try:
                orders = self.withdraw_demo.get_withdraw_orders_from_database()
                if orders:
                    total_count = len(orders)
                    total_amount = sum(order.get('withdraw_amount', 0) for order in orders)

                    message = f"找到 {total_count} 笔待提现订单\n\n"
                    message += f"📊 金额统计:\n"
                    message += f"• 合计总金额: {total_amount / 100:.2f}元\n\n"

                    # 显示前几笔订单的明细
                    message += f"📄 订单明细（前5笔）:\n"
                    for i, order in enumerate(orders[:5], 1):
                        message += f"{i}. {order['billid']} "
                        message += f"{order.get('withdraw_amount', 0) / 100:.2f}元\n"

                    self.update_status(f"查询完成: 找到 {total_count} 笔待提现订单，总金额 {total_amount / 100:.2f}元",
                                       'success')
                    self.show_message_box("查询结果", message, 'info')
                else:
                    self.update_status("没有找到待提现的订单", 'info')
                    self.show_message_box("查询结果", "没有找到待提现的订单", 'info')
            except Exception as e:
                self.update_status(f"查询订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询订单异常: {str(e)}", 'error')

        self.run_in_thread(show_in_thread)

    def withdraw_single_order(self):
        """提现单个订单"""
        order_id = self.single_order_var.get().strip()
        if not order_id:
            self.show_message_box("警告", "请输入订单号！", 'warning')
            return

        def withdraw_in_thread():
            self.update_status(f"正在提现订单: {order_id}", 'info')
            try:
                result = self.withdraw_demo.withdraw_single_order_by_billid(order_id)
                if result:
                    # 添加结果到显示区域
                    self.add_withdraw_results([result])

                    if result['success']:
                        self.update_status(f"订单 {order_id} 提现成功", 'success')
                        self.show_message_box("成功", f"订单 {order_id} 提现成功！\n金额: {result['amount'] / 100:.2f}元",
                                              'info')
                        # 清空输入框
                        self.single_order_var.set("")
                    else:
                        self.update_status(f"订单 {order_id} 提现失败", 'error')
                        self.show_message_box("失败", f"订单 {order_id} 提现失败！\n原因: {result['message']}",
                                              'error')
                else:
                    self.update_status(f"未找到订单: {order_id}", 'warning')
                    self.show_message_box("警告", f"未找到订单: {order_id} 或订单不符合提现条件", 'warning')

            except Exception as e:
                self.update_status(f"提现订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"提现订单异常: {str(e)}", 'error')

        self.run_in_thread(withdraw_in_thread)

    def batch_withdraw_orders(self):
        """批量提现订单"""
        result = self.show_message_box("确认", "确认要批量提现所有待处理订单吗？", 'question')
        if not result:
            return

        def withdraw_in_thread():
            self.update_status("开始批量提现申请...", 'info')
            self.progress_var.set(0)

            try:
                results = self.withdraw_demo.batch_withdraw_orders()

                self.progress_var.set(100)
                total_withdraws = len(results)
                success_withdraws = sum(1 for r in results if r['success'])
                success_rate = (success_withdraws / total_withdraws) * 100 if total_withdraws > 0 else 0

                # 添加结果到显示区域
                self.add_withdraw_results(results)

                summary = f"批量提现完成\n总提现数: {total_withdraws}\n成功: {success_withdraws}\n失败: {total_withdraws - success_withdraws}\n成功率: {success_rate:.1f}%"

                self.update_status(f"批量提现完成: {success_withdraws}/{total_withdraws} 成功", 'success')
                self.show_message_box("完成", summary, 'info')

            except Exception as e:
                self.update_status(f"批量提现异常: {str(e)}", 'error')
                self.show_message_box("错误", f"批量提现异常: {str(e)}", 'error')

        self.run_in_thread(withdraw_in_thread)

    def add_withdraw_results(self, results):
        """添加提现结果到显示区域"""
        for result in results:
            # 确定状态标签
            tag = 'success' if result['success'] else 'failed'

            # 显示金额（转换为元）
            amount_yuan = result['amount'] / 100

            # 状态显示
            status_text = "成功" if result['success'] else "失败"

            # 插入到结果树
            item_id = self.result_tree.insert('', tk.END, values=(
                result.get('billid', ''),
                result.get('merchantno', ''),
                result.get('storeid', ''),
                f"{amount_yuan:.2f}",
                status_text,
                result.get('message', ''),
                result.get('execute_time', '')
            ), tags=(tag,))

            # 保存完整结果数据
            self.withdraw_results.append({
                'item_id': item_id,
                'result': result
            })

        # 自动滚动到底部
        children = self.result_tree.get_children()
        if children:
            self.result_tree.see(children[-1])

    def clear_results(self):
        """清空提现结果"""
        result = self.show_message_box("确认", "确认要清空所有提现结果吗？", 'question')
        if result:
            # 清空树形控件
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            # 清空结果数据
            self.withdraw_results.clear()

            self.update_status("提现结果已清空", 'info')

    def copy_results(self):
        """复制提现结果到剪贴板"""
        try:
            if not self.withdraw_results:
                self.show_message_box("信息", "没有提现结果可复制", 'info')
                return

            result_text = []
            result_text.append("提现结果明细:")
            result_text.append("=" * 100)
            result_text.append(
                f"{'提现单据号':<20} {'商户号':<15} {'门店ID':<10} {'金额(元)':<10} {'状态':<8} {'结果消息':<30} {'执行时间':<20}")
            result_text.append("-" * 100)

            for result_item in self.withdraw_results:
                result = result_item['result']
                amount_yuan = result['amount'] / 100
                status_text = "成功" if result['success'] else "失败"

                line = f"{result.get('billid', ''):<20} {result.get('merchantno', ''):<15} {result.get('storeid', ''):<10} {amount_yuan:<10.2f} {status_text:<8} {result.get('message', ''):<30} {result.get('execute_time', ''):<20}"
                result_text.append(line)

            result_text.append("=" * 100)

            if self.window:
                self.window.clipboard_clear()
                self.window.clipboard_append('\n'.join(result_text))
                self.show_message_box("成功", f"已复制 {len(self.withdraw_results)} 条提现结果到剪贴板", 'info')

        except Exception as e:
            self.show_message_box("错误", f"复制结果失败: {str(e)}", 'error')

    def export_results(self):
        """导出提现结果到文件"""
        try:
            if not self.withdraw_results:
                self.show_message_box("信息", "没有提现结果可导出", 'info')
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
                title="导出提现结果"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("提现结果明细报告\n")
                    f.write("=" * 100 + "\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"记录数量: {len(self.withdraw_results)}\n")
                    f.write("=" * 100 + "\n\n")

                    # 统计信息
                    success_count = sum(1 for item in self.withdraw_results if item['result']['success'])
                    failed_count = len(self.withdraw_results) - success_count

                    f.write("统计信息:\n")
                    f.write(f"成功数量: {success_count}\n")
                    f.write(f"失败数量: {failed_count}\n")
                    f.write("\n" + "-" * 100 + "\n\n")

                    # 详细记录
                    f.write("详细记录:\n")
                    for i, result_item in enumerate(self.withdraw_results, 1):
                        result = result_item['result']
                        amount_yuan = result['amount'] / 100
                        status_text = "成功" if result['success'] else "失败"

                        f.write(f"{i}. 提现记录\n")
                        f.write(f"   提现单据号: {result.get('billid', '')}\n")
                        f.write(f"   商户号: {result.get('merchantno', '')}\n")
                        f.write(f"   门店ID: {result.get('storeid', '')}\n")
                        f.write(f"   金额: {amount_yuan:.2f}元\n")
                        f.write(f"   状态: {status_text}\n")
                        f.write(f"   结果消息: {result.get('message', '')}\n")
                        f.write(f"   执行时间: {result.get('execute_time', '')}\n")
                        if result.get('request_id'):
                            f.write(f"   请求ID: {result.get('request_id')}\n")
                        if result.get('trade_no'):
                            f.write(f"   交易流水号: {result.get('trade_no')}\n")
                        f.write("\n")

                self.show_message_box("成功", f"提现结果已导出到: {filename}", 'info')

        except Exception as e:
            self.show_message_box("错误", f"导出结果失败: {str(e)}", 'error')

    def show_result_detail(self, event):
        """显示提现结果详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return

        item_id = selection[0]

        # 查找对应的结果数据
        result_data = None
        for result_item in self.withdraw_results:
            if result_item['item_id'] == item_id:
                result_data = result_item['result']
                break

        if not result_data:
            return

        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"提现结果详情 - {result_data.get('billid', 'N/A')}")
        detail_window.geometry("700x600")
        detail_window.transient(self.window)
        detail_window.grab_set()

        # 详情信息
        detail_info = f"""提现结果详细信息
{'=' * 50}

基本信息:
提现单据号: {result_data.get('billid', 'N/A')}
商户号: {result_data.get('merchantno', 'N/A')}
门店ID: {result_data.get('storeid', 'N/A')}

金额信息:
提现金额: {result_data.get('amount', 0) / 100:.2f}元

执行结果:
执行状态: {'成功' if result_data.get('success') else '失败'}
结果消息: {result_data.get('message', 'N/A')}
执行时间: {result_data.get('execute_time', 'N/A')}

API响应:
请求ID: {result_data.get('request_id', 'N/A')}
交易流水号: {result_data.get('trade_no', 'N/A')}

完整响应数据:
{json.dumps(result_data.get('response', {}), indent=2, ensure_ascii=False) if result_data.get('response') else '无响应数据'}
"""

        text_widget = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, detail_info)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(detail_window, text="关闭",
                   command=detail_window.destroy).pack(pady=5)

    def start_auto_execution(self):
        """启动自动执行"""
        if not SCHEDULE_AVAILABLE:
            self.show_message_box("错误", "自动执行功能不可用，缺少schedule库", 'error')
            return
            
        if self.is_auto_running:
            self.show_message_box("信息", "自动执行已在运行中", 'info')
            return

        hour = int(self.auto_hour_var.get())
        minute = int(self.auto_minute_var.get())

        # 清除之前的调度
        if schedule_module:
            schedule_module.clear()

        # 设置新的调度
        if schedule_module:
            schedule_module.every().day.at(f"{hour:02d}:{minute:02d}").do(self._auto_withdraw_job)

        self.is_auto_running = True
        self.auto_status_var.set(f"⏰ 自动执行已启动 - 每日 {hour:02d}:{minute:02d}")

        # 启动调度线程
        self.auto_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.auto_thread.start()

        self.update_status(f"自动执行已启动 - 每日 {hour:02d}:{minute:02d}", 'success')
        self.show_message_box("成功", f"自动执行已启动\n每日 {hour:02d}:{minute:02d} 自动批量提现申请", 'info')

    def stop_auto_execution(self):
        """停止自动执行"""
        if not SCHEDULE_AVAILABLE:
            return
            
        self.is_auto_running = False
        if schedule_module:
            schedule_module.clear()
        self.auto_status_var.set("ℹ️ 自动执行已停止")
        self.update_status("自动执行已停止", 'info')
        self.show_message_box("信息", "自动执行已停止", 'info')

    def _run_scheduler(self):
        """运行调度器"""
        if not SCHEDULE_AVAILABLE:
            return
            
        while self.is_auto_running:
            if schedule_module:
                schedule_module.run_pending()
            time.sleep(1)

    def _auto_withdraw_job(self):
        """自动提现任务"""
        self.update_status("自动任务开始执行", 'info')
        try:
            results = self.withdraw_demo.batch_withdraw_orders()
            if results:
                total_withdraws = len(results)
                success_withdraws = sum(1 for r in results if r['success'])

                # 添加结果到显示区域
                self.add_withdraw_results(results)

                self.update_status(f"自动任务完成: {success_withdraws}/{total_withdraws} 成功", 'success')
            else:
                self.update_status("自动任务完成: 没有待提现订单", 'info')
        except Exception as e:
            self.update_status(f"自动任务异常: {str(e)}", 'error')

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动执行
        if self.is_auto_running:
            self.stop_auto_execution()
        super().on_window_close()