"""
Тесты для моделей данных (Student, Ticket, ExamResult).
"""

import pytest
from ticket_gui.models import Student, Ticket, ExamResult


class TestStudentModel:
    def test_valid_student(self):
        s = Student(group="ИВТ-21", last_name="Иванов", first_name="Иван")
        assert s.group == "ИВТ-21"
        assert s.last_name == "Иванов"
        assert s.first_name == "Иван"
        assert s.full_name == "Иванов Иван"
        assert s.identity_key == ("ивт-21", "иванов", "иван")

    def test_whitespace_normalization(self):
        s = Student(group="  ПИ-22  ", last_name="  Петров  ", first_name="  Петр  ")
        assert s.group == "ПИ-22"
        assert s.last_name == "Петров"
        assert s.first_name == "Петр"
        assert s.full_name == "Петров Петр"

    def test_empty_fields_raise_value_error(self):
        with pytest.raises(ValueError, match="группы"):
            Student(group="   ", last_name="Иванов", first_name="Иван")

        with pytest.raises(ValueError, match="Фамилия"):
            Student(group="ИВТ-21", last_name="", first_name="Иван")

        with pytest.raises(ValueError, match="Имя"):
            Student(group="ИВТ-21", last_name="Иванов", first_name="  ")


class TestTicketModel:
    def test_valid_ticket(self):
        t = Ticket(number=1, questions=("Вопрос 1", "Вопрос 2", "Вопрос 3"))
        assert t.number == 1
        assert len(t.questions) == 3

    def test_invalid_number_raises_error(self):
        with pytest.raises(ValueError, match="Некорректный номер"):
            Ticket(number=0, questions=("В1", "В2", "В3"))

        with pytest.raises(ValueError, match="Некорректный номер"):
            Ticket(number=-5, questions=("В1", "В2", "В3"))

    def test_fewer_than_three_questions_raises_error(self):
        with pytest.raises(ValueError, match="меньше 3 вопросов"):
            Ticket(number=2, questions=("Вопрос 1", "Вопрос 2"))


class TestExamResultModel:
    def test_result_to_row_format(self):
        res = ExamResult(
            group="ИВТ-21",
            last_name="Смирнов",
            first_name="Олег",
            ticket_number=7,
            is_repeat=False,
            timestamp="2026-11-07 15:00:00",
        )
        row = res.to_row()
        assert row == ["ИВТ-21", "Смирнов", "Олег", 7, "2026-11-07 15:00:00", "нет"]

    def test_repeat_flag_string(self):
        res_repeat = ExamResult(
            group="ИВТ-21",
            last_name="Смирнов",
            first_name="Олег",
            ticket_number=7,
            is_repeat=True,
            timestamp="2026-11-07 15:05:00",
        )
        assert res_repeat.repeat_str == "да"
        assert res_repeat.to_row()[5] == "да"
