# app/core/logging_config.py

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器，方便日志分析"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外的上下文信息
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "graph_id"):
            log_data["graph_id"] = record.graph_id
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # 格式化时间
        record.asctime = self.formatTime(record, self.datefmt)

        # 构建日志消息
        message = super().format(record)

        return message


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    json_logs: bool = False,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
) -> None:
    """
    配置应用程序的日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录，如果为None则使用默认目录 ./logs
        json_logs: 是否使用JSON格式输出日志（文件日志）
        enable_file_logging: 是否启用文件日志
        enable_console_logging: 是否启用控制台日志
    """
    # 创建日志目录
    if log_dir is None:
        log_dir = "logs"
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 控制台处理器（带颜色）
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    if enable_file_logging:
        # 应用日志文件（按大小轮转）
        if json_logs:
            app_log_file = log_path / "app.json.log"
            app_file_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            app_file_handler.setFormatter(JSONFormatter())
        else:
            app_log_file = log_path / "app.log"
            app_file_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            app_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            app_file_handler.setFormatter(app_formatter)

        app_file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(app_file_handler)

        # 错误日志文件（按天轮转，只记录WARNING及以上）
        error_log_file = log_path / "error.log"
        error_file_handler = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.WARNING)
        error_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s\n%(pathname)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_file_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)

    # 记录日志系统初始化完成
    logger = logging.getLogger(__name__)
    logger.info(
        f"日志系统初始化完成: level={log_level}, "
        f"console={enable_console_logging}, file={enable_file_logging}, "
        f"json_format={json_logs}, log_dir={log_path.absolute()}"
    )


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)
