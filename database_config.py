#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
数据库配置表结构定义 - database_config.py
用于存储系统配置信息的数据库表结构
"""

# 配置相关数据库表的DDL语句

# 1. 系统配置主表
CREATE_SYS_CONFIG_TABLE = """
CREATE TABLE P_BL_FZ_SYS_CONFIG (
    CONFIG_ID VARCHAR2(50) PRIMARY KEY,           -- 配置项ID
    CONFIG_NAME VARCHAR2(200) NOT NULL,           -- 配置项名称
    CONFIG_VALUE CLOB,                            -- 配置值(支持大文本)
    CONFIG_TYPE VARCHAR2(50) NOT NULL,            -- 配置类型(API/DB/BUSINESS等)
    ENVIRONMENT VARCHAR2(20) NOT NULL,            -- 环境(TEST/PROD)
    IS_ENCRYPTED VARCHAR2(1) DEFAULT 'N',         -- 是否加密存储
    IS_ACTIVE VARCHAR2(1) DEFAULT 'Y',            -- 是否启用
    DESCRIPTION VARCHAR2(500),                    -- 配置描述
    CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    UPDATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 更新时间
    CREATE_BY VARCHAR2(50),                       -- 创建人
    UPDATE_BY VARCHAR2(50)                        -- 更新人
)
"""

# 2. 环境设置表
CREATE_ENV_CONFIG_TABLE = """
CREATE TABLE P_BL_FZ_ENV_CONFIG (
    ID NUMBER(10) PRIMARY KEY,                   -- 主键ID
    CURRENT_ENV VARCHAR2(20) NOT NULL,           -- 当前环境(TEST/PROD)
    AUTO_SWITCH VARCHAR2(1) DEFAULT 'Y',         -- 是否自动切换
    LAST_SWITCH_TIME TIMESTAMP,                  -- 最后切换时间
    SWITCH_BY VARCHAR2(50),                      -- 切换人
    CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UPDATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# 3. 业务功能配置表
CREATE_BUSINESS_CONFIG_TABLE = """
CREATE TABLE P_BL_FZ_BUSINESS_CONFIG (
    ID NUMBER(10) PRIMARY KEY,                   -- 主键ID
    MODULE_NAME VARCHAR2(50) NOT NULL,           -- 模块名称
    FUNCTION_NAME VARCHAR2(100) NOT NULL,        -- 功能名称
    CONFIG_KEY VARCHAR2(100) NOT NULL,           -- 配置键
    CONFIG_VALUE CLOB,                           -- 配置值
    ENVIRONMENT VARCHAR2(20) NOT NULL,           -- 环境
    IS_ACTIVE VARCHAR2(1) DEFAULT 'Y',           -- 是否启用
    SORT_ORDER NUMBER(5) DEFAULT 0,              -- 排序
    DESCRIPTION VARCHAR2(500),                   -- 描述
    CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UPDATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# 4. 配置模板表
CREATE_CONFIG_TEMPLATE_TABLE = """
CREATE TABLE P_BL_FZ_CONFIG_TEMPLATE (
    TEMPLATE_ID VARCHAR2(50) PRIMARY KEY,        -- 模板ID
    TEMPLATE_NAME VARCHAR2(200) NOT NULL,        -- 模板名称
    TEMPLATE_TYPE VARCHAR2(50) NOT NULL,         -- 模板类型
    TEMPLATE_CONTENT CLOB NOT NULL,              -- 模板内容(JSON格式)
    IS_DEFAULT VARCHAR2(1) DEFAULT 'N',          -- 是否默认模板
    DESCRIPTION VARCHAR2(500),                   -- 模板描述
    CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UPDATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# 创建序列
CREATE_SEQUENCES = [
    "CREATE SEQUENCE SEQ_P_BL_FZ_ENV_CONFIG START WITH 1 INCREMENT BY 1",
    "CREATE SEQUENCE SEQ_P_BL_FZ_BUSINESS_CONFIG START WITH 1 INCREMENT BY 1"
]

# 创建索引
CREATE_INDEXES = [
    "CREATE INDEX IDX_SYS_CONFIG_ENV ON P_BL_FZ_SYS_CONFIG(ENVIRONMENT, CONFIG_TYPE)",
    "CREATE INDEX IDX_SYS_CONFIG_ACTIVE ON P_BL_FZ_SYS_CONFIG(IS_ACTIVE)",
    "CREATE INDEX IDX_BUSINESS_CONFIG_MODULE ON P_BL_FZ_BUSINESS_CONFIG(MODULE_NAME, ENVIRONMENT)",
    "CREATE INDEX IDX_CONFIG_TEMPLATE_TYPE ON P_BL_FZ_CONFIG_TEMPLATE(TEMPLATE_TYPE)"
]

# 插入默认环境配置
INSERT_DEFAULT_ENV_CONFIG = """
INSERT INTO P_BL_FZ_ENV_CONFIG (ID, CURRENT_ENV, AUTO_SWITCH, CREATE_TIME)
VALUES (SEQ_P_BL_FZ_ENV_CONFIG.NEXTVAL, 'TEST', 'Y', CURRENT_TIMESTAMP)
"""

# 插入默认系统配置模板
DEFAULT_CONFIG_TEMPLATE = """
INSERT INTO P_BL_FZ_CONFIG_TEMPLATE (TEMPLATE_ID, TEMPLATE_NAME, TEMPLATE_TYPE, TEMPLATE_CONTENT, IS_DEFAULT, DESCRIPTION)
VALUES (
    'DEFAULT_SYS_CONFIG',
    '默认系统配置模板',
    'SYSTEM',
    '{
        "API_CONFIG": {
            "TEST": {
                "API_URL": "https://fzxt-yzt-openapi.imageco.cn",
                "APP_ID": "202507261398698683184185344",
                "NODE_ID": "00061990",
                "REQUEST_TIMEOUT": 30,
                "RETRY_COUNT": 3
            },
            "PROD": {
                "API_URL": "https://fzxt-yzt-openapi.wangcaio2o.com",
                "APP_ID": "你的生产APP_ID",
                "NODE_ID": "你的生产NODE_ID",
                "REQUEST_TIMEOUT": 60,
                "RETRY_COUNT": 5
            }
        },
        "DB_CONFIG": {
            "TEST": {
                "USER": "mmserp",
                "PASSWORD": "mu89so7mu",
                "DSN": "47.102.84.152:1521/mmserp"
            },
            "PROD": {
                "USER": "生产数据库用户",
                "PASSWORD": "生产数据库密码", 
                "DSN": "生产数据库地址"
            }
        },
        "BUSINESS_CONFIG": {
            "MERCHANT_CONFIG": {
                "TEST": {
                    "MERCHANT_ID": "1000000001222",
                    "STORE_ID": "123a",
                    "USE_DYNAMIC_MERCHANT_ID": false,
                    "USE_DYNAMIC_STORE_ID": false
                },
                "PROD": {
                    "MERCHANT_ID": "你的生产备用商户号",
                    "STORE_ID": "你的生产备用门店ID",
                    "USE_DYNAMIC_MERCHANT_ID": false,
                    "USE_DYNAMIC_STORE_ID": false
                }
            },
            "PAYMENT_CONFIG": {
                "TEST": {
                    "PAY_MERCHANT_ID": "测试支付商户号",
                    "ORDER_UPLOAD_MODE_NORMAL": "3",
                    "ORDER_UPLOAD_MODE_RECHARGE": "2",
                    "ACCOUNT_TYPE": "2",
                    "ACCOUNT_TYPE_NORMAL": "2",
                    "ACCOUNT_TYPE_RECHARGE": "2"
                },
                "PROD": {
                    "PAY_MERCHANT_ID": "生产支付商户号",
                    "ORDER_UPLOAD_MODE_NORMAL": "3",
                    "ORDER_UPLOAD_MODE_RECHARGE": "2",
                    "ACCOUNT_TYPE": "2",
                    "ACCOUNT_TYPE_NORMAL": "2",
                    "ACCOUNT_TYPE_RECHARGE": "2"
                }
            },
            "SPLIT_CONFIG": {
                "COMMON": {
                    "DEFAULT_USER_ID": "01",
                    "DEFAULT_FEE_AMOUNT": 100,
                    "SPLIT_RULE_SOURCE": "1"
                }
            },
            "SYSTEM_CONFIG": {
                "COMMON": {
                    "AUTO_EXECUTE_TIME": "04:00",
                    "BATCH_SIZE": 100,
                    "LOG_LEVEL": "INFO"
                }
            }
        }
    }',
    'Y',
    '系统默认配置模板，包含API、数据库、业务等所有配置项'
)
"""


def get_all_ddl_statements():
    """获取所有DDL语句"""
    ddl_statements = []

    # 添加表创建语句
    ddl_statements.extend([
        CREATE_SYS_CONFIG_TABLE,
        CREATE_ENV_CONFIG_TABLE,
        CREATE_BUSINESS_CONFIG_TABLE,
        CREATE_CONFIG_TEMPLATE_TABLE
    ])

    # 添加序列创建语句
    ddl_statements.extend(CREATE_SEQUENCES)

    # 添加索引创建语句
    ddl_statements.extend(CREATE_INDEXES)

    # 添加默认数据插入语句
    ddl_statements.extend([
        INSERT_DEFAULT_ENV_CONFIG,
        DEFAULT_CONFIG_TEMPLATE
    ])

    return ddl_statements


def get_drop_statements():
    """获取删除表的语句（用于重建）"""
    return [
        "DROP TABLE P_BL_FZ_SYS_CONFIG CASCADE CONSTRAINTS",
        "DROP TABLE P_BL_FZ_ENV_CONFIG CASCADE CONSTRAINTS",
        "DROP TABLE P_BL_FZ_BUSINESS_CONFIG CASCADE CONSTRAINTS",
        "DROP TABLE P_BL_FZ_CONFIG_TEMPLATE CASCADE CONSTRAINTS",
        "DROP SEQUENCE SEQ_P_BL_FZ_ENV_CONFIG",
        "DROP SEQUENCE SEQ_P_BL_FZ_BUSINESS_CONFIG"
    ]


if __name__ == '__main__':
    print("数据库配置表结构定义")
    print("=" * 50)
    print("包含的表:")
    print("1. P_BL_FZ_SYS_CONFIG - 系统配置主表")
    print("2. P_BL_FZ_ENV_CONFIG - 环境设置表")
    print("3. P_BL_FZ_BUSINESS_CONFIG - 业务功能配置表")
    print("4. P_BL_FZ_CONFIG_TEMPLATE - 配置模板表")
    print("\n使用方法:")
    print("from database_config import get_all_ddl_statements")
    print("ddl_list = get_all_ddl_statements()")