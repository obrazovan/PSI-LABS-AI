"""
Сервисный слой бизнес-логики (Business Logic / Application Service).
"""

from __future__ import annotations
import logging
import random
from typing import Sequence

from .exceptions import NoTicketsAvailableError
from .models import ExamResult, InitializationReport, Student, Ticket
from .ports import (
    ResultStorageProtocol,
    StudentReaderProtocol,
    TicketParserProtocol,
    TicketSelectionStrategyProtocol,
)

logger = logging.getLogger(__name__)


class RandomTicketSelector:
    """Стратегия случайного выбора номера билета из доступных (OCP)."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def select_ticket_number(self, available_numbers: Sequence[int]) -> int:
        if not available_numbers:
            raise NoTicketsAvailableError("Список доступных номеров билетов пуст.")
        return self._rng.choice(sorted(available_numbers))


class TicketService:
    """
    Координатор бизнес-логики приложения.

    Зависит исключительно от абстракций (StudentReaderProtocol, TicketParserProtocol,
    ResultStorageProtocol, TicketSelectionStrategyProtocol) согласно DIP и ISP.
    """

    def __init__(
        self,
        student_reader: StudentReaderProtocol,
        ticket_parser: TicketParserProtocol,
        storage: ResultStorageProtocol,
        ticket_selector: TicketSelectionStrategyProtocol | None = None,
        seed: int | None = None,
    ) -> None:
        self.student_reader = student_reader
        self.ticket_parser = ticket_parser
        self.storage = storage
        self._ticket_selector: TicketSelectionStrategyProtocol = (
            ticket_selector if ticket_selector is not None else RandomTicketSelector(seed=seed)
        )

        self._tickets: dict[int, Ticket] = {}
        self._groups: list[str] = []
        self._initialized: bool = False
        self._last_report: InitializationReport | None = None

    @property
    def tickets(self) -> dict[int, Ticket]:
        return self._tickets

    def initialize(self, force: bool = False) -> InitializationReport:
        """
        Инициализирует хранилище результатов, проверяет источники и загружает данные.
        """
        if self._initialized and self._last_report is not None and not force:
            return self._last_report

        self.storage.ensure_initialized()

        missing_sources: list[str] = []

        if self.student_reader.is_available():
            try:
                self._groups = self.student_reader.load_groups()
            except Exception as exc:
                logger.error("Ошибка при чтении групп из источника студентов: %s", exc)
                self._groups = []
        else:
            missing_sources.append(self.student_reader.source_name)
            self._groups = []

        if self.ticket_parser.is_available():
            try:
                self._tickets = self.ticket_parser.parse_tickets()
            except Exception as exc:
                logger.error("Ошибка при парсинге билетов: %s", exc)
                self._tickets = {}
        else:
            missing_sources.append(self.ticket_parser.source_name)
            self._tickets = {}

        self._last_report = InitializationReport(
            missing_sources=tuple(missing_sources),
            groups_count=len(self._groups),
            tickets_count=len(self._tickets),
        )
        self._initialized = True
        return self._last_report

    def get_groups(self) -> list[str]:
        """Возвращает список доступных групп."""
        return list(self._groups)

    def get_students(self, group: str) -> list[Student]:
        """Возвращает список студентов для заданной группы."""
        if not group or not self.student_reader.is_available():
            return []
        try:
            return self.student_reader.load_students_for_group(group)
        except Exception as exc:
            logger.error("Не удалось загрузить студентов для группы %s: %s", group, exc)
            return []

    def assign_ticket(self, student: Student) -> tuple[Ticket, ExamResult]:
        """
        Назначает экзаменационный билет студенту согласно правилам ТЗ.

        Returns:
            Кортеж (Ticket, ExamResult).
        """
        if not self._tickets:
            raise NoTicketsAvailableError("В файле tickets.docx отсутствуют корректные билеты.")

        first_ticket_number = self.storage.get_first_ticket_for_student(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
        )

        if first_ticket_number is not None:
            assigned_number = first_ticket_number
            is_repeat = True
        else:
            assigned_number = self._ticket_selector.select_ticket_number(list(self._tickets.keys()))
            is_repeat = False

        ticket = self._resolve_ticket(assigned_number)

        result = ExamResult(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
            ticket_number=assigned_number,
            is_repeat=is_repeat,
        )

        self.storage.append_result(result)
        return ticket, result

    def _resolve_ticket(self, ticket_number: int) -> Ticket:
        """Возвращает объект билета по номеру или резервный билет, если номер удален из docx."""
        if ticket_number in self._tickets:
            return self._tickets[ticket_number]
        return Ticket(
            number=ticket_number,
            questions=("Вопрос 1", "Вопрос 2", "Вопрос 3"),
        )
