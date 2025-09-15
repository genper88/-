#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
配置适配器 - config_adapter.py
统一配置获取入口，实现数据库配置优先，静态配置兜底的策略
"""

import logging
from typing import Any, Optional
from config import Config
from config_manager import config_manager


class ConfigAdapter:
    """配置适配器 - 统一配置获取接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config_manager_ready = False
        self._init_config_manager()
    
    def _init_config_manager(self):
        """初始化配置管理器"""
        try:
            # 使用静态配置初始化config_manager的数据库连接
            user, password, dsn = Config.get_db_connection_info()
            config_manager.set_db_config(user, password, dsn)
            self._config_manager_ready = True
            self.logger.info("[配置适配器] 配置管理器初始化成功")
        except Exception as e:
            self.logger.warning(f"[配置适配器] 配置管理器初始化失败，将使用静态配置: {str(e)}")
            self._config_manager_ready = False
    
    def get_config(self, key: str, static_fallback: Any = None) -> Any:
        """
        获取配置值 - 数据库优先，静态配置兜底
        
        Args:
            key: 配置键名
            static_fallback: 静态配置兜底值
            
        Returns:
            配置值
        """
        if self._config_manager_ready:
            try:
                value = config_manager.get_config(key)
                if value is not None:
                    self.logger.info(f"[配置适配器] ✅ 从数据库获取配置 {key}: {type(value).__name__} 值={value}")
                    return value
            except Exception as e:
                self.logger.warning(f"[配置适配器] 从数据库获取配置 {key} 失败: {str(e)}")
        
        # 兜底到静态配置
        self.logger.info(f"[配置适配器] 📄 使用静态配置文件 {key}: 值={static_fallback}")
        return static_fallback
    
    def get_config_with_source(self, key: str, static_fallback: Any = None) -> tuple[Any, str]:
        """
        获取配置值并返回配置来源信息
        
        Args:
            key: 配置键名
            static_fallback: 静态配置兜底值
            
        Returns:
            (配置值, 配置来源)
        """
        if self._config_manager_ready:
            try:
                value = config_manager.get_config(key)
                if value is not None:
                    return value, "数据库"
            except Exception as e:
                self.logger.warning(f"[配置适配器] 从数据库获取配置 {key} 失败: {str(e)}")
        
        # 兜底到静态配置
        return static_fallback, "静态文件"
    
    def set_config(self, key: str, config_value: Any, description: str = "", is_encrypted: bool = False) -> tuple[bool, str]:
        """
        设置配置值到数据库
        
        Args:
            key: 配置键名
            config_value: 配置值 (修复参数名称)
            description: 配置描述
            is_encrypted: 是否加密存储
            
        Returns:
            (成功标志, 消息)
        """
        if not self._config_manager_ready:
            return False, "配置管理器未就绪"
        
        try:
            # 修复参数传递 - 使用正确的参数名
            return config_manager.set_config(
                config_id=key, 
                config_value=config_value, 
                description=description, 
                is_encrypted=is_encrypted
            )
        except Exception as e:
            self.logger.error(f"[配置适配器] 设置配置 {key} 失败: {str(e)}")
            return False, f"设置失败: {str(e)}"
    
    def get_current_environment(self) -> str:
        """获取当前环境"""
        if self._config_manager_ready:
            try:
                return config_manager.get_current_environment()
            except Exception as e:
                self.logger.warning(f"[配置适配器] 从数据库获取环境失败: {str(e)}")
        
        # 兜底到静态配置
        return Config.get_env_name()
    
    def set_current_environment(self, env: str) -> tuple[bool, str]:
        """设置当前环境"""
        if not self._config_manager_ready:
            return False, "配置管理器未就绪"
        
        try:
            return config_manager.set_current_environment(env)
        except Exception as e:
            self.logger.error(f"[配置适配器] 设置环境失败: {str(e)}")
            return False, f"设置失败: {str(e)}"
    
    # =====  API 配置获取方法 =====
    def get_api_url(self) -> str:
        """获取API地址"""
        return self.get_config("API_URL", Config.API_URL)
    
    def get_app_id(self) -> str:
        """获取APP_ID"""
        return self.get_config("APP_ID", Config.APP_ID)
    
    def get_node_id(self) -> str:
        """获取机构号"""
        return self.get_config("NODE_ID", Config.NODE_ID)
    
    def get_merchant_id(self) -> str:
        """获取商户号"""
        return self.get_config("MERCHANT_ID", Config.MERCHANT_ID)
    
    def get_store_id(self) -> str:
        """获取门店ID"""
        return self.get_config("STORE_ID", Config.STORE_ID)
    
    def get_private_key(self) -> str:
        """获取私钥"""
        return self.get_config("PRIVATE_KEY", Config.PRIVATE_KEY)
    
    # =====  数据库配置获取方法 =====
    def get_db_connection_info(self) -> tuple[str, str, str]:
        """获取数据库连接信息"""
        try:
            db_config = self.get_config("DB_CONFIG", Config.DB_CONFIG)
            return db_config['user'], db_config['password'], db_config['dsn']
        except Exception:
            return Config.get_db_connection_info()
    
    # =====  业务配置获取方法 =====
    def get_pay_merchant_id(self) -> str:
        """获取支付商户号"""
        return self.get_config("PAY_MERCHANT_ID", Config.PAY_MERCHANT_ID)
    
    def get_order_upload_mode_normal(self) -> str:
        """获取普通订单上传模式"""
        return self.get_config("ORDER_UPLOAD_MODE_NORMAL", Config.ORDER_UPLOAD_MODE_NORMAL)
    
    def get_order_upload_mode_recharge(self) -> str:
        """获取挂账充值上传模式"""
        return self.get_config("ORDER_UPLOAD_MODE_RECHARGE", Config.ORDER_UPLOAD_MODE_RECHARGE)
    
    def get_account_type(self) -> str:
        """获取账户类型"""
        return self.get_config("ACCOUNT_TYPE", Config.ACCOUNT_TYPE)
    
    def get_account_type_normal(self) -> str:
        """获取普通订单账户类型"""
        return self.get_config("ACCOUNT_TYPE_NORMAL", Config.ACCOUNT_TYPE_NORMAL)
    
    def get_account_type_recharge(self) -> str:
        """获取挂账充值账户类型"""
        return self.get_config("ACCOUNT_TYPE_RECHARGE", Config.ACCOUNT_TYPE_RECHARGE)
    
    def get_auto_execute_time(self) -> str:
        """获取自动执行时间"""
        return self.get_config("AUTO_EXECUTE_TIME", Config.AUTO_EXECUTE_TIME)
    
    def get_request_timeout(self) -> int:
        """获取请求超时时间"""
        return self.get_config("REQUEST_TIMEOUT", Config.REQUEST_TIMEOUT)
    
    def get_batch_size(self) -> int:
        """获取批量处理大小"""
        return self.get_config("BATCH_SIZE", Config.BATCH_SIZE)
    
    def get_retry_count(self) -> int:
        """获取重试次数"""
        return self.get_config("RETRY_COUNT", Config.RETRY_COUNT)
    
    # =====  分账配置获取方法 =====
    def get_split_config(self) -> dict:
        """获取分账配置"""
        return self.get_config("SPLIT_CONFIG", Config.SPLIT_CONFIG)
    
    def get_split_target_merchants(self) -> list:
        """获取分账目标商户列表"""
        return self.get_config("SPLIT_TARGET_MERCHANTS", Config.SPLIT_TARGET_MERCHANTS)
    
    def get_payer_merchant_id(self) -> str:
        """获取付款方商户号"""
        split_config = self.get_split_config()
        return split_config.get('PAYER_MERCHANT_ID', '')
    
    def get_payee_jms_merchant_id(self) -> str:
        """获取加盟商收款账号"""
        split_config = self.get_split_config()
        return split_config.get('PAYEE_JMS_MERCHANT_ID', '')
    
    def get_payee_gs_merchant_id(self) -> str:
        """获取公司收款账号"""
        split_config = self.get_split_config()
        return split_config.get('PAYEE_GS_MERCHANT_ID', '')
    
    # =====  查询配置获取方法 =====
    def get_balance_pay_query_config(self) -> dict:
        """获取余额支付查询配置"""
        return self.get_config("BALANCE_PAY_QUERY_CONFIG", Config.BALANCE_PAY_QUERY_CONFIG)
    
    def get_balance_pay_query_node_id(self) -> str:
        """获取余额支付查询机构号"""
        config = self.get_balance_pay_query_config()
        return config.get('NODE_ID', self.get_node_id())
    
    def get_auto_query_interval(self) -> int:
        """获取自动查询间隔"""
        config = self.get_balance_pay_query_config()
        return config.get('AUTO_QUERY_INTERVAL', 5)
    
    def get_account_balance_query_config(self) -> dict:
        """获取账户余额查询配置"""
        return self.get_config("ACCOUNT_BALANCE_QUERY_CONFIG", Config.ACCOUNT_BALANCE_QUERY_CONFIG)
    
    def get_account_balance_node_id(self) -> str:
        """获取账户余额查询机构号"""
        config = self.get_account_balance_query_config()
        return config.get('NODE_ID', self.get_node_id())
    
    def get_default_account_type(self) -> str:
        """获取默认账户类型"""
        config = self.get_account_balance_query_config()
        return config.get('DEFAULT_ACCOUNT_TYPE', '1')
    
    def get_account_balance_auto_interval(self) -> int:
        """获取账户余额自动查询间隔"""
        config = self.get_account_balance_query_config()
        return config.get('AUTO_QUERY_INTERVAL', 10)
    
    def get_default_merchant_id_for_balance(self) -> str:
        """获取默认查询余额的商户号"""
        config = self.get_account_balance_query_config()
        return config.get('DEFAULT_MERCHANT_ID', '')
    
    def get_merchant_query_sql(self) -> str:
        """获取商户查询SQL语句"""
        config = self.get_account_balance_query_config()
        return config.get('QUERY_SQL', '')

    # =====  动态配置策略方法 =====
    def should_use_dynamic_merchant_id(self) -> bool:
        """判断是否应该使用动态商户号"""
        return self.get_config("USE_DYNAMIC_MERCHANT_ID", Config.should_use_dynamic_merchant_id())
    
    def should_use_dynamic_store_id(self) -> bool:
        """判断是否应该使用动态门店ID"""
        return self.get_config("USE_DYNAMIC_STORE_ID", Config.should_use_dynamic_store_id())
    
    # =====  环境相关方法 =====
    def get_env_name(self) -> str:
        """获取环境名称"""
        env = self.get_current_environment()
        return "生产环境" if env == "PROD" else "测试环境"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.get_current_environment() == "PROD"
    
    # =====  配置验证方法 =====
    def is_config_ready(self) -> tuple[bool, str]:
        """检查配置是否完整"""
        try:
            errors = []
            
            # 检查基本配置
            if not self.get_app_id():
                errors.append("APP_ID未配置")
            if not self.get_node_id():
                errors.append("NODE_ID未配置")
            if not self.get_merchant_id():
                errors.append("MERCHANT_ID未配置")
            if not self.get_store_id():
                errors.append("STORE_ID未配置")
            
            # 检查数据库配置
            user, password, dsn = self.get_db_connection_info()
            if not user or not password or not dsn:
                errors.append("数据库配置不完整")
            
            # 检查私钥配置
            private_key = self.get_private_key()
            if not private_key or '-----BEGIN' not in private_key:
                errors.append("私钥未正确配置")
            
            if errors:
                return False, f"配置不完整: {', '.join(errors)}"
            
            return True, f"配置已就绪 - {self.get_env_name()}"
            
        except Exception as e:
            return False, f"配置验证异常: {str(e)}"
    
    def get_config_summary(self) -> dict:
        """获取配置摘要"""
        return {
            'environment': self.get_env_name(),
            'api_url': self.get_api_url(),
            'app_id': self.get_app_id(),
            'node_id': self.get_node_id(),
            'merchant_strategy': '动态获取' if self.should_use_dynamic_merchant_id() else '配置文件',
            'store_strategy': '动态获取' if self.should_use_dynamic_store_id() else '配置文件',
            'database_ready': self._config_manager_ready,
            'auto_execute_time': self.get_auto_execute_time(),
            'split_merchants_count': len(self.get_split_target_merchants())
        }
    
    def get_config_sources_info(self) -> dict:
        """
        获取配置来源信息详情
        
        Returns:
            包含各配置项及其来源的字典
        """
        sources = {}
        
        # 关键配置项及其静态配置值
        key_configs = {
            'API_URL': Config.API_URL,
            'APP_ID': Config.APP_ID,
            'NODE_ID': Config.NODE_ID,
            'MERCHANT_ID': Config.MERCHANT_ID,
            'STORE_ID': Config.STORE_ID,
            'PAY_MERCHANT_ID': Config.PAY_MERCHANT_ID,
            'ORDER_UPLOAD_MODE_NORMAL': Config.ORDER_UPLOAD_MODE_NORMAL,
            'ORDER_UPLOAD_MODE_RECHARGE': Config.ORDER_UPLOAD_MODE_RECHARGE,
            'ACCOUNT_TYPE': Config.ACCOUNT_TYPE,
            'ACCOUNT_TYPE_NORMAL': Config.ACCOUNT_TYPE_NORMAL,
            'ACCOUNT_TYPE_RECHARGE': Config.ACCOUNT_TYPE_RECHARGE,
            'AUTO_EXECUTE_TIME': Config.AUTO_EXECUTE_TIME,
            'REQUEST_TIMEOUT': Config.REQUEST_TIMEOUT,
            'BATCH_SIZE': Config.BATCH_SIZE,
            'RETRY_COUNT': Config.RETRY_COUNT
        }
        
        for key, static_value in key_configs.items():
            value, source = self.get_config_with_source(key, static_value)
            sources[key] = {
                'value': value,
                'source': source,
                'static_fallback': static_value
            }
        
        return sources
    
    def print_config_sources(self):
        """
        打印配置来源信息到控制台
        """
        sources = self.get_config_sources_info()
        
        print("\n" + "="*70)
        print("📄 MUMUSO系统配置来源信息")
        print("="*70)
        
        # 修复f-string中的反斜杠问题
        db_status = "✅ 已就绪" if self._config_manager_ready else "❌ 未就绪 (使用静态文件)"
        print(f"🔄 数据库连接状态: {db_status}")
        print(f"🌍 当前环境: {self.get_env_name()}")
        print()
        
        for key, info in sources.items():
            source_icon = "✅" if info['source'] == "数据库" else "📄"
            print(f"{source_icon} {key}:")
            print(f"   来源: {info['source']}")
            print(f"   当前值: {info['value']}")
            if info['source'] == "静态文件":
                print(f"   静态配置: {info['static_fallback']}")
            print()
        
        print("="*70)
        print("ℹ️ 说明:")
        print("  ✅ = 从数据库获取的配置")
        print("  📄 = 从静态文件获取的配置")
        print("  如需修改配置，请使用配置管理界面或修改config.py文件")
        print("="*70 + "\n")


# 全局配置适配器实例
config_adapter = ConfigAdapter()

if __name__ == '__main__':
    print("🔧 配置适配器测试")
    print("=" * 50)
    
    # 测试配置获取
    print(f"🌍 当前环境: {config_adapter.get_env_name()}")
    print(f"🔗 API地址: {config_adapter.get_api_url()}")
    print(f"🏢 APP_ID: {config_adapter.get_app_id()}")
    
    # 修复f-string中的反斜杠问题
    status_text = "✅ 就绪" if config_adapter._config_manager_ready else "❌ 未就绪"
    print(f"🔄 配置管理器状态: {status_text}")
    
    # 测试配置验证
    ready, msg = config_adapter.is_config_ready()
    print(f"🔍 配置状态: {msg}")
    
    # 显示配置摘要
    summary = config_adapter.get_config_summary()
    print("\n📊 配置摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 显示详细的配置来源信息
    config_adapter.print_config_sources()