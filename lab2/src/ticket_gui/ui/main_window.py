"""
Главное окно графического интерфейса приложения.
"""

from __future__ import annotations
import logging
import tkinter as tk
from tkinter import ttk

from ..exceptions import NoTicketsAvailableError, StorageLockedError
from ..models import Student
from ..ports import AlertNotifierProtocol, ResultPresenterProtocol, TicketServiceProtocol
from .presenters import TkAlertNotifier, TkResultPresenter

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """
    Главное окно приложения выбора группы и студента.

    Зависит исключительно от абстракций (TicketServiceProtocol,
    ResultPresenterProtocol, AlertNotifierProtocol) согласно DIP и ISP.
    """

    def __init__(
        self,
        service: TicketServiceProtocol,
        result_presenter: ResultPresenterProtocol | None = None,
        alert_notifier: AlertNotifierProtocol | None = None,
        auto_initialize: bool = True,
    ) -> None:
        for _attempt in range(5):
            try:
                super().__init__()
                break
            except tk.TclError:
                if _attempt < 4:
                    import time
                    time.sleep(0.08 * (_attempt + 1))
                    continue
                raise

        self.service: TicketServiceProtocol = service
        self._result_presenter: ResultPresenterProtocol = (
            result_presenter if result_presenter is not None else TkResultPresenter(self)
        )
        self._alert_notifier: AlertNotifierProtocol = (
            alert_notifier if alert_notifier is not None else TkAlertNotifier(self)
        )

        self.title("Генератор экзаменационных билетов — Лабораторная работа №2")
        self.geometry("560x430")
        self.minsize(500, 390)

        self._group_students: list[Student] = []
        self._selected_student: Student | None = None

        self._setup_styles()
        self._build_ui()
        self._center_window()

        if auto_initialize:
            self.initialize()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

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

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 16))

        ttk.Label(
            header_frame,
            text="Распределение экзаменационных билетов",
            style="Header.TLabel",
            anchor="center",
        ).pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text="Автоматизированная система назначения билетов студентам",
            style="SubHeader.TLabel",
            anchor="center",
        ).pack(fill=tk.X, pady=(2, 0))

        form_frame = ttk.LabelFrame(main_frame, text="Параметры выбора", padding="16 14")
        form_frame.pack(fill=tk.X, expand=False, pady=(0, 16))

        ttk.Label(
            form_frame,
            text="🎓 1. Выберите учебную группу:",
            style="FieldTitle.TLabel",
        ).pack(anchor="w", pady=(0, 5))
        self.group_combo = ttk.Combobox(form_frame, state="readonly", font=("Segoe UI", 10))
        self.group_combo.pack(fill=tk.X, pady=(0, 14))
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        ttk.Label(
            form_frame,
            text="👤 2. Выберите студента:",
            style="FieldTitle.TLabel",
        ).pack(anchor="w", pady=(0, 5))
        self.student_combo = ttk.Combobox(form_frame, state="disabled", font=("Segoe UI", 10))
        self.student_combo.pack(fill=tk.X, pady=(0, 6))
        self.student_combo.bind("<<ComboboxSelected>>", self._on_student_selected)

        self.generate_btn = ttk.Button(
            main_frame,
            text="Сгенерировать билет",
            style="Accent.TButton",
            state="disabled",
            command=self._on_generate_clicked,
        )
        self.generate_btn.pack(fill=tk.X, pady=(4, 16), ipady=2)

        status_bar = ttk.Frame(main_frame, relief=tk.FLAT)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_lbl = ttk.Label(
            status_bar,
            text="Готово к работе",
            style="Status.TLabel",
            anchor="w",
        )
        self.status_lbl.pack(fill=tk.X, side=tk.LEFT)

    def initialize(self) -> None:
        """Инициализирует сервис и заполняет начальный список групп."""
        try:
            report = self.service.initialize()
        except StorageLockedError as exc:
            logger.error("Ошибка доступа к журналу при инициализации: %s", exc)
            self.status_lbl.config(
                text="⚠️ Журнал результатов заблокирован!",
                foreground="#DC2626",
            )
            self._alert_notifier.show_error("Ошибка доступа к журналу", str(exc))
            return
        except Exception as exc:
            logger.error("Ошибка при инициализации сервиса: %s", exc)
            self.status_lbl.config(
                text="⚠️ Ошибка инициализации данных!",
                foreground="#DC2626",
            )
            self._alert_notifier.show_error("Ошибка инициализации", f"Ошибка: {exc}")
            return

        if not report.is_ready:
            err_msg = (
                "Не найдены следующие входные файлы данных:\n• "
                + "\n• ".join(report.missing_sources)
                + "\n\nПожалуйста, поместите необходимые файлы в каталог приложения."
            )
            self.status_lbl.config(
                text="⚠️ Входные файлы не найдены!",
                foreground="#DC2626",
            )
            self._alert_notifier.show_warning("Входные файлы не найдены", err_msg)
            return

        groups = self.service.get_groups()
        if not groups:
            self.status_lbl.config(
                text="⚠️ В файле students.xlsx нет листов с группами.",
                foreground="#D97706",
            )
            return

        self.group_combo["values"] = groups
        self.status_lbl.config(
            text=f"● Загружено групп: {len(groups)}, валидных билетов: {report.tickets_count}",
            foreground="#16A34A",
        )

    def _on_group_selected(self, event: tk.Event | None = None) -> None:
        """Обработка выбора группы."""
        selected_group = self.group_combo.get().strip()
        if not selected_group:
            self._reset_student_selection()
            return

        self._group_students = self.service.get_students(selected_group)
        self._selected_student = None

        if not self._group_students:
            self._clear_student_combobox()
            self.status_lbl.config(
                text=f"⚠️ В группе '{selected_group}' нет студентов.",
                foreground="#D97706",
            )
            return

        student_names = [st.full_name for st in self._group_students]
        self.student_combo.config(state="readonly")
        self.student_combo["values"] = student_names
        self.student_combo.set("")
        self.generate_btn.config(state="disabled")
        self.status_lbl.config(
            text=f"Группа '{selected_group}': {len(student_names)} студентов. Выберите студента.",
            foreground="#475569",
        )

    def _on_student_selected(self, event: tk.Event | None = None) -> None:
        """Обработка выбора студента."""
        selected_index = self.student_combo.current()
        if 0 <= selected_index < len(self._group_students):
            self._selected_student = self._group_students[selected_index]
            self.generate_btn.config(state="normal")
            self.status_lbl.config(
                text=f"● Выбран: {self._selected_student.full_name}. Нажмите 'Сгенерировать билет'.",
                foreground="#1E3A8A",
            )
        else:
            self._selected_student = None
            self.generate_btn.config(state="disabled")

    def _clear_student_combobox(self) -> None:
        self.student_combo.set("")
        self.student_combo["values"] = []
        self.student_combo.config(state="disabled")
        self.generate_btn.config(state="disabled")

    def _reset_student_selection(self) -> None:
        self._group_students = []
        self._selected_student = None
        self._clear_student_combobox()

    def _on_generate_clicked(self) -> None:
        """Обработка клика по кнопке генерации билета."""
        if not self._selected_student:
            return

        try:
            ticket, result = self.service.assign_ticket(self._selected_student)
        except NoTicketsAvailableError as exc:
            self._alert_notifier.show_error("Ошибка билетов", str(exc))
            return
        except StorageLockedError as exc:
            self._alert_notifier.show_error("Ошибка сохранения", str(exc))
            return
        except Exception as exc:
            logger.exception("Ошибка при генерации билета: %s", exc)
            self._alert_notifier.show_error("Непредвиденная ошибка", f"Ошибка: {exc}")
            return

        self._result_presenter.show_result(
            ticket=ticket,
            student=self._selected_student,
            is_repeat=result.is_repeat,
        )

        repeat_badge = " (ПОВТОРНО)" if result.is_repeat else ""
        self.status_lbl.config(
            text=f"✓ Билет №{ticket.number} назначен для {self._selected_student.full_name}{repeat_badge}",
            foreground="#16A34A",
        )
