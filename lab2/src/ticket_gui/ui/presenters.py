"""
Tkinter-реализации UI-презентеров и обработчика блокировок (адаптеры DIP).
"""

from __future__ import annotations
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from ..models import Student, Ticket
from .result_dialog import ResultDialog


class TkResultPresenter:
    """Отображает результат назначения билета в модальном окне Tkinter."""

    def __init__(self, parent: tk.Misc) -> None:
        self._parent = parent

    def show_result(self, ticket: Ticket, student: Student, is_repeat: bool) -> None:
        ResultDialog(
            parent=self._parent,
            ticket=ticket,
            student=student,
            is_repeat=is_repeat,
        )


class TkAlertNotifier:
    """Показывает предупреждения и ошибки через стандартные диалоги Tkinter."""

    def __init__(self, parent: tk.Misc) -> None:
        self._parent = parent

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message, parent=self._parent)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self._parent)


class TkFileLockHandler:
    """
    Обработчик блокировки файла журнала через диалог Повторить / Отмена.
    """

    def __init__(self, parent: tk.Misc) -> None:
        self._parent = parent

    def __call__(self, file_path: Path, exc: Exception) -> bool:
        msg = (
            f"Файл журнала '{file_path.name}' открыт в Microsoft Excel или заблокирован другой программой.\n\n"
            f"Пожалуйста, закройте файл в Excel и нажмите 'Повторить' для сохранения записи,\n"
            f"или 'Отмена' для отмены сохранения."
        )
        return messagebox.askretrycancel(
            title="Файл заблокирован",
            message=msg,
            parent=self._parent,
        )

