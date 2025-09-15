#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
配置管理器 - config_manager.py
负责从数据库读取和管理所有系统配置
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import cx_Oracle
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib


class ConfigManager:
    """配置管理器 - 统一管理系统配置"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config_cache = {}  # 配置缓存
        self._current_env = None  # 当前环境
        self._db_config = None  # 数据库配置（用于连接配置数据库）
        self._encryption_key = None  # 加密密钥

        # 初始化加密密钥
        self._init_encryption_key()

    def _init_encryption_key(self):
        """初始化加密密钥"""
        try:
            # 使用固定的密钥种子，在实际部署时应该从环境变量或配置文件读取
            key_seed = "MUMUSO_CONFIG_ENCRYPT_KEY_2025"
            self._encryption_key = hashlib.sha256(key_seed.encode()).digest()
        except Exception as e:
            self.logger.error(f"初始化加密密钥失败: {str(e)}")
            self._encryption_key = None

    def _encrypt_value(self, value: str) -> str:
        """加密配置值"""
        if not self._encryption_key or not value:
            return value

        try:
            cipher = AES.new(self._encryption_key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(value.encode(), AES.block_size))
            iv = cipher.iv
            encrypted = base64.b64encode(iv + ct_bytes).decode('utf-8')
            return f"ENC({encrypted})"
        except Exception as e:
            self.logger.error(f"加密配置值失败: {str(e)}")
            return value

    def _decrypt_value(self, encrypted_value: str) -> str:
        """解密配置值"""
        if not self._encryption_key or not encrypted_value:
            return encrypted_value

        # 检查是否是加密值
        if not isinstance(encrypted_value, str) or not encrypted_value.startswith("ENC(") or not encrypted_value.endswith(")"):
            return encrypted_value

        try:
            # 提取加密内容
            encrypted_content = encrypted_value[4:-1]
            encrypted_bytes = base64.b64decode(encrypted_content)

            # 提取IV和密文
            iv = encrypted_bytes[:AES.block_size]
            ct = encrypted_bytes[AES.block_size:]

            # 解密
            cipher = AES.new(self._encryption_key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ct), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            self.logger.error(f"解密配置值失败: {str(e)}")
            return encrypted_value

    def set_db_config(self, user: str, password: str, dsn: str):
        """设置数据库连接配置（用于读取配置数据）"""
        self._db_config = {
            'user': user,
            'password': password,
            'dsn': dsn
        }

    def _get_db_connection(self):
        """获取数据库连接"""
        if not self._db_config:
            raise Exception("数据库配置未设置，请先调用set_db_config()方法")

        try:
            connection = cx_Oracle.connect(
                self._db_config['user'],
                self._db_config['password'],
                self._db_config['dsn']
            )
            return connection
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            raise

    def initialize_database(self) -> Tuple[bool, str]:
        """初始化配置数据库表结构"""
        try:
            from database_config import get_all_ddl_statements

            connection = self._get_db_connection()
            cursor = connection.cursor()

            ddl_statements = get_all_ddl_statements()
            success_count = 0

            for ddl in ddl_statements:
                try:
                    cursor.execute(ddl)
                    success_count += 1
                except cx_Oracle.DatabaseError as e:
                    error_code = e.args[0].code if e.args and hasattr(e.args[0], 'code') else 0
                    # 忽略表已存在等错误
                    if error_code in [955, 1013, 2264]:  # 表已存在，序列已存在，索引已存在
                        continue
                    else:
                        self.logger.warning(f"执行DDL失败: {str(e)}")

            connection.commit()
            cursor.close()
            connection.close()

            return True, f"数据库初始化完成，成功执行 {success_count} 条语句"

        except Exception as e:
            self.logger.error(f"初始化数据库失败: {str(e)}")
            return False, f"初始化失败: {str(e)}"

    def get_current_environment(self) -> str:
        """获取当前环境设置"""
        if self._current_env:
            return self._current_env

        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT CURRENT_ENV FROM P_BL_FZ_ENV_CONFIG 
                WHERE ROWNUM = 1 ORDER BY UPDATE_TIME DESC
            """)

            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result:
                self._current_env = result[0]
                return self._current_env
            else:
                # 如果没有记录，返回默认测试环境
                self._current_env = "TEST"
                return self._current_env

        except Exception as e:
            self.logger.error(f"获取当前环境失败: {str(e)}")
            # 发生错误时返回测试环境
            self._current_env = "TEST"
            return self._current_env

    def set_current_environment(self, env: str, switch_by: str = "SYSTEM") -> Tuple[bool, str]:
        """设置当前环境"""
        if env not in ["TEST", "PROD"]:
            return False, "环境参数必须为 TEST 或 PROD"

        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            # 更新环境设置
            cursor.execute("""
                UPDATE P_BL_FZ_ENV_CONFIG SET 
                    CURRENT_ENV = :1,
                    LAST_SWITCH_TIME = CURRENT_TIMESTAMP,
                    SWITCH_BY = :2,
                    UPDATE_TIME = CURRENT_TIMESTAMP
                WHERE ROWNUM = 1
            """, [env, switch_by])

            # 如果没有记录则插入
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO P_BL_FZ_ENV_CONFIG (ID, CURRENT_ENV, LAST_SWITCH_TIME, SWITCH_BY)
                    VALUES (SEQ_P_BL_FZ_ENV_CONFIG.NEXTVAL, :1, CURRENT_TIMESTAMP, :2)
                """, [env, switch_by])

            connection.commit()
            cursor.close()
            connection.close()

            # 清空缓存，强制重新加载配置
            self._config_cache = {}
            self._current_env = env

            return True, f"环境已切换到: {env}"

        except Exception as e:
            self.logger.error(f"设置环境失败: {str(e)}")
            return False, f"设置失败: {str(e)}"

    def get_config(self, config_id: str, default_value: Any = None) -> Any:
        """获取配置值"""
        # 先从缓存获取
        cache_key = f"{self.get_current_environment()}_{config_id}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT CONFIG_VALUE, IS_ENCRYPTED FROM P_BL_FZ_SYS_CONFIG
                WHERE CONFIG_ID = :1 
                  AND ENVIRONMENT = :2
                  AND IS_ACTIVE = 'Y'
            """, [
                config_id,
                self.get_current_environment()
            ])

            result = cursor.fetchone()
            
            if result:
                config_value, is_encrypted = result
                
                # 处理Oracle LOB字段 - 必须在连接关闭前读取
                if hasattr(config_value, 'read'):
                    config_value = config_value.read()
                
                # 关闭连接
                cursor.close()
                connection.close()
                
                # 确保config_value是字符串
                if config_value is None:
                    config_value = ''
                elif not isinstance(config_value, str):
                    config_value = str(config_value)

                # 解密处理
                if is_encrypted == 'Y':
                    config_value = self._decrypt_value(config_value)

                # 尝试解析JSON
                try:
                    parsed_value = json.loads(config_value)
                    self._config_cache[cache_key] = parsed_value
                    return parsed_value
                except (json.JSONDecodeError, TypeError):
                    # 不是JSON格式，直接返回字符串值
                    self._config_cache[cache_key] = config_value
                    return config_value
            else:
                cursor.close()
                connection.close()
                # 配置不存在，返回默认值
                self._config_cache[cache_key] = default_value
                return default_value

        except Exception as e:
            self.logger.error(f"获取配置失败 [{config_id}]: {str(e)}")
            return default_value

    def set_config(self, config_id: str, config_value: Any, config_type: str = "CUSTOM",
                   description: str = "", is_encrypted: bool = False,
                   update_by: str = "SYSTEM") -> Tuple[bool, str]:
        """设置配置值"""
        try:
            # 处理配置值
            if isinstance(config_value, (dict, list)):
                value_str = json.dumps(config_value, ensure_ascii=False, indent=2)
            else:
                value_str = str(config_value)

            # 加密处理
            if is_encrypted:
                value_str = self._encrypt_value(value_str)

            connection = self._get_db_connection()
            cursor = connection.cursor()

            # 尝试更新
            cursor.execute("""
                UPDATE P_BL_FZ_SYS_CONFIG SET 
                    CONFIG_VALUE = :1,
                    IS_ENCRYPTED = :2,
                    DESCRIPTION = :3,
                    UPDATE_TIME = CURRENT_TIMESTAMP,
                    UPDATE_BY = :4
                WHERE CONFIG_ID = :5 
                  AND ENVIRONMENT = :6
            """, [
                value_str,
                'Y' if is_encrypted else 'N',
                description,
                update_by,
                config_id,
                self.get_current_environment()
            ])

            # 如果没有更新到记录，则插入新记录
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO P_BL_FZ_SYS_CONFIG (
                        CONFIG_ID, CONFIG_NAME, CONFIG_VALUE, CONFIG_TYPE,
                        ENVIRONMENT, IS_ENCRYPTED, DESCRIPTION, CREATE_BY, UPDATE_BY
                    ) VALUES (
                        :1, :2, :3, :4,
                        :5, :6, :7, :8, :9
                    )
                """, [
                    config_id,
                    config_id,  # 默认使用config_id作为名称
                    value_str,
                    config_type,
                    self.get_current_environment(),
                    'Y' if is_encrypted else 'N',
                    description,
                    update_by,
                    update_by
                ])

            connection.commit()
            cursor.close()
            connection.close()

            # 更新缓存
            cache_key = f"{self.get_current_environment()}_{config_id}"
            self._config_cache[cache_key] = config_value

            return True, f"配置 [{config_id}] 保存成功"

        except Exception as e:
            self.logger.error(f"设置配置失败 [{config_id}]: {str(e)}")
            return False, f"设置失败: {str(e)}"

    def get_all_configs(self, config_type: Optional[str] = None) -> Dict[str, Any]:
        """获取所有配置"""
        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            sql = """
                SELECT CONFIG_ID, CONFIG_VALUE, IS_ENCRYPTED, CONFIG_TYPE, DESCRIPTION
                FROM P_BL_FZ_SYS_CONFIG
                WHERE ENVIRONMENT = :1 AND IS_ACTIVE = 'Y'
            """
            params = [self.get_current_environment()]

            if config_type:
                sql += " AND CONFIG_TYPE = :2"
                params.append(config_type)

            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # 处理结果 - 必须在连接关闭前读取LOB
            processed_results = []
            for config_id, config_value, is_encrypted, cfg_type, description in results:
                # 处理Oracle LOB字段
                if hasattr(config_value, 'read'):
                    config_value = config_value.read()
                processed_results.append((config_id, config_value, is_encrypted, cfg_type, description))
            
            cursor.close()
            connection.close()

            configs = {}
            for config_id, config_value, is_encrypted, cfg_type, description in processed_results:
                # 确保config_value是字符串
                if config_value is None:
                    config_value = ''
                elif not isinstance(config_value, str):
                    config_value = str(config_value)
                    
                # 解密处理
                if is_encrypted == 'Y':
                    config_value = self._decrypt_value(config_value)

                # JSON解析
                try:
                    parsed_value = json.loads(config_value)
                except (json.JSONDecodeError, TypeError):
                    parsed_value = config_value

                configs[config_id] = {
                    'value': parsed_value,
                    'type': cfg_type,
                    'description': description,
                    'is_encrypted': is_encrypted == 'Y'
                }

            return configs

        except Exception as e:
            self.logger.error(f"获取所有配置失败: {str(e)}")
            return {}

    def delete_config(self, config_id: str) -> Tuple[bool, str]:
        """删除配置"""
        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE P_BL_FZ_SYS_CONFIG SET 
                    IS_ACTIVE = 'N',
                    UPDATE_TIME = CURRENT_TIMESTAMP
                WHERE CONFIG_ID = :1 
                  AND ENVIRONMENT = :2
            """, [
                config_id,
                self.get_current_environment()
            ])

            connection.commit()
            cursor.close()
            connection.close()

            # 清除缓存
            cache_key = f"{self.get_current_environment()}_{config_id}"
            if cache_key in self._config_cache:
                del self._config_cache[cache_key]

            return True, f"配置 [{config_id}] 删除成功"

        except Exception as e:
            self.logger.error(f"删除配置失败 [{config_id}]: {str(e)}")
            return False, f"删除失败: {str(e)}"

    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache = {}
        self._current_env = None

    def export_configs(self, file_path: str) -> Tuple[bool, str]:
        """导出配置到文件"""
        try:
            configs = self.get_all_configs()

            export_data = {
                'environment': self.get_current_environment(),
                'export_time': datetime.now().isoformat(),
                'configs': configs
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True, f"配置导出成功: {file_path}"

        except Exception as e:
            self.logger.error(f"导出配置失败: {str(e)}")
            return False, f"导出失败: {str(e)}"

    def import_configs(self, file_path: str, override: bool = False) -> Tuple[bool, str]:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            configs = import_data.get('configs', {})
            success_count = 0
            error_count = 0

            for config_id, config_info in configs.items():
                try:
                    # 检查配置是否已存在
                    if not override and self.get_config(config_id) is not None:
                        continue

                    success, msg = self.set_config(
                        config_id=config_id,
                        config_value=config_info['value'],
                        config_type=config_info.get('type', 'IMPORTED'),
                        description=config_info.get('description', ''),
                        is_encrypted=config_info.get('is_encrypted', False),
                        update_by='IMPORT'
                    )

                    if success:
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    self.logger.error(f"导入配置项 [{config_id}] 失败: {str(e)}")
                    error_count += 1

            return True, f"配置导入完成: 成功 {success_count} 项，失败 {error_count} 项"

        except Exception as e:
            self.logger.error(f"导入配置失败: {str(e)}")
            return False, f"导入失败: {str(e)}"


# 全局配置管理器实例
config_manager = ConfigManager()

if __name__ == '__main__':
    print("配置管理器测试")
    print("=" * 50)

    # 这里可以添加测试代码
    print("使用方法:")
    print("from config_manager import config_manager")
    print("config_manager.set_db_config('user', 'password', 'dsn')")
    print("value = config_manager.get_config('API_URL')")