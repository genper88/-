#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账管理功能窗口
从原SplitAccountTab重构而来
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

# 尝试导入schedule库
try:
    import schedule
except ImportError:
    schedule = None

# 导入业务模块和基础类
from split_account_demo import SplitAccountDemo
from config_adapter import config_adapter
from utils.base_window import BaseWindow


class SplitAccountWindow(BaseWindow):
    """分账管理功能窗口"""

    def __init__(self, parent, title="📊 分账管理", size="1000x700", log_queue=None):
        self.split_demo = SplitAccountDemo()
        self.is_auto_running = False
        self.auto_thread = None
        self.split_results = []  # 分账结果数据存储
        self.module_name = "分账管理"

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="📊 分账管理", font=('Arial', 16, 'bold'))
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

        # 分账结果显示框架
        result_frame = ttk.LabelFrame(main_frame, text="📋 分账结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.setup_result_display(result_frame)

    def create_env_info_section(self, parent):
        """创建环境信息区域"""
        env_frame = self.create_env_info_frame(parent)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 分账配置信息
        split_config = config_adapter.get_split_config()
        desc_info = f"付款方: {split_config['PAYER_MERCHANT_ID']} | 加盟商收款: {split_config['PAYEE_JMS_MERCHANT_ID']} | 公司收款: {split_config['PAYEE_GS_MERCHANT_ID']}"
        ttk.Label(env_frame, text=desc_info, foreground='blue').pack(anchor=tk.W)

        # 业务模式说明
        mode_info = "支持常规分账（加盟商付款→两收款账号）和营销转账（营销子账号→供应商付款账户）两种模式"
        ttk.Label(env_frame, text=mode_info, foreground='green').pack(anchor=tk.W)

    def setup_control_panel(self, parent):
        """设置控制面板"""
        # 手动操作区域
        manual_frame = ttk.Frame(parent)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(buttons_frame, text="🔍 查看待分账订单",
                   command=self.show_pending_splits, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="💰 批量分账申请",
                   command=self.batch_split_orders, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20).pack(side=tk.LEFT, padx=5)

        # 单个分账区域
        single_frame = ttk.Frame(parent)
        single_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(single_frame, text="单个订单分账:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(single_input_frame, text="订单号(XPbillid):").pack(side=tk.LEFT)
        self.single_order_var = tk.StringVar()
        ttk.Entry(single_input_frame, textvariable=self.single_order_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(single_input_frame, text="💰 分账此订单",
                   command=self.split_single_order, width=15).pack(side=tk.LEFT, padx=5)

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
        """设置分账结果显示区域"""
        # 结果控制按钮
        result_control_frame = ttk.Frame(parent)
        result_control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(result_control_frame, text="🗑️ 清空结果",
                   command=self.clear_results, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_control_frame, text="📋 复制结果",
                   command=self.copy_results, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_control_frame, text="💾 导出结果",
                   command=self.export_results, width=12).pack(side=tk.LEFT)

        # 创建Treeview显示分账结果
        columns = ('billid', 'xpbillid', 'business_type', 'target_type', 'amount', 'status', 'message', 'execute_time')
        self.result_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        # 设置列标题和宽度
        self.result_tree.heading('billid', text='分账单据号')
        self.result_tree.heading('xpbillid', text='明细单据号')
        self.result_tree.heading('business_type', text='业务类型')
        self.result_tree.heading('target_type', text='分账类型')
        self.result_tree.heading('amount', text='金额(元)')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('message', text='结果消息')
        self.result_tree.heading('execute_time', text='执行时间')

        self.result_tree.column('billid', width=150, minwidth=120)
        self.result_tree.column('xpbillid', width=150, minwidth=120)
        self.result_tree.column('business_type', width=100, minwidth=80)
        self.result_tree.column('target_type', width=100, minwidth=80)
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
        self.result_tree.tag_configure('marketing', background='#f0f8ff')  # 营销转账背景色

        # 双击查看详细信息
        self.result_tree.bind('<Double-1>', self.show_result_detail)

    def setup_logger(self):
        """设置日志系统"""
        super().setup_logger()
        # 重新创建split_demo实例，传入logger
        self.split_demo = SplitAccountDemo(logger=self.logger)

    def test_database(self):
        """测试数据库连接"""

        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                connection = self.split_demo.get_database_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM P_BL_SELL_PAYAMOUNT_HZ_HD WHERE ROWNUM <= 1")
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

    def show_pending_splits(self):
        """显示待分账订单"""

        def show_in_thread():
            self.update_status("正在查询待分账订单...", 'info')
            try:
                orders = self.split_demo.get_split_orders_from_database()
                if orders:
                    total_count = len(orders)

                    # 修正：统计3部分金额总和
                    total_gs_amount = 0  # 公司分账金额
                    total_jms_amount = 0  # 加盟商分账金额
                    total_marketing_amount = 0  # 营销转账金额

                    regular_split_count = 0  # 常规分账订单数
                    marketing_transfer_count = 0  # 营销转账订单数

                    for order in orders:
                        gs_amount = order.get('gs_amount', 0)
                        jms_amount = order.get('jms_amount', 0)
                        marketing_amount = order.get('marketing_transfer_amount', 0)

                        total_gs_amount += gs_amount
                        total_jms_amount += jms_amount
                        total_marketing_amount += marketing_amount

                        if marketing_amount > 0:
                            marketing_transfer_count += 1
                        else:
                            regular_split_count += 1

                    # 计算总金额（3部分之和）
                    total_amount = total_gs_amount + total_jms_amount + total_marketing_amount

                    message = f"找到 {total_count} 笔待分账订单\n\n"
                    message += f"📊 金额统计:\n"
                    message += f"• 公司分账总金额: {total_gs_amount / 100:.2f}元\n"
                    message += f"• 加盟商分账总金额: {total_jms_amount / 100:.2f}元\n"
                    message += f"• 营销转账总金额: {total_marketing_amount / 100:.2f}元\n"
                    message += f"• 合计总金额: {total_amount / 100:.2f}元\n\n"

                    message += f"📋 业务类型统计:\n"
                    message += f"• 常规分账订单: {regular_split_count} 笔\n"
                    message += f"• 营销转账订单: {marketing_transfer_count} 笔\n\n"

                    # 显示前几笔订单的明细
                    message += f"📄 订单明细（前5笔）:\n"
                    for i, order in enumerate(orders[:5], 1):
                        business_type = order.get('business_type', '常规分账')
                        total_order_amount = order.get('total_amount', 0)
                        message += f"{i}. {order['billid']}-{order.get('xpbillid', 'N/A')} "
                        message += f"[{business_type}] {total_order_amount / 100:.2f}元\n"

                    self.update_status(f"查询完成: 找到 {total_count} 笔待分账订单，总金额 {total_amount / 100:.2f}元",
                                       'success')
                    self.show_message_box("查询结果", message, 'info')
                else:
                    self.update_status("没有找到待分账的订单", 'info')
                    self.show_message_box("查询结果", "没有找到待分账的订单", 'info')
            except Exception as e:
                self.update_status(f"查询订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"查询订单异常: {str(e)}", 'error')

        self.run_in_thread(show_in_thread)

    def split_single_order(self):
        """分账单个订单"""
        order_id = self.single_order_var.get().strip()
        if not order_id:
            self.show_message_box("警告", "请输入订单号！", 'warning')
            return

        def split_in_thread():
            self.update_status(f"正在分账订单: {order_id}", 'info')
            try:
                # 直接根据xpbillid查找此订单
                orders = self.split_demo.get_split_order_by_xpbillid(order_id)
                if orders:
                    # 使用找到的第一个订单进行分账
                    target_order = orders[0]
                    results = self.split_demo.split_single_order(target_order)
                    success_count = sum(1 for r in results if r['success'])
                    total_count = len(results)

                    # 添加结果到显示区域
                    self.add_split_results(results)

                    if success_count == total_count and total_count > 0:
                        self.update_status(f"订单 {order_id} 分账成功", 'success')
                        self.show_message_box("成功", f"订单 {order_id} 分账成功！\n成功: {success_count}/{total_count}",
                                              'info')
                        # 清空输入框
                        self.single_order_var.set("")
                    else:
                        self.update_status(f"订单 {order_id} 分账部分或全部失败", 'error')
                        self.show_message_box("失败", f"订单 {order_id} 分账失败！\n成功: {success_count}/{total_count}",
                                              'error')
                else:
                    self.update_status(f"未找到订单: {order_id}", 'warning')
                    self.show_message_box("警告", f"未找到订单: {order_id} 或订单不符合分账条件", 'warning')

            except Exception as e:
                self.update_status(f"分账订单异常: {str(e)}", 'error')
                self.show_message_box("错误", f"分账订单异常: {str(e)}", 'error')

        self.run_in_thread(split_in_thread)

    def batch_split_orders(self):
        """批量分账订单"""
        result = self.show_message_box("确认", "确认要批量分账所有待处理订单吗？", 'question')
        if not result:
            return

        def split_in_thread():
            self.update_status("开始批量分账申请...", 'info')
            self.progress_var.set(0)

            try:
                results = self.split_demo.batch_split_orders()

                self.progress_var.set(100)
                total_splits = len(results)
                success_splits = sum(1 for r in results if r['success'])
                success_rate = (success_splits / total_splits) * 100 if total_splits > 0 else 0

                # 添加结果到显示区域
                self.add_split_results(results)

                summary = f"批量分账完成\n总分账数: {total_splits}\n成功: {success_splits}\n失败: {total_splits - success_splits}\n成功率: {success_rate:.1f}%"

                self.update_status(f"批量分账完成: {success_splits}/{total_splits} 成功", 'success')
                self.show_message_box("完成", summary, 'info')

            except Exception as e:
                self.update_status(f"批量分账异常: {str(e)}", 'error')
                self.show_message_box("错误", f"批量分账异常: {str(e)}", 'error')

        self.run_in_thread(split_in_thread)

    def add_split_results(self, results):
        """添加分账结果到显示区域"""
        for result in results:
            # 确定状态标签
            tag = 'success' if result['success'] else 'failed'
            if result.get('target_type') == 'MARKETING_TO_SUPPLIER':
                tag = 'marketing'

            # 显示金额（转换为元）
            amount_yuan = result['amount'] / 100

            # 业务类型显示
            business_type = "营销转账" if result.get('target_type') == 'MARKETING_TO_SUPPLIER' else "常规分账"

            # 状态显示
            status_text = "成功" if result['success'] else "失败"

            # 插入到结果树
            item_id = self.result_tree.insert('', tk.END, values=(
                result.get('billid', ''),
                result.get('xpbillid', ''),
                business_type,
                result.get('target_type', ''),
                f"{amount_yuan:.2f}",
                status_text,
                result.get('message', ''),
                result.get('execute_time', '')
            ), tags=(tag,))

            # 保存完整结果数据
            self.split_results.append({
                'item_id': item_id,
                'result': result
            })

        # 自动滚动到底部
        children = self.result_tree.get_children()
        if children:
            self.result_tree.see(children[-1])

    def clear_results(self):
        """清空分账结果"""
        result = self.show_message_box("确认", "确认要清空所有分账结果吗？", 'question')
        if result:
            # 清空树形控件
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            # 清空结果数据
            self.split_results.clear()

            self.update_status("分账结果已清空", 'info')

    def copy_results(self):
        """复制分账结果到剪贴板"""
        try:
            if not self.split_results:
                self.show_message_box("信息", "没有分账结果可复制", 'info')
                return

            result_text = []
            result_text.append("分账结果明细:")
            result_text.append("=" * 100)
            result_text.append(
                f"{'分账单据号':<20} {'明细单据号':<20} {'业务类型':<10} {'分账类型':<15} {'金额(元)':<10} {'状态':<8} {'结果消息':<30} {'执行时间':<20}")
            result_text.append("-" * 100)

            for result_item in self.split_results:
                result = result_item['result']
                amount_yuan = result['amount'] / 100
                business_type = "营销转账" if result.get('target_type') == 'MARKETING_TO_SUPPLIER' else "常规分账"
                status_text = "成功" if result['success'] else "失败"

                line = f"{result.get('billid', ''):<20} {result.get('xpbillid', ''):<20} {business_type:<10} {result.get('target_type', ''):<15} {amount_yuan:<10.2f} {status_text:<8} {result.get('message', ''):<30} {result.get('execute_time', ''):<20}"
                result_text.append(line)

            result_text.append("=" * 100)

            self.window.clipboard_clear()
            self.window.clipboard_append('\n'.join(result_text))
            self.show_message_box("成功", f"已复制 {len(self.split_results)} 条分账结果到剪贴板", 'info')

        except Exception as e:
            self.show_message_box("错误", f"复制结果失败: {str(e)}", 'error')

    def export_results(self):
        """导出分账结果到文件"""
        try:
            if not self.split_results:
                self.show_message_box("信息", "没有分账结果可导出", 'info')
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
                title="导出分账结果",
                initialname=f"分账结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("分账结果明细报告\n")
                    f.write("=" * 100 + "\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"记录数量: {len(self.split_results)}\n")
                    f.write("=" * 100 + "\n\n")

                    # 统计信息
                    success_count = sum(1 for item in self.split_results if item['result']['success'])
                    failed_count = len(self.split_results) - success_count
                    marketing_count = sum(1 for item in self.split_results if
                                          item['result'].get('target_type') == 'MARKETING_TO_SUPPLIER')

                    f.write("统计信息:\n")
                    f.write(f"成功数量: {success_count}\n")
                    f.write(f"失败数量: {failed_count}\n")
                    f.write(f"营销转账数量: {marketing_count}\n")
                    f.write(f"常规分账数量: {len(self.split_results) - marketing_count}\n")
                    f.write("\n" + "-" * 100 + "\n\n")

                    # 详细记录
                    f.write("详细记录:\n")
                    for i, result_item in enumerate(self.split_results, 1):
                        result = result_item['result']
                        amount_yuan = result['amount'] / 100
                        business_type = "营销转账" if result.get('target_type') == 'MARKETING_TO_SUPPLIER' else "常规分账"
                        status_text = "成功" if result['success'] else "失败"

                        f.write(f"{i}. 分账记录\n")
                        f.write(f"   分账单据号: {result.get('billid', '')}\n")
                        f.write(f"   明细单据号: {result.get('xpbillid', '')}\n")
                        f.write(f"   业务类型: {business_type}\n")
                        f.write(f"   分账类型: {result.get('target_type', '')}\n")
                        f.write(f"   金额: {amount_yuan:.2f}元\n")
                        f.write(f"   状态: {status_text}\n")
                        f.write(f"   结果消息: {result.get('message', '')}\n")
                        f.write(f"   执行时间: {result.get('execute_time', '')}\n")
                        if result.get('request_id'):
                            f.write(f"   请求ID: {result.get('request_id')}\n")
                        if result.get('trade_no'):
                            f.write(f"   交易流水号: {result.get('trade_no')}\n")
                        f.write("\n")

                self.show_message_box("成功", f"分账结果已导出到: {filename}", 'info')

        except Exception as e:
            self.show_message_box("错误", f"导出结果失败: {str(e)}", 'error')

    def show_result_detail(self, event):
        """显示分账结果详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return

        item_id = selection[0]

        # 查找对应的结果数据
        result_data = None
        for result_item in self.split_results:
            if result_item['item_id'] == item_id:
                result_data = result_item['result']
                break

        if not result_data:
            return

        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"分账结果详情 - {result_data.get('billid', 'N/A')}")
        detail_window.geometry("700x600")
        detail_window.transient(self.window)
        detail_window.grab_set()

        # 详情信息
        detail_info = f"""分账结果详细信息
{'=' * 50}

基本信息:
分账单据号: {result_data.get('billid', 'N/A')}
明细单据号: {result_data.get('xpbillid', 'N/A')}
分账类型: {result_data.get('target_type', 'N/A')}
目标商户: {result_data.get('target_merchant', 'N/A')}

金额信息:
分账金额: {result_data.get('amount', 0) / 100:.2f}元

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
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._auto_split_job)

        self.is_auto_running = True
        self.auto_status_var.set(f"⏰ 自动执行已启动 - 每日 {hour:02d}:{minute:02d}")

        # 启动调度线程
        self.auto_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.auto_thread.start()

        self.update_status(f"自动执行已启动 - 每日 {hour:02d}:{minute:02d}", 'success')
        self.show_message_box("成功", f"自动执行已启动\n每日 {hour:02d}:{minute:02d} 自动批量分账申请", 'info')

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

    def _auto_split_job(self):
        """自动分账任务"""
        self.update_status("自动任务开始执行", 'info')
        try:
            results = self.split_demo.batch_split_orders()
            if results:
                total_splits = len(results)
                success_splits = sum(1 for r in results if r['success'])

                # 添加结果到显示区域
                self.add_split_results(results)

                self.update_status(f"自动任务完成: {success_splits}/{total_splits} 成功", 'success')
            else:
                self.update_status("自动任务完成: 没有待分账订单", 'info')
        except Exception as e:
            self.update_status(f"自动任务异常: {str(e)}", 'error')

    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止自动执行
        if self.is_auto_running:
            self.stop_auto_execution()
        super().on_window_close()