"""
Конфигурация приложения (Production-ready configuration).

Поддерживает чтение из переменных окружения (12-Factor App)
и параметров командной строки с валидацией путей.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    """
    Неизменяемая конфигурация приложения генератора билетов.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    students_path: Path = field(default_factory=lambda: Path("students.xlsx"))
    tickets_path: Path = field(default_factory=lambda: Path("tickets.docx"))
    results_path: Path = field(default_factory=lambda: Path("results.xlsx"))
    log_level: str = "INFO"
    auto_browser: bool = False

    @classmethod
    def from_env_or_args(
        cls,
        args: Any = None,
        base_dir: Path | None = None,
    ) -> AppConfig:
        """
        Создает экземпляр AppConfig с приоритетом: CLI аргументы > Переменные окружения > Значения по умолчанию.
        """
        root = base_dir or Path.cwd()

        # 1. Значения из окружения
        env_host = os.getenv("APP_HOST") or os.getenv("HOST") or "127.0.0.1"
        env_port_str = os.getenv("APP_PORT") or os.getenv("PORT") or "8000"
        try:
            env_port = int(env_port_str)
        except ValueError:
            env_port = 8000

        env_students = Path(os.getenv("APP_STUDENTS_FILE", str(root / "students.xlsx")))
        env_tickets = Path(os.getenv("APP_TICKETS_FILE", str(root / "tickets.docx")))
        env_results = Path(os.getenv("APP_RESULTS_FILE", str(root / "results.xlsx")))
        env_log_level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
        env_auto_browser = os.getenv("APP_AUTO_BROWSER", "false").lower() in ("true", "1", "yes")

        # 2. Переопределение аргументами командной строки
        host = getattr(args, "host", None) or env_host
        port = getattr(args, "port", None) if getattr(args, "port", None) is not None else env_port
        
        students = Path(getattr(args, "students", None) or env_students)
        tickets = Path(getattr(args, "tickets", None) or env_tickets)
        results = Path(getattr(args, "results", None) or env_results)
        
        log_level = getattr(args, "log_level", None) or env_log_level
        auto_browser = getattr(args, "browser", None) if getattr(args, "browser", None) is not None else env_auto_browser

        # Приведение путей к абсолютным, если они относительные
        if not students.is_absolute():
            students = (root / students).resolve()
        if not tickets.is_absolute():
            tickets = (root / tickets).resolve()
        if not results.is_absolute():
            results = (root / results).resolve()

        return cls(
            host=str(host).strip(),
            port=int(port),
            students_path=students,
            tickets_path=tickets,
            results_path=results,
            log_level=log_level.strip(),
            auto_browser=bool(auto_browser),
        )
