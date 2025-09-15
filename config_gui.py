#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
配置管理GUI界面 - config_gui.py
提供可视化的系统配置管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import threading
from config_manager import config_manager


class ConfigManagerGUI:
    """配置管理GUI界面"""

    def __init__(self, parent_frame, log_queue=None):
        self.parent_frame = parent_frame
        self.log_queue = log_queue
        self.logger = logging.getLogger(__name__)

        # 配置数据
        self.current_configs = {}
        self.config_categories = {
            'API配置': 'API',
            '数据库配置': 'DATABASE', 
            '商户配置': 'MERCHANT',
            '支付配置': 'PAYMENT',
            '分账配置': 'SPLIT',
            '余额查询配置': 'BALANCE_QUERY',
            '账户余额查询配置': 'ACCOUNT_BALANCE',
            '系统配置': 'SYSTEM'
        }
        
        # 定义所有需要管理的配置项目
        self.default_configs = {
            # API配置
            'API_URL': {
                'category': 'API',
                'type': 'text',
                'description': 'API接口地址',
                'default_test': 'https://fzxt-yzt-openapi.imageco.cn',
                'default_prod': 'https://fzxt-yzt-openapi.wangcaio2o.com'
            },
            'APP_ID': {
                'category': 'API',
                'type': 'text', 
                'description': '应用ID',
                'default_test': '202507261398698683184185344',
                'default_prod': '你的生产APP_ID'
            },
            'NODE_ID': {
                'category': 'API',
                'type': 'text',
                'description': '机构号',
                'default_test': '00061990',
                'default_prod': '你的生产NODE_ID'
            },
            'PRIVATE_KEY': {
                'category': 'API',
                'type': 'textarea',
                'description': 'RSA私钥',
                'default_test': '-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----',
                'default_prod': '你的生产环境私钥'
            },
            
            # 数据库配置
            'DB_USER': {
                'category': 'DATABASE',
                'type': 'text',
                'description': '数据库用户名',
                'default_test': 'mmserp',
                'default_prod': '生产数据库用户'
            },
            'DB_PASSWORD': {
                'category': 'DATABASE', 
                'type': 'password',
                'description': '数据库密码',
                'default_test': 'mu89so7mu',
                'default_prod': '生产数据库密码'
            },
            'DB_DSN': {
                'category': 'DATABASE',
                'type': 'text',
                'description': '数据库连接地址',
                'default_test': '47.102.84.152:1521/mmserp',
                'default_prod': '生产数据库地址'
            },
            
            # 商户配置
            'MERCHANT_ID': {
                'category': 'MERCHANT',
                'type': 'text',
                'description': '商户号(备用)',
                'default_test': '1000000001222',
                'default_prod': '你的生产备用商户号'
            },
            'STORE_ID': {
                'category': 'MERCHANT',
                'type': 'text',
                'description': '门店ID(备用)',
                'default_test': '123a',
                'default_prod': '你的生产备用门店ID'
            },
            'USE_DYNAMIC_MERCHANT_ID': {
                'category': 'MERCHANT',
                'type': 'boolean',
                'description': '是否使用动态商户号',
                'default_test': 'false',
                'default_prod': 'true'
            },
            'USE_DYNAMIC_STORE_ID': {
                'category': 'MERCHANT',
                'type': 'boolean',
                'description': '是否使用动态门店ID',
                'default_test': 'false',
                'default_prod': 'true'
            },
            
            # 支付配置
            'PAY_MERCHANT_ID': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '支付商户号',
                'default_test': '1302329392',
                'default_prod': '生产支付商户号'
            },
            'ORDER_UPLOAD_MODE_NORMAL': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '普通订单上传模式',
                'default_test': '3',
                'default_prod': '3'
            },
            'ORDER_UPLOAD_MODE_RECHARGE': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '挂账充值上传模式',
                'default_test': '2',
                'default_prod': '2'
            },
            'ACCOUNT_TYPE': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '账户类型(通用)',
                'default_test': '2',
                'default_prod': '2'
            },
            'ACCOUNT_TYPE_NORMAL': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '普通订单账户类型',
                'default_test': '2',
                'default_prod': '2'
            },
            'ACCOUNT_TYPE_RECHARGE': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '挂账充值账户类型',
                'default_test': '2',
                'default_prod': '2'
            },
            'DEFAULT_USER_ID': {
                'category': 'PAYMENT',
                'type': 'text',
                'description': '默认用户ID',
                'default_test': '01',
                'default_prod': '01'
            },
            'DEFAULT_FEE_AMOUNT': {
                'category': 'PAYMENT',
                'type': 'number',
                'description': '默认手续费金额',
                'default_test': '0',
                'default_prod': '0'
            },
            
            # 分账配置
            'PAYER_MERCHANT_ID': {
                'category': 'SPLIT',
                'type': 'text',
                'description': '加盟商付款账号',
                'default_test': '4637000000016017',
                'default_prod': '生产加盟商付款账号'
            },
            'PAYEE_JMS_MERCHANT_ID': {
                'category': 'SPLIT',
                'type': 'text',
                'description': '加盟商收款账号',
                'default_test': '1000000001225',
                'default_prod': '生产加盟商收款账号'
            },
            'PAYEE_GS_MERCHANT_ID': {
                'category': 'SPLIT',
                'type': 'text',
                'description': '公司收款账号',
                'default_test': '1000000001227',
                'default_prod': '生产公司收款账号'
            },
            'DEFAULT_JMS_AMOUNT': {
                'category': 'SPLIT',
                'type': 'number',
                'description': '默认加盟商分账金额(分)',
                'default_test': '1000',
                'default_prod': '1000'
            },
            'DEFAULT_GS_AMOUNT': {
                'category': 'SPLIT',
                'type': 'number',
                'description': '默认公司分账金额(分)',
                'default_test': '500',
                'default_prod': '500'
            },
            
            # 余额查询配置
            'BALANCE_QUERY_NODE_ID': {
                'category': 'BALANCE_QUERY',
                'type': 'text',
                'description': '余额查询机构号',
                'default_test': '00061990',
                'default_prod': '生产环境机构号'
            },
            'BALANCE_QUERY_INTERVAL': {
                'category': 'BALANCE_QUERY',
                'type': 'number',
                'description': '自动查询间隔(分钟)',
                'default_test': '5',
                'default_prod': '5'
            },
            'BALANCE_QUERY_SQL': {
                'category': 'BALANCE_QUERY',
                'type': 'textarea',
                'description': '余额查询SQL语句',
                'default_test': "select dt.billid,dt.xpbillid,dt.TRADE_NO from P_BL_SELL_PAYAMOUNT_HZ_dt dt where dt.cancelsign='N' and dt.TRADE_NO is not null",
                'default_prod': "select dt.billid,dt.xpbillid,dt.TRADE_NO from P_BL_SELL_PAYAMOUNT_HZ_dt dt where dt.cancelsign='N' and dt.TRADE_NO is not null"
            },
            'BALANCE_QUERY_BATCH_SIZE': {
                'category': 'BALANCE_QUERY',
                'type': 'number',
                'description': '批量查询大小',
                'default_test': '50',
                'default_prod': '100'
            },
            
            # 账户余额查询配置
            'ACCOUNT_BALANCE_NODE_ID': {
                'category': 'ACCOUNT_BALANCE',
                'type': 'text',
                'description': '账户余额查询机构号',
                'default_test': '00061990',
                'default_prod': '生产环境机构号'
            },
            'ACCOUNT_BALANCE_DEFAULT_TYPE': {
                'category': 'ACCOUNT_BALANCE',
                'type': 'text',
                'description': '默认账户类型',
                'default_test': '1',
                'default_prod': '1'
            },
            'ACCOUNT_BALANCE_INTERVAL': {
                'category': 'ACCOUNT_BALANCE',
                'type': 'number',
                'description': '自动查询间隔(分钟)',
                'default_test': '10',
                'default_prod': '15'
            },
            'ACCOUNT_BALANCE_BATCH_SIZE': {
                'category': 'ACCOUNT_BALANCE',
                'type': 'number',
                'description': '批量查询大小',
                'default_test': '20',
                'default_prod': '50'
            },
            
            # 系统配置
            'AUTO_EXECUTE_TIME': {
                'category': 'SYSTEM',
                'type': 'text',
                'description': '自动执行时间(HH:MM)',
                'default_test': '04:00',
                'default_prod': '03:00'
            },
            'REQUEST_TIMEOUT': {
                'category': 'SYSTEM',
                'type': 'number',
                'description': '请求超时时间(秒)',
                'default_test': '30',
                'default_prod': '60'
            },
            'BATCH_SIZE': {
                'category': 'SYSTEM',
                'type': 'number',
                'description': '批量处理大小',
                'default_test': '100',
                'default_prod': '50'
            },
            'RETRY_COUNT': {
                'category': 'SYSTEM',
                'type': 'number',
                'description': '重试次数',
                'default_test': '3',
                'default_prod': '5'
            }
        }

        # 初始化界面
        self.setup_ui()

        # 初始化配置管理器
        self.init_config_manager()

        # 加载配置数据
        self.load_configs()

    def setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题区域
        self.setup_title_frame(main_frame)

        # 环境切换区域
        self.setup_env_frame(main_frame)

        # 主内容区域
        self.setup_content_frame(main_frame)

        # 操作按钮区域
        self.setup_action_frame(main_frame)

    def setup_title_frame(self, parent):
        """设置标题区域"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(title_frame, text="🔧 系统环境配置管理",
                                font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)

        # 状态标签
        self.status_label = ttk.Label(title_frame, text="准备就绪",
                                      foreground="green")
        self.status_label.pack(side=tk.RIGHT)

    def setup_env_frame(self, parent):
        """设置环境切换区域"""
        env_frame = ttk.LabelFrame(parent, text="环境设置", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 当前环境显示
        current_frame = ttk.Frame(env_frame)
        current_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(current_frame, text="当前环境:").pack(side=tk.LEFT)

        self.current_env_var = tk.StringVar(value="TEST")
        self.current_env_label = ttk.Label(current_frame, textvariable=self.current_env_var,
                                           font=('Arial', 10, 'bold'))
        self.current_env_label.pack(side=tk.LEFT, padx=(10, 0))

        # 环境切换按钮
        switch_frame = ttk.Frame(env_frame)
        switch_frame.pack(fill=tk.X)

        self.test_env_btn = ttk.Button(switch_frame, text="🧪 切换到测试环境",
                                       command=lambda: self.switch_environment("TEST"))
        self.test_env_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.prod_env_btn = ttk.Button(switch_frame, text="🚀 切换到生产环境",
                                       command=lambda: self.switch_environment("PROD"))
        self.prod_env_btn.pack(side=tk.LEFT)

    def setup_content_frame(self, parent):
        """设置主内容区域"""
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧配置分类
        left_frame = ttk.LabelFrame(content_frame, text="配置分类", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.configure(width=200)

        # 配置分类列表
        self.category_listbox = tk.Listbox(left_frame, height=15, width=25)
        self.category_listbox.pack(fill=tk.BOTH, expand=True)
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)

        # 填充分类列表
        for category_name in self.config_categories.keys():
            self.category_listbox.insert(tk.END, category_name)

        # 右侧配置详情
        right_frame = ttk.LabelFrame(content_frame, text="配置详情", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 搜索区域
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        search_btn = ttk.Button(search_frame, text="🔍", width=3,
                                command=self.search_configs)
        search_btn.pack(side=tk.RIGHT)

        # 配置项列表
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ('配置项', '值', '类型', '描述')
        self.config_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # 设置列
        self.config_tree.heading('配置项', text='配置项')
        self.config_tree.heading('值', text='当前值')
        self.config_tree.heading('类型', text='类型')
        self.config_tree.heading('描述', text='描述')

        self.config_tree.column('配置项', width=150)
        self.config_tree.column('值', width=200)
        self.config_tree.column('类型', width=80)
        self.config_tree.column('描述', width=200)

        # 滚动条
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
        self.config_tree.configure(yscrollcommand=tree_scroll.set)

        self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定双击事件
        self.config_tree.bind('<Double-1>', self.on_config_edit)

        # 配置编辑区域
        edit_frame = ttk.LabelFrame(right_frame, text="编辑配置", padding=5)
        edit_frame.pack(fill=tk.X, pady=(10, 0))

        # 配置ID
        id_frame = ttk.Frame(edit_frame)
        id_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(id_frame, text="配置ID:", width=10).pack(side=tk.LEFT)
        self.config_id_var = tk.StringVar()
        self.config_id_entry = ttk.Entry(id_frame, textvariable=self.config_id_var)
        self.config_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 配置值
        value_frame = ttk.Frame(edit_frame)
        value_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(value_frame, text="配置值:", width=10).pack(side=tk.LEFT)
        self.config_value_text = tk.Text(value_frame, height=4)
        self.config_value_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 配置选项
        options_frame = ttk.Frame(edit_frame)
        options_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(options_frame, text="类型:").pack(side=tk.LEFT, padx=(0, 5))
        self.config_type_var = tk.StringVar(value="CUSTOM")
        type_combo = ttk.Combobox(options_frame, textvariable=self.config_type_var,
                                  values=['API', 'DATABASE', 'MERCHANT', 'PAYMENT', 'SPLIT', 'SYSTEM', 'CUSTOM'],
                                  width=10)
        type_combo.pack(side=tk.LEFT)

        # 描述
        desc_frame = ttk.Frame(edit_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(desc_frame, text="描述:", width=10).pack(side=tk.LEFT)
        self.config_desc_var = tk.StringVar()
        self.config_desc_entry = ttk.Entry(desc_frame, textvariable=self.config_desc_var)
        self.config_desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 编辑按钮
        edit_btn_frame = ttk.Frame(edit_frame)
        edit_btn_frame.pack(fill=tk.X, pady=(5, 0))

        save_btn = ttk.Button(edit_btn_frame, text="💾 保存配置",
                              command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_btn = ttk.Button(edit_btn_frame, text="🗑️ 删除配置",
                                command=self.delete_config)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(edit_btn_frame, text="🧹 清空表单",
                               command=self.clear_edit_form)
        clear_btn.pack(side=tk.LEFT)

    def setup_action_frame(self, parent):
        """设置操作按钮区域"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X)

        # 左侧按钮
        left_btn_frame = ttk.Frame(action_frame)
        left_btn_frame.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(left_btn_frame, text="🔄 刷新配置",
                                 command=self.load_configs)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        test_btn = ttk.Button(left_btn_frame, text="🧪 测试连接",
                              command=self.test_connection)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 右侧按钮
        right_btn_frame = ttk.Frame(action_frame)
        right_btn_frame.pack(side=tk.RIGHT)

        import_btn = ttk.Button(right_btn_frame, text="📥 导入配置",
                                command=self.import_configs)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))

        export_btn = ttk.Button(right_btn_frame, text="📤 导出配置",
                                command=self.export_configs)
        export_btn.pack(side=tk.LEFT)

    def init_config_manager(self):
        """初始化配置管理器"""
        try:
            # 从原config.py获取数据库配置
            from config import Config
            user, password, dsn = Config.get_db_connection_info()
            
            # 设置数据库配置
            config_manager.set_db_config(user, password, dsn)
            
            # 清空缓存，强制重新加载
            config_manager.clear_cache()
            
            # 测试数据库连接
            current_env = config_manager.get_current_environment()
            
            # 初始化默认配置项
            self.ensure_default_configs()
            
            self.update_status("配置管理器初始化成功", "green")
            self.log_message("INFO", f"配置管理器初始化成功，当前环境: {current_env}")

        except Exception as e:
            error_msg = f"配置管理器初始化失败: {str(e)}"
            self.update_status(error_msg, "red")
            self.log_message("ERROR", error_msg)
            # 显示详细错误信息
            import traceback
            detailed_error = traceback.format_exc()
            self.log_message("ERROR", f"详细错误: {detailed_error}")

    def ensure_default_configs(self):
        """确保默认配置项存在"""
        try:
            current_env = config_manager.get_current_environment()
            env_suffix = '_prod' if current_env == 'PROD' else '_test'
            
            for config_id, config_def in self.default_configs.items():
                # 检查配置是否存在
                existing_config = config_manager.get_config(config_id)
                if not existing_config:
                    # 不存在则创建默认配置
                    default_value = config_def.get(f'default{env_suffix}', config_def.get('default_test', ''))
                    
                    success, message = config_manager.set_config(
                        config_id=config_id,
                        config_value=default_value,
                        config_type=config_def['category'],
                        description=config_def['description'],
                        update_by='SYSTEM_INIT'
                    )
                    
                    if success:
                        self.log_message("INFO", f"创建默认配置: {config_id}")
                    else:
                        self.log_message("WARNING", f"创建默认配置失败: {config_id} - {message}")
            
            self.log_message("INFO", f"默认配置项检查完成")
            
        except Exception as e:
            self.log_message("ERROR", f"初始化默认配置失败: {str(e)}")

    def switch_environment(self, env):
        """切换环境"""
        if messagebox.askyesno("确认", f"确定要切换到{'生产' if env == 'PROD' else '测试'}环境吗？"):
            def switch_worker():
                try:
                    self.update_status(f"正在切换到{env}环境...", "blue")
                    success, message = config_manager.set_current_environment(env, "GUI_USER")

                    if success:
                        self.current_env_var.set(env)
                        self.update_status(f"已切换到{env}环境", "green")
                        self.log_message("INFO", message)

                        # 重新加载配置
                        self.load_configs()
                    else:
                        self.update_status("环境切换失败", "red")
                        self.log_message("ERROR", message)
                        messagebox.showerror("失败", message)

                except Exception as e:
                    error_msg = f"环境切换异常: {str(e)}"
                    self.update_status("环境切换异常", "red")
                    self.log_message("ERROR", error_msg)
                    messagebox.showerror("异常", error_msg)

            # 在后台线程执行
            threading.Thread(target=switch_worker, daemon=True).start()

    def load_configs(self):
        """加载配置数据"""

        def load_worker():
            try:
                self.update_status("正在加载配置...", "blue")
                self.log_message("INFO", "开始加载配置数据")

                # 检查配置管理器是否初始化
                if not hasattr(config_manager, '_db_config') or not config_manager._db_config:
                    self.log_message("WARNING", "配置管理器未初始化，重新初始化...")
                    self.init_config_manager()
                
                # 获取当前环境
                current_env = config_manager.get_current_environment()
                self.current_env_var.set(current_env)
                self.log_message("INFO", f"当前环境: {current_env}")

                # 获取所有配置
                self.log_message("INFO", "正在从数据库获取配置...")
                self.current_configs = config_manager.get_all_configs()
                self.log_message("INFO", f"数据库返回 {len(self.current_configs)} 个配置项")

                # 更新界面
                self.parent_frame.after(0, self.update_config_display)

                self.update_status("配置加载成功", "green")
                self.log_message("INFO", f"已加载 {len(self.current_configs)} 个配置项")

            except Exception as e:
                error_msg = f"加载配置失败: {str(e)}"
                self.update_status("配置加载失败", "red")
                self.log_message("ERROR", error_msg)
                
                # 显示详细错误信息
                import traceback
                detailed_error = traceback.format_exc()
                self.log_message("ERROR", f"详细错误: {detailed_error}")

        # 在后台线程执行
        threading.Thread(target=load_worker, daemon=True).start()

    def update_config_display(self):
        """更新配置显示"""
        # 清空树形控件
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        # 添加配置项
        for config_id, config_info in self.current_configs.items():
            value_display = str(config_info['value'])
            if len(value_display) > 50:
                value_display = value_display[:50] + "..."

            self.config_tree.insert('', tk.END, values=(
                config_id,
                value_display,
                config_info['type'],
                config_info['description']
            ))

    def on_category_select(self, event):
        """配置分类选择事件"""
        selection = self.category_listbox.curselection()
        if selection:
            category_name = self.category_listbox.get(selection[0])
            category_type = self.config_categories[category_name]
            self.filter_configs_by_type(category_type)

    def filter_configs_by_type(self, config_type):
        """根据类型筛选配置"""
        # 清空树形控件
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        # 添加匹配的配置项
        for config_id, config_info in self.current_configs.items():
            if config_info['type'] == config_type:
                value_display = str(config_info['value'])
                if len(value_display) > 50:
                    value_display = value_display[:50] + "..."

                self.config_tree.insert('', tk.END, values=(
                    config_id,
                    value_display,
                    config_info['type'],
                    config_info['description']
                ))

    def on_search(self, event):
        """搜索事件"""
        search_text = self.search_var.get().lower()

        # 清空树形控件
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        # 搜索匹配的配置项
        for config_id, config_info in self.current_configs.items():
            if (search_text in config_id.lower() or
                    search_text in str(config_info['value']).lower() or
                    search_text in config_info['description'].lower()):

                value_display = str(config_info['value'])
                if len(value_display) > 50:
                    value_display = value_display[:50] + "..."

                self.config_tree.insert('', tk.END, values=(
                    config_id,
                    value_display,
                    config_info['type'],
                    config_info['description']
                ))

    def search_configs(self):
        """搜索配置"""
        self.on_search(None)

    def on_config_edit(self, event):
        """配置编辑事件"""
        selection = self.config_tree.selection()
        if selection:
            item = self.config_tree.item(selection[0])
            config_id = item['values'][0]

            if config_id in self.current_configs:
                config_info = self.current_configs[config_id]

                # 填充编辑表单
                self.config_id_var.set(config_id)

                # 格式化配置值
                value = config_info['value']
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False, indent=2)
                else:
                    value_str = str(value)

                self.config_value_text.delete(1.0, tk.END)
                self.config_value_text.insert(1.0, value_str)

                self.config_type_var.set(config_info['type'])
                self.config_desc_var.set(config_info['description'])
                self.is_encrypted_var.set(config_info['is_encrypted'])

    def save_config(self):
        """保存配置"""
        config_id = self.config_id_var.get().strip()
        if not config_id:
            messagebox.showwarning("警告", "请输入配置ID")
            return

        config_value = self.config_value_text.get(1.0, tk.END).strip()
        config_type = self.config_type_var.get()
        description = self.config_desc_var.get().strip()

        # 尝试解析JSON
        try:
            parsed_value = json.loads(config_value)
        except json.JSONDecodeError:
            # 不是JSON格式，作为字符串处理
            parsed_value = config_value

        def save_worker():
            try:
                self.update_status("正在保存配置...", "blue")
                success, message = config_manager.set_config(
                    config_id=config_id,
                    config_value=parsed_value,
                    config_type=config_type,
                    description=description,
                    update_by="GUI_USER"
                )

                if success:
                    self.update_status("配置保存成功", "green")
                    self.log_message("INFO", message)

                    # 重新加载配置
                    self.load_configs()
                else:
                    self.update_status("配置保存失败", "red")
                    self.log_message("ERROR", message)
                    messagebox.showerror("失败", message)

            except Exception as e:
                error_msg = f"保存配置异常: {str(e)}"
                self.update_status("保存配置异常", "red")
                self.log_message("ERROR", error_msg)
                messagebox.showerror("异常", error_msg)

        # 在后台线程执行
        threading.Thread(target=save_worker, daemon=True).start()

    def delete_config(self):
        """删除配置"""
        config_id = self.config_id_var.get().strip()
        if not config_id:
            messagebox.showwarning("警告", "请选择要删除的配置项")
            return

        if messagebox.askyesno("确认", f"确定要删除配置 [{config_id}] 吗？"):
            def delete_worker():
                try:
                    self.update_status("正在删除配置...", "blue")
                    success, message = config_manager.delete_config(config_id)

                    if success:
                        self.update_status("配置删除成功", "green")
                        self.log_message("INFO", message)

                        # 清空编辑表单
                        self.clear_edit_form()

                        # 重新加载配置
                        self.load_configs()
                    else:
                        self.update_status("配置删除失败", "red")
                        self.log_message("ERROR", message)
                        messagebox.showerror("失败", message)

                except Exception as e:
                    error_msg = f"删除配置异常: {str(e)}"
                    self.update_status("删除配置异常", "red")
                    self.log_message("ERROR", error_msg)
                    messagebox.showerror("异常", error_msg)

            # 在后台线程执行
            threading.Thread(target=delete_worker, daemon=True).start()

    def clear_edit_form(self):
        """清空编辑表单"""
        self.config_id_var.set("")
        self.config_value_text.delete(1.0, tk.END)
        self.config_type_var.set("CUSTOM")
        self.config_desc_var.set("")

    def test_connection(self):
        """测试数据库连接"""

        def test_worker():
            try:
                self.update_status("正在测试连接...", "blue")
                self.log_message("INFO", "开始测试数据库连接")
                
                # 检查配置管理器是否初始化
                if not hasattr(config_manager, '_db_config') or not config_manager._db_config:
                    self.log_message("ERROR", "配置管理器未初始化")
                    raise Exception("配置管理器未初始化，请先初始化")
                
                # 显示数据库配置信息
                db_config = config_manager._db_config
                self.log_message("INFO", f"数据库配置: {db_config['user']}@{db_config['dsn']}")
                
                # 测试直接数据库连接
                import cx_Oracle
                connection = cx_Oracle.connect(
                    db_config['user'],
                    db_config['password'], 
                    db_config['dsn'],
                    encoding="UTF-8"
                )
                self.log_message("INFO", "数据库原始连接成功")
                
                # 测试基本查询
                cursor = connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                self.log_message("INFO", "基本查询测试成功")

                # 尝试获取当前环境（这会测试配置表）
                current_env = config_manager.get_current_environment()
                self.log_message("INFO", f"获取当前环境成功: {current_env}")
                
                # 测试配置查询
                test_configs = config_manager.get_all_configs()
                self.log_message("INFO", f"配置查询成功，找到 {len(test_configs)} 个配置项")

                self.update_status("数据库连接正常", "green")
                self.log_message("INFO", f"数据库连接测试成功")
                
                test_result = f"数据库连接正常\n当前环境: {current_env}\n配置项数量: {len(test_configs)}"
                messagebox.showinfo("成功", test_result)

            except Exception as e:
                error_msg = f"数据库连接测试失败: {str(e)}"
                self.update_status("数据库连接失败", "red")
                self.log_message("ERROR", error_msg)
                
                # 显示详细错误信息
                import traceback
                detailed_error = traceback.format_exc()
                self.log_message("ERROR", f"详细错误: {detailed_error}")
                
                messagebox.showerror("失败", error_msg)

        # 在后台线程执行
        threading.Thread(target=test_worker, daemon=True).start()

    def export_configs(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            def export_worker():
                try:
                    self.update_status("正在导出配置...", "blue")
                    success, message = config_manager.export_configs(file_path)

                    if success:
                        self.update_status("配置导出成功", "green")
                        self.log_message("INFO", message)
                        messagebox.showinfo("成功", message)
                    else:
                        self.update_status("配置导出失败", "red")
                        self.log_message("ERROR", message)
                        messagebox.showerror("失败", message)

                except Exception as e:
                    error_msg = f"导出配置异常: {str(e)}"
                    self.update_status("导出配置异常", "red")
                    self.log_message("ERROR", error_msg)
                    messagebox.showerror("异常", error_msg)

            # 在后台线程执行
            threading.Thread(target=export_worker, daemon=True).start()

    def import_configs(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            # 询问是否覆盖现有配置
            override = messagebox.askyesno("确认", "是否覆盖已存在的配置项？")

            def import_worker():
                try:
                    self.update_status("正在导入配置...", "blue")
                    success, message = config_manager.import_configs(file_path, override)

                    if success:
                        self.update_status("配置导入成功", "green")
                        self.log_message("INFO", message)
                        messagebox.showinfo("成功", message)

                        # 重新加载配置
                        self.load_configs()
                    else:
                        self.update_status("配置导入失败", "red")
                        self.log_message("ERROR", message)
                        messagebox.showerror("失败", message)

                except Exception as e:
                    error_msg = f"导入配置异常: {str(e)}"
                    self.update_status("导入配置异常", "red")
                    self.log_message("ERROR", error_msg)
                    messagebox.showerror("异常", error_msg)

            # 在后台线程执行
            threading.Thread(target=import_worker, daemon=True).start()

    def on_category_select(self, event):
        """分类选择事件"""
        selection = self.category_listbox.curselection()
        if selection:
            category_name = self.category_listbox.get(selection[0])
            category_code = self.config_categories.get(category_name, '')
            self.filter_configs_by_category(category_code)

    def filter_configs_by_category(self, category_code):
        """按分类过滤配置"""
        # 清空树形控件
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        # 添加过滤后的配置项
        for config_id, config_info in self.current_configs.items():
            if not category_code or config_info.get('type') == category_code:
                value_display = str(config_info['value'])
                if len(value_display) > 50:
                    value_display = value_display[:50] + "..."

                self.config_tree.insert('', tk.END, values=(
                    config_id,
                    value_display,
                    config_info.get('type', ''),
                    config_info.get('description', '')
                ))

    def on_search(self, event):
        """搜索事件"""
        # 延迟搜索，避免输入过程中频繁搜索
        if hasattr(self, '_search_timer'):
            self.parent_frame.after_cancel(self._search_timer)
        self._search_timer = self.parent_frame.after(500, self.search_configs)

    def search_configs(self):
        """搜索配置"""
        search_text = self.search_var.get().strip().lower()
        
        # 清空树形控件
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        # 添加符合搜索条件的配置项
        for config_id, config_info in self.current_configs.items():
            if (not search_text or 
                search_text in config_id.lower() or 
                search_text in str(config_info.get('value', '')).lower() or
                search_text in config_info.get('description', '').lower()):
                
                value_display = str(config_info['value'])
                if len(value_display) > 50:
                    value_display = value_display[:50] + "..."

                self.config_tree.insert('', tk.END, values=(
                    config_id,
                    value_display,
                    config_info.get('type', ''),
                    config_info.get('description', '')
                ))

    def on_config_edit(self, event):
        """配置编辑事件"""
        selection = self.config_tree.selection()
        if selection:
            item = self.config_tree.item(selection[0])
            config_id = item['values'][0]
            
            # 加载配置到编辑表单
            if config_id in self.current_configs:
                config_info = self.current_configs[config_id]
                
                self.config_id_var.set(config_id)
                self.config_value_text.delete(1.0, tk.END)
                
                # 格式化显示JSON数据
                value = config_info['value']
                if isinstance(value, (dict, list)):
                    import json
                    formatted_value = json.dumps(value, indent=2, ensure_ascii=False)
                    self.config_value_text.insert(tk.END, formatted_value)
                else:
                    self.config_value_text.insert(tk.END, str(value))
                
                self.config_type_var.set(config_info.get('type', 'CUSTOM'))
                self.config_desc_var.set(config_info.get('description', ''))

    def get_config_summary(self):
        """获取配置摘要"""
        try:
            current_env = config_manager.get_current_environment()
            total_configs = len(self.current_configs)
            
            # 按类型统计
            category_stats = {}
            for config_info in self.current_configs.values():
                category = config_info.get('type', 'UNKNOWN')
                category_stats[category] = category_stats.get(category, 0) + 1
            
            return {
                'environment': current_env,
                'total_configs': total_configs,
                'category_stats': category_stats,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def refresh_ui_state(self):
        """刷新UI状态"""
        try:
            current_env = config_manager.get_current_environment()
            self.current_env_var.set(current_env)
            
            # 更新按钮状态
            if current_env == 'TEST':
                self.test_env_btn.config(state='disabled')
                self.prod_env_btn.config(state='normal')
            else:
                self.test_env_btn.config(state='normal')
                self.prod_env_btn.config(state='disabled')
                
        except Exception as e:
            self.log_message('ERROR', f'刷新UI状态失败: {str(e)}')

    def update_status(self, message, color="black"):
        """更新状态显示"""
        def update():
            try:
                self.status_label.config(text=message, foreground=color)
            except:
                pass  # 忽略GUI组件不存在的错误
        
        try:
            self.parent_frame.after(0, update)
        except:
            pass  # 忽略主线程不在主循环中的错误

    def log_message(self, level, message):
        """记录日志消息"""
        if self.log_queue:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_msg = f"[配置管理] {message}"
            # 使用字典格式发送日志
            self.log_queue.put({
                'level': level,
                'message': log_msg,
                'module': '配置管理',
                'time': timestamp
            })


if __name__ == '__main__':
    # 测试界面
    root = tk.Tk()
    root.title("配置管理器测试")
    root.geometry("1200x800")

    config_gui = ConfigManagerGUI(root)

    root.mainloop()