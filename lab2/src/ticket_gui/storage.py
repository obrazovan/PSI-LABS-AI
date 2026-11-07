"""
Хранилище результатов экзаменационных билетов в формате Excel (results.xlsx).
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable, List, Optional, Any
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

from .models import ExamResult

logger = logging.getLogger(__name__)

RESULTS_HEADER = ["Группа", "Фамилия", "Имя", "Номер билета", "Дата и время", "Повтор (да/нет)"]


class StorageLockedError(OSError):
    """Исключение при невозможности записи из-за блокировки файла (например, открыт в Excel)."""
    pass


class ResultJournalStorage:
    """
    Класс для управления файлом журнала results.xlsx.

    Обеспечивает:
    - Создание файла с заголовками при первом обращении.
    - Дописывание новых записей в конец без перезаписи старых.
    - Поиск первого назначенного билета для студента (для правила идемпотентности).
    - Обработку блокировки файла (PermissionError) с механизмом повтора.
    """

    def __init__(
        self,
        file_path: str | Path = "results.xlsx",
        lock_handler: Callable[[Path, Exception], bool] | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.lock_handler = lock_handler

    def ensure_initialized(self) -> None:
        """Создает файл журнала с шапкой, если файл еще не существует."""
        if self.file_path.exists():
            return

        self._create_new_journal()

    def _create_new_journal(self) -> None:
        """Создает новый Excel-файл с шапкой."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Журнал"

        ws.append(RESULTS_HEADER)

        # Стилизация шапки
        header_font = Font(name="Calibri", size=11, bold=True, color="000000")
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")

        for col_idx in range(1, len(RESULTS_HEADER) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        # Ширина столбцов
        col_widths = {"A": 16, "B": 20, "C": 20, "D": 16, "E": 22, "F": 18}
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width

        self._save_with_retry(wb)
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

        try:
            wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
            ws = wb.active

            # Идем построчно сверху вниз (хронологический порядок)
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 4:
                    continue
                row_group = str(row[0] or "").strip().lower()
                row_last = str(row[1] or "").strip().lower()
                row_first = str(row[2] or "").strip().lower()

                if row_group == target_group and row_last == target_last and row_first == target_first:
                    try:
                        ticket_num = int(row[3])
                        wb.close()
                        return ticket_num
                    except (ValueError, TypeError):
                        continue

            wb.close()
        except (PermissionError, OSError) as exc:
            logger.warning("Не удалось прочитать results.xlsx для проверки повтора: %s", exc)

        return None

    def append_result(self, result: ExamResult) -> None:
        """
        Дописывает результат в конец results.xlsx и немедленно сохраняет на диск.
        """
        if not self.file_path.exists():
            self._create_new_journal()

        try:
            wb = openpyxl.load_workbook(self.file_path)
        except (PermissionError, OSError) as exc:
            if self._handle_lock(exc):
                return self.append_result(result)
            raise StorageLockedError(f"Файл '{self.file_path}' заблокирован.") from exc

        ws = wb.active

        # Если файл был пустой, добавляем шапку
        if ws.max_row == 0 or (ws.max_row == 1 and all(cell.value is None for cell in ws[1])):
            ws.append(RESULTS_HEADER)

        ws.append(result.to_row())

        current_row = ws.max_row
        ws.cell(row=current_row, column=1).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=2).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=3).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=4).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=5).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=6).alignment = Alignment(horizontal="center", vertical="center")

        self._save_with_retry(wb)
        wb.close()

    def _save_with_retry(self, wb: openpyxl.Workbook) -> None:
        """Сохраняет книгу Excel с обработкой блокировки."""
        while True:
            try:
                wb.save(self.file_path)
                return
            except (PermissionError, OSError) as exc:
                should_retry = self._handle_lock(exc)
                if not should_retry:
                    raise StorageLockedError(
                        f"Не удалось сохранить запись: файл '{self.file_path}' открыт или заблокирован."
                    ) from exc

    def _handle_lock(self, exc: Exception) -> bool:
        if self.lock_handler:
            return self.lock_handler(self.file_path, exc)
        return False

    def read_all_rows(self) -> list[tuple[Any, ...]]:
        """Возвращает все строки из results.xlsx."""
        if not self.file_path.exists():
            return []
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        return rows
