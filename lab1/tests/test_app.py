"""
Интеграционные тесты полного сценария работы приложения TicketApp.
Проверяют все сценарии из раздела 'Проверка результата' ТЗ.
"""

from pathlib import Path
from unittest.mock import patch
import pytest

from ticket_generator.app import TicketApp
from ticket_generator.storage import ExcelJournalStorage, HEADER_ROW
from ticket_generator.generator import FixedTicketGenerator
from ticket_generator.models import StudentRecord


class TestTicketAppWorkflow:
    def test_scenario_1_enter_three_students_and_exit_with_esc(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """
        Сценарий 1 из ТЗ:
        'Запустить, ввести трёх студентов, выйти по ESC — в файле три строки и шапка.'
        """
        # Ввод 3 студентов, затем ESC (None)
        inputs = [
            "Иванов", "Иван",       # Студент 1
            "Петров", "Петр",       # Студент 2
            "Сидоров", "Алексей",   # Студент 3
            None,                   # ESC на шаге ввода Last name
        ]
        mock_console = mock_console_factory(inputs)
        storage = ExcelJournalStorage(tmp_excel_path)
        generator = FixedTicketGenerator([7, 12, 3])

        app = TicketApp(storage=storage, generator=generator, console=mock_console)
        exit_code = app.run()

        assert exit_code == 0
        assert mock_console.startup_hint_shown is True
        assert "Для выхода нажмите ESC." in mock_console.output_messages
        assert "Билет № 7." in mock_console.output_messages
        assert "Билет № 12." in mock_console.output_messages
        assert "Билет № 3." in mock_console.output_messages
        assert "Работа программы завершена." in mock_console.output_messages

        # Проверка содержимого файла Excel: ровно 3 строки данных + 1 строка шапки
        rows = storage.read_all_rows()
        assert len(rows) == 4
        assert list(rows[0]) == HEADER_ROW
        assert rows[1][0] == "Иванов" and rows[1][1] == "Иван" and rows[1][2] == 7
        assert rows[2][0] == "Петров" and rows[2][1] == "Петр" and rows[2][2] == 12
        assert rows[3][0] == "Сидоров" and rows[3][1] == "Алексей" and rows[3][2] == 3
        assert storage.get_records_count() == 3

    def test_scenario_2_run_again_enter_two_students_preserves_first_three(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """
        Сценарий 2 из ТЗ:
        'Запустить снова, ввести двух студентов — в файле пять строк, первые три не изменились.'
        """
        # Первый запуск (3 студента)
        inputs1 = ["Иванов", "Иван", "Петров", "Петр", "Сидоров", "Алексей", None]
        storage1 = ExcelJournalStorage(tmp_excel_path)
        app1 = TicketApp(
            storage=storage1,
            generator=FixedTicketGenerator([1, 2, 3]),
            console=mock_console_factory(inputs1),
        )
        app1.run()
        assert storage1.get_records_count() == 3

        # Второй запуск на том же файле (еще 2 студента)
        inputs2 = ["Кузнецов", "Дмитрий", "Морозова", "Елена", None]
        storage2 = ExcelJournalStorage(tmp_excel_path)
        app2 = TicketApp(
            storage=storage2,
            generator=FixedTicketGenerator([15, 20]),
            console=mock_console_factory(inputs2),
        )
        app2.run()

        # Проверяем: в файле теперь 5 строк + шапка, первые 3 не изменились
        rows = storage2.read_all_rows()
        assert len(rows) == 6
        assert list(rows[0]) == HEADER_ROW
        # Первые 3 строки
        assert rows[1][0] == "Иванов" and rows[1][2] == 1
        assert rows[2][0] == "Петров" and rows[2][2] == 2
        assert rows[3][0] == "Сидоров" and rows[3][2] == 3
        # Новые 2 строки
        assert rows[4][0] == "Кузнецов" and rows[4][1] == "Дмитрий" and rows[4][2] == 15
        assert rows[5][0] == "Морозова" and rows[5][1] == "Елена" and rows[5][2] == 20
        assert storage2.get_records_count() == 5

    def test_scenario_3_immediate_persistence_each_student(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """
        Сценарий 3 из ТЗ:
        'Закрыть приложение через диспетчер задач после ввода студента — запись в файле сохранилась.'
        Проверяем, что файл обновляется сразу же после добавления каждого студента.
        """
        storage = ExcelJournalStorage(tmp_excel_path)
        generator = FixedTicketGenerator([10])

        # Добавляем 1 студента
        record1 = StudentRecord("Васильев", "Василий", 10)
        storage.append_record(record1)

        # Проверяем напрямую с диска без участия процесса app
        rows_disk = storage.read_all_rows()
        assert len(rows_disk) == 2
        assert rows_disk[1][0] == "Васильев"

    def test_scenario_4_file_locked_in_excel_handled_without_crashing(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """
        Сценарий 4 из ТЗ:
        'Открыть journal.xlsx в Excel и попытаться ввести студента —
        приложение сообщает об ошибке и не падает.'
        """
        retry_called = False

        def mock_lock_handler(path: Path, exc: Exception) -> bool:
            nonlocal retry_called
            retry_called = True
            return True  # Пользователь закрыл файл

        storage = ExcelJournalStorage(tmp_excel_path, lock_retry_handler=mock_lock_handler)
        console = mock_console_factory(["Иванов", "Иван", None])
        app = TicketApp(
            storage=storage,
            generator=FixedTicketGenerator([7]),
            console=console,
        )

        import openpyxl
        original_save = openpyxl.Workbook.save
        save_counter = 0

        def locked_once_save(self, filename):
            nonlocal save_counter
            save_counter += 1
            if save_counter == 1:
                # Имитируем блокировку файла Excel при первой попытке сохранения
                raise PermissionError(13, "Файл заблокирован Excel")
            return original_save(self, filename)

        with patch.object(openpyxl.Workbook, "save", locked_once_save):
            exit_code = app.run()

        assert exit_code == 0
        assert retry_called is True
        assert storage.get_records_count() == 1

    def test_scenario_5_empty_input_reprompt(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """
        Сценарий 5 из ТЗ:
        'Нажать Enter на пустом поле — приложение повторяет запрос.'
        """
        # Пустые строки, пробелы, затем валидные данные
        inputs = [
            "", "   ", "Смирнов",  # Last name: 2 пустых, потом Смирнов
            "", "Олег",             # First name: 1 пустой, потом Олег
            None,
        ]
        console = mock_console_factory(inputs)
        storage = ExcelJournalStorage(tmp_excel_path)
        app = TicketApp(
            storage=storage,
            generator=FixedTicketGenerator([9]),
            console=console,
        )
        app.run()

        assert storage.get_records_count() == 1
        rows = storage.read_all_rows()
        assert rows[1][0] == "Смирнов"
        assert rows[1][1] == "Олег"

    def test_esc_on_first_name_cancels_current_student(
        self, tmp_excel_path: Path, mock_console_factory
    ):
        """Если ESC нажат на этапе ввода имени, незаконченная запись не сохраняется."""
        inputs = [
            "Иванов", None  # Ввели фамилию, а на имени нажали ESC
        ]
        console = mock_console_factory(inputs)
        storage = ExcelJournalStorage(tmp_excel_path)
        app = TicketApp(
            storage=storage,
            generator=FixedTicketGenerator([1]),
            console=console,
        )
        app.run()

        # Запись не должна быть сохранена
        assert storage.get_records_count() == 0
