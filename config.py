#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
完整环境配置文件 - config.py (支持动态 STORE_ID 版本)
测试和生产环境各自独立完整配置，支持动态商户号和动态门店ID
"""


class Config:
    """配置类 - 支持动态 STORE_ID 版本"""

    # ===== 🎯 环境切换开关（只需要改这里！）=====
    USE_PRODUCTION = False  # True=生产环境，False=测试环境

    # ===== 💼 动态配置策略 =====
    USE_DYNAMIC_MERCHANT_ID = True  # True=从数据库动态获取商户号(适用于生产环境)
    # False=使用配置文件固定商户号(适用于测试环境)

    USE_DYNAMIC_STORE_ID = True  # True=从数据库动态获取门店ID(适用于生产环境)
    # False=使用配置文件固定门店ID(适用于测试环境)

    # ===== 测试环境完整配置 =====
    _TEST_CONFIG = {
        # API配置
        'API_URL': 'https://fzxt-yzt-openapi.imageco.cn',
        'APP_ID': '202507261398698683184185344',
        'NODE_ID': '00061990',
        'MERCHANT_ID': '1000000001222',  # 测试环境商户号
        'STORE_ID': '123a',  # 测试环境门店ID

        # 阿里云短信服务配置（测试环境）
        'ALIYUN_SMS_CONFIG': {
            'ACCESS_KEY_ID': 'your-test-access-key-id',
            'ACCESS_KEY_SECRET': 'your-test-access-key-secret',
            'REGION_ID': 'cn-hangzhou',
            'SIGN_NAME': '测试签名',
            'TEMPLATE_CODE': 'SMS_123456789'
        },

        # 数据库配置
        'DB_CONFIG': {
            'user': 'mmserp',
            'password': 'mu89so7mu',
            'dsn': '47.102.84.152:1521/mmserp'
        },

        # 私钥配置（测试环境）
        'PRIVATE_KEY': """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAoHkgAKyHM/oum3dJ4yOrqWTbrevNt/M+ndkPnWPyqBkHUEq43QIoUm4U+mZExANDkyrc7PopY4/oybgFS8oPZA6OJO4E7+lcD9Kdxkc/ll5knBVjFfVpMxkxF6vWb5YgOgbnflO2aMoofIZSB+SNRoWdDldk6lm41552GV5BiyRib8qDTcqCgutf/IEYmnH3ui+R1d/IF1b4pF1e6Gn/vmyNkIUPKiZ0HGk4W0Ip7qVS55Gz5Krt0CBJPxqeN00oU3rNZWhNOCUoJzYCDVMgpNLzFABIrbMd2NBOrByawkizhMSoTOqVXsUck4iIeZEuGwoZsMg7wYaN+J9M6suLKQIDAQABAoIBACikRJynFV7un9sz7PyfzhwKtTBpJiLOci9cB/5ej9hO7nFBW2xt3XRy+NEqEYRrJzQgiO9jtBPJILXl60F0nU1D+nAT8CAqw+wl9VuAM/SLV4PITt4C12/fk3VhSd/c77CCiyKNZQdJG9Pd2Oyyz6zqrgoxzBcmPhAty89E9eidGU0PgUpitmmXdNHK6fTl9z0V63N+iqOShzth+feTUZwtPBVd1Mrt8Rkv8Kcx6fjHPNGPqwpio80IlQUcIEZ6N3U49+BCF7eUyRHVRsS7v6/0AendamsLuqqc3ckr51k01iA7G03ZyYq5lSZwG+jR1DT44PFwtOTxIepy2mlfzmECgYEA3mwWeiS7JYmdAAn/HsOuTOAAji9uc6oF/4NVJsbOldpcG4+rvzZdi5t1Kr4OwJNXPWWeJbe2eYVq3oh74yngrTARq7NErEC1NfeWf0x3KeCIf5YacAconG5pqI1N7KTUzzNg3PYiX55PHNCPBx7NZF+TO7o4vuskEwNsPQn1St0CgYEAuLLm/WDkqJNL/kQiG2dIvVglMlSysVYxnr+ZLgU1OtN0mhB9Wsx5ajLFUoJLHW5pW+tRSlePRd87QvTKQ/FIm1nxFrIEKkWgfUQZp+yH3kddZK/pS/sPToM9dj69JqX6pGrJ76l/RBZ540IzD4Oz8peiVPdeMFeSZ0io6l1c/r0CgYEA3W2FwvumRGyHnG5XSW1NrMKkSuj1cLinWASLVRs+tvi4EcgqFyYsYrvVHUQws477nuf3VV1bkAc+qWP+0dvzDPd54BGMIGAbBysA7KJXT510xm/MyhKWX4WcMmzaUuiV4+EmYVO4TLDx2aHXgiMsHuz3StLNg2PcegFCVFIBnRECgYABa57LJAueIEPdWLjKbSjqC9t9X5lgM8F97wtGh1O5eBbVeHr+T8Q/RNSvpcDeIRM+WbjuUW4Qo37ZLPjBPQHJ8A8ilYvip1ZsoDFyUSdaVkIpnBC3PN8JQ4kdd64MtgoPaaLT7QHFjEazsLajz+d6XiApdx2KUaIWmUBzTPSCIQKBgD87Jt9TNkP70GEolnZgA7nJT4BxP0+seNs5hTK1mg1ZtGL7sc7qfm1AHJgj1tsHsgrqXYWNi5DKh8fuwFHC8VSDg6Wf23oTnQ7WQDgwbATjZH7ZISXj/41zFyL2iiRheCZpzRLhhHqsj4EaCxX187zmI/EN6MSpEM7OMwqBg5ev
