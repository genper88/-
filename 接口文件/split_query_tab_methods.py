#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
分账结果查询标签页方法模块
文件名: split_query_tab_methods.py
功能: 提供分账结果查询标签页的UI界面和业务逻辑
作者: 系统自动生成
更新时间: 2025-08-28
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
from datetime import datetime
import queue

# 导入项目模块
from config import Config
from split_query_demo import SplitQueryDemo


class SimpleLogHandler(logging.Handler):
    """简单的日志处理器"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        try:
            msg = self.format(record)
            
            # 从日志消息中提取模块名
            module_name = "系统"
            if '[分账结果查询]' in msg:
                module_name = "分账结果查询"
            elif '[余额支付查询]' in msg:
                module_name = "分账结果查询"
            elif '[分账管理]' in msg:
                module_name = "分账管理"
            elif '[挂账充值]' in msg:
                module_name = "挂账充值"
            elif '[账户余额查询]' in msg:
                module_name = "账户余额查询"
            elif '[订单上传]' in msg:
                module_name = "订单上传"
            
            # 发送字典格式的日志条目
            self.log_queue.put({
                'level': record.levelname,
                'message': msg,
                'module': module_name,
                'time': datetime.now().strftime('%H:%M:%S')
            })
        except Exception:
            pass


class SplitQueryTabMethods:
    """分账结果查询标签页方法类"""
    
    def __init__(self, parent, log_queue):
        """初始化
        
        Args:
            parent: 父级widget
            log_queue: 日志队列
        """
        self.parent = parent
        self.log_queue = log_queue
        self.logger = None
        self.split_query_demo = None
        
        # UI变量
        self.status_var = None
        self.progress_var = None
        self.progress_bar = None
        self.result_tree = None
        self.single_seq_var = None
        self.auto_interval_var = None
        self.auto_status_var = None
        
        # 数据存储
        self.query_results = {}  # 存储查询结果详情
        self.is_auto_running = False  # 自动查询状态
        
        # 初始化
        self.setup_logger()
        self.setup_ui()
    
    def setup_logger(self):
        """设置日志系统"""
        self.logger = logging.getLogger('SplitQuery')
        self.logger.setLevel(logging.DEBUG)
        
        # 添加自定义处理器
        handler = SimpleLogHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 重新创建split_query_demo实例，传入logger
        self.split_query_demo = SplitQueryDemo(logger=self.logger)
        
        # 设置回调函数
        self.split_query_demo.set_progress_callback(self.on_progress_update)
        self.split_query_demo.set_result_callback(self.on_result_update)
    
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔍 分账结果查询", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 环境信息框架
        env_frame = ttk.LabelFrame(main_frame, text="🌐 环境信息", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 环境信息
        env_info = f"当前环境: {Config.get_env_name()} | API地址: {Config.get_url()}"
        ttk.Label(env_frame, text=env_info).pack(anchor=tk.W)
        
        # 机构号信息
        node_info = f"机构号: {Config.get_split_query_node_id()} | 查询间隔: {Config.get_auto_query_interval()}分钟"
        ttk.Label(env_frame, text=node_info, foreground='blue').pack(anchor=tk.W)
        
        # 控制面板框架
        control_frame = ttk.LabelFrame(main_frame, text="🎮 操作控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 手动操作区域
        manual_frame = ttk.Frame(control_frame)
        manual_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(manual_frame, text="手动操作:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(buttons_frame, text="🔍 查看待查询记录",
                   command=self.show_pending_records, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🚀 批量查询结果",
                   command=self.batch_query_results, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔧 测试数据库连接",
                   command=self.test_database, width=20).pack(side=tk.LEFT, padx=5)
        
        # 单个查询区域
        single_frame = ttk.Frame(control_frame)
        single_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(single_frame, text="单个流水号查询:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        single_input_frame = ttk.Frame(single_frame)
        single_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(single_input_frame, text="分账流水号:").pack(side=tk.LEFT)
        self.single_seq_var = tk.StringVar()
        ttk.Entry(single_input_frame, textvariable=self.single_seq_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(single_input_frame, text="🔍 查询此流水号",
                   command=self.query_single_result, width=15).pack(side=tk.LEFT, padx=5)
        
        # 自动查询设置
        auto_frame = ttk.LabelFrame(main_frame, text="⏰ 自动查询设置", padding=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 间隔设置
        interval_frame = ttk.Frame(auto_frame)
        interval_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(interval_frame, text="查询间隔(分钟):").pack(side=tk.LEFT)
        self.auto_interval_var = tk.StringVar(value=str(Config.get_auto_query_interval()))
        ttk.Spinbox(interval_frame, from_=1, to=60, textvariable=self.auto_interval_var,
                    width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(interval_frame, text="分钟一次").pack(side=tk.LEFT, padx=5)
        
        # 自动查询控制
        auto_control_frame = ttk.Frame(auto_frame)
        auto_control_frame.pack(fill=tk.X, pady=5)
        
        self.auto_status_var = tk.StringVar(value="⏹️ 自动查询已停止")
        ttk.Label(auto_control_frame, textvariable=self.auto_status_var).pack(side=tk.LEFT)
        
        ttk.Button(auto_control_frame, text="▶️ 启动自动查询",
                   command=self.start_auto_query).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(auto_control_frame, text="⏹️ 停止自动查询",
                   command=self.stop_auto_query).pack(side=tk.RIGHT)
        
        # 状态信息框架
        status_frame = ttk.LabelFrame(main_frame, text="📊 执行状态", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="就绪状态 - 等待操作")
        ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10)).pack(anchor=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                            mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="📄 查询结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview显示结果
        columns = ('seq', 'status', 'amount', 'details', 'query_time')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=8)
        
        # 设置列标题和宽度
        self.result_tree.heading('seq', text='分账流水号')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('amount', text='金额(元)')
        self.result_tree.heading('details', text='明细数量')
        self.result_tree.heading('query_time', text='查询时间')
        
        self.result_tree.column('seq', width=200, minwidth=150)
        self.result_tree.column('status', width=100, minwidth=80)
        self.result_tree.column('amount', width=100, minwidth=80)
        self.result_tree.column('details', width=100, minwidth=80)
        self.result_tree.column('query_time', width=150, minwidth=120)
        
        # 添加滚动条
        result_scrollbar_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scrollbar_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=result_scrollbar_y.set, xscrollcommand=result_scrollbar_x.set)
        
        # 布局
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        result_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 设置不同状态的颜色
        self.result_tree.tag_configure('success', foreground='green')
        self.result_tree.tag_configure('failed', foreground='red')
        self.result_tree.tag_configure('processing', foreground='orange')
        self.result_tree.tag_configure('pending', foreground='blue')
        
        # 双击查看详细信息
        self.result_tree.bind('<Double-1>', self.show_detail_info)
    
    def update_status(self, message, level='info'):
        """更新状态信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_msg = f"[{timestamp}] {message}"
        self.status_var.set(status_msg)
        
        # 记录日志，确保有模块标识
        log_message = f"[分账结果查询] {message}"
        if level == 'info':
            self.logger.info(log_message)
        elif level == 'warning':
            self.logger.warning(log_message)
        elif level == 'error':
            self.logger.error(log_message)
        elif level == 'success':
            self.logger.info(f"[分账结果查询] ✅ {message}")
    
    def on_progress_update(self, message, progress):
        """进度更新回调"""
        self.update_status(message, 'info')
        self.progress_var.set(progress)
    
    def on_result_update(self, result_type, data):
        """结果更新回调"""
        if result_type == 'single_result':
            self.add_result_to_tree(data['seq'], data['result'])
        elif result_type == 'batch_complete':
            self.update_status(f"批量查询完成: {data['success_count']}/{data['total_count']}", 'success')
        elif result_type == 'auto_status':
            if data['status'] == 'started':
                self.auto_status_var.set(f"⏰ 自动查询已启动 - 每{data['interval']}分钟一次")
            elif data['status'] == 'stopped':
                self.auto_status_var.set("⏹️ 自动查询已停止")
        elif result_type == 'auto_query_result':
            self.update_status(f"自动查询完成: 查询了 {data['results_count']} 个结果", 'info')
    
    def add_result_to_tree(self, seq, result):
        """向结果树中添加查询结果"""
        try:
            if result.is_success() and result.data:
                status_text = result.data.get_status_text()
                amount_text = f"{result.data.get_total_amount_yuan():.2f}"
                details_text = f"{len(result.data.split_detail_list)}项"
                
                # 确定状态标签
                if result.data.status == 1:
                    tag = 'success'
                elif result.data.status == 0:
                    tag = 'failed'
                elif result.data.status == 6:
                    tag = 'processing'
                else:
                    tag = 'pending'
            else:
                status_text = "查询失败"
                amount_text = "0.00"
                details_text = "0项"
                tag = 'failed'
            
            query_time = datetime.now().strftime('%H:%M:%S')
            
            # 添加到树中
            item_id = self.result_tree.insert('', tk.END, values=(
                seq,
                status_text,
                amount_text,
                details_text,
                query_time
            ), tags=(tag,))
            
            # 保存结果数据以便查看详情
            self.query_results[item_id] = {
                'seq': seq,
                'result': result,
                'timestamp': datetime.now()
            }
            
            # 自动滚动到底部
            children = self.result_tree.get_children()
            if children:
                self.result_tree.see(children[-1])
                
        except Exception as e:
            self.logger.error(f"[分账结果查询] 添加结果到树失败: {str(e)}")
    
    def show_detail_info(self, event):
        """显示详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        if item_id not in self.query_results:
            return
        
        result_data = self.query_results[item_id]
        result = result_data['result']
        
        # 创建详情窗口
        detail_window = tk.Toplevel(self.parent)
        detail_window.title(f"分账结果详情 - {result_data['seq']}")
        detail_window.geometry("700x500")
        detail_window.transient(self.parent.winfo_toplevel())
        detail_window.grab_set()
        
        # 详情信息
        detail_info = self.split_query_demo.query_handler.get_detailed_result_info(result)
        detail_text = "\n".join(detail_info)
        
        text_widget = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, detail_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(detail_window, text="关闭",
                   command=detail_window.destroy).pack(pady=5)
    
    def test_database(self):
        """测试数据库连接"""
        def test_in_thread():
            self.update_status("正在测试数据库连接...", 'info')
            try:
                db_ok = self.split_query_demo.test_database_connection()
                if db_ok:
                    self.update_status("数据库连接测试成功", 'success')
                    messagebox.showinfo("成功", "数据库连接测试成功！")
                else:
                    self.update_status("数据库连接失败", 'error')
                    messagebox.showerror("错误", "数据库连接失败！")
            except Exception as e:
                self.update_status(f"数据库测试异常: {str(e)}", 'error')
                messagebox.showerror("错误", f"数据库测试异常: {str(e)}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def show_pending_records(self):
        """显示待查询记录"""
        def show_in_thread():
            self.update_status("正在查询待查询记录...", 'info')
            try:
                records = self.split_query_demo.query_pending_split_records(20)  # 限制最多20条
                if records:
                    total_count = len(records)
                    valid_count = len([r for r in records if r.has_split_result()])
                    
                    message = f"找到 {total_count} 条记录\n"
                    message += f"其中有分账结果的: {valid_count} 条\n\n"
                    
                    if valid_count > 0:
                        message += "有效记录示例:\n"
                        for i, record in enumerate(records[:5], 1):  # 显示前5条
                            if record.has_split_result():
                                message += f"{i}. {record.xpbillid} -> {record.get_split_apply_seq()}\n"
                    
                    self.update_status(f"查询完成: 找到 {valid_count} 条有效记录", 'success')
                    messagebox.showinfo("查询结果", message)
                else:
                    self.update_status("没有找到待查询的记录", 'info')
                    messagebox.showinfo("查询结果", "没有找到待查询的记录")
            except Exception as e:
                self.update_status(f"查询记录异常: {str(e)}", 'error')
                messagebox.showerror("错误", f"查询记录异常: {str(e)}")
        
        threading.Thread(target=show_in_thread, daemon=True).start()
    
    def query_single_result(self):
        """查询单个结果"""
        seq = self.single_seq_var.get().strip()
        if not seq:
            messagebox.showwarning("警告", "请输入分账流水号！")
            return
        
        def query_in_thread():
            self.update_status(f"正在查询流水号: {seq}", 'info')
            try:
                result = self.split_query_demo.query_single_split_result(seq)
                
                if result.is_success():
                    summary = self.split_query_demo.query_handler.format_query_result_summary(result)
                    self.update_status(f"查询成功: {seq}", 'success')
                    
                    # 添加到结果树
                    self.add_result_to_tree(seq, result)
                    
                    # 清空输入框
                    self.single_seq_var.set("")
                    
                    messagebox.showinfo("成功", f"查询成功！\n{summary}")
                else:
                    self.update_status(f"查询失败: {seq}", 'error')
                    messagebox.showerror("失败", f"查询失败: {result.get_error_message()}")
                    
            except Exception as e:
                self.update_status(f"查询异常: {str(e)}", 'error')
                messagebox.showerror("错误", f"查询异常: {str(e)}")
        
        threading.Thread(target=query_in_thread, daemon=True).start()
    
    def batch_query_results(self):
        """批量查询结果"""
        result = messagebox.askyesno("确认", "确认要批量查询所有待处理记录吗？")
        if not result:
            return
        
        def batch_query_in_thread():
            self.update_status("开始批量查询分账结果...", 'info')
            self.progress_var.set(0)
            
            try:
                # 清空之前的结果
                for item in self.result_tree.get_children():
                    self.result_tree.delete(item)
                self.query_results.clear()
                
                # 执行批量查询
                results = self.split_query_demo.batch_query_from_database()
                
                self.progress_var.set(100)
                total_count = len(results)
                success_count = sum(1 for r in results.values() if r.is_success())
                success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                
                summary = f"批量查询完成\n总查询数: {total_count}\n成功: {success_count}\n失败: {total_count - success_count}\n成功率: {success_rate:.1f}%"
                
                self.update_status(f"批量查询完成: {success_count}/{total_count} 成功", 'success')
                messagebox.showinfo("完成", summary)
                
            except Exception as e:
                self.update_status(f"批量查询异常: {str(e)}", 'error')
                messagebox.showerror("错误", f"批量查询异常: {str(e)}")
        
        threading.Thread(target=batch_query_in_thread, daemon=True).start()
    
    def start_auto_query(self):
        """启动自动查询"""
        if self.is_auto_running:
            messagebox.showinfo("信息", "自动查询已在运行中")
            return
        
        try:
            interval = int(self.auto_interval_var.get())
            if interval < 1 or interval > 60:
                messagebox.showerror("错误", "查询间隔必须在1-60分钟之间")
                return
        except ValueError:
            messagebox.showerror("错误", "查询间隔必须是有效数字")
            return
        
        # 更新配置中的间隔时间
        self.split_query_demo.auto_query_interval = interval
        
        # 启动自动查询
        self.split_query_demo.start_auto_query()
        self.is_auto_running = True
        
        self.update_status(f"自动查询已启动 - 每{interval}分钟执行一次", 'success')
        messagebox.showinfo("成功", f"自动查询已启动\n每{interval}分钟执行一次批量查询")
    
    def stop_auto_query(self):
        """停止自动查询"""
        self.split_query_demo.stop_auto_query()
        self.is_auto_running = False
        self.update_status("自动查询已停止", 'info')
        messagebox.showinfo("信息", "自动查询已停止")

