#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
数据库初始化脚本 - init_database.py
用于初始化配置管理相关的数据库表和基础数据
"""

import cx_Oracle
import logging
import json
import sys
import os
from datetime import datetime

# 确保能正确导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config_manager import ConfigManager
from database_config import get_all_ddl_statements, get_drop_statements


class DatabaseInitializer:
    """数据库初始化器"""

    def __init__(self, user: str, password: str, dsn: str):
        self.user = user
        self.password = password
        self.dsn = dsn
        self.logger = logging.getLogger(__name__)

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = cx_Oracle.connect(self.user, self.password, self.dsn)
            return connection
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            raise

    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name
            """, {'table_name': table_name.upper()})

            result = cursor.fetchone()
            exists = result[0] > 0

            cursor.close()
            connection.close()

            return exists

        except Exception as e:
            self.logger.error(f"检查表存在性失败 [{table_name}]: {str(e)}")
            return False

    def drop_all_tables(self, force: bool = False) -> tuple[bool, str]:
        """删除所有配置相关表"""
        if not force:
            confirm = input("⚠️  确定要删除所有配置表吗？这将清除所有配置数据！(yes/no): ")
            if confirm.lower() != 'yes':
                return False, "用户取消操作"

        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            drop_statements = get_drop_statements()
            success_count = 0

            self.logger.info("开始删除配置表...")

            for drop_sql in drop_statements:
                try:
                    cursor.execute(drop_sql)
                    success_count += 1
                    table_name = drop_sql.split()[2]  # 提取表名
                    self.logger.info(f"已删除: {table_name}")
                except cx_Oracle.DatabaseError as e:
                    error_code = e.args[0].code if e.args and hasattr(e.args[0], 'code') else 0
                    # 忽略表不存在等错误
                    if error_code in [942, 2289]:  # 表或序列不存在
                        continue
                    else:
                        self.logger.warning(f"删除失败: {str(e)}")

            connection.commit()
            cursor.close()
            connection.close()

            return True, f"表删除完成，成功删除 {success_count} 个对象"

        except Exception as e:
            self.logger.error(f"删除表失败: {str(e)}")
            return False, f"删除失败: {str(e)}"

    def create_tables(self) -> tuple[bool, str]:
        """创建配置表"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            ddl_statements = get_all_ddl_statements()
            success_count = 0
            error_count = 0

            self.logger.info("开始创建配置表...")

            for ddl in ddl_statements:
                try:
                    cursor.execute(ddl)
                    success_count += 1

                    # 提取对象名称用于日志
                    if "CREATE TABLE" in ddl:
                        table_name = ddl.split()[2]
                        self.logger.info(f"已创建表: {table_name}")
                    elif "CREATE SEQUENCE" in ddl:
                        seq_name = ddl.split()[2]
                        self.logger.info(f"已创建序列: {seq_name}")
                    elif "CREATE INDEX" in ddl:
                        idx_name = ddl.split()[2]
                        self.logger.info(f"已创建索引: {idx_name}")
                    elif "INSERT INTO" in ddl:
                        table_name = ddl.split()[2]
                        self.logger.info(f"已插入数据到: {table_name}")

                except cx_Oracle.DatabaseError as e:
                    error_code = e.args[0].code if e.args and hasattr(e.args[0], 'code') else 0
                    # 忽略已存在的错误
                    if error_code in [955, 1013, 2264]:  # 表已存在，序列已存在，索引已存在
                        self.logger.info(f"对象已存在，跳过: {error_code}")
                        continue
                    else:
                        error_count += 1
                        self.logger.error(f"执行DDL失败: {str(e)}")
                        self.logger.debug(f"失败的SQL: {ddl[:100]}...")

            connection.commit()
            cursor.close()
            connection.close()

            if error_count == 0:
                return True, f"数据库初始化成功，执行了 {success_count} 条语句"
            else:
                return False, f"数据库初始化部分成功，成功 {success_count} 条，失败 {error_count} 条"

        except Exception as e:
            self.logger.error(f"创建表失败: {str(e)}")
            return False, f"创建失败: {str(e)}"

    def migrate_default_configs(self) -> tuple[bool, str]:
        """迁移默认配置数据"""
        try:
            # 初始化配置管理器
            config_manager = ConfigManager()
            config_manager.set_db_config(self.user, self.password, self.dsn)

            # 检查是否已有配置数据
            existing_configs = config_manager.get_all_configs()
            if existing_configs:
                return True, f"配置数据已存在，跳过迁移 (现有 {len(existing_configs)} 项配置)"

            self.logger.info("开始迁移默认配置...")

            # 设置为测试环境
            config_manager.set_current_environment("TEST")

            # 迁移测试环境配置
            test_configs = {
                "API_URL": {
                    "value": "https://fzxt-yzt-openapi.imageco.cn",
                    "type": "API",
                    "description": "测试环境API地址"
                },
                "APP_ID": {
                    "value": "202507261398698683184185344",
                    "type": "API",
                    "description": "测试环境APP_ID"
                },
                "NODE_ID": {
                    "value": "00061990",
                    "type": "API",
                    "description": "测试环境机构号"
                },
                "MERCHANT_ID": {
                    "value": "1000000001222",
                    "type": "MERCHANT",
                    "description": "测试环境商户号"
                },
                "STORE_ID": {
                    "value": "123a",
                    "type": "MERCHANT",
                    "description": "测试环境门店ID"
                },
                "USE_DYNAMIC_MERCHANT_ID": {
                    "value": False,
                    "type": "MERCHANT",
                    "description": "是否使用动态商户号"
                },
                "USE_DYNAMIC_STORE_ID": {
                    "value": False,
                    "type": "MERCHANT",
                    "description": "是否使用动态门店ID"
                },
                "PAY_MERCHANT_ID": {
                    "value": "测试支付商户号",
                    "type": "PAYMENT",
                    "description": "支付商户号"
                },
                "ORDER_UPLOAD_MODE_NORMAL": {
                    "value": "3",
                    "type": "PAYMENT",
                    "description": "普通订单上传模式"
                },
                "ORDER_UPLOAD_MODE_RECHARGE": {
                    "value": "2",
                    "type": "PAYMENT",
                    "description": "挂账充值上传模式"
                },
                "ACCOUNT_TYPE": {
                    "value": "2",
                    "type": "PAYMENT",
                    "description": "账户类型(通用)"
                },
                "ACCOUNT_TYPE_NORMAL": {
                    "value": "2",
                    "type": "PAYMENT",
                    "description": "普通订单账户类型"
                },
                "ACCOUNT_TYPE_RECHARGE": {
                    "value": "2",
                    "type": "PAYMENT",
                    "description": "挂账充值账户类型"
                },
                "DB_CONFIG": {
                    "value": {
                        "user": "mmserp",
                        "password": "mu89so7mu",
                        "dsn": "47.102.84.152:1521/mmserp"
                    },
                    "type": "DATABASE",
                    "description": "数据库连接配置"
                },
                "AUTO_EXECUTE_TIME": {
                    "value": "04:00",
                    "type": "SYSTEM",
                    "description": "自动执行时间"
                },
                "REQUEST_TIMEOUT": {
                    "value": 30,
                    "type": "SYSTEM",
                    "description": "请求超时时间(秒)"
                },
                "BATCH_SIZE": {
                    "value": 100,
                    "type": "SYSTEM",
                    "description": "批量处理大小"
                },
                "RETRY_COUNT": {
                    "value": 3,
                    "type": "SYSTEM",
                    "description": "重试次数"
                },
                "PRIVATE_KEY": {
                    "value": """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAoHkgAKyHM/oum3dJ4yOrqWTbrevNt/M+ndkPnWPyqBkHUEq43QIoUm4U+mZExANDkyrc7PopY4/oybgFS8oPZA6OJO4E7+lcD9Kdxkc/ll5knBVjFfVpMxkxF6vWb5YgOgbnflO2aMoofIZSB+SNRoWdDldk6lm41552GV5BiyRib8qDTcqCgutf/IEYmnH3ui+R1d/IF1b4pF1e6Gn/vmyNkIUPKiZ0HGk4W0Ip7qVS55Gz5Krt0CBJPxqeN00oU3rNZWhNOCUoJzYCDVMgpNLzFABIrbMd2NBOrByawkizhMSoTOqVXsUck4iIeZEuGwoZsMg7wYaN+J9M6suLKQIDAQAB
