"""
Абстракции (порты) и базовые исключения приложения.

Определяет узкие интерфейсы (ISP) для инверсии зависимостей (DIP):
бизнес-логика зависит только от этих протоколов и исключений,
а не от конкретных реализаций хранения, генерации или ввода/вывода.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from .models import StudentRecord


class StorageError(Exception):
    """Базовая ошибка уровня хранилища записей."""


class StorageLockedError(StorageError):
    """Исключение при блокировке ресурса хранения другим процессом."""


@runtime_checkable
class TicketGenerator(Protocol):
    """Интерфейс генератора номеров экзаменационных билетов."""

    def generate(self) -> int:
        """Сгенерировать номер билета."""
        ...


@runtime_checkable
class ConsoleOutput(Protocol):
    """Узкий интерфейс вывода сообщений пользователю."""

    def print(self, message: str) -> None:
        """Вывести сообщение."""
        ...


@runtime_checkable
class ConsoleInput(Protocol):
    """Узкий интерфейс ввода строковых данных пользователем."""

    def read_name(self, prompt: str) -> str | None:
        """
        Запросить непустую строку у пользователя.

        Возвращает None при сигнале завершения (ESC / EOF).
        """
        ...


@runtime_checkable
class ConsoleIO(ConsoleOutput, ConsoleInput, Protocol):
    """Объединенный интерфейс интерактивного консольного ввода/вывода."""

    def show_startup_hint(self) -> None:
        """Вывести стартовую подсказку пользователю."""
        ...


@runtime_checkable
class JournalWriter(Protocol):
    """Узкий интерфейс записи в журнал (используется прикладной логикой)."""

    def ensure_initialized(self) -> None:
        """Гарантировать готовность хранилища к записи."""
        ...

    def append_record(self, record: StudentRecord) -> None:
        """Добавить запись о студенте в хранилище."""
        ...


@runtime_checkable
class JournalReader(Protocol):
    """Узкий интерфейс чтения из журнала."""

    def read_all_rows(self) -> list[tuple[Any, ...]]:
        """Прочитать все строки журнала."""
        ...

    def get_records_count(self) -> int:
        """Вернуть количество записей студентов."""
        ...


@runtime_checkable
class JournalStorage(JournalWriter, JournalReader, Protocol):
    """Полный интерфейс хранилища, поддерживающий чтение и запись."""


@runtime_checkable
class RecordRowMapper(Protocol):
    """Интерфейс маппинга доменной записи в табличное представление."""

    @property
    def headers(self) -> Sequence[str]:
        """Заголовки колонок таблицы."""
        ...

    def to_row(self, record: StudentRecord) -> list[Any]:
        """Преобразовать запись студента в строку таблицы."""
        ...


@runtime_checkable
class LockRetryHandler(Protocol):
    """Стратегия реакции на временную блокировку ресурса хранения."""

    def __call__(self, resource: Any, exception: Exception) -> bool:
        """Возвращает True для повторной попытки, False для отмены."""
        ...