-----END RSA PRIVATE KEY-----""",

        # 业务配置（测试环境）
        'ORDER_UPLOAD_MODE_NORMAL': '3',  # 普通订单上传模式
        'ORDER_UPLOAD_MODE_RECHARGE': '2',  # 挂账充值上传模式
        'ACCOUNT_TYPE': '2',
        'ACCOUNT_TYPE_NORMAL': '2',  # 普通订单账户类型
        'ACCOUNT_TYPE_RECHARGE': '2',  # 挂账充值账户类型
        'PAY_MERCHANT_ID': '564290057345GBM',#1302329392   挂账 挂账充值用
        'DEFAULT_USER_ID': '01',
        'DEFAULT_FEE_AMOUNT': 0,
        'SPLIT_RULE_SOURCE': '1',

        # 分账相关配置（测试环境）
        'SPLIT_CONFIG': {
            'PAYER_MERCHANT_ID': '4637000000016017YYYYYYY',  # 加盟商付款账号  4637000000016017
            'PAYEE_JMS_MERCHANT_ID': '1000000001225',  # 加盟商收款账号
            'PAYEE_GS_MERCHANT_ID': '1000000001227',  # 公司收款账号
            'PAYER_ACCOUNT_TYPE': '1',  # 付款账户类型：1-付款账户
            'PAYEE_ACCOUNT_TYPE': '0',  # 收款账户类型：0-收款账户
            'DEFAULT_JMS_AMOUNT': 1000,  # 默认加盟商分账金额(分)
            'DEFAULT_GS_AMOUNT': 500,  # 默认公司分账金额(分)
        },

        'SPLIT_TARGET_MERCHANTS': [
            {
                'merchant_id': '1000000001225',
                'name': '加盟商收款账号',
                'amount': 1000  # 10元 = 1000分
            },
            {
                'merchant_id': '1000000001227',
                'name': '公司收款账号',
                'amount': 500  # 5元 = 500分
            }
        ],

        # 余额支付查询配置（测试环境）
        'BALANCE_PAY_QUERY_CONFIG': {
            'NODE_ID': '00061990',  # 测试环境机构号
            'AUTO_QUERY_INTERVAL': 5,  # 自动查询间隔(分钟)
            # 使用您提供的调整后的SQL查询语句
            'QUERY_SQL': "select dt.billid,dt.xpbillid,dt.fz_requestback_no TRADE_NO from P_BL_SELL_PAYAMOUNT_HZ_dt dt where dt.cancelsign='N' and dt.is_fz_execute='Y' and dt.fz_execute_result='N' and dt.fz_requestback_no <> ' '",
            'BATCH_QUERY_SIZE': 50,  # 每次查询的最大记录数
        },

        # 账号余额查询配置（测试环境）
        'ACCOUNT_BALANCE_QUERY_CONFIG': {
            'NODE_ID': '00061990',  # 测试环境机构号
            'DEFAULT_ACCOUNT_TYPE': '1',  # 默认查询付款账号类型 1=付款账户
            'DEFAULT_MERCHANT_ID': '1000000001222',  # 默认查询的商户号
            'AUTO_QUERY_INTERVAL': 10,  # 自动查询间隔(分钟)
            'BATCH_QUERY_SIZE': 20,  # 批量查询时的最大记录数
            'QUERY_SQL': "SELECT hd.ymshanghuhao as merchant_id, NVL(hd.merchantname, '') as merchant_name FROM P_BL_SELL_PAYAMOUNT_HZ_hd hd WHERE hd.allresult_check_sign='Y' AND hd.BALANCE_MONEY_SIGN='N' AND ROWNUM <= 100 ORDER BY hd.CREATE_TIME DESC",  # 商户查询SQL
        },

        # 其他业务配置
        'AUTO_EXECUTE_TIME': '04:00',  # 自动执行时间
        'REQUEST_TIMEOUT': 30,  # 请求超时时间(秒)
        'BATCH_SIZE': 100,  # 批量处理大小
        'RETRY_COUNT': 3,  # 重试次数
    }

    # ===== 生产环境完整配置 =====
    _PROD_CONFIG = {
        # API配置（生产环境）
        'API_URL': 'https://fzxt-yzt-openapi.wangcaio2o.com',
        'APP_ID': '你的生产APP_ID',  # 👈 改成你的生产APP_ID
        'NODE_ID': '你的生产NODE_ID',  # 👈 改成你的生产NODE_ID
        'MERCHANT_ID': '你的生产备用商户号',  # 👈 生产环境备用商户号
        'STORE_ID': '你的生产备用门店ID',  # 👈 生产环境备用门店ID

        # 阿里云短信服务配置（生产环境）
        'ALIYUN_SMS_CONFIG': {
            'ACCESS_KEY_ID': 'your-prod-access-key-id',
            'ACCESS_KEY_SECRET': 'your-prod-access-key-secret',
            'REGION_ID': 'cn-hangzhou',
            'SIGN_NAME': '正式签名',
            'TEMPLATE_CODE': 'SMS_987654321'
        },

        # 数据库配置（生产环境）
        'DB_CONFIG': {
            'user': '生产数据库用户',  # 👈 改成你的生产数据库用户
            'password': '生产数据库密码',  # 👈 改成你的生产数据库密码
            'dsn': '生产数据库地址'  # 👈 改成你的生产数据库地址
        },

        # 私钥配置（生产环境 - 需要替换为生产环境私钥）
        'PRIVATE_KEY': """-----BEGIN RSA PRIVATE KEY-----
            你的生产环境私钥内容
            替换为真实的生产环境RSA私钥
        -----END RSA PRIVATE KEY-----""",

        # 业务配置（生产环境）
        'ORDER_UPLOAD_MODE_NORMAL': '3',  # 普通订单上传模式
        'ORDER_UPLOAD_MODE_RECHARGE': '2',  # 挂账充值上传模式
        'ACCOUNT_TYPE': '2',
        'ACCOUNT_TYPE_NORMAL': '2',  # 普通订单账户类型
        'ACCOUNT_TYPE_RECHARGE': '2',  # 挂账充值账户类型
        'PAY_MERCHANT_ID': '生产支付商户号',  # 👈 改成你的生产支付商户号  挂账用
        'DEFAULT_USER_ID': '01',
        'DEFAULT_FEE_AMOUNT': 0,
        'SPLIT_RULE_SOURCE': '1',

        # 分账相关配置（生产环境）
        'SPLIT_CONFIG': {
            'PAYER_MERCHANT_ID': '生产加盟商付款账号',  # 👈 改成生产环境加盟商付款账号
            'PAYEE_JMS_MERCHANT_ID': '生产加盟商收款账号',  # 👈 改成生产环境加盟商收款账号
            'PAYEE_GS_MERCHANT_ID': '生产公司收款账号',  # 👈 改成生产环境公司收款账号
            'PAYER_ACCOUNT_TYPE': '1',  # 付款账户类型：1-付款账户
            'PAYEE_ACCOUNT_TYPE': '0',  # 收款账户类型：0-收款账户
            'DEFAULT_JMS_AMOUNT': 1000,  # 默认加盟商分账金额(分)
            'DEFAULT_GS_AMOUNT': 500,  # 默认公司分账金额(分)
        },

        'SPLIT_TARGET_MERCHANTS': [
            {
                'merchant_id': '生产加盟商收款账号',
                'name': '加盟商收款账号',
                'amount': 1000
            },
            {
                'merchant_id': '生产公司收款账号',
                'name': '公司收款账号',
                'amount': 500
            }
        ],

        # 余额支付查询配置（生产环境）
        'BALANCE_PAY_QUERY_CONFIG': {
            'NODE_ID': '生产环境机构号',  # 👈 改成生产环境机构号
            'AUTO_QUERY_INTERVAL': 5,  # 自动查询间隔(分钟)
            'QUERY_SQL': "select dt.billid,dt.xpbillid,dt.fz_requestback_no TRADE_NO from P_BL_SELL_PAYAMOUNT_HZ_dt dt where dt.cancelsign='N' and dt.is_fz_execute='Y' and dt.fz_execute_result='N' and dt.fz_requestback_no <> ' '",
            'BATCH_QUERY_SIZE': 100,  # 生产环境可以查询更多记录
        },

        # 账号余额查询配置（生产环境）
        'ACCOUNT_BALANCE_QUERY_CONFIG': {
            'NODE_ID': '你的生产环境机构号',  # 👈 改成生产环境机构号
            'DEFAULT_ACCOUNT_TYPE': '1',  # 默认查询付款账号类型 1=付款账户
            'DEFAULT_MERCHANT_ID': '生产环境商户号',  # 默认查询的商户号，待用户提供
            'AUTO_QUERY_INTERVAL': 15,  # 生产环境查询间隔可以更长
            'BATCH_QUERY_SIZE': 50,  # 生产环境批量查询更保守
            'QUERY_SQL': "SELECT hd.ymshanghuhao as merchant_id, NVL(hd.merchantname, '') as merchant_name FROM P_BL_SELL_PAYAMOUNT_HZ_hd hd WHERE hd.allresult_check_sign='Y' AND hd.BALANCE_MONEY_SIGN='N' AND ROWNUM <= 100 ORDER BY hd.CREATE_TIME DESC",  # 商户查询SQL
        },

        # 其他业务配置（生产环境可能有不同设置）
        'AUTO_EXECUTE_TIME': '03:00',  # 生产环境自动执行时间
        'REQUEST_TIMEOUT': 60,  # 生产环境超时时间更长
        'BATCH_SIZE': 50,  # 生产环境批量处理更保守
        'RETRY_COUNT': 5,  # 生产环境重试次数更多
    }

    # ===== 自动选择配置 =====
    _CURRENT_CONFIG = _PROD_CONFIG if USE_PRODUCTION else _TEST_CONFIG

    # ===== 对外接口（自动从当前环境配置获取） =====
    APP_ID = _CURRENT_CONFIG['APP_ID']
    NODE_ID = _CURRENT_CONFIG['NODE_ID']
    MERCHANT_ID = _CURRENT_CONFIG['MERCHANT_ID']  # 备用商户号
    STORE_ID = _CURRENT_CONFIG['STORE_ID']  # 备用门店ID
    API_URL = _CURRENT_CONFIG['API_URL']
    DB_CONFIG = _CURRENT_CONFIG['DB_CONFIG']
    PRIVATE_KEY = _CURRENT_CONFIG['PRIVATE_KEY']
    
    # 阿里云短信服务配置
    ALIYUN_SMS_CONFIG = _CURRENT_CONFIG.get('ALIYUN_SMS_CONFIG', {})

    # 业务配置
    ORDER_UPLOAD_MODE_NORMAL = _CURRENT_CONFIG['ORDER_UPLOAD_MODE_NORMAL']  # 普通订单上传模式
    ORDER_UPLOAD_MODE_RECHARGE = _CURRENT_CONFIG['ORDER_UPLOAD_MODE_RECHARGE']  # 挂账充值上传模式
    ACCOUNT_TYPE = _CURRENT_CONFIG['ACCOUNT_TYPE']
    ACCOUNT_TYPE_NORMAL = _CURRENT_CONFIG['ACCOUNT_TYPE_NORMAL']  # 普通订单账户类型
    ACCOUNT_TYPE_RECHARGE = _CURRENT_CONFIG['ACCOUNT_TYPE_RECHARGE']  # 挂账充值账户类型
    PAY_MERCHANT_ID = _CURRENT_CONFIG['PAY_MERCHANT_ID']
    DEFAULT_USER_ID = _CURRENT_CONFIG['DEFAULT_USER_ID']
    DEFAULT_FEE_AMOUNT = _CURRENT_CONFIG['DEFAULT_FEE_AMOUNT']
    SPLIT_RULE_SOURCE = _CURRENT_CONFIG['SPLIT_RULE_SOURCE']

    # 分账配置
    SPLIT_CONFIG = _CURRENT_CONFIG['SPLIT_CONFIG']
    SPLIT_TARGET_MERCHANTS = _CURRENT_CONFIG['SPLIT_TARGET_MERCHANTS']

    # 余额支付查询配置
    BALANCE_PAY_QUERY_CONFIG = _CURRENT_CONFIG['BALANCE_PAY_QUERY_CONFIG']

    # 账号余额查询配置
    ACCOUNT_BALANCE_QUERY_CONFIG = _CURRENT_CONFIG['ACCOUNT_BALANCE_QUERY_CONFIG']

    # 保持对旧配置的兼容性支持
    SPLIT_QUERY_CONFIG = BALANCE_PAY_QUERY_CONFIG  # 为了兼容性，映射到新的配置

    # 其他配置
    AUTO_EXECUTE_TIME = _CURRENT_CONFIG['AUTO_EXECUTE_TIME']
    REQUEST_TIMEOUT = _CURRENT_CONFIG['REQUEST_TIMEOUT']
    BATCH_SIZE = _CURRENT_CONFIG['BATCH_SIZE']
    RETRY_COUNT = _CURRENT_CONFIG['RETRY_COUNT']

    # ===== 工具方法 =====
    @classmethod
    def get_url(cls):
        return cls.API_URL

    @classmethod
    def get_env_name(cls):
        return "生产环境" if cls.USE_PRODUCTION else "测试环境"

    @classmethod
    def get_balance_pay_query_node_id(cls):
        """获取余额支付查询机构号"""
        return cls.BALANCE_PAY_QUERY_CONFIG.get('NODE_ID', cls.NODE_ID)

    @classmethod
    def get_balance_pay_query_sql(cls):
        """获取余额支付查询SQL语句"""
        return cls.BALANCE_PAY_QUERY_CONFIG.get('QUERY_SQL', '')

    @classmethod
    def get_auto_query_interval(cls):
        """获取自动查询间隔（分钟）"""
        return cls.BALANCE_PAY_QUERY_CONFIG.get('AUTO_QUERY_INTERVAL', 5)

    # 保持对旧方法的兼容性支持
    @classmethod
    def get_split_query_node_id(cls):
        """获取分账查询机构号（兼容性方法）"""
        return cls.get_balance_pay_query_node_id()

    @classmethod
    def get_split_query_sql(cls):
        """获取分账查询SQL语句（兼容性方法）"""
        return cls.get_balance_pay_query_sql()

    @classmethod
    def get_db_connection_info(cls):
        return cls.DB_CONFIG['user'], cls.DB_CONFIG['password'], cls.DB_CONFIG['dsn']

    @classmethod
    def should_use_dynamic_merchant_id(cls):
        """判断是否应该使用动态商户号"""
        # 生产环境默认使用动态商户号，测试环境可以选择
        if cls.USE_PRODUCTION:
            return True
        else:
            return cls.USE_DYNAMIC_MERCHANT_ID

    @classmethod
    def should_use_dynamic_store_id(cls):
        """判断是否应该使用动态门店ID"""
        # 生产环境默认使用动态门店ID，测试环境可以选择
        if cls.USE_PRODUCTION:
            return True
        else:
            return cls.USE_DYNAMIC_STORE_ID

    @classmethod
    def get_fallback_merchant_id(cls):
        """获取备用商户号（动态获取失败时使用）"""
        return cls.MERCHANT_ID

    @classmethod
    def get_fallback_store_id(cls):
        """获取备用门店ID（动态获取失败时使用）"""
        return cls.STORE_ID

    @classmethod
    def get_split_config(cls):
        """获取分账配置信息"""
        return cls.SPLIT_CONFIG

    @classmethod
    def get_split_target_merchants(cls):
        """获取分账目标商户列表"""
        return cls.SPLIT_TARGET_MERCHANTS

    @classmethod
    def get_payer_merchant_id(cls):
        """获取付款方商户号"""
        return cls.SPLIT_CONFIG['PAYER_MERCHANT_ID']

    @classmethod
    def get_payee_jms_merchant_id(cls):
        """获取加盟商收款账号"""
        return cls.SPLIT_CONFIG['PAYEE_JMS_MERCHANT_ID']

    @classmethod
    def get_payee_gs_merchant_id(cls):
        """获取公司收款账号"""
        return cls.SPLIT_CONFIG['PAYEE_GS_MERCHANT_ID']

    @classmethod
    def get_split_query_config(cls):
        """获取分账结果查询配置"""
        return cls.SPLIT_QUERY_CONFIG

    @classmethod
    def get_split_query_node_id(cls):
        """获取分账结果查询的机构号"""
        return cls.SPLIT_QUERY_CONFIG['NODE_ID']

    @classmethod
    def get_split_query_sql(cls):
        """获取分账结果查询的SQL语句"""
        return cls.SPLIT_QUERY_CONFIG['QUERY_SQL']

    @classmethod
    def get_auto_query_interval(cls):
        """获取自动查询间隔(分钟)"""
        return cls.SPLIT_QUERY_CONFIG['AUTO_QUERY_INTERVAL']

    @classmethod
    def get_account_balance_query_config(cls):
        """获取账号余额查询配置"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG

    @classmethod
    def get_account_balance_node_id(cls):
        """获取账号余额查询的机构号"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG['NODE_ID']

    @classmethod
    def get_default_account_type(cls):
        """获取默认账户类型（1=付款账户）"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG['DEFAULT_ACCOUNT_TYPE']

    @classmethod
    def get_default_merchant_id_for_balance(cls):
        """获取默认查询余额的商户号"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG['DEFAULT_MERCHANT_ID']

    @classmethod
    def get_account_balance_auto_interval(cls):
        """获取账号余额自动查询间隔(分钟)"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG['AUTO_QUERY_INTERVAL']

    @classmethod
    def get_merchant_query_sql(cls):
        """获取商户查询SQL语句"""
        return cls.ACCOUNT_BALANCE_QUERY_CONFIG['QUERY_SQL']

    @classmethod
    def get_auto_execute_time(cls):
        """获取自动执行时间"""
        time_str = cls.AUTO_EXECUTE_TIME
        if ':' in time_str:
            hour, minute = time_str.split(':')
            return int(hour), int(minute)
        return 4, 0  # 默认4点

    @classmethod
    def is_config_ready(cls):
        """检查配置是否完整"""
        errors = []

        # 检查基本配置
        if not cls.APP_ID or cls.APP_ID == '你的生产APP_ID':
            errors.append("APP_ID未正确配置")
        if not cls.NODE_ID or cls.NODE_ID == '你的生产NODE_ID':
            errors.append("NODE_ID未正确配置")
        if not cls.MERCHANT_ID or cls.MERCHANT_ID == '你的生产备用商户号':
            errors.append("MERCHANT_ID未正确配置")
        if not cls.STORE_ID or cls.STORE_ID == '你的生产备用门店ID':
            errors.append("STORE_ID未正确配置")

        # 检查数据库配置
        if cls.DB_CONFIG['user'] == '生产数据库用户':
            errors.append("数据库用户名未正确配置")
        if cls.DB_CONFIG['password'] == '生产数据库密码':
            errors.append("数据库密码未正确配置")
        if cls.DB_CONFIG['dsn'] == '生产数据库地址':
            errors.append("数据库地址未正确配置")

        # 检查私钥配置
        if '你的生产环境私钥内容' in cls.PRIVATE_KEY:
            errors.append("私钥未正确配置")

        # 检查业务配置
        if cls.PAY_MERCHANT_ID == '生产支付商户号':
            errors.append("支付商户号未正确配置")

        if errors:
            return False, f"配置不完整: {', '.join(errors)}"

        # 检查配置策略
        merchant_strategy = "动态获取" if cls.should_use_dynamic_merchant_id() else "配置文件"
        store_strategy = "动态获取" if cls.should_use_dynamic_store_id() else "配置文件"
        return True, f"配置已就绪 - {cls.get_env_name()} (商户号: {merchant_strategy}, 门店ID: {store_strategy})"

    @classmethod
    def print_config_info(cls):
        """打印配置信息"""
        print("=" * 70)
        print("📋 当前完整配置信息")
        print("=" * 70)
        print(f"🌐 环境: {cls.get_env_name()}")
        print(f"🔗 API地址: {cls.get_url()}")
        print(f"📱 APP_ID: {cls.APP_ID}")
        print(f"🏢 机构号: {cls.NODE_ID}")

        print(f"\n💼 动态配置策略:")
        print(f"   商户号策略: {'动态获取' if cls.should_use_dynamic_merchant_id() else '配置文件固定'}")
        if not cls.should_use_dynamic_merchant_id():
            print(f"   固定商户号: {cls.MERCHANT_ID}")
        else:
            print(f"   备用商户号: {cls.MERCHANT_ID}")

        print(f"   门店ID策略: {'动态获取' if cls.should_use_dynamic_store_id() else '配置文件固定'}")
        if not cls.should_use_dynamic_store_id():
            print(f"   固定门店ID: {cls.STORE_ID}")
        else:
            print(f"   备用门店ID: {cls.STORE_ID}")

        print(f"\n💳 支付配置:")
        print(f"   支付商户号: {cls.PAY_MERCHANT_ID}")
        print(f"   普通订单上传模式: {cls.ORDER_UPLOAD_MODE_NORMAL}")
        print(f"   挂账充值上传模式: {cls.ORDER_UPLOAD_MODE_RECHARGE}")
        print(f"   账户类型: {cls.ACCOUNT_TYPE}")

        print(f"\n🔗 数据库配置:")
        print(f"   地址: {cls.DB_CONFIG['dsn']}")
        print(f"   用户: {cls.DB_CONFIG['user']}")

        print(f"\n📊 分账配置:")
        for i, merchant in enumerate(cls.SPLIT_TARGET_MERCHANTS, 1):
            print(f"   {i}. {merchant['name']} ({merchant['merchant_id']}) - {merchant['amount'] / 100}元")

        print(f"\n⚙️ 系统配置:")
        print(f"   自动执行时间: {cls.AUTO_EXECUTE_TIME}")
        print(f"   请求超时: {cls.REQUEST_TIMEOUT}秒")
        print(f"   批量大小: {cls.BATCH_SIZE}")
        print(f"   重试次数: {cls.RETRY_COUNT}")

        print(f"\n🔐 私钥状态: {'已配置' if cls.PRIVATE_KEY and '-----BEGIN' in cls.PRIVATE_KEY else '未配置'}")
        print("=" * 70)

    @classmethod
    def validate_production_config(cls):
        """验证生产环境配置完整性"""
        if not cls.USE_PRODUCTION:
            return True, "当前为测试环境，跳过生产配置验证"

        prod_config = cls._PROD_CONFIG
        issues = []

        # 检查是否还有占位符
        placeholders = [
            '你的生产APP_ID',
            '你的生产NODE_ID',
            '你的生产备用商户号',
            '你的生产备用门店ID',
            '生产数据库用户',
            '生产数据库密码',
            '生产数据库地址',
            '你的生产环境私钥内容',
            '生产支付商户号',
            '生产目标商户A',
            '生产目标商户B'
        ]

        config_str = str(prod_config)
        for placeholder in placeholders:
            if placeholder in config_str:
                issues.append(f"包含占位符: {placeholder}")

        if issues:
            return False, f"生产环境配置未完成: {'; '.join(issues)}"

        return True, "生产环境配置验证通过"

    @classmethod
    def get_config_summary(cls):
        """获取配置摘要"""
        return {
            'environment': cls.get_env_name(),
            'api_url': cls.API_URL,
            'app_id': cls.APP_ID,
            'node_id': cls.NODE_ID,
            'merchant_strategy': '动态获取' if cls.should_use_dynamic_merchant_id() else '配置文件',
            'store_strategy': '动态获取' if cls.should_use_dynamic_store_id() else '配置文件',
            'database_dsn': cls.DB_CONFIG['dsn'],
            'auto_execute_time': cls.AUTO_EXECUTE_TIME,
            'split_merchants_count': len(cls.SPLIT_TARGET_MERCHANTS)
        }

    @staticmethod
    def get_order_upload_mode_normal():
        """获取普通订单上传模式"""
        return Config.ORDER_UPLOAD_MODE_NORMAL

    @staticmethod
    def get_order_upload_mode_recharge():
        """获取挂账充值的上传模式"""
        return Config.ORDER_UPLOAD_MODE_RECHARGE

    @staticmethod
    def get_account_type_normal():
        """获取普通订单的账户类型"""
        return Config.ACCOUNT_TYPE_NORMAL

    @staticmethod
    def get_account_type_recharge():
        """获取挂账充值的账户类型"""
        return Config.ACCOUNT_TYPE_RECHARGE

    @classmethod
    def get_aliyun_sms_config(cls):
        """获取阿里云短信服务配置"""
        return cls.ALIYUN_SMS_CONFIG


# ===== 使用说明和配置检查 =====
if __name__ == '__main__':
    print("🔧 MUMUSO系统环境配置工具")
    print("=" * 70)
    print("环境切换说明:")
    print("1. 测试环境：USE_PRODUCTION = False")
    print("2. 生产环境：USE_PRODUCTION = True")
    print("3. 动态商户号：USE_DYNAMIC_MERCHANT_ID = True")
    print("4. 动态门店ID：USE_DYNAMIC_STORE_ID = True")
    print("=" * 70)

    # 显示当前配置
    Config.print_config_info()

    # 检查配置状态
    ready, msg = Config.is_config_ready()
    if ready:
        print(f"✅ 配置状态: {msg}")
    else:
        print(f"❌ 配置状态: {msg}")

    # 如果是生产环境，额外验证
    if Config.USE_PRODUCTION:
        prod_ready, prod_msg = Config.validate_production_config()
        if prod_ready:
            print(f"✅ 生产环境验证: {prod_msg}")
        else:
            print(f"⚠️ 生产环境验证: {prod_msg}")

    # 显示配置摘要
    print(f"\n📋 配置摘要:")
    summary = Config.get_config_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")