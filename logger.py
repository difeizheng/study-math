"""
日志系统模块
提供统一的日志记录功能
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import functools


# 日志目录
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / f"study_math_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str = "study_math", level: int = logging.INFO) -> logging.Logger:
    """
    设置 logger

    Args:
        name: logger 名称
        level: 日志级别

    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 创建 formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件 handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# 创建默认 logger
logger = setup_logger()


def log_function_call(func):
    """
    装饰器：记录函数调用
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"调用函数：{func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败：{e}")
            raise
    return wrapper


def log_error(error: Exception, context: str = ""):
    """记录错误信息"""
    logger.error(f"{context} - 错误：{type(error).__name__}: {error}", exc_info=True)


def log_info(message: str):
    """记录信息"""
    logger.info(message)


def log_warning(message: str):
    """记录警告"""
    logger.warning(message)


def log_debug(message: str):
    """记录调试信息"""
    logger.debug(message)


# 性能分析装饰器
def log_execution_time(func):
    """
    装饰器：记录函数执行时间
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"函数 {func.__name__} 执行时间：{elapsed:.3f}秒")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"函数 {func.__name__} 执行失败（耗时{elapsed:.3f}秒）: {e}")
            raise
    return wrapper


def get_logger(name: str = None) -> logging.Logger:
    """获取 logger 实例"""
    if name:
        return setup_logger(name)
    return logger


# 初始化日志系统
def init_logging():
    """初始化日志系统"""
    logger.info("=" * 50)
    logger.info("学习数学分析系统启动")
    logger.info(f"日志文件：{LOG_FILE}")
    logger.info("=" * 50)
    return logger


if __name__ == "__main__":
    # 测试日志系统
    init_logging()
    log_info("这是一条信息日志")
    log_warning("这是一条警告日志")
    log_debug("这是一条调试日志")

    try:
        raise ValueError("测试错误")
    except Exception as e:
        log_error(e, "测试上下文")

    print(f"日志已写入：{LOG_FILE}")