-----END RSA PRIVATE KEY-----""",
                    "type": "API",
                    "description": "RSA私钥",
                    "is_encrypted": True
                }
            }

            # 保存测试环境配置
            success_count = 0
            for config_id, config_info in test_configs.items():
                try:
                    success, message = config_manager.set_config(
                        config_id=config_id,
                        config_value=config_info["value"],
                        config_type=config_info["type"],
                        description=config_info["description"],
                        is_encrypted=config_info.get("is_encrypted", False),
                        update_by="MIGRATION"
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"已迁移配置: {config_id}")
                    else:
                        self.logger.error(f"迁移配置失败 [{config_id}]: {message}")
                except Exception as e:
                    self.logger.error(f"迁移配置异常 [{config_id}]: {str(e)}")

            # 切换到生产环境并创建占位符配置
            config_manager.set_current_environment("PROD")

            prod_configs = {
                "API_URL": {
                    "value": "https://fzxt-yzt-openapi.wangcaio2o.com",
                    "type": "API",
                    "description": "生产环境API地址"
                },
                "APP_ID": {
                    "value": "你的生产APP_ID",
                    "type": "API",
                    "description": "生产环境APP_ID（需要配置）"
                },
                "NODE_ID": {
                    "value": "你的生产NODE_ID",
                    "type": "API",
                    "description": "生产环境机构号（需要配置）"
                },
                "MERCHANT_ID": {
                    "value": "你的生产备用商户号",
                    "type": "MERCHANT",
                    "description": "生产环境商户号（需要配置）"
                },
                "STORE_ID": {
                    "value": "你的生产备用门店ID",
                    "type": "MERCHANT",
                    "description": "生产环境门店ID（需要配置）"
                },
                "DB_CONFIG": {
                    "value": {
                        "user": "生产数据库用户",
                        "password": "生产数据库密码",
                        "dsn": "生产数据库地址"
                    },
                    "type": "DATABASE",
                    "description": "生产环境数据库配置（需要配置）"
                },
                "PRIVATE_KEY": {
                    "value": "你的生产环境私钥内容",
                    "type": "API",
                    "description": "生产环境RSA私钥（需要配置）",
                    "is_encrypted": True
                }
            }

            # 保存生产环境配置
            for config_id, config_info in prod_configs.items():
                try:
                    success, message = config_manager.set_config(
                        config_id=config_id,
                        config_value=config_info["value"],
                        config_type=config_info["type"],
                        description=config_info["description"],
                        is_encrypted=config_info.get("is_encrypted", False),
                        update_by="MIGRATION"
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"已创建生产配置占位符: {config_id}")
                except Exception as e:
                    self.logger.error(f"创建生产配置异常 [{config_id}]: {str(e)}")

            # 切换回测试环境
            config_manager.set_current_environment("TEST")

            return True, f"配置数据迁移完成，共迁移 {success_count} 项配置"

        except Exception as e:
            self.logger.error(f"迁移配置数据失败: {str(e)}")
            return False, f"迁移失败: {str(e)}"

    def verify_installation(self) -> tuple[bool, str]:
        """验证安装结果"""
        try:
            # 检查表是否存在
            tables_to_check = [
                'P_BL_FZ_SYS_CONFIG',
                'P_BL_FZ_ENV_CONFIG',
                'P_BL_FZ_BUSINESS_CONFIG',
                'P_BL_FZ_CONFIG_TEMPLATE'
            ]

            missing_tables = []
            for table in tables_to_check:
                if not self.check_table_exists(table):
                    missing_tables.append(table)

            if missing_tables:
                return False, f"缺少表: {', '.join(missing_tables)}"

            # 检查配置数据
            config_manager = ConfigManager()
            config_manager.set_db_config(self.user, self.password, self.dsn)

            # 检查环境设置
            current_env = config_manager.get_current_environment()

            # 检查配置数量
            test_configs = config_manager.get_all_configs()

            if not test_configs:
                return False, "没有找到配置数据"

            return True, f"安装验证通过 - 当前环境: {current_env}, 配置项: {len(test_configs)} 个"

        except Exception as e:
            self.logger.error(f"验证安装失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

    def full_install(self, rebuild: bool = False) -> tuple[bool, str]:
        """完整安装"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始数据库配置系统完整安装")
            self.logger.info("=" * 60)

            # 如果需要重建，先删除表
            if rebuild:
                self.logger.info("🗑️  删除现有表...")
                success, message = self.drop_all_tables(force=True)
                if not success:
                    return False, f"删除表失败: {message}"
                self.logger.info(f"✅ {message}")

            # 创建表
            self.logger.info("🏗️  创建数据库表...")
            success, message = self.create_tables()
            if not success:
                return False, f"创建表失败: {message}"
            self.logger.info(f"✅ {message}")

            # 迁移配置
            self.logger.info("📦 迁移配置数据...")
            success, message = self.migrate_default_configs()
            if not success:
                return False, f"迁移配置失败: {message}"
            self.logger.info(f"✅ {message}")

            # 验证安装
            self.logger.info("🔍 验证安装结果...")
            success, message = self.verify_installation()
            if not success:
                return False, f"验证失败: {message}"
            self.logger.info(f"✅ {message}")

            self.logger.info("=" * 60)
            self.logger.info("🎉 数据库配置系统安装完成！")
            self.logger.info("=" * 60)

            return True, "数据库配置系统安装成功！可以启动应用程序了。"

        except Exception as e:
            self.logger.error(f"完整安装失败: {str(e)}")
            return False, f"安装失败: {str(e)}"


