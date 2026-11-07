"""
Тесты для сервисного слоя TicketService (бизнес-логика и идемпотентность).
"""

from pathlib import Path
import pytest

from ticket_gui.models import Student
from ticket_gui.service import TicketService, NoTicketsAvailableError


class TestTicketService:
    def test_first_generation_assigns_random_ticket(self, ticket_service: TicketService):
        student = Student("ИВТ-21", "Иванов", "Иван")

        ticket, result = ticket_service.assign_ticket(student)

        # Билет должен быть одним из валидных (1, 2, 3)
        assert ticket.number in (1, 2, 3)
        assert len(ticket.questions) == 3
        assert result.ticket_number == ticket.number
        assert result.is_repeat is False
        assert result.repeat_str == "нет"

        # Проверяем немедленную запись в results.xlsx
        rows = ticket_service.storage.read_all_rows()
        assert len(rows) == 2  # шапка + 1 запись
        assert rows[1][0] == "ИВТ-21"
        assert rows[1][1] == "Иванов"
        assert rows[1][2] == "Иван"
        assert rows[1][3] == ticket.number
        assert rows[1][5] == "нет"

    def test_idempotence_repeat_selection_returns_same_ticket_and_appends_row(
        self, ticket_service: TicketService
    ):
        """
        Критерии приёмки 4 и 8:
        - Повторный выбор того же студента возвращает тот же номер билета.
        - Добавляется новая строка в конце журнала, старые не меняются.
        - Номер билета совпадает с первой записью.
        - Колонка 'Повтор' = 'да'.
        """
        student = Student("ИВТ-21", "Иванов", "Иван")

        # 1. Первая генерация
        ticket1, result1 = ticket_service.assign_ticket(student)
        first_ticket_number = ticket1.number
        assert result1.is_repeat is False

        # 2. Повторная генерация того же студента
        ticket2, result2 = ticket_service.assign_ticket(student)
        assert ticket2.number == first_ticket_number
        assert result2.ticket_number == first_ticket_number
        assert result2.is_repeat is True
        assert result2.repeat_str == "да"

        # 3. Третья генерация того же студента
        ticket3, result3 = ticket_service.assign_ticket(student)
        assert ticket3.number == first_ticket_number
        assert result3.is_repeat is True

        # Проверка журнала: 1 шапка + 3 строки в хронологическом порядке
        rows = ticket_service.storage.read_all_rows()
        assert len(rows) == 4

        # Первая запись
        assert rows[1][1] == "Иванов"
        assert rows[1][3] == first_ticket_number
        assert rows[1][5] == "нет"

        # Вторая запись (повтор)
        assert rows[2][1] == "Иванов"
        assert rows[2][3] == first_ticket_number
        assert rows[2][5] == "да"

        # Третья запись (повтор)
        assert rows[3][1] == "Иванов"
        assert rows[3][3] == first_ticket_number
        assert rows[3][5] == "да"

    def test_chronological_history_multiple_students(self, ticket_service: TicketService):
        """Критерий 9: Восстановление полной истории всех генераций."""
        s1 = Student("ИВТ-21", "Иванов", "Иван")
        s2 = Student("ИВТ-21", "Петров", "Петр")
        s3 = Student("ПИ-22", "Васильев", "Василий")

        t1, _ = ticket_service.assign_ticket(s1)
        t2, _ = ticket_service.assign_ticket(s2)
        # Повтор первого
        t1_repeat, _ = ticket_service.assign_ticket(s1)
        t3, _ = ticket_service.assign_ticket(s3)

        assert t1_repeat.number == t1.number

        rows = ticket_service.storage.read_all_rows()
        assert len(rows) == 5  # Шапка + 4 записи
        assert rows[1][1] == "Иванов" and rows[1][5] == "нет"
        assert rows[2][1] == "Петров" and rows[2][5] == "нет"
        assert rows[3][1] == "Иванов" and rows[3][5] == "да"
        assert rows[4][1] == "Васильев" and rows[4][5] == "нет"

    def test_no_tickets_available_raises_error(self, ticket_service: TicketService):
        student = Student("ИВТ-21", "Иванов", "Иван")
        ticket_service._tickets.clear()

        with pytest.raises(NoTicketsAvailableError, match="отсутствуют"):
            ticket_service.assign_ticket(student)
