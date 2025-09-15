#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
配置检查脚本 - check_config.py
用于验证动态商户号功能的配置是否正确
"""

import sys
import os
from datetime import datetime


def check_config_file():
    """检查配置文件"""
    print("🔧 检查配置文件...")
    try:
        from config import Config
        print("✅ config.py 文件导入成功")

        # 检查基本配置
        print(f"📊 基本配置:")
        print(f"   环境: {Config.get_env_name()}")
        print(f"   API地址: {Config.get_url()}")
        print(f"   APP_ID: {Config.APP_ID}")
        print(f"   机构号: {Config.NODE_ID}")

        # 检查商户号策略
        print(f"\n💼 商户号配置:")
        print(f"   动态商户号: {'启用' if Config.should_use_dynamic_merchant_id() else '禁用'}")
        print(f"   备用商户号: {Config.get_fallback_merchant_id()}")

        # 配置状态
        ready, msg = Config.is_config_ready()
        if ready:
            print(f"✅ 配置状态: {msg}")
            return True
        else:
            print(f"❌ 配置状态: {msg}")
            return False

    except ImportError as e:
        print(f"❌ 配置文件导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 配置检查异常: {str(e)}")
        return False


def check_database_connection():
    """检查数据库连接"""
    print("\n🔗 检查数据库连接...")
    try:
        from config import Config
        import cx_Oracle

        user, password, dsn = Config.get_db_connection_info()
        print(f"📊 数据库配置:")
        print(f"   用户: {user}")
        print(f"   地址: {dsn}")

        connection = cx_Oracle.connect(user, password, dsn)
        print("✅ 数据库连接成功")

        # 测试基本查询
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM P_BL_SELL_PAYAMOUNT_HZ_dt WHERE ROWNUM <= 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        print(f"✅ 数据库查询测试成功")
        return True

    except ImportError as e:
        print(f"❌ 缺少cx_Oracle库: {str(e)}")
        print("   请安装: pip install cx_Oracle")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


def check_merchant_id_field():
    """检查商户号字段"""
    print("\n💼 检查商户号字段...")
    try:
        from config import Config
        import cx_Oracle

        if not Config.should_use_dynamic_merchant_id():
            print("ℹ️ 当前使用固定商户号模式，跳过动态字段检查")
            return True

        user, password, dsn = Config.get_db_connection_info()
        connection = cx_Oracle.connect(user, password, dsn)
        cursor = connection.cursor()

        # 检查商户号字段是否存在且有数据
        sql = """
        SELECT COUNT(*) as total_count,
               COUNT(hd.ymshanghuhao) as merchant_count,
               COUNT(CASE WHEN hd.ymshanghuhao IS NOT NULL AND TRIM(hd.ymshanghuhao) != '' THEN 1 END) as valid_merchant_count
        FROM P_BL_SELL_PAYAMOUNT_HZ_HD hd
        LEFT JOIN P_BL_SELL_PAYAMOUNT_HZ_dt dt ON hd.billid = dt.billid 
        WHERE hd.cancelsign = 'N' 
        AND dt.cancelsign = 'N'
        AND hd.status = '002'
        AND (dt.WXMONEY <> 0 OR dt.zfbmoney <> 0)
        AND NVL(dt.ISUPLOAD_FZ, 'N') = 'N'
        AND ROWNUM <= 100
        """

        cursor.execute(sql)
        result = cursor.fetchone()
        total_count, merchant_count, valid_merchant_count = result

        print(f"📊 商户号字段统计 (样本100条):")
        print(f"   订单总数: {total_count}")
        print(f"   有商户号字段: {merchant_count}")
        print(f"   有效商户号: {valid_merchant_count}")

        if valid_merchant_count == 0:
            print("⚠️ 警告: 没有找到有效的商户号数据")
            print("   建议检查数据库中 ymshanghuhao 字段的数据")
            cursor.close()
            connection.close()
            return False

        # 获取商户号样本
        sample_sql = """
        SELECT DISTINCT hd.ymshanghuhao 
        FROM P_BL_SELL_PAYAMOUNT_HZ_HD hd
        WHERE hd.ymshanghuhao IS NOT NULL 
        AND TRIM(hd.ymshanghuhao) != ''
        AND ROWNUM <= 5
        """

        cursor.execute(sample_sql)
        samples = cursor.fetchall()

        print(f"📋 商户号样本:")
        for i, (merchant_id,) in enumerate(samples, 1):
            print(f"   {i}. {merchant_id}")

        cursor.close()
        connection.close()
        print("✅ 商户号字段检查通过")
        return True

    except Exception as e:
        print(f"❌ 商户号字段检查失败: {str(e)}")
        return False


def check_order_upload_demo():
    """检查订单上传模块"""
    print("\n📦 检查订单上传模块...")
    try:
        from order_upload_demo import OrderUploadDemo

        demo = OrderUploadDemo()
        print("✅ 订单上传模块导入成功")

        # 检查是否能获取订单统计
        stats = demo.get_order_statistics()
        if stats is not None:
            print(f"📊 订单统计:")
            print(f"   待上传订单: {stats['total']} 笔")
            print(f"   微信支付: {stats['wx_count']} 笔")
            print(f"   支付宝: {stats['alipay_count']} 笔")
            print(f"   总金额: {stats['total_amount']:.2f} 元")
            print("✅ 订单上传模块功能正常")
            return True
        else:
            print("⚠️ 无法获取订单统计，可能是数据库连接问题")
            return False

    except ImportError as e:
        print(f"❌ 订单上传模块导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 订单上传模块检查失败: {str(e)}")
        return False


def generate_config_report():
    """生成配置报告"""
    print("\n📄 生成配置报告...")
    try:
        from config import Config

        report_filename = f"config_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("MUMUSO订单上传系统 - 配置报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("基本配置:\n")
            f.write(f"  环境: {Config.get_env_name()}\n")
            f.write(f"  API地址: {Config.get_url()}\n")
            f.write(f"  APP_ID: {Config.APP_ID}\n")
            f.write(f"  机构号: {Config.NODE_ID}\n\n")

            f.write("商户号配置:\n")
            f.write(f"  动态商户号: {'启用' if Config.should_use_dynamic_merchant_id() else '禁用'}\n")
            f.write(f"  备用商户号: {Config.get_fallback_merchant_id()}\n\n")

            f.write("数据库配置:\n")
            user, password, dsn = Config.get_db_connection_info()
            f.write(f"  用户: {user}\n")
            f.write(f"  地址: {dsn}\n\n")

            ready, msg = Config.is_config_ready()
            f.write(f"配置状态: {msg}\n")

        print(f"✅ 配置报告已生成: {report_filename}")
        return True

    except Exception as e:
        print(f"❌ 生成配置报告失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🔍 MUMUSO订单上传系统 - 配置检查工具")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_passed = True

    # 1. 检查配置文件
    if not check_config_file():
        all_passed = False

    # 2. 检查数据库连接
    if not check_database_connection():
        all_passed = False

    # 3. 检查商户号字段
    if not check_merchant_id_field():
        all_passed = False

    # 4. 检查订单上传模块
    if not check_order_upload_demo():
        all_passed = False

    # 5. 生成配置报告
    generate_config_report()

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查都通过！系统配置正确，可以正常使用。")
        print("\n建议:")
        print("1. 先在测试环境进行小批量测试")
        print("2. 确认无误后再部署到生产环境")
        print("3. 定期检查日志确保系统正常运行")
    else:
        print("❌ 发现配置问题，请根据上述提示进行修正。")
        print("\n建议:")
        print("1. 检查config.py配置文件")
        print("2. 确认数据库连接参数正确")
        print("3. 验证数据库权限和数据质量")
        print("4. 联系技术支持获取帮助")

    print("=" * 60)

    # 询问是否启动测试
    if all_passed:
        try:
            choice = input("\n是否要进行简单的功能测试？(y/N): ").strip().lower()
            if choice in ['y', 'yes', '是']:
                print("\n🧪 执行简单功能测试...")
                from order_upload_demo import OrderUploadDemo
                demo = OrderUploadDemo()

                # 获取少量订单进行测试
                orders = demo.get_orders_from_database()
                if orders:
                    test_order = orders[0]
                    print(f"📝 测试订单信息:")
                    print(f"   订单号: {test_order['order_id']}")
                    print(f"   商户号: {test_order['merchant_id']}")
                    print(f"   金额: {test_order['order_amount'] / 100}元")
                    print(f"   支付方式: {test_order['payment_method']}")

                    confirm = input("\n⚠️ 确认要上传这个测试订单吗？(y/N): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        success = demo.upload_single_order(test_order)
                        if success:
                            print("✅ 测试订单上传成功！")
                        else:
                            print("❌ 测试订单上传失败，请查看日志")
                    else:
                        print("📝 跳过实际上传测试")
                else:
                    print("ℹ️ 没有找到测试订单")
        except KeyboardInterrupt:
            print("\n👋 用户取消")
        except Exception as e:
            print(f"\n❌ 测试过程异常: {str(e)}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户中断检查过程")
    except Exception as e:
        print(f"\n❌ 检查过程异常: {str(e)}")
        import traceback

        traceback.print_exc()

    input("\n按回车键退出...")