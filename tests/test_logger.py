"""
日志模块单元测试
"""
import unittest
import logging
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger import (
    setup_logger, get_logger, log_info, log_warning,
    log_debug, log_error, log_function_call, log_execution_time
)


class TestLoggerSetup(unittest.TestCase):
    """测试日志设置"""

    def test_setup_logger(self):
        """测试设置 logger"""
        logger = setup_logger("test_logger")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)

    def test_setup_logger_custom_level(self):
        """测试自定义日志级别"""
        logger = setup_logger("test_debug_logger", logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_logger(self):
        """测试获取 logger"""
        logger = get_logger()
        self.assertIsNotNone(logger)

    def test_get_logger_by_name(self):
        """测试按名称获取 logger"""
        logger = get_logger("custom_logger")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "custom_logger")


class TestLoggingFunctions(unittest.TestCase):
    """测试日志函数"""

    def test_log_info(self):
        """测试信息日志"""
        # 不应抛出异常
        try:
            log_info("测试信息")
        except Exception as e:
            self.fail(f"log_info 抛出异常：{e}")

    def test_log_warning(self):
        """测试警告日志"""
        try:
            log_warning("测试警告")
        except Exception as e:
            self.fail(f"log_warning 抛出异常：{e}")

    def test_log_debug(self):
        """测试调试日志"""
        try:
            log_debug("测试调试")
        except Exception as e:
            self.fail(f"log_debug 抛出异常：{e}")

    def test_log_error(self):
        """测试错误日志"""
        try:
            test_error = ValueError("测试错误")
            log_error(test_error, "测试上下文")
        except Exception as e:
            self.fail(f"log_error 抛出异常：{e}")


class TestDecorators(unittest.TestCase):
    """测试装饰器"""

    def test_log_function_call(self):
        """测试函数调用日志装饰器"""
        @log_function_call
        def test_func(x, y):
            return x + y

        result = test_func(3, 5)
        self.assertEqual(result, 8)

    def test_log_execution_time(self):
        """测试执行时间日志装饰器"""
        @log_execution_time
        def slow_func():
            total = 0
            for i in range(1000):
                total += i
            return total

        result = slow_func()
        self.assertEqual(result, 499500)

    def test_log_execution_time_with_error(self):
        """测试执行时间装饰器的错误处理"""
        @log_execution_time
        def error_func():
            raise ValueError("测试错误")

        with self.assertRaises(ValueError):
            error_func()


if __name__ == "__main__":
    unittest.main(verbosity=2)
