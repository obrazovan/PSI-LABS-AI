"""
Хранилище результатов экзаменационных билетов в формате Excel (results.xlsx).
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Callable, TypeVar
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

from .exceptions import StorageLockedError
from .models import ExamResult
from .ports import JournalStylerProtocol, LockHandlerProtocol

logger = logging.getLogger(__name__)

RESULTS_HEADER = ["Группа", "Фамилия", "Имя", "Номер билета", "Дата и время", "Повтор (да/нет)"]

_T = TypeVar("_T")


class DelegatingLockHandler:
    """
    Позднесвязываемый обработчик блокировки файла.

    Позволяет соединить хранилище и UI в точке сборки приложения
    без прямой зависимости хранилища от UI и UI от хранилища.
    """

    def __init__(self, handler: LockHandlerProtocol | None = None) -> None:
        self._handler: LockHandlerProtocol | None = handler

    def attach(self, handler: LockHandlerProtocol) -> None:
        """Назначает делегата обработки блокировок."""
        self._handler = handler

    def __call__(self, file_path: Path, exc: Exception) -> bool:
        if self._handler is not None:
            return self._handler(file_path, exc)
        return False


class ExcelJournalStyler:
    """
    Отвечает исключительно за визуальное оформление книги Excel журнала (SRP / OCP).
    """

    COLUMN_WIDTHS = {"A": 16, "B": 20, "C": 20, "D": 16, "E": 22, "F": 18}
    ROW_HORIZONTAL_ALIGNMENTS = ("center", "left", "left", "center", "center", "center")

    def style_header(self, worksheet: Any) -> None:
        """Применяет стили заголовка и ширину столбцов."""
        header_font = Font(name="Calibri", size=11, bold=True, color="000000")
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")

        for col_idx in range(1, len(RESULTS_HEADER) + 1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for col_letter, width in self.COLUMN_WIDTHS.items():
            worksheet.column_dimensions[col_letter].width = width

    def style_row(self, worksheet: Any, row_index: int) -> None:
        """Применяет выравнивание к добавленной строке результатов."""
        for col_idx, horizontal in enumerate(self.ROW_HORIZONTAL_ALIGNMENTS, start=1):
            worksheet.cell(row=row_index, column=col_idx).alignment = Alignment(
                horizontal=horizontal,
                vertical="center",
            )


class ResultJournalStorage:
    """
    Класс управления файлом журнала results.xlsx.

    Отвечает за:
    - Инициализацию файла с заголовками.
    - Поиск первого назначенного билета студента (для идемпотентности).
    - Дописывание новых записей в конец без изменения существующих строк.
    - Оркестрацию повтора при блокировке файла через LockHandlerProtocol.
    """

    def __init__(
        self,
        file_path: str | Path = "results.xlsx",
        lock_handler: LockHandlerProtocol | None = None,
        styler: JournalStylerProtocol | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.lock_handler = lock_handler
        self._styler: JournalStylerProtocol = styler or ExcelJournalStyler()

    def ensure_initialized(self) -> None:
        """Создает файл журнала с шапкой, если файл еще не существует."""
        if self.file_path.exists():
            return
        self._create_new_journal()

    def _create_new_journal(self) -> None:
        """Создает новый Excel-файл с шапкой."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        try:
            ws = wb.active
            ws.title = "Журнал"
            ws.append(RESULTS_HEADER)
            self._styler.style_header(ws)
            self._run_with_lock_retry(
                lambda: wb.save(self.file_path),
                f"Не удалось сохранить запись: файл '{self.file_path}' открыт или заблокирован.",
            )
        finally:
            wb.close()

    def get_first_ticket_for_student(self, group: str, last_name: str, first_name: str) -> int | None:
        """
        Ищет номер билета из самой первой записи по данному студенту в results.xlsx.
        Возвращает None, если студент еще не сдавал билет.
        """
        if not self.file_path.exists():
            return None

        target_group = group.strip().lower()
        target_last = last_name.strip().lower()
        target_first = first_name.strip().lower()

        def read_first_ticket() -> int | None:
            wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
            try:
                ws = wb.active
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not row or len(row) < 4:
                        continue
                    row_group = str(row[0] or "").strip().lower()
                    row_last = str(row[1] or "").strip().lower()
                    row_first = str(row[2] or "").strip().lower()

                    if (
                        row_group == target_group
                        and row_last == target_last
                        and row_first == target_first
                    ):
                        try:
                            return int(row[3])
                        except (ValueError, TypeError):
                            continue
                return None
            finally:
                wb.close()

        return self._run_with_lock_retry(
            read_first_ticket,
            f"Не удалось прочитать журнал '{self.file_path}': файл открыт или заблокирован.",
        )

    def append_result(self, result: ExamResult) -> None:
        """Дописывает результат в конец results.xlsx и немедленно сохраняет на диск."""
        if not self.file_path.exists():
            self._create_new_journal()

        wb = self._run_with_lock_retry(
            lambda: openpyxl.load_workbook(self.file_path),
            f"Файл '{self.file_path}' заблокирован.",
        )
        try:
            ws = wb.active

            if ws.max_row == 0 or (ws.max_row == 1 and all(cell.value is None for cell in ws[1])):
                ws.append(RESULTS_HEADER)
                self._styler.style_header(ws)

            ws.append(result.to_row())
            self._styler.style_row(ws, ws.max_row)

            self._run_with_lock_retry(
                lambda: wb.save(self.file_path),
                f"Не удалось сохранить запись: файл '{self.file_path}' открыт или заблокирован.",
            )
        finally:
            wb.close()

    def _run_with_lock_retry(self, operation: Callable[[], _T], error_message: str) -> _T:
        """Выполняет операцию с Excel-файлом и запрашивает повтор при блокировке."""
        while True:
            try:
                return operation()
            except (PermissionError, OSError) as exc:
                if not self._handle_lock(exc):
                    raise StorageLockedError(error_message) from exc

    def _handle_lock(self, exc: Exception) -> bool:
        if self.lock_handler is not None:
            return self.lock_handler(self.file_path, exc)
        return False

    def read_all_rows(self) -> list[tuple[Any, ...]]:
        """Возвращает все строки из results.xlsx."""
        if not self.file_path.exists():
            return []
        wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
        try:
            ws = wb.active
            return list(ws.iter_rows(values_only=True))
        finally:
            wb.close()
