"""
Enhanced Logging Utility
Advanced logging with rich console output and structured file logging.
"""
import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
import threading


class EnhancedLoggingUtility:
    """Enhanced logging with rich UI components."""

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
        self.console = Console()
        self._setup_loguru()
        self._progress_lock = threading.Lock()
        self._active_progress: Optional[Progress] = None

    def _setup_loguru(self):
        logger.remove()
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            format=log_format,
            level="INFO",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "pea_{time:YYYY-MM-DD}.log",
            rotation="100 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            compression="zip"
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
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def failure(self, message: str):
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def create_table(self, title: str, columns: list, rows: list) -> Table:
        table = Table(title=title, show_header=True, header_style="bold magenta")
        for col in columns:
            table.add_column(col, style="cyan", no_wrap=False)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        return table

    def display_table(self, table: Table):
        self.console.print(table)

    def display_panel(self, content: str, title: str, style: str = "blue"):
        panel = Panel(content, title=title, border_style=style)
        self.console.print(panel)

    def create_progress(self) -> Progress:
        with self._progress_lock:
            if self._active_progress:
                return self._active_progress
            self._active_progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )
            return self._active_progress

    def log_execution_summary(self, task_name: str, duration: float, status: str, details: dict):
        status_color = "green" if status == "success" else "red"
        summary = f"""
[bold]Task:[/bold] {task_name}
[bold]Duration:[/bold] {duration:.2f}s
[bold]Status:[/bold] [{status_color}]{status}[/{status_color}]
"""
        if details:
            for key, value in details.items():
                summary += f"[bold]{key}:[/bold] {value}\n"
        self.display_panel(summary.strip(), "Execution Summary", "cyan")

    def log_optimization(self, optimization_type: str, improvement: float, details: str):
        improvement_str = f"{improvement:.2%}"
        self.console.print(f"\n[bold yellow]⚡ Optimization Applied[/bold yellow]")
        self.console.print(f"  Type: {optimization_type}")
        self.console.print(f"  Improvement: [green]+{improvement_str}[/green]")
        self.console.print(f"  Details: {details}\n")

    def log_system_status(self, status_data: dict):
        table = self.create_table(
            "System Status",
            ["Component", "Status", "Details"],
            [[k, v.get("status", "unknown"), v.get("details", "")] for k, v in status_data.items()]
        )
        self.console.print(table)

    def log_rule_update(self, rule_name: str, old_value: Any, new_value: Any):
        self.console.print(f"\n[bold cyan]⟳ Rule Updated:[/bold cyan] {rule_name}")
        self.console.print(f"  Old: {old_value}")
        self.console.print(f"  New: {new_value}\n")

    def log_guardian_event(self, event_type: str, details: str):
        event_icons = {
            "start": "🛡️",
            "restart": "🔄",
            "error": "⚠️",
            "recovered": "✅"
        }
        icon = event_icons.get(event_type, "📋")
        self.console.print(f"{icon} Guardian [{event_type.upper()}]: {details}")

    def section_divider(self, title: str = ""):
        if title:
            self.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            self.console.print(f"[bold cyan]  {title}[/bold cyan]")
            self.console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
        else:
            self.console.print(f"\n[dim]{'─'*60}[/dim]\n")

    def header(self, text: str, style: str = "bold blue"):
        self.console.print(f"[{style}]{text}[/{style}]")

    def get_logger(self):
        return logger
