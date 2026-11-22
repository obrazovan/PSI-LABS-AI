"""
Структурированное логирование для продакшена (Structured Production Logging).
"""

from __future__ import annotations
import logging
import sys
from typing import TextIO


class StructuredFormatter(logging.Formatter):
    """
    Форматтер логирования с ISO-8601 временными метками и именами модулей.
    """

    FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


def setup_logging(
    level: str = "INFO",
    stream: TextIO | None = None,
) -> logging.Logger:
    """
    Инициализирует глобальное логирование приложения.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    
    # Избегаем дублирования хэндлеров при повторной инициализации
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)

    root_logger.setLevel(numeric_level)
    return logging.getLogger("ticket_gui")
