"""
Модуль работы с хранилищем Excel (journal.xlsx).
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Callable, Sequence, Any
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils.exceptions import InvalidFileException

from .models import StudentRecord


HEADER_ROW = ["Last name", "First name", "Номер билета", "Дата и время"]


class FileLockedError(OSError):
    """Исключение, сигнализирующее о том, что файл заблокирован другим процессом."""
    pass


def default_lock_handler(file_path: Path, exception: Exception) -> bool:
    """
    Обработчик блокировки файла по умолчанию для консольного режима.
    Информирует пользователя и ожидает закрытия файла.
    Возвращает True для повтора, False для отмены.
    """
    msg = (
        f"\n[ВНИМАНИЕ] Файл '{file_path.name}' открыт в Excel или заблокирован другой программой.\n"
        f"Пожалуйста, закройте файл в Excel и нажмите Enter для повторной попытки сохранения.\n"
        f"(Или введите 'exit'/'q' и нажмите Enter для отмены): "
    )
    sys.stdout.write(msg)
    sys.stdout.flush()

    try:
        response = sys.stdin.readline().strip().lower()
        if response in ("exit", "q", "quit"):
            return False
        return True
    except (KeyboardInterrupt, EOFError):
        return False


class ExcelJournalStorage:
    """
    Управление файлом журнала в формате Excel.

    Обеспечивает:
    - Создание файла с корректной шапкой при первом запуске.
    - Дописывание записей в конец без изменения существующих строк.
    - Мгновенное сохранение каждой записи на диск.
    - Обработку блокировки файла (если открыт в Excel).
    """

    def __init__(
        self,
        file_path: str | Path = "journal.xlsx",
        lock_retry_handler: Callable[[Path, Exception], bool] | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.lock_retry_handler = lock_retry_handler or default_lock_handler

    def ensure_initialized(self) -> None:
        """Создает файл журнала с шапкой, если файл еще не существует."""
        if self.file_path.exists():
            return

        self._create_new_journal()

    def _create_new_journal(self) -> None:
        """Создает новый рабочий файл с заголовками и форматированием."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Экзамен"

        # Добавление шапки
        ws.append(HEADER_ROW)

        # Стилизация шапки
        header_font = Font(name="Calibri", size=11, bold=True, color="000000")
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for col_idx in range(1, len(HEADER_ROW) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        # Настройка ширины колонок для красивого отображения
        col_widths = {"A": 20, "B": 20, "C": 16, "D": 22}
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width

        self._save_workbook_with_retry(wb)
        wb.close()

    def append_record(self, record: StudentRecord) -> None:
        """
        Дописывает запись о студенте в файл Excel и немедленно сохраняет на диск.

        Если файл отсутствует, создает его с шапкой.
        Если файл заблокирован, запрашивает у пользователя закрытие файла и повторяет попытку.
        """
        if not self.file_path.exists():
            self._create_new_journal()

        try:
            wb = openpyxl.load_workbook(self.file_path)
        except (PermissionError, OSError) as exc:
            # Если даже прочитать не удается из-за эксклюзивной блокировки
            if self._handle_lock(exc):
                return self.append_record(record)
            raise FileLockedError(f"Файл '{self.file_path}' заблокирован и недоступен для чтения.") from exc
        except InvalidFileException:
            # Если файл поврежден, перезапускаем с шапкой
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Экзамен"
            ws.append(HEADER_ROW)

        ws = wb.active

        # Проверяем наличие шапки, если файл был пустой
        if ws.max_row == 0 or (ws.max_row == 1 and all(cell.value is None for cell in ws[1])):
            ws.append(HEADER_ROW)

        # Дописываем строку данных
        row_values = record.to_row()
        ws.append(row_values)

        # Выравнивание ячеек в новой строке
        current_row = ws.max_row
        ws.cell(row=current_row, column=1).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=2).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=3).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=4).alignment = Alignment(horizontal="center", vertical="center")

        # Сохранение с обработкой блокировки
        self._save_workbook_with_retry(wb)
        wb.close()

    def _save_workbook_with_retry(self, wb: openpyxl.Workbook) -> None:
        """Сохраняет книгу Excel, обрабатывая блокировку файла."""
        while True:
            try:
                wb.save(self.file_path)
                return
            except (PermissionError, OSError) as exc:
                should_retry = self._handle_lock(exc)
                if not should_retry:
                    raise FileLockedError(
                        f"Не удалось сохранить запись: файл '{self.file_path}' заблокирован."
                    ) from exc

    def _handle_lock(self, exc: Exception) -> bool:
        """Вызывает обработчик блокировки файла."""
        return self.lock_retry_handler(self.file_path, exc)

    def read_all_rows(self) -> list[tuple[Any, ...]]:
        """Возвращает все строки из файла Excel (включая шапку)."""
        if not self.file_path.exists():
            return []
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        return rows

    def get_records_count(self) -> int:
        """Возвращает количество записей студентов (строки за вычетом шапки)."""
        rows = self.read_all_rows()
        if not rows:
            return 0
        # Исключаем шапку
        return max(0, len(rows) - 1)
