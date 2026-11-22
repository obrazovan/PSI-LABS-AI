"""
Модуль работы с хранилищем Excel (journal.xlsx).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, Sequence

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.worksheet import Worksheet

from .models import StudentRecord
from .ports import LockRetryHandler, RecordRowMapper, StorageLockedError

HEADER_ROW = ["Last name", "First name", "Номер билета", "Дата и время"]


class FileLockedError(StorageLockedError, OSError):
    """Исключение, сигнализирующее о том, что файл заблокирован другим процессом."""


class StudentRecordRowMapper:
    """Преобразует запись студента в табличную строку и задает заголовки колонок."""

    def __init__(self, headers: Sequence[str] = HEADER_ROW) -> None:
        self._headers = tuple(headers)

    @property
    def headers(self) -> tuple[str, ...]:
        """Возвращает заголовки колонок таблицы."""
        return self._headers

    def to_row(self, record: StudentRecord) -> list[Any]:
        """Возвращает строку таблицы для записи в журнал."""
        return [record.last_name, record.first_name, record.ticket_number, record.timestamp]


class ExcelSheetStyler(Protocol):
    """Интерфейс оформления листа Excel."""

    def style_header(self, ws: Worksheet, column_count: int) -> None:
        """Оформляет шапку таблицы и ширину столбцов."""
        ...

    def style_data_row(self, ws: Worksheet, row_index: int) -> None:
        """Оформляет добавленную строку данных."""
        ...


class DefaultExcelSheetStyler:
    """Стандартное визуальное оформление листа Excel для журнала экзамена."""

    def __init__(self, column_widths: dict[str, int] | None = None) -> None:
        self._column_widths = column_widths or {"A": 20, "B": 20, "C": 16, "D": 22}
        self._header_font = Font(name="Calibri", size=11, bold=True, color="000000")
        self._header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        self._header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self._left_align = Alignment(horizontal="left", vertical="center")
        self._center_align = Alignment(horizontal="center", vertical="center")

    def style_header(self, ws: Worksheet, column_count: int) -> None:
        """Применяет шрифт, заливку, выравнивание к шапке и задает ширину колонок."""
        for col_idx in range(1, column_count + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = self._header_font
            cell.fill = self._header_fill
            cell.alignment = self._header_align

        for col_letter, width in self._column_widths.items():
            ws.column_dimensions[col_letter].width = width

    def style_data_row(self, ws: Worksheet, row_index: int) -> None:
        """Выравнивает ячейки новой строки данных."""
        ws.cell(row=row_index, column=1).alignment = self._left_align
        ws.cell(row=row_index, column=2).alignment = self._left_align
        ws.cell(row=row_index, column=3).alignment = self._center_align
        ws.cell(row=row_index, column=4).alignment = self._center_align


class ExcelJournalStorage:
    """
    Управление файлом журнала в формате Excel.

    Отвечает только за жизненный цикл книги Excel и сохранение на диск,
    делегируя маппинг строк, оформление и стратегию повторов внешним зависимостям.
    """

    def __init__(
        self,
        file_path: str | Path = "journal.xlsx",
        lock_retry_handler: LockRetryHandler | None = None,
        mapper: RecordRowMapper | None = None,
        styler: ExcelSheetStyler | None = None,
        sheet_name: str = "Экзамен",
    ) -> None:
        self.file_path = Path(file_path)
        self.lock_retry_handler = lock_retry_handler
        self._mapper: RecordRowMapper = mapper or StudentRecordRowMapper()
        self._styler: ExcelSheetStyler = styler or DefaultExcelSheetStyler()
        self._sheet_name = sheet_name

    def describe(self) -> str:
        """Возвращает человекочитаемое описание расположения журнала."""
        return f"Файл журнала: {self.file_path.resolve()}"

    def ensure_initialized(self) -> None:
        """Создает файл журнала с шапкой, если файл еще не существует."""
        if self.file_path.exists():
            return

        self._create_new_journal()

    def _build_initialized_workbook(self) -> openpyxl.Workbook:
        """Создает новую книгу Excel с заполненной и оформленной шапкой."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self._sheet_name
        headers = list(self._mapper.headers)
        ws.append(headers)
        self._styler.style_header(ws, len(headers))
        return wb

    def _create_new_journal(self) -> None:
        """Создает новый рабочий файл с заголовками и сохраняет на диск."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        wb = self._build_initialized_workbook()
        try:
            self._save_workbook_with_retry(wb)
        finally:
            wb.close()

    def _load_or_recreate_workbook(self) -> openpyxl.Workbook:
        """Загружает существующую книгу Excel с обработкой блокировки или повреждения."""
        while True:
            if not self.file_path.exists():
                return self._build_initialized_workbook()

            try:
                return openpyxl.load_workbook(self.file_path)
            except (PermissionError, OSError) as exc:
                if self._should_retry(exc):
                    continue
                raise FileLockedError(
                    f"Файл '{self.file_path}' заблокирован и недоступен для чтения."
                ) from exc
            except InvalidFileException:
                return self._build_initialized_workbook()

    def append_record(self, record: StudentRecord) -> None:
        """
        Дописывает запись о студенте в файл Excel и немедленно сохраняет на диск.

        Если файл отсутствует, создает его с шапкой.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        wb = self._load_or_recreate_workbook()
        try:
            ws = wb.active
            # Проверяем наличие шапки, если файл был пустой
            if ws.max_row == 0 or (ws.max_row == 1 and all(cell.value is None for cell in ws[1])):
                headers = list(self._mapper.headers)
                ws.append(headers)
                self._styler.style_header(ws, len(headers))

            ws.append(self._mapper.to_row(record))
            self._styler.style_data_row(ws, ws.max_row)
            self._save_workbook_with_retry(wb)
        finally:
            wb.close()

    def _save_workbook_with_retry(self, wb: openpyxl.Workbook) -> None:
        """Сохраняет книгу Excel, делегируя реакцию на блокировку файла."""
        while True:
            try:
                wb.save(self.file_path)
                return
            except (PermissionError, OSError) as exc:
                if not self._should_retry(exc):
                    raise FileLockedError(
                        f"Не удалось сохранить запись: файл '{self.file_path}' заблокирован."
                    ) from exc

    def _should_retry(self, exc: Exception) -> bool:
        """Запрашивает у обработчика блокировки необходимость повторной попытки."""
        if self.lock_retry_handler is None:
            return False
        return self.lock_retry_handler(self.file_path, exc)

    def read_all_rows(self) -> list[tuple[Any, ...]]:
        """Возвращает все строки из файла Excel (включая шапку)."""
        if not self.file_path.exists():
            return []
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        try:
            ws = wb.active
            return list(ws.iter_rows(values_only=True))
        finally:
            wb.close()

    def get_records_count(self) -> int:
        """Возвращает количество записей студентов (строки за вычетом шапки)."""
        rows = self.read_all_rows()
        if not rows:
            return 0
        return max(0, len(rows) - 1)


__all__ = [
    "HEADER_ROW",
    "FileLockedError",
    "StudentRecordRowMapper",
    "ExcelSheetStyler",
    "DefaultExcelSheetStyler",
    "ExcelJournalStorage",
]
