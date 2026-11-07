"""
Pytest fixtures для тестирования приложения генератора билетов с UI.
"""

from __future__ import annotations
import tempfile
from pathlib import Path
from typing import Iterator
import pytest
import openpyxl
import docx

from ticket_gui.models import Student, Ticket
from ticket_gui.parsers import ExcelStudentReader, DocxTicketParser
from ticket_gui.storage import ResultJournalStorage
from ticket_gui.service import TicketService


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    """Создает временную директорию для изолированных файловых тестов."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_students_file(tmp_dir: Path) -> Path:
    """Создает тестовый students.xlsx с тремя группами, включая пустую."""
    file_path = tmp_dir / "test_students.xlsx"
    wb = openpyxl.Workbook()

    # Лист 1: ИВТ-21
    ws1 = wb.active
    ws1.title = "ИВТ-21"
    ws1.append(["Фамилия", "Имя"])
    ws1.append(["Иванов", "Иван"])
    ws1.append(["Петров", "Петр"])
    ws1.append(["Сидорова", "Анна"])

    # Лист 2: ПИ-22
    ws2 = wb.create_sheet("ПИ-22")
    ws2.append(["Фамилия", "Имя"])
    ws2.append(["Васильев", "Василий"])
    ws2.append(["Морозова", "Елена"])

    # Лист 3: ПУСТАЯ-00 (для проверки требования пустой группы)
    ws3 = wb.create_sheet("ПУСТАЯ-00")
    ws3.append(["Фамилия", "Имя"])

    wb.save(file_path)
    wb.close()
    return file_path


@pytest.fixture
def sample_tickets_file(tmp_dir: Path) -> Path:
    """
    Создает тестовый tickets.docx с валидными билетами и одним дефектным (<3 вопросов).
    """
    file_path = tmp_dir / "test_tickets.docx"
    doc = docx.Document()

    # Валидный Билет 1
    doc.add_paragraph("Билет 1")
    doc.add_paragraph("1. Вопрос 1.1")
    doc.add_paragraph("2. Вопрос 1.2")
    doc.add_paragraph("3. Вопрос 1.3")
    doc.add_paragraph("")

    # Валидный Билет 2
    doc.add_paragraph("Билет 2")
    doc.add_paragraph("1. Вопрос 2.1")
    doc.add_paragraph("2. Вопрос 2.2")
    doc.add_paragraph("3. Вопрос 2.3")
    doc.add_paragraph("")

    # Валидный Билет 3
    doc.add_paragraph("Билет 3")
    doc.add_paragraph("1. Вопрос 3.1")
    doc.add_paragraph("2. Вопрос 3.2")
    doc.add_paragraph("3. Вопрос 3.3")
    doc.add_paragraph("")

    # Дефектный Билет 4 (меньше 3 вопросов — должен быть пропущен)
    doc.add_paragraph("Билет 4")
    doc.add_paragraph("1. Единственный вопрос дефектного билета")
    doc.add_paragraph("")

    doc.save(file_path)
    return file_path


@pytest.fixture
def sample_results_path(tmp_dir: Path) -> Path:
    """Путь к тестовому файлу results.xlsx."""
    return tmp_dir / "test_results.xlsx"


@pytest.fixture
def ticket_service(
    sample_students_file: Path,
    sample_tickets_file: Path,
    sample_results_path: Path,
) -> TicketService:
    """Инициализированный TicketService на тестовых данных."""
    reader = ExcelStudentReader(sample_students_file)
    parser = DocxTicketParser(sample_tickets_file)
    storage = ResultJournalStorage(sample_results_path)
    service = TicketService(reader, parser, storage, seed=42)
    service.initialize()
    return service
