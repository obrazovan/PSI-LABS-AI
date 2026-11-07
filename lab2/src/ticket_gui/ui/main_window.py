"""
Главное окно графического интерфейса приложения.
"""

from __future__ import annotations
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from ..models import Student, Ticket, ExamResult
from ..service import TicketService, NoTicketsAvailableError
from ..storage import StorageLockedError
from .result_dialog import ResultDialog

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """
    Главное окно приложения выбора группы и студента.

    Реализует сценарии:
    - Заполнение групп из students.xlsx при запуске.
    - Динамическое заполнение студентов при выборе группы.
    - Неактивность кнопки «Сгенерировать билет» до выбора обоих значений.
    - Обработка пустых групп без исключений.
    - Информирование об отсутствии входных файлов (students.xlsx, tickets.docx).
    - Обработка блокировки results.xlsx с возможностью повтора.
    """

    def __init__(self, service: TicketService) -> None:
        super().__init__()
        self.service = service

        self.title("Генератор экзаменационных билетов — Лабораторная работа №2")
        self.geometry("560x430")
        self.minsize(500, 390)

        # Данные интерфейса
        self._group_students: list[Student] = []
        self._selected_student: Student | None = None

        # Настройка стиля
        self._setup_styles()

        # Построение элементов
        self._build_ui()

        # Центрирование главного окна
        self._center_window()

        # Инициализация сервиса и заполнение списков
        self._initialize_data()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Настройка шрифтов и цветов ttk
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#1E3A8A")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B")
        style.configure("FieldTitle.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1E293B")
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#334155")
        style.configure("TLabelframe", padding=12)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#334155")

    def _center_window(self) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = 560
        h = 430
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self, padding="24 20 24 16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Заголовок и подзаголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 16))

        header = ttk.Label(
            header_frame,
            text="Распределение экзаменационных билетов",
            style="Header.TLabel",
            anchor="center",
        )
        header.pack(fill=tk.X)

        sub_header = ttk.Label(
            header_frame,
            text="Автоматизированная система назначения билетов студентам",
            style="SubHeader.TLabel",
            anchor="center",
        )
        sub_header.pack(fill=tk.X, pady=(2, 0))

        # 2. Карточка формы выбора
        form_frame = ttk.LabelFrame(main_frame, text="Параметры выбора", padding="16 14")
        form_frame.pack(fill=tk.X, expand=False, pady=(0, 16))

        # 1. Выпадающий список групп
        ttk.Label(form_frame, text="🎓 1. Выберите учебную группу:", style="FieldTitle.TLabel").pack(anchor="w", pady=(0, 5))
        self.group_combo = ttk.Combobox(form_frame, state="readonly", font=("Segoe UI", 10))
        self.group_combo.pack(fill=tk.X, pady=(0, 14))
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        # 2. Выпадающий список студентов
        ttk.Label(form_frame, text="👤 2. Выберите студента:", style="FieldTitle.TLabel").pack(anchor="w", pady=(0, 5))
        self.student_combo = ttk.Combobox(form_frame, state="disabled", font=("Segoe UI", 10))
        self.student_combo.pack(fill=tk.X, pady=(0, 6))
        self.student_combo.bind("<<ComboboxSelected>>", self._on_student_selected)

        # 3. Кнопка «Сгенерировать билет» (по умолчанию неактивна)
        self.generate_btn = ttk.Button(
            main_frame,
            text="Сгенерировать билет",
            style="Accent.TButton",
            state="disabled",
            command=self._on_generate_clicked,
        )
        self.generate_btn.pack(fill=tk.X, pady=(4, 16), ipady=2)

        # 4. Нижняя статусная панель
        status_bar = ttk.Frame(main_frame, relief=tk.FLAT)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_lbl = ttk.Label(
            status_bar,
            text="Готово к работе",
            style="Status.TLabel",
            anchor="w",
        )
        self.status_lbl.pack(fill=tk.X, side=tk.LEFT)

    def _initialize_data(self) -> None:
        """Инициализация сервиса и заполнение начальных списков с валидацией файлов."""
        # Настраиваем обработчик блокировки файла для хранилища
        self.service.storage.lock_handler = self._prompt_file_lock_retry

        try:
            self.service.initialize()
        except Exception as e:
            logger.error("Ошибка при инициализации сервиса: %s", e)

        # Проверка наличия исходных файлов (students.xlsx, tickets.docx)
        missing_sources: list[str] = []
        if not self.service.student_reader.is_available():
            missing_sources.append(f"Список студентов ({self.service.student_reader.file_path.name})")
        if not self.service.ticket_parser.is_available():
            missing_sources.append(f"Список билетов ({self.service.ticket_parser.file_path.name})")

        if missing_sources:
            err_msg = (
                "Не найдены следующие входные файлы данных:\n• "
                + "\n• ".join(missing_sources)
                + "\n\nПожалуйста, поместите необходимые файлы в каталог приложения."
            )
            self.status_lbl.config(
                text="⚠️ Входные файлы не найдены!",
                foreground="#DC2626",
            )
            messagebox.showwarning("Входные файлы не найдены", err_msg, parent=self)
            return

        # Заполняем группы
        groups = self.service.get_groups()
        if not groups:
            self.status_lbl.config(
                text="⚠️ В файле students.xlsx нет листов с группами.",
                foreground="#D97706",
            )
            return

        self.group_combo["values"] = groups
        self.status_lbl.config(
            text=f"● Загружено групп: {len(groups)}, валидных билетов: {len(self.service.tickets)}",
            foreground="#16A34A",
        )

    def _on_group_selected(self, event: tk.Event | None = None) -> None:
        """Обработка выбора группы."""
        selected_group = self.group_combo.get().strip()
        if not selected_group:
            self._reset_student_selection()
            return

        # Загружаем студентов для выбранной группы
        self._group_students = self.service.get_students(selected_group)
        self._selected_student = None

        if not self._group_students:
            # Требование ТЗ: если у выбранной группы нет студентов —
            # второй список пуст, кнопка остаётся неактивной, без исключения.
            self.student_combo.set("")
            self.student_combo["values"] = []
            self.student_combo.config(state="disabled")
            self.generate_btn.config(state="disabled")
            self.status_lbl.config(
                text=f"⚠️ В группе '{selected_group}' нет студентов.",
                foreground="#D97706",
            )
            return

        # Заполняем второй выпадающий список в формате «Фамилия Имя»
        student_names = [st.full_name for st in self._group_students]
        self.student_combo.config(state="readonly")
        self.student_combo["values"] = student_names
        self.student_combo.set("")

        # Кнопка пока неактивна, пока не выбран конкретный студент
        self.generate_btn.config(state="disabled")
        self.status_lbl.config(
            text=f"Группа '{selected_group}': {len(student_names)} студентов. Выберите студента.",
            foreground="#475569",
        )

    def _on_student_selected(self, event: tk.Event | None = None) -> None:
        """Обработка выбора студента."""
        selected_index = self.student_combo.current()
        if selected_index >= 0 and selected_index < len(self._group_students):
            self._selected_student = self._group_students[selected_index]
            # Кнопка становится активной только при наличии обоих выборов
            self.generate_btn.config(state="normal")
            self.status_lbl.config(
                text=f"● Выбран: {self._selected_student.full_name}. Нажмите 'Сгенерировать билет'.",
                foreground="#1E3A8A",
            )
        else:
            self._selected_student = None
            self.generate_btn.config(state="disabled")

    def _reset_student_selection(self) -> None:
        self._group_students = []
        self._selected_student = None
        self.student_combo.set("")
        self.student_combo["values"] = []
        self.student_combo.config(state="disabled")
        self.generate_btn.config(state="disabled")

    def _on_generate_clicked(self) -> None:
        """Обработка клика по кнопке генерации билета."""
        if not self._selected_student:
            return

        try:
            ticket, result = self.service.assign_ticket(self._selected_student)
        except NoTicketsAvailableError as e:
            messagebox.showerror("Ошибка билетов", str(e), parent=self)
            return
        except StorageLockedError as e:
            messagebox.showerror("Ошибка сохранения", str(e), parent=self)
            return
        except Exception as e:
            logger.exception("Ошибка при генерации билета: %s", e)
            messagebox.showerror("Непредвиденная ошибка", f"Ошибка: {e}", parent=self)
            return

        # Открываем окно результата с билетом и 3 вопросами
        ResultDialog(
            parent=self,
            ticket=ticket,
            student=self._selected_student,
            is_repeat=result.is_repeat,
        )

        # Обновляем статус
        repeat_badge = " (ПОВТОРНО)" if result.is_repeat else ""
        self.status_lbl.config(
            text=f"✓ Билет №{ticket.number} назначен для {self._selected_student.full_name}{repeat_badge}",
            foreground="#16A34A",
        )

    def _prompt_file_lock_retry(self, file_path: Path, exc: Exception) -> bool:
        """
        Диалог при блокировке файла Excel.
        Предлагает пользователю закрыть файл в Excel и повторить попытку.
        """
        msg = (
            f"Файл журнала '{file_path.name}' открыт в Microsoft Excel или заблокирован другой программой.\n\n"
            f"Пожалуйста, закройте файл в Excel и нажмите 'Повторить' для сохранения записи,\n"
            f"или 'Отмена' для отмены сохранения."
        )
        return messagebox.askretrycancel(
            title="Файл заблокирован",
            message=msg,
            parent=self,
        )
