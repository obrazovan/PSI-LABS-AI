"""
Модули парсинга и загрузки данных из students.xlsx и tickets.docx.
"""

from __future__ import annotations
import logging
import re
from pathlib import Path
import docx
import openpyxl

from .exceptions import SourceNotFoundError
from .models import Student, Ticket

logger = logging.getLogger(__name__)


class ExcelStudentReader:
    """
    Чтение списка студентов и групп из файла Excel (students.xlsx).

    Формат файла:
    - Каждый лист соответствует одной учебной группе (имя листа = название группы).
    - Строка 1 — заголовки (Колонка A: Фамилия, Колонка B: Имя).
    - Данные начинаются со строки 2.
    """

    def __init__(self, file_path: str | Path = "students.xlsx") -> None:
        self.file_path = Path(file_path)

    @property
    def source_name(self) -> str:
        """Возвращает отображаемое имя источника студентов."""
        return f"Список студентов ({self.file_path.name})"

    def is_available(self) -> bool:
        """Проверяет существование файла на диске."""
        return self.file_path.exists() and self.file_path.is_file()

    def load_groups(self) -> list[str]:
        """
        Возвращает список всех групп (имен листов).

        Raises:
            SourceNotFoundError: Если файл не найден.
        """
        if not self.is_available():
            raise SourceNotFoundError(f"Файл со списком студентов не найден: {self.file_path}")

        wb = openpyxl.load_workbook(self.file_path, read_only=True)
        try:
            return [sheet_name.strip() for sheet_name in wb.sheetnames if sheet_name.strip()]
        finally:
            wb.close()

    def load_students_for_group(self, group_name: str) -> list[Student]:
        """
        Загружает студентов указанной группы.
        Если группа пуста или отсутствует — возвращает пустой список без исключений.
        """
        if not self.is_available():
            raise SourceNotFoundError(f"Файл со списком студентов не найден: {self.file_path}")

        wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
        try:
            if group_name not in wb.sheetnames:
                return []

            ws = wb[group_name]
            students: list[Student] = []

            # Читаем со строки 2 (строка 1 — шапка)
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 2:
                    continue
                last_name_val, first_name_val = row[0], row[1]
                if last_name_val is None or first_name_val is None:
                    continue

                last_name = str(last_name_val).strip()
                first_name = str(first_name_val).strip()
                if last_name and first_name:
                    students.append(
                        Student(group=group_name, last_name=last_name, first_name=first_name)
                    )

            return students
        finally:
            wb.close()


class DocxTicketParser:
    """
    Парсер экзаменационных билетов из файла Word (tickets.docx).

    Формат:
    Билет N
    1. Вопрос первый
    2. Вопрос второй
    3. Вопрос третий

    Устойчивость:
    Если в билете меньше 3 вопросов или заголовок не распознан — билет
    пропускается, ошибка логируется, приложение продолжает работу.
    """

    TICKET_HEADER_PATTERN = re.compile(r"^\s*Билет\s*(?:№\s*)?(\d+)\s*$", re.IGNORECASE)
    HEADER_CANDIDATE_PATTERN = re.compile(r"^\s*Билет\b", re.IGNORECASE)
    QUESTION_PATTERN = re.compile(r"^\s*(\d+)[\.\)]\s*(.+)$")

    def __init__(self, file_path: str | Path = "tickets.docx") -> None:
        self.file_path = Path(file_path)

    @property
    def source_name(self) -> str:
        """Возвращает отображаемое имя источника билетов."""
        return f"Список билетов ({self.file_path.name})"

    def is_available(self) -> bool:
        """Проверяет существование файла tickets.docx."""
        return self.file_path.exists() and self.file_path.is_file()

    def parse_tickets(self) -> dict[int, Ticket]:
        """
        Парсит все билеты из Word-файла.

        Returns:
            Словарь {номер_билета: Ticket}.
        Raises:
            SourceNotFoundError: Если файл не найден.
        """
        if not self.is_available():
            raise SourceNotFoundError(f"Файл с билетами не найден: {self.file_path}")

        doc = docx.Document(self.file_path)
        tickets: dict[int, Ticket] = {}

        current_number: int | None = None
        current_questions: list[str] = []

        def finalize_ticket() -> None:
            nonlocal current_number, current_questions
            if current_number is not None:
                if len(current_questions) >= 3:
                    tickets[current_number] = Ticket(
                        number=current_number,
                        questions=tuple(current_questions),
                    )
                else:
                    logger.warning(
                        "Билет №%d пропущен: содержит %d вопросов (требуется минимум 3).",
                        current_number,
                        len(current_questions),
                    )
            current_number = None
            current_questions = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            header_match = self.TICKET_HEADER_PATTERN.match(text)
            if header_match:
                finalize_ticket()
                current_number = int(header_match.group(1))
                continue

            if self.HEADER_CANDIDATE_PATTERN.match(text):
                finalize_ticket()
                logger.warning("Нераспознанный заголовок билета пропущен: %s", text)
                continue

            if current_number is not None:
                current_questions.append(self._extract_question_text(text))
            else:
                logger.warning("Строка вне распознанного билета пропущена: %s", text)

        finalize_ticket()

        if not tickets:
            logger.warning("В файле %s не найдено ни одного валидного билета.", self.file_path)

        return tickets

    def _extract_question_text(self, text: str) -> str:
        """Извлекает формулировку вопроса, удаляя ведущий номер вида '1. ' или '1) '."""
        q_match = self.QUESTION_PATTERN.match(text)
        if q_match:
            cleaned = q_match.group(2).strip()
            if cleaned:
                return cleaned
        return text
