"""
Абстракции (протоколы) для соблюдения принципов DIP, ISP, OCP и LSP.

Модуль не зависит от конкретных библиотек ввода-вывода (openpyxl, python-docx)
и графических тулкитов (tkinter).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Protocol, Sequence, runtime_checkable

from .models import ExamResult, InitializationReport, Student, Ticket


@runtime_checkable
class StudentReaderProtocol(Protocol):
    """Узкий интерфейс источника данных о группах и студентах."""

    @property
    def source_name(self) -> str:
        """Человекочитаемое имя источника данных для сообщений пользователю."""
        ...

    def is_available(self) -> bool:
        """Проверяет доступность источника данных."""
        ...

    def load_groups(self) -> list[str]:
        """Возвращает список доступных учебных групп."""
        ...

    def load_students_for_group(self, group_name: str) -> list[Student]:
        """Возвращает студентов указанной группы (или пустой список)."""
        ...


@runtime_checkable
class TicketParserProtocol(Protocol):
    """Узкий интерфейс источника экзаменационных билетов."""

    @property
    def source_name(self) -> str:
        """Человекочитаемое имя источника билетов для сообщений пользователю."""
        ...

    def is_available(self) -> bool:
        """Проверяет доступность источника билетов."""
        ...

    def parse_tickets(self) -> dict[int, Ticket]:
        """Загружает и возвращает словарь валидных билетов {номер: Ticket}."""
        ...


@runtime_checkable
class ResultJournalReaderProtocol(Protocol):
    """Интерфейс чтения истории назначений из журнала (ISP)."""

    def get_first_ticket_for_student(
        self,
        group: str,
        last_name: str,
        first_name: str,
    ) -> int | None:
        """Возвращает номер первого выданного билета студенту или None."""
        ...


@runtime_checkable
class ResultJournalWriterProtocol(Protocol):
    """Интерфейс записи назначений в журнал (ISP)."""

    def ensure_initialized(self) -> None:
        """Гарантирует готовность хранилища к работе."""
        ...

    def append_result(self, result: ExamResult) -> None:
        """Немедленно дописывает результат в конец журнала."""
        ...


@runtime_checkable
class ResultStorageProtocol(ResultJournalReaderProtocol, ResultJournalWriterProtocol, Protocol):
    """Комбинированный контракт хранилища для сервисного слоя."""

    ...


@runtime_checkable
class TicketSelectionStrategyProtocol(Protocol):
    """Стратегия выбора номера билета из доступных (OCP)."""

    def select_ticket_number(self, available_numbers: Sequence[int]) -> int:
        """Выбирает номер билета из непустой последовательности доступных номеров."""
        ...


@runtime_checkable
class LockHandlerProtocol(Protocol):
    """Обработчик блокировки файла хранилища при чтении/сохранении."""

    def __call__(self, file_path: Path, exc: Exception) -> bool:
        """Возвращает True для повтора операции или False для отмены."""
        ...


@runtime_checkable
class JournalStylerProtocol(Protocol):
    """Контракт оформления таблицы журнала Excel (SRP / OCP)."""

    def style_header(self, worksheet: Any) -> None:
        """Оформляет строку заголовков и ширину столбцов."""
        ...

    def style_row(self, worksheet: Any, row_index: int) -> None:
        """Оформляет новую добавленную строку данных."""
        ...


@runtime_checkable
class TicketServiceProtocol(Protocol):
    """Узкий контракт прикладного сервиса для слоя пользовательского интерфейса (ISP)."""

    def initialize(self) -> InitializationReport:
        """Инициализирует хранилище, загружает входные данные и возвращает сводку."""
        ...

    def get_groups(self) -> list[str]:
        """Возвращает список доступных групп."""
        ...

    def get_students(self, group: str) -> list[Student]:
        """Возвращает список студентов выбранной группы."""
        ...

    def assign_ticket(self, student: Student) -> tuple[Ticket, ExamResult]:
        """Назначает билет студенту и сохраняет запись в журнал."""
        ...


@runtime_checkable
class ResultPresenterProtocol(Protocol):
    """Контракт отображения окна/представления выданного билета (DIP)."""

    def show_result(self, ticket: Ticket, student: Student, is_repeat: bool) -> None:
        """Показывает результат назначения билета пользователю."""
        ...


@runtime_checkable
class AlertNotifierProtocol(Protocol):
    """Контракт показа предупреждений и ошибок пользователю (DIP)."""

    def show_warning(self, title: str, message: str) -> None:
        """Отображает предупреждение."""
        ...

    def show_error(self, title: str, message: str) -> None:
        """Отображает сообщение об ошибке."""
        ...

