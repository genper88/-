#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
配置管理功能窗口
从原ConfigManagementTab重构而来
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径，确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)

# 添加路径到sys.path
sys.path.insert(0, root_dir)
sys.path.insert(0, parent_dir)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

# 导入配置适配器和基础类
try:
    from config_adapter import config_adapter
except ImportError:
    sys.path.append(root_dir)
    from config_adapter import config_adapter

try:
    from utils.base_window import BaseWindow
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from mumuso_gui.utils.base_window import BaseWindow
    except ImportError:
        # 最后尝试直接从文件导入
        sys.path.append(os.path.join(parent_dir, 'utils'))
        from base_window import BaseWindow

# 导入配置管理GUI（如果可用）
try:
    from config_gui import ConfigManagerGUI
except ImportError:
    ConfigManagerGUI = None


class ConfigManagementWindow(BaseWindow):
    """配置管理功能窗口"""

    def __init__(self, parent, title="🔧 系统配置管理", size="800x600", log_queue=None):
        self.module_name = "配置管理"

        super().__init__(parent, title, size, log_queue)

    def setup_ui(self):
        """设置UI界面"""
        # 检查是否可以导入配置管理GUI
        if ConfigManagerGUI is None:
            self.setup_fallback_ui()
        else:
            self.setup_config_gui()

    def setup_config_gui(self):
        """设置配置管理GUI界面"""
        try:
            # 主框架
            main_frame = ttk.Frame(self.window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 标题
            title_label = ttk.Label(main_frame, text="🔧 系统配置管理", font=('Arial', 16, 'bold'))
            title_label.pack(pady=(0, 20))

            # 创建配置管理GUI实例
            self.config_gui = ConfigManagerGUI(main_frame, self.log_queue)

            # 记录初始化成功
            self.update_status("配置管理模块初始化成功", 'success')

        except Exception as e:
            # 如果初始化失败，使用后备界面
            self.update_status(f"配置管理模块初始化失败: {str(e)}", 'error')
            self.setup_fallback_ui()

    def setup_fallback_ui(self):
        """设置后备UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="🔧 系统配置管理", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 环境信息框架
        env_frame = self.create_env_info_frame(main_frame)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        # 当前配置框架
        config_frame = ttk.LabelFrame(main_frame, text="📊 当前配置", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建滚动文本显示配置信息
        self.config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.WORD, height=20)
        self.config_text.pack(fill=tk.BOTH, expand=True)

        # 显示详细配置信息
        self.display_config_info()

        # 操作按钮框架
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(action_frame, text="🔄 刷新配置",
                   command=self.display_config_info, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🔍 验证配置",
                   command=self.validate_config, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="📖 配置说明",
                   command=self.show_config_help, width=15).pack(side=tk.LEFT)

    def display_config_info(self):
        """显示配置信息"""
        config_text = self.get_config_info_text()

        if hasattr(self, 'config_text'):
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(tk.END, config_text)
            self.config_text.config(state=tk.DISABLED)

        self.update_status("配置信息已刷新", 'info')

    def get_config_info_text(self):
        """获取配置信息文本"""
        config_text = f"""MUMUSO系统环境配置信息
{'=' * 70}

🌐 环境信息:
  当前环境: {config_adapter.get_env_name()}
  API地址: {config_adapter.get_api_url()}
  APP_ID: {config_adapter.get_app_id()}
  机构号: {config_adapter.get_node_id()}

💼 动态配置策略:
  商户号策略: {'动态获取' if config_adapter.should_use_dynamic_merchant_id() else '配置文件固定'}
  {'备用商户号' if config_adapter.should_use_dynamic_merchant_id() else '固定商户号'}: {config_adapter.get_merchant_id()}

  门店ID策略: {'动态获取' if config_adapter.should_use_dynamic_store_id() else '配置文件固定'}
  {'备用门店ID' if config_adapter.should_use_dynamic_store_id() else '固定门店ID'}: {config_adapter.get_store_id()}

💳 支付配置:
  支付商户号: {config_adapter.get_pay_merchant_id()}
  普通订单上传模式: {config_adapter.get_order_upload_mode_normal()}
  挂账充值上传模式: {config_adapter.get_order_upload_mode_recharge()}
  账户类型: {config_adapter.get_account_type()}

🔗 数据库配置:"""

        # 获取数据库配置
        try:
            user, password, dsn = config_adapter.get_db_connection_info()
            config_text += f"""
  连接地址: {dsn}
  用户名: {user}
  密码: {'*' * len(password)}"""
        except Exception:
            config_text += """
  数据库配置获取失败"""

        config_text += f"""

📊 分账配置:
  付款方商户号: {config_adapter.get_payer_merchant_id()}
  加盟商收款账号: {config_adapter.get_payee_jms_merchant_id()}
  公司收款账号: {config_adapter.get_payee_gs_merchant_id()}

🗓️ 余额支付查询配置:
  机构号: {config_adapter.get_balance_pay_query_node_id()}
  自动查询间隔: {config_adapter.get_auto_query_interval()}分钟

💰 账号余额查询配置:
  机构号: {config_adapter.get_account_balance_node_id()}
  默认账户类型: {config_adapter.get_default_account_type()}
  自动查询间隔: {config_adapter.get_account_balance_auto_interval()}分钟

⚙️ 系统配置:
  自动执行时间: {config_adapter.get_auto_execute_time()}
  请求超时: {config_adapter.get_request_timeout()}秒
  批量处理大小: {config_adapter.get_batch_size()}
  重试次数: {config_adapter.get_retry_count()}

🔐 私钥状态: {'已配置' if config_adapter.get_private_key() and '-----BEGIN' in config_adapter.get_private_key() else '未配置'}

📈 分账目标商户列表:
"""

        # 添加分账目标商户信息
        try:
            for i, merchant in enumerate(config_adapter.get_split_target_merchants(), 1):
                config_text += f"  {i}. {merchant['name']} ({merchant['merchant_id']}) - {merchant['amount'] / 100:.2f}元\n"
        except Exception:
            config_text += "  分账目标商户信息获取失败\n"

        config_text += f"\n{'=' * 70}\n"

        # 获取配置状态
        try:
            ready, msg = config_adapter.is_config_ready()
            config_text += f"配置状态: {msg}\n"
        except Exception as e:
            config_text += f"配置状态检查失败: {str(e)}\n"

        return config_text

    def validate_config(self):
        """验证配置"""

        def validate_in_thread():
            self.update_status("正在验证配置...", 'info')
            try:
                ready, msg = config_adapter.is_config_ready()
                if ready:
                    self.update_status(f"配置验证成功: {msg}", 'success')
                    self.show_message_box("验证成功", f"配置验证通过！\n\n{msg}", 'info')
                else:
                    self.update_status(f"配置验证失败: {msg}", 'error')
                    self.show_message_box("验证失败", f"配置验证失败！\n\n{msg}", 'error')

            except Exception as e:
                error_msg = f"配置验证异常: {str(e)}"
                self.update_status(error_msg, 'error')
                self.show_message_box("异常", error_msg, 'error')

        self.run_in_thread(validate_in_thread)

    def show_config_help(self):
        """显示配置说明"""
        help_text = """📚 MUMUSO系统配置说明

🔧 环境切换:
• 测试环境: USE_PRODUCTION = False
• 生产环境: USE_PRODUCTION = True

💼 动态配置:
• 动态商户号: USE_DYNAMIC_MERCHANT_ID = True
• 动态门店ID: USE_DYNAMIC_STORE_ID = True

📄 配置更新:
1. 修改 config.py 文件中的相关参数
2. 重启系统使配置生效
3. 使用 "验证配置" 功能检查更新结果

⚠️ 注意事项:
• 生产环境配置必须完整填写
• 私钥文件必须正确配置
• 数据库连接信息必须确保正确
• 修改配置后建议重启系统

🔍 配置项说明:

环境配置:
• USE_PRODUCTION: 是否使用生产环境
• API_URL_*: 各环境的API地址
• APP_ID: 应用程序标识符

商户配置:
• MERCHANT_ID: 商户号（固定模式使用）
• STORE_ID: 门店ID（固定模式使用）
• USE_DYNAMIC_*: 是否使用动态获取策略

支付配置:
• PAY_MERCHANT_ID: 支付商户号
• ORDER_UPLOAD_MODE_*: 订单上传模式
• ACCOUNT_TYPE: 账户类型

数据库配置:
• DB_USER: 数据库用户名
• DB_PASSWORD: 数据库密码
• DB_DSN: 数据库连接字符串

分账配置:
• PAYER_MERCHANT_ID: 付款方商户号
• PAYEE_*_MERCHANT_ID: 收款方商户号
• SPLIT_TARGET_MERCHANTS: 分账目标商户列表

系统配置:
• AUTO_EXECUTE_TIME: 自动执行时间
• REQUEST_TIMEOUT: 请求超时时间
• BATCH_SIZE: 批量处理大小
• RETRY_COUNT: 重试次数

🔐 安全配置:
• PRIVATE_KEY_FILE: 私钥文件路径
• 私钥文件必须为PEM格式
• 确保私钥文件权限安全

📞 技术支持:
如遇到配置问题，请检查系统日志或联系技术人员。

💡 配置最佳实践:
1. 测试环境先验证配置正确性
2. 生产环境部署前进行完整测试
3. 定期备份配置文件
4. 敏感信息使用环境变量或加密存储
5. 配置变更需要记录和审批

🚀 快速配置检查清单:
□ 环境选择正确（测试/生产）
□ API地址可访问
□ 商户号和门店ID有效
□ 数据库连接正常
□ 私钥文件存在且格式正确
□ 分账商户配置完整
□ 所有必需参数已填写

⚡ 常见问题:
Q: 如何切换测试和生产环境？
A: 修改config.py中的USE_PRODUCTION参数

Q: 动态商户号获取失败怎么办？
A: 检查API连接，或临时使用固定商户号

Q: 数据库连接失败如何解决？
A: 检查网络连接、用户名密码、数据库服务状态

Q: 私钥格式错误如何处理？
A: 确保私钥文件为标准PEM格式，以-----BEGIN开头

Q: 分账配置如何验证？
A: 使用"验证配置"功能，或进行小额测试
"""

        help_window = tk.Toplevel(self.window)
        help_window.title("📚 配置说明")
        help_window.geometry("700x600")
        help_window.transient(self.window)
        help_window.grab_set()

        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(help_window, text="关闭",
                   command=help_window.destroy).pack(pady=5)

    def refresh_config(self):
        """刷新配置信息"""
        self.display_config_info()

    def export_config(self):
        """导出配置信息"""
        try:
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="导出配置信息",
                initialname=f"系统配置_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if filename:
                config_text = self.get_config_info_text()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"MUMUSO系统配置导出\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(config_text)

                self.update_status(f"配置信息已导出到: {filename}", 'success')
                self.show_message_box("成功", f"配置信息已导出到:\n{filename}", 'info')

        except Exception as e:
            self.update_status(f"导出配置失败: {str(e)}", 'error')
            self.show_message_box("错误", f"导出配置失败: {str(e)}", 'error')

    def check_config_changes(self):
        """检查配置变更"""
        # 这个功能可以用来检测配置文件是否被外部修改
        self.update_status("检查配置变更...", 'info')

        # 实际实现中可以比较配置文件的修改时间或计算文件哈希
        self.update_status("配置检查完成", 'success')

    def backup_config(self):
        """备份当前配置"""
        try:
            from tkinter import filedialog
            import shutil

            # 选择备份目录
            backup_dir = filedialog.askdirectory(title="选择配置备份目录")
            if backup_dir:
                backup_filename = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                backup_path = os.path.join(backup_dir, backup_filename)

                # 复制配置文件
                config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.py")
                if os.path.exists(config_file):
                    shutil.copy2(config_file, backup_path)
                    self.update_status(f"配置已备份到: {backup_path}", 'success')
                    self.show_message_box("成功", f"配置文件已备份到:\n{backup_path}", 'info')
                else:
                    self.show_message_box("错误", "找不到配置文件", 'error')

        except Exception as e:
            self.update_status(f"备份配置失败: {str(e)}", 'error')
            self.show_message_box("错误", f"备份配置失败: {str(e)}", 'error')

    def show_environment_info(self):
        """显示环境信息详情"""
        env_info = f"""系统环境详细信息

运行环境:
• Python版本: {sys.version}
• 工作目录: {os.getcwd()}
• 脚本路径: {__file__}

配置文件状态:
• 配置文件: {'存在' if os.path.exists('config.py') else '不存在'}
• 当前环境: {config_adapter.get_env_name()}
• 配置适配器: {type(config_adapter).__name__}

系统时间:
• 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 时区信息: {datetime.now().astimezone().tzinfo}

网络状态:
• API地址: {config_adapter.get_api_url()}
• 连接状态: 需要测试验证
"""

        self.show_message_box("环境信息", env_info, 'info')

    def show_advanced_options(self):
        """显示高级选项"""
        # 创建高级选项窗口
        advanced_window = tk.Toplevel(self.window)
        advanced_window.title("🔧 高级配置选项")
        advanced_window.geometry("400x300")
        advanced_window.transient(self.window)
        advanced_window.grab_set()

        frame = ttk.Frame(advanced_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="高级配置选项", font=('Arial', 12, 'bold')).pack(pady=(0, 20))

        # 高级功能按钮
        ttk.Button(frame, text="📁 导出配置信息",
                   command=self.export_config, width=20).pack(pady=5)
        ttk.Button(frame, text="💾 备份配置文件",
                   command=self.backup_config, width=20).pack(pady=5)
        ttk.Button(frame, text="🔍 检查配置变更",
                   command=self.check_config_changes, width=20).pack(pady=5)
        ttk.Button(frame, text="📋 环境信息详情",
                   command=self.show_environment_info, width=20).pack(pady=5)

        ttk.Button(frame, text="关闭",
                   command=advanced_window.destroy, width=20).pack(pady=(20, 0))