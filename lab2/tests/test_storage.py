"""
Тесты для хранилища ResultJournalStorage (results.xlsx).
"""

from pathlib import Path
from unittest.mock import patch
import pytest
import openpyxl

from ticket_gui.storage import (
    ResultJournalStorage,
    RESULTS_HEADER,
    StorageLockedError,
)
from ticket_gui.models import ExamResult


class TestResultJournalStorage:
    def test_ensure_initialized_creates_file_with_headers(self, sample_results_path: Path):
        storage = ResultJournalStorage(sample_results_path)
        assert not sample_results_path.exists()

        storage.ensure_initialized()
        assert sample_results_path.exists()

        rows = storage.read_all_rows()
        assert len(rows) == 1
        assert list(rows[0]) == RESULTS_HEADER

    def test_append_result_preserves_previous_rows(self, sample_results_path: Path):
        storage = ResultJournalStorage(sample_results_path)

        res1 = ExamResult("ИВТ-21", "Иванов", "Иван", 5, False, "2026-11-07 10:00:00")
        res2 = ExamResult("ПИ-22", "Петров", "Петр", 2, False, "2026-11-07 10:05:00")

        storage.append_result(res1)
        storage.append_result(res2)

        rows = storage.read_all_rows()
        assert len(rows) == 3  # 1 шапка + 2 записи
        assert list(rows[0]) == RESULTS_HEADER
        assert list(rows[1]) == res1.to_row()
        assert list(rows[2]) == res2.to_row()

    def test_get_first_ticket_for_student(self, sample_results_path: Path):
        storage = ResultJournalStorage(sample_results_path)

        # Первая попытка студента: билет 7
        storage.append_result(
            ExamResult("ИВТ-21", "Иванов", "Иван", 7, False, "2026-11-07 10:00:00")
        )
        # Вторая попытка того же студента: билет 7 (повтор)
        storage.append_result(
            ExamResult("ИВТ-21", "Иванов", "Иван", 7, True, "2026-11-07 10:15:00")
        )
        # Другой студент
        storage.append_result(
            ExamResult("ИВТ-21", "Петров", "Петр", 3, False, "2026-11-07 10:20:00")
        )

        # Должен возвращаться номер 7
        ticket = storage.get_first_ticket_for_student("ИВТ-21", "Иванов", "Иван")
        assert ticket == 7

        # Проверка регистронезависимости
        ticket_case = storage.get_first_ticket_for_student("ивт-21", "иванов", "иван")
        assert ticket_case == 7

        # Несуществующий студент
        not_found = storage.get_first_ticket_for_student("ИВТ-21", "Сидоров", "Сидор")
        assert not_found is None

    def test_file_locked_retry_handled(self, sample_results_path: Path):
        """Проверка требования: если файл заблокирован, предлагается повтор."""
        retry_called = 0

        def mock_retry_handler(path: Path, exc: Exception) -> bool:
            nonlocal retry_called
            retry_called += 1
            return True

        storage = ResultJournalStorage(sample_results_path, lock_handler=mock_retry_handler)
        res = ExamResult("ИВТ-21", "Иванов", "Иван", 1, False)

        original_save = openpyxl.Workbook.save
        call_count = 0

        def flaky_save(self, filename):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PermissionError(13, "Заблокировано Excel")
            return original_save(self, filename)

        with patch.object(openpyxl.Workbook, "save", flaky_save):
            storage.append_result(res)

        assert retry_called == 1
        assert len(storage.read_all_rows()) == 2

    def test_file_locked_abort_raises_storage_locked_error(self, sample_results_path: Path):
        def mock_abort_handler(path: Path, exc: Exception) -> bool:
            return False

        storage = ResultJournalStorage(sample_results_path, lock_handler=mock_abort_handler)
        res = ExamResult("ИВТ-21", "Иванов", "Иван", 1, False)

        with patch.object(openpyxl.Workbook, "save", side_effect=PermissionError(13, "Locked")):
            with pytest.raises(StorageLockedError, match="заблокирован"):
                storage.append_result(res)
