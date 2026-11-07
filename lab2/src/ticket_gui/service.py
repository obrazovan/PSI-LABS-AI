"""
Сервисный слой бизнес-логики (Business Logic / Application Service).
"""

from __future__ import annotations
import logging
import random
from typing import Dict, List, Optional, Tuple

from .models import Student, Ticket, ExamResult
from .parsers import ExcelStudentReader, DocxTicketParser, SourceNotFoundError
from .storage import ResultJournalStorage

logger = logging.getLogger(__name__)


class NoTicketsAvailableError(RuntimeError):
    """Исключение при отсутствии доступных билетов."""
    pass


class TicketService:
    """
    Координатор бизнес-логики приложения.

    Реализует правила:
    1. Идемпотентность: если студент уже есть в results.xlsx, ему назначается
       номер билета из самой первой записи по этому студенту, новый билет не
       генерируется, а строка пишется с пометкой 'да' в колонке 'Повтор'.
    2. Случайный выбор: если студента нет в журнале — билет выбирается случайно
       из доступных валидных билетов, с пометкой 'нет'.
    3. Мгновенное сохранение в журнал.
    """

    def __init__(
        self,
        student_reader: ExcelStudentReader,
        ticket_parser: DocxTicketParser,
        storage: ResultJournalStorage,
        seed: int | None = None,
    ) -> None:
        self.student_reader = student_reader
        self.ticket_parser = ticket_parser
        self.storage = storage
        self._rng = random.Random(seed)

        self._tickets: dict[int, Ticket] = {}
        self._groups: list[str] = []

    @property
    def tickets(self) -> dict[int, Ticket]:
        return self._tickets

    def initialize(self) -> None:
        """
        Инициализирует хранилище результатов и загружает данные из входных файлов.
        """
        self.storage.ensure_initialized()

        if self.student_reader.is_available():
            try:
                self._groups = self.student_reader.load_groups()
            except Exception as e:
                logger.error("Ошибка при чтении groups из students.xlsx: %s", e)
                self._groups = []
        else:
            self._groups = []

        if self.ticket_parser.is_available():
            try:
                self._tickets = self.ticket_parser.parse_tickets()
            except Exception as e:
                logger.error("Ошибка при парсинге tickets.docx: %s", e)
                self._tickets = {}
        else:
            self._tickets = {}

    def get_groups(self) -> list[str]:
        """Возвращает список доступных групп."""
        return list(self._groups)

    def get_students(self, group: str) -> list[Student]:
        """Возвращает список студентов для заданной группы."""
        if not group or not self.student_reader.is_available():
            return []
        try:
            return self.student_reader.load_students_for_group(group)
        except Exception as e:
            logger.error("Не удалось загрузить студентов для группы %s: %s", group, e)
            return []

    def assign_ticket(self, student: Student) -> tuple[Ticket, ExamResult]:
        """
        Назначает экзаменационный билет студенту согласно правилам ТЗ.

        Returns:
            Кортеж (Ticket, ExamResult).
        """
        if not self._tickets:
            raise NoTicketsAvailableError("В файле tickets.docx отсутствуют корректные билеты.")

        # 1. Проверяем, есть ли студент в results.xlsx (идемпотентность)
        first_ticket_number = self.storage.get_first_ticket_for_student(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
        )

        if first_ticket_number is not None:
            # Студент уже сдавал — берем номер из первой записи
            assigned_number = first_ticket_number
            is_repeat = True
        else:
            # Студент сдает впервые — случайный выбор из доступных билетов
            available_numbers = sorted(list(self._tickets.keys()))
            assigned_number = self._rng.choice(available_numbers)
            is_repeat = False

        # Получаем объект билета (если номер есть в словаре)
        if assigned_number in self._tickets:
            ticket = self._tickets[assigned_number]
        else:
            # Редкий случай: билет был в старых записях results, но удален из docx
            ticket = Ticket(
                number=assigned_number,
                questions=("Вопрос 1", "Вопрос 2", "Вопрос 3"),
            )

        # Создаем результат и сразу сохраняем в файл
        result = ExamResult(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
            ticket_number=assigned_number,
            is_repeat=is_repeat,
        )

        self.storage.append_result(result)
        return ticket, result
