"""
Тесты для парсеров ExcelStudentReader и DocxTicketParser.
"""

from pathlib import Path
import pytest

from ticket_gui.parsers import (
    ExcelStudentReader,
    DocxTicketParser,
    SourceNotFoundError,
)


class TestExcelStudentReader:
    def test_load_groups(self, sample_students_file: Path):
        reader = ExcelStudentReader(sample_students_file)
        groups = reader.load_groups()
        assert groups == ["ИВТ-21", "ПИ-22", "ПУСТАЯ-00"]

    def test_load_students_for_group(self, sample_students_file: Path):
        reader = ExcelStudentReader(sample_students_file)
        students = reader.load_students_for_group("ИВТ-21")
        assert len(students) == 3
        assert students[0].full_name == "Иванов Иван"
        assert students[1].full_name == "Петров Петр"
        assert students[2].full_name == "Сидорова Анна"

    def test_load_empty_group_returns_empty_list_without_exception(self, sample_students_file: Path):
        """Проверка требования: если группа пустая — список пуст, без исключений."""
        reader = ExcelStudentReader(sample_students_file)
        students = reader.load_students_for_group("ПУСТАЯ-00")
        assert students == []

    def test_load_nonexistent_group_returns_empty_list(self, sample_students_file: Path):
        reader = ExcelStudentReader(sample_students_file)
        assert reader.load_students_for_group("НЕИЗВЕСТНАЯ_ГРУППА") == []

    def test_missing_students_file_raises_source_not_found(self, tmp_dir: Path):
        reader = ExcelStudentReader(tmp_dir / "nonexistent.xlsx")
        with pytest.raises(SourceNotFoundError, match="не найден"):
            reader.load_groups()


class TestDocxTicketParser:
    def test_parse_valid_tickets(self, sample_tickets_file: Path):
        parser = DocxTicketParser(sample_tickets_file)
        tickets = parser.parse_tickets()

        # Билеты 1, 2, 3 валидны
        assert 1 in tickets
        assert 2 in tickets
        assert 3 in tickets

        assert len(tickets[1].questions) == 3
        assert "Вопрос 1.1" in tickets[1].questions[0]
        assert "Вопрос 1.2" in tickets[1].questions[1]
        assert "Вопрос 1.3" in tickets[1].questions[2]

    def test_skip_defective_ticket_with_fewer_than_three_questions(self, sample_tickets_file: Path):
        """
        Проверка требования:
        'Если в tickets.docx меньше 3 вопросов у какого-то билета —
        билет пропускается при парсинге, ошибка логируется, приложение продолжает работать'.
        """
        parser = DocxTicketParser(sample_tickets_file)
        tickets = parser.parse_tickets()

        # Билет 4 содержит всего 1 вопрос, поэтому должен быть пропущен
        assert 4 not in tickets
        assert len(tickets) == 3

    def test_missing_tickets_file_raises_source_not_found(self, tmp_dir: Path):
        parser = DocxTicketParser(tmp_dir / "nonexistent.docx")
        with pytest.raises(SourceNotFoundError, match="не найден"):
            parser.parse_tickets()
