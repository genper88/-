#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
窗口管理器
负责管理所有功能窗口的生命周期
"""

from datetime import datetime


class WindowManager:
    """窗口管理器"""

    def __init__(self, main_window=None, log_queue=None):
        print(f"[DEBUG] WindowManager.__init__()")
        print(f"[DEBUG] 接收到的log_queue: {log_queue is not None}")
        print(f"[DEBUG] log_queue对象: {log_queue}")

        self.main_window = main_window
        self.log_queue = log_queue
        self.windows = {}

        print(f"[DEBUG] WindowManager初始化完成")
        print(f"[DEBUG] self.log_queue: {self.log_queue is not None}")

    def register_window(self, window_name, window_class, title, size, *args, **kwargs):
        """注册窗口类"""
        print(f"[DEBUG] 注册窗口: {window_name}, 标题: {title}, 大小: {size}")

        if window_name not in self.windows:
            self.windows[window_name] = {
                'class': window_class,
                'instance': None,
                'title': title,
                'size': size,
                'args': args,
                'kwargs': kwargs
            }
            print(f"[DEBUG] 窗口 {window_name} 注册成功")

    def show_window(self, window_name):
        """显示指定窗口"""
        print(f"[DEBUG] WindowManager.show_window() - {window_name}")
        print(f"[DEBUG] WindowManager.log_queue: {self.log_queue is not None}")
        print(f"[DEBUG] WindowManager.log_queue 对象: {self.log_queue}")

        if window_name not in self.windows:
            error_msg = f"窗口 '{window_name}' 未注册"
            print(f"[DEBUG] {error_msg}")
            self._log_error(error_msg)
            raise ValueError(error_msg)

        window_info = self.windows[window_name]

        # 如果窗口实例不存在，创建它
        if window_info['instance'] is None:
            try:
                print(f"[DEBUG] 创建新窗口实例: {window_name}")
                print(f"[DEBUG] 传递的参数:")
                print(f"[DEBUG]   parent: {self.main_window}")
                print(f"[DEBUG]   title: {window_info['title']}")
                print(f"[DEBUG]   size: {window_info['size']}")
                print(f"[DEBUG]   log_queue: {self.log_queue}")
                print(f"[DEBUG]   log_queue类型: {type(self.log_queue)}")

                # 修复参数传递 - 按照正确的顺序传递参数
                window_info['instance'] = window_info['class'](
                    parent=self.main_window,  # parent参数
                    title=window_info['title'],  # title参数
                    size=window_info['size'],  # size参数
                    log_queue=self.log_queue,  # log_queue参数
                    *window_info['args'],  # 其他位置参数
                    **window_info['kwargs']  # 其他关键字参数
                )

                print(f"[DEBUG] 窗口实例创建完成")

                # 验证实例是否正确接收了log_queue
                if hasattr(window_info['instance'], 'log_queue'):
                    print(f"[DEBUG] 实例的log_queue: {window_info['instance'].log_queue is not None}")
                    print(f"[DEBUG] 实例的log_queue对象: {window_info['instance'].log_queue}")
                else:
                    print(f"[DEBUG] 实例没有log_queue属性")

                self._log_info(f"创建窗口实例: {window_name}")
            except Exception as e:
                error_msg = f"创建窗口 {window_name} 失败: {str(e)}"
                print(f"[DEBUG] {error_msg}")
                import traceback
                traceback.print_exc()
                self._log_error(error_msg)
                return None

        # 显示窗口
        try:
            window_info['instance'].show_window()
            print(f"[DEBUG] 窗口显示完成")
            self._log_info(f"显示窗口: {window_name}")
            return window_info['instance']
        except Exception as e:
            error_msg = f"显示窗口 {window_name} 失败: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            self._log_error(error_msg)
            return None

    def hide_window(self, window_name):
        """隐藏指定窗口"""
        if window_name in self.windows and self.windows[window_name]['instance']:
            try:
                self.windows[window_name]['instance'].hide_window()
                self._log_info(f"隐藏窗口: {window_name}")
            except Exception as e:
                self._log_error(f"隐藏窗口 {window_name} 失败: {str(e)}")

    def destroy_window(self, window_name):
        """销毁指定窗口"""
        if window_name in self.windows and self.windows[window_name]['instance']:
            try:
                self.windows[window_name]['instance'].destroy_window()
                self.windows[window_name]['instance'] = None
                self._log_info(f"销毁窗口: {window_name}")
            except Exception as e:
                self._log_error(f"销毁窗口 {window_name} 失败: {str(e)}")

    def is_window_visible(self, window_name):
        """检查窗口是否可见"""
        if window_name in self.windows and self.windows[window_name]['instance']:
            return self.windows[window_name]['instance'].is_visible
        return False

    def get_window_instance(self, window_name):
        """获取窗口实例"""
        if window_name in self.windows:
            return self.windows[window_name]['instance']
        return None

    def get_all_windows_status(self):
        """获取所有窗口状态"""
        status = {}
        for window_name, window_info in self.windows.items():
            instance = window_info['instance']
            if instance:
                status[window_name] = {
                    'initialized': getattr(instance, 'is_initialized', False),
                    'visible': getattr(instance, 'is_visible', False),
                    'title': getattr(instance, 'title', window_info['title'])
                }
            else:
                status[window_name] = {
                    'initialized': False,
                    'visible': False,
                    'title': window_info['title']
                }
        return status

    def hide_all_windows(self):
        """隐藏所有窗口"""
        for window_name in self.windows:
            self.hide_window(window_name)
        self._log_info("隐藏所有窗口")

    def destroy_all_windows(self):
        """销毁所有窗口"""
        for window_name in self.windows:
            self.destroy_window(window_name)
        self._log_info("销毁所有窗口")

    def cleanup(self):
        """清理资源"""
        self.destroy_all_windows()
        self.windows.clear()
        self._log_info("窗口管理器清理完成")

    def _log_info(self, message):
        """记录信息日志"""
        print(f"[DEBUG] WindowManager INFO: {message}")
        if self.log_queue:
            try:
                self.log_queue.put({
                    'level': 'INFO',
                    'message': f"[窗口管理器] {message}",
                    'module': '系统',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                print(f"[DEBUG] 日志已放入队列: {message}")
            except Exception as e:
                print(f"[DEBUG] 放入日志队列失败: {e}")
        else:
            print(f"[DEBUG] log_queue为None，无法记录日志")

    def _log_error(self, message):
        """记录错误日志"""
        print(f"[DEBUG] WindowManager ERROR: {message}")
        if self.log_queue:
            try:
                self.log_queue.put({
                    'level': 'ERROR',
                    'message': f"[窗口管理器] {message}",
                    'module': '系统',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                print(f"[DEBUG] 错误日志已放入队列: {message}")
            except Exception as e:
                print(f"[DEBUG] 放入错误日志队列失败: {e}")
        else:
            print(f"[DEBUG] log_queue为None，无法记录错误日志")


def setup_window_manager(main_window, log_queue):
    """初始化窗口管理器"""
    print(f"[DEBUG] setup_window_manager() 函数被调用")
    print(f"[DEBUG] 接收到的main_window: {main_window}")
    print(f"[DEBUG] 接收到的log_queue: {log_queue is not None}")
    print(f"[DEBUG] log_queue对象: {log_queue}")

    # 创建新的WindowManager实例（移除单例模式）
    window_manager = WindowManager(main_window, log_queue)

    print(f"[DEBUG] setup_window_manager() 函数完成")
    print(f"[DEBUG] 返回的window_manager.log_queue: {window_manager.log_queue is not None}")

    return window_manager