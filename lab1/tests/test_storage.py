"""
Unit-тесты для модуля storage.py (ExcelJournalStorage).
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import openpyxl

from ticket_generator.storage import (
    ExcelJournalStorage,
    HEADER_ROW,
    FileLockedError,
)
from ticket_generator.models import StudentRecord


class TestExcelJournalStorage:
    def test_initialization_creates_file_with_headers(self, tmp_excel_path: Path):
        storage = ExcelJournalStorage(tmp_excel_path)
        assert not tmp_excel_path.exists()

        storage.ensure_initialized()
        assert tmp_excel_path.exists()

        rows = storage.read_all_rows()
        assert len(rows) == 1
        assert list(rows[0]) == HEADER_ROW
        assert storage.get_records_count() == 0

    def test_append_record_creates_file_if_not_exists(self, tmp_excel_path: Path, sample_record: StudentRecord):
        storage = ExcelJournalStorage(tmp_excel_path)
        assert not tmp_excel_path.exists()

        storage.append_record(sample_record)
        assert tmp_excel_path.exists()

        rows = storage.read_all_rows()
        assert len(rows) == 2
        assert list(rows[0]) == HEADER_ROW
        assert list(rows[1]) == sample_record.to_row()
        assert storage.get_records_count() == 1

    def test_append_multiple_records_preserves_order_and_data(self, tmp_excel_path: Path):
        storage = ExcelJournalStorage(tmp_excel_path)

        rec1 = StudentRecord("Иванов", "Иван", 5, "2026-11-04 10:00:00")
        rec2 = StudentRecord("Петров", "Петр", 12, "2026-11-04 10:05:00")
        rec3 = StudentRecord("Сидорова", "Анна", 7, "2026-11-04 10:10:00")

        storage.append_record(rec1)
        storage.append_record(rec2)
        storage.append_record(rec3)

        rows = storage.read_all_rows()
        assert len(rows) == 4
        assert list(rows[0]) == HEADER_ROW
        assert list(rows[1]) == rec1.to_row()
        assert list(rows[2]) == rec2.to_row()
        assert list(rows[3]) == rec3.to_row()
        assert storage.get_records_count() == 3

    def test_persistence_between_sessions(self, tmp_excel_path: Path):
        """Проверка требования: последующий запуск продолжает дописывать строки."""
        # Сессия 1: вводим 3 записи
        storage_session1 = ExcelJournalStorage(tmp_excel_path)
        for i in range(1, 4):
            storage_session1.append_record(
                StudentRecord(f"Фамилия_{i}", f"Имя_{i}", i, f"2026-11-04 10:0{i}:00")
            )
        assert storage_session1.get_records_count() == 3

        # Сессия 2: создаем новый экземпляр (как при перезапуске приложения)
        storage_session2 = ExcelJournalStorage(tmp_excel_path)
        for i in range(4, 6):
            storage_session2.append_record(
                StudentRecord(f"Фамилия_{i}", f"Имя_{i}", i, f"2026-11-04 10:0{i}:00")
            )

        # Проверяем, что первые 3 записи не изменились, а всего стало 5 записей
        rows = storage_session2.read_all_rows()
        assert len(rows) == 6  # 1 шапка + 5 записей
        assert rows[1][0] == "Фамилия_1"
        assert rows[2][0] == "Фамилия_2"
        assert rows[3][0] == "Фамилия_3"
        assert rows[4][0] == "Фамилия_4"
        assert rows[5][0] == "Фамилия_5"
        assert storage_session2.get_records_count() == 5

    def test_file_lock_handled_and_retried_successfully(self, tmp_excel_path: Path, sample_record: StudentRecord):
        """
        Проверка требования: если файл открыт в Excel (PermissionError),
        приложение вызывает обработчик и при закрытии файла успешно сохраняет запись.
        """
        attempts = 0

        def mock_retry_handler(path: Path, exc: Exception) -> bool:
            nonlocal attempts
            attempts += 1
            return True  # Пользователь якобы закрыл файл в Excel

        storage = ExcelJournalStorage(tmp_excel_path, lock_retry_handler=mock_retry_handler)

        original_save = openpyxl.Workbook.save
        call_count = 0

        def flaky_save(self, filename):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Первый вызов имитирует открытый в Excel файл
                raise PermissionError(13, "Permission denied (locked by Excel)")
            return original_save(self, filename)

        with patch.object(openpyxl.Workbook, "save", flaky_save):
            storage.append_record(sample_record)

        assert attempts == 1
        assert storage.get_records_count() == 1

    def test_file_lock_abort_raises_file_locked_error(self, tmp_excel_path: Path, sample_record: StudentRecord):
        """Если пользователь отказался закрывать файл, выбрасывается FileLockedError."""
        def mock_abort_handler(path: Path, exc: Exception) -> bool:
            return False  # Пользователь выбрал отмену

        storage = ExcelJournalStorage(tmp_excel_path, lock_retry_handler=mock_abort_handler)

        with patch.object(openpyxl.Workbook, "save", side_effect=PermissionError(13, "File locked")):
            with pytest.raises(FileLockedError, match="заблокирован"):
                storage.append_record(sample_record)
