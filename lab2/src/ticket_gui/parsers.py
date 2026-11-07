"""
Модули парсинга и загрузки данных из students.xlsx и tickets.docx.
"""

from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
import openpyxl
import docx

from .models import Student, Ticket

logger = logging.getLogger(__name__)


class SourceNotFoundError(FileNotFoundError):
    """Исключение при отсутствии входного файла данных."""
    pass


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
        groups = [sheet_name.strip() for sheet_name in wb.sheetnames if sheet_name.strip()]
        wb.close()
        return groups

    def load_students_for_group(self, group_name: str) -> list[Student]:
        """
        Загружает студентов указанной группы.
        Если группа пуста — возвращает пустой список без исключений.
        """
        if not self.is_available():
            raise SourceNotFoundError(f"Файл со списком студентов не найден: {self.file_path}")

        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        if group_name not in wb.sheetnames:
            wb.close()
            return []

        ws = wb[group_name]
        students: list[Student] = []

        # Читаем со строки 2 (строка 1 — шапка)
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 2:
                continue
            last_name_val = row[0]
            first_name_val = row[1]

            if last_name_val is None or first_name_val is None:
                continue

            last_name = str(last_name_val).strip()
            first_name = str(first_name_val).strip()

            if last_name and first_name:
                students.append(Student(group=group_name, last_name=last_name, first_name=first_name))

        wb.close()
        return students

    def load_all_students(self) -> dict[str, list[Student]]:
        """Загружает структуру всех групп и их студентов в словарь {группа: [студенты]}."""
        groups = self.load_groups()
        result: dict[str, list[Student]] = {}
        for group in groups:
            result[group] = self.load_students_for_group(group)
        return result


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
    QUESTION_PATTERN = re.compile(r"^\s*(\d+)[\.\)]\s*(.+)$")

    def __init__(self, file_path: str | Path = "tickets.docx") -> None:
        self.file_path = Path(file_path)

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
                # Нашли заголовок следующего билета — финализируем предыдущий
                finalize_ticket()
                current_number = int(header_match.group(1))
                continue

            if current_number is not None:
                # Проверяем, является ли абзац вопросом
                q_match = self.QUESTION_PATTERN.match(text)
                if q_match:
                    # Извлекаем текст вопроса (с сохранением или без номера)
                    current_questions.append(text)
                else:
                    # Если строка без цифры, но идет внутри билета
                    current_questions.append(text)

        # Финализируем последний билет документа
        finalize_ticket()

        if not tickets:
            logger.warning("В файле %s не найдено ни одного валидного билета.", self.file_path)

        return tickets