def main():
    """主函数"""
    print("🔧 MUMUSO配置系统数据库初始化工具")
    print("=" * 60)

    # 自动从config.py读取数据库连接信息
    try:
        # 导入现有配置
        import sys
        import os

        # 确保能导入config模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)

        from config import Config

        # 获取数据库连接信息
        user, password, dsn = Config.get_db_connection_info()

        print("📋 自动读取数据库配置:")
        print(f"   环境: {Config.get_env_name()}")
        print(f"   用户: {user}")
        print(f"   地址: {dsn}")

        # 测试数据库连接
        print("\n🔌 测试数据库连接...")
        test_connection = cx_Oracle.connect(user, password, dsn)
        test_connection.close()
        print("✅ 数据库连接正常")

    except ImportError as e:
        print(f"⚠️  无法导入config模块: {str(e)}")
        print("📝 请手动输入数据库连接信息:")
        user = input("数据库用户名 (默认: mmserp): ") or "mmserp"
        password = input("数据库密码 (默认: mu89so7mu): ") or "mu89so7mu"
        dsn = input("数据库地址 (默认: 47.102.84.152:1521/mmserp): ") or "47.102.84.152:1521/mmserp"

    except Exception as e:
        print(f"❌ 读取配置或连接数据库失败: {str(e)}")
        print("\n是否要手动输入数据库信息？(y/n): ", end="")
        if input().lower() == 'y':
            user = input("数据库用户名 (默认: mmserp): ") or "mmserp"
            password = input("数据库密码 (默认: mu89so7mu): ") or "mu89so7mu"
            dsn = input("数据库地址 (默认: 47.102.84.152:1521/mmserp): ") or "47.102.84.152:1521/mmserp"
        else:
            print("初始化中止")
            return

    print(f"\n🔗 使用数据库连接:")
    print(f"   用户: {user}")
    print(f"   地址: {dsn}")

    # 创建初始化器
    initializer = DatabaseInitializer(user, password, dsn)

    print("\n选择操作:")
    print("1. 完整安装（推荐）")
    print("2. 仅创建表结构")
    print("3. 仅迁移配置数据")
    print("4. 重建系统（删除后重新安装）")
    print("5. 验证安装")

    choice = input("\n请选择操作 (1-5): ")

    if choice == "1":
        # 完整安装
        success, message = initializer.full_install()
        if success:
            print(f"\n✅ {message}")
            print("\n📋 后续步骤:")
            print("1. 运行 python mumuso_gui.py 启动应用")
            print("2. 在【系统环境配置】页签中完善生产环境配置")
            print("3. 根据需要调整各项业务配置")
        else:
            print(f"\n❌ {message}")

    elif choice == "2":
        # 仅创建表
        success, message = initializer.create_tables()
        print(f"\n{'✅' if success else '❌'} {message}")

    elif choice == "3":
        # 仅迁移配置
        success, message = initializer.migrate_default_configs()
        print(f"\n{'✅' if success else '❌'} {message}")

    elif choice == "4":
        # 重建系统
        print("\n⚠️  重建系统将删除所有现有配置数据！")
        confirm = input("确定要继续吗？(yes/no): ")
        if confirm.lower() == 'yes':
            success, message = initializer.full_install(rebuild=True)
            print(f"\n{'✅' if success else '❌'} {message}")
        else:
            print("操作已取消")

    elif choice == "5":
        # 验证安装
        success, message = initializer.verify_installation()
        print(f"\n{'✅' if success else '❌'} {message}")

    else:
        print("\n❌ 无效的选择")

    input("\n按回车键退出...")


if __name__ == '__main__':
    main()