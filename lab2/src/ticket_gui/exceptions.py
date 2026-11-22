"""
Доменные и прикладные исключения генератора билетов.

Вынесены в отдельный модуль, чтобы верхние слои (service, ui) не зависели
от модулей конкретной инфраструктуры (parsers, storage).
"""

from __future__ import annotations


class SourceNotFoundError(FileNotFoundError):
    """Исключение при отсутствии входного файла данных."""


class NoTicketsAvailableError(RuntimeError):
    """Исключение при отсутствии доступных билетов."""


class StorageLockedError(OSError):
    """Исключение при невозможности доступа из-за блокировки файла (например, открыт в Excel)."""

