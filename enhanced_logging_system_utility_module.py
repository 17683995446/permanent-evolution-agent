#!/usr/bin/env python3
"""
Enhanced Logging Utility (Stability Version)
简化的日志模块，避免在CI环境中卡住。
"""
import sys
import os
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from loguru import logger
import threading


class EnhancedLoggingUtility:
    """Enhanced logging - simplified for stability."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._setup_loguru()

    def _setup_loguru(self):
        logger.remove()
        log_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        logger.add(
            sys.stdout,
            format=log_format,
            level="INFO",
            colorize=False,
            backtrace=False,
            diagnose=False
        )
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "pea_{time:YYYY-MM-DD}.log",
            rotation="100 MB",
            retention="7 days",
            format=log_format,
            level="DEBUG"
        )

    def info(self, message: str, **kwargs):
        logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        logger.critical(message, **kwargs)

    def success(self, message: str):
        print(f"✓ {message}")

    def failure(self, message: str):
        print(f"✗ {message}")

    def display_panel(self, content: str, title: str, style: str = "blue"):
        print()
        print("=" * 60)
        print(f"  {title}")
        print("=" * 60)
        for line in content.split('\n'):
            print(f"  {line}")
        print("=" * 60)
        print()

    def log_execution_summary(self, task_name: str, duration: float, status: str, details: dict):
        print(f"\n=== Execution Summary: {task_name} ===")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Status: {status}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")

    def log_optimization(self, optimization_type: str, improvement: float, details: str):
        print(f"\n⚡ Optimization Applied")
        print(f"  Type: {optimization_type}")
        print(f"  Improvement: +{improvement:.2%}")
        print(f"  Details: {details}\n")

    def log_guardian_event(self, event_type: str, details: str):
        event_icons = {
            "start": "🛡️",
            "restart": "🔄",
            "error": "⚠️",
            "recovered": "✅"
        }
        icon = event_icons.get(event_type, "📋")
        print(f"{icon} Guardian [{event_type.upper()}]: {details}")

    def section_divider(self, title: str = ""):
        if title:
            print()
            print("=" * 60)
            print(f"  {title}")
            print("=" * 60)
        else:
            print()
            print("-" * 60)

    def header(self, text: str, style: str = "bold blue"):
        print(text)

    def get_logger(self):
        return logger
