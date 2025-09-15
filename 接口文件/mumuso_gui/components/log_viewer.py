#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
日志查看器组件
可嵌入到主窗口或独立窗口中使用
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
from datetime import datetime


class LogViewer:
    """日志查看器组件"""

    def __init__(self, parent, log_queue, height=15):
        self.parent = parent
        self.log_queue = log_queue
        self.log_data = []
        self.height = height
        self.setup_ui()
        self.start_log_monitor()

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 标题和控制
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="📄 系统日志", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)

        # 筛选控制区域
        filter_frame = ttk.Frame(title_frame)
        filter_frame.pack(side=tk.RIGHT)

        # 模块筛选
        ttk.Label(filter_frame, text="模块:").pack(side=tk.LEFT, padx=(0, 5))
        self.module_var = tk.StringVar(value="全部")
        module_combo = ttk.Combobox(filter_frame, textvariable=self.module_var,
                                    values=["全部", "订单上传", "余额查询", "账户余额查询",
                                            "分账管理", "挂账充值", "分账结果查询", "配置管理", "系统"],
                                    width=12, state="readonly")
        module_combo.pack(side=tk.LEFT, padx=(0, 10))
        module_combo.bind('<<ComboboxSelected>>', self.apply_filter)

        # 级别筛选
        ttk.Label(filter_frame, text="级别:").pack(side=tk.LEFT, padx=(0, 5))
        self.level_var = tk.StringVar(value="全部")
        level_combo = ttk.Combobox(filter_frame, textvariable=self.level_var,
                                   values=["全部", "INFO", "WARNING", "ERROR"],
                                   width=10, state="readonly")
        level_combo.pack(side=tk.LEFT, padx=(0, 10))
        level_combo.bind('<<ComboboxSelected>>', self.apply_filter)

        # 操作按钮
        ttk.Button(filter_frame, text="🗑️ 清空", command=self.clear_logs, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="📋 复制", command=self.copy_logs, width=8).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="💾 导出", command=self.export_logs, width=8).pack(side=tk.LEFT)

        # 日志显示区域
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview显示日志
        columns = ('time', 'module', 'level', 'message')
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show='headings', height=self.height)

        # 设置列标题和宽度
        self.log_tree.heading('time', text='时间')
        self.log_tree.heading('module', text='模块')
        self.log_tree.heading('level', text='级别')
        self.log_tree.heading('message', text='消息')

        self.log_tree.column('time', width=80, minwidth=80)
        self.log_tree.column('module', width=100, minwidth=80)
        self.log_tree.column('level', width=80, minwidth=80)
        self.log_tree.column('message', width=500, minwidth=200)

        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        scrollbar_x = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL, command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 布局
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置不同级别的颜色
        self.log_tree.tag_configure('INFO', foreground='black')
        self.log_tree.tag_configure('WARNING', foreground='orange')
        self.log_tree.tag_configure('ERROR', foreground='red')
        self.log_tree.tag_configure('SUCCESS', foreground='green')

        # 设置不同模块的背景色（浅色）
        self.log_tree.tag_configure('分账结果查询', background='#f0fff8')
        self.log_tree.tag_configure('配置管理', background='#fff0f5')
        self.log_tree.tag_configure('系统', background='#f8f8f8')
        self.log_tree.tag_configure('挂账充值', background='#f8f0ff')

    def start_log_monitor(self):
        """启动日志监控"""
        self.check_log_queue()

    def check_log_queue(self):
        """检查日志队列"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.add_log_entry(log_entry)
        except queue.Empty:
            pass

        # 每100ms检查一次
        self.parent.after(100, self.check_log_queue)

    def add_log_entry(self, log_entry):
        """添加日志条目"""
        self.log_data.append(log_entry)

        # 限制日志数量，避免内存过大
        if len(self.log_data) > 2000:
            self.log_data = self.log_data[-1000:]  # 保留最后1000条
            self.refresh_display()
        else:
            self.insert_log_item(log_entry)

    def insert_log_item(self, log_entry):
        """插入日志项"""
        level = log_entry['level']
        module = log_entry['module']

        # 确定显示标签
        tags = []

        # 级别标签
        if level in ['INFO', 'WARNING', 'ERROR']:
            tags.append(level)
        elif '✅' in log_entry['message']:
            tags.append('SUCCESS')
        else:
            tags.append('INFO')

        # 模块标签
        if module in ['订单上传', '余额查询', '账户余额查询', '分账管理', '挂账充值',
                      '分账结果查询', '配置管理', '系统']:
            tags.append(module)

        # 检查是否应该显示此日志项
        if self._should_show_log(log_entry):
            self.log_tree.insert('', tk.END, values=(
                log_entry['time'],
                module,
                level,
                log_entry['message']
            ), tags=tuple(tags))

            # 自动滚动到底部
            children = self.log_tree.get_children()
            if children:
                self.log_tree.see(children[-1])

    def _should_show_log(self, log_entry):
        """判断是否应该显示此日志项"""
        # 模块筛选
        module_filter = self.module_var.get()
        if module_filter != "全部" and log_entry['module'] != module_filter:
            return False

        # 级别筛选
        level_filter = self.level_var.get()
        if level_filter != "全部" and log_entry['level'] != level_filter:
            return False

        return True

    def apply_filter(self, event=None):
        """应用筛选"""
        self.refresh_display()

    def refresh_display(self):
        """刷新显示"""
        # 清空现有项目
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        # 应用筛选并重新显示
        for log_entry in self.log_data:
            if self._should_show_log(log_entry):
                self.insert_log_item(log_entry)

    def clear_logs(self):
        """清空日志"""
        result = messagebox.askyesno("确认", "确认要清空所有日志吗？")
        if result:
            self.log_data.clear()
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)

    def copy_logs(self):
        """复制日志到剪贴板"""
        try:
            log_text = []

            for log_entry in self.log_data:
                if self._should_show_log(log_entry):
                    log_line = f"{log_entry['time']} [{log_entry['module']}] [{log_entry['level']}] {log_entry['message']}"
                    log_text.append(log_line)

            if log_text:
                self.parent.clipboard_clear()
                self.parent.clipboard_append('\n'.join(log_text))
                messagebox.showinfo("成功", f"已复制 {len(log_text)} 条日志到剪贴板")
            else:
                messagebox.showinfo("信息", "没有日志可复制")
        except Exception as e:
            messagebox.showerror("错误", f"复制日志失败: {str(e)}")

    def export_logs(self):
        """导出日志到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="导出日志",
                initialname=f"系统日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    for log_entry in self.log_data:
                        if self._should_show_log(log_entry):
                            log_line = f"{log_entry['time']} [{log_entry['module']}] [{log_entry['level']}] {log_entry['message']}\n"
                            f.write(log_line)

                messagebox.showinfo("成功", f"日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {str(e)}")

    def add_log(self, level, module, message):
        """手动添加日志（可供外部调用）"""
        log_entry = {
            'level': level,
            'message': message,
            'module': module,
            'time': datetime.now().strftime('%H:%M:%S')
        }
        self.add_log_entry(log_entry)

    def get_log_count(self):
        """获取日志数量"""
        return len(self.log_data)

    def get_filtered_log_count(self):
        """获取筛选后的日志数量"""
        return len([log for log in self.log_data if self._should_show_log(log)])