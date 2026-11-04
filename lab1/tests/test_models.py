"""
Unit-тесты для модуля models.py.
"""

import pytest
from ticket_generator.models import StudentRecord


class TestStudentRecord:
    def test_valid_record_creation(self):
        record = StudentRecord(last_name="Смирнов", first_name="Алексей", ticket_number=5)
        assert record.last_name == "Смирнов"
        assert record.first_name == "Алексей"
        assert record.ticket_number == 5
        assert isinstance(record.timestamp, str)
        assert len(record.timestamp) > 0

    def test_whitespace_is_trimmed(self):
        record = StudentRecord(last_name="  Петров   ", first_name="  Иван  ", ticket_number=12)
        assert record.last_name == "Петров"
        assert record.first_name == "Иван"

    def test_empty_last_name_raises_error(self):
        with pytest.raises(ValueError, match="Фамилия не может быть пустой"):
            StudentRecord(last_name="   ", first_name="Иван", ticket_number=1)

    def test_empty_first_name_raises_error(self):
        with pytest.raises(ValueError, match="Имя не может быть пустым"):
            StudentRecord(last_name="Иванов", first_name="", ticket_number=1)

    def test_non_string_names_raise_type_error(self):
        with pytest.raises(TypeError, match="Фамилия должна быть строкой"):
            StudentRecord(last_name=123, first_name="Иван", ticket_number=1)  # type: ignore

        with pytest.raises(TypeError, match="Имя должна быть строкой|Имя должно быть строкой"):
            StudentRecord(last_name="Иванов", first_name=None, ticket_number=1)  # type: ignore

    def test_invalid_ticket_number(self):
        with pytest.raises(ValueError, match="положительным"):
            StudentRecord(last_name="Иванов", first_name="Иван", ticket_number=0)

        with pytest.raises(ValueError, match="положительным"):
            StudentRecord(last_name="Иванов", first_name="Иван", ticket_number=-5)

        with pytest.raises(TypeError, match="целым числом"):
            StudentRecord(last_name="Иванов", first_name="Иван", ticket_number="7")  # type: ignore

        with pytest.raises(TypeError, match="целым числом"):
            StudentRecord(last_name="Иванов", first_name="Иван", ticket_number=True)  # type: ignore

    def test_to_row(self):
        record = StudentRecord(
            last_name="Сидоров",
            first_name="Олег",
            ticket_number=18,
            timestamp="2026-11-04 15:30:00",
        )
        assert record.to_row() == ["Сидоров", "Олег", 18, "2026-11-04 15:30:00"]
