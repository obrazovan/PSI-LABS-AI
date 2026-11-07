"""
Тесты логики интерфейса (состояния кнопок, выпадающих списков и событий).
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import tkinter as tk
import pytest

from ticket_gui.ui.main_window import MainWindow
from ticket_gui.ui.result_dialog import ResultDialog
from ticket_gui.models import Student, Ticket
from ticket_gui.service import TicketService


@pytest.fixture
def tk_root():
    """Фикстура для корневого окна Tkinter."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


class TestUIStateAndInteractions:
    def test_initial_state(self, ticket_service: TicketService):
        """
        Критерии 1 и 2:
        - Группы заполняются из sheets.
        - Кнопка неактивна до выбора и группы, и студента.
        """
        app = MainWindow(ticket_service)
        app.withdraw()

        try:
            # 1. Список групп заполнен
            group_values = list(app.group_combo["values"])
            assert "ИВТ-21" in group_values
            assert "ПИ-22" in group_values
            assert "ПУСТАЯ-00" in group_values

            # 2. Список студентов и кнопка неактивны при старте
            assert str(app.student_combo["state"]) == "disabled"
            assert str(app.generate_btn["state"]) == "disabled"
        finally:
            app.destroy()

    def test_group_selection_populates_students(self, ticket_service: TicketService):
        """Выбор группы заполняет студентов этой группы в формате 'Фамилия Имя'."""
        app = MainWindow(ticket_service)
        app.withdraw()

        try:
            # Выбираем группу 'ИВТ-21'
            app.group_combo.set("ИВТ-21")
            app._on_group_selected()

            # Список студентов должен быть активирован
            assert str(app.student_combo["state"]) == "readonly"
            student_values = list(app.student_combo["values"])
            assert len(student_values) == 3
            assert "Иванов Иван" in student_values
            assert "Петров Петр" in student_values
            assert "Сидорова Анна" in student_values

            # Кнопка генерации все еще неактивна (студент еще не выбран)
            assert str(app.generate_btn["state"]) == "disabled"
        finally:
            app.destroy()

    def test_empty_group_selection_disables_button_without_exception(self, ticket_service: TicketService):
        """
        Обязательное требование:
        Если у выбранной группы нет студентов — второй список пуст,
        кнопка остаётся неактивной, без исключения.
        """
        app = MainWindow(ticket_service)
        app.withdraw()

        try:
            app.group_combo.set("ПУСТАЯ-00")
            app._on_group_selected()

            assert list(app.student_combo["values"]) == []
            assert str(app.student_combo["state"]) == "disabled"
            assert str(app.generate_btn["state"]) == "disabled"
        finally:
            app.destroy()

    def test_student_selection_enables_generate_button(self, ticket_service: TicketService):
        """Критерий 2: Кнопка активна только при обоих выборах."""
        app = MainWindow(ticket_service)
        app.withdraw()

        try:
            # 1. Выбираем группу
            app.group_combo.set("ИВТ-21")
            app._on_group_selected()
            assert str(app.generate_btn["state"]) == "disabled"

            # 2. Выбираем студента
            app.student_combo.current(0)  # Иванов Иван
            app._on_student_selected()

            # Кнопка должна стать активной
            assert str(app.generate_btn["state"]) == "normal"
            assert app._selected_student is not None
            assert app._selected_student.full_name == "Иванов Иван"
        finally:
            app.destroy()

    def test_result_dialog_esc_key_closes_dialog(self, tk_root: tk.Tk):
        """
        Критерий 5:
        ESC закрывает окно результата и возвращает к выбору — приложение не завершается.
        """
        student = Student("ИВТ-21", "Иванов", "Иван")
        ticket = Ticket(
            number=7,
            questions=("Вопрос 1", "Вопрос 2", "Вопрос 3"),
        )

        dialog = ResultDialog(parent=tk_root, ticket=ticket, student=student)
        dialog.withdraw()

        # Проверяем, что окно существует
        assert dialog.winfo_exists()

        # Имитируем нажатие клавиши ESC
        dialog._close_dialog()

        # Окно результата должно быть уничтожено
        assert not dialog.winfo_exists()
        # Родительское окно осталось существовать
        assert tk_root.winfo_exists()
