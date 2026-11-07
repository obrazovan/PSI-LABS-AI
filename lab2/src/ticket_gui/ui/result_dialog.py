"""
Диалоговое окно отображения результатов сгенерированного билета.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..models import Student, Ticket


class ResultDialog(tk.Toplevel):
    """
    Модальное окно с отображением номера билета и его вопросов.

    Требования ТЗ:
    - Показывает 'Ваш билет № N' и три вопроса билета.
    - Нажатие клавиши ESC закрывает окно результата и возвращает к выбору
      в основном окне, само приложение при этом не завершается.
    """

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        ticket: Ticket,
        student: Student,
        is_repeat: bool = False,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.ticket = ticket
        self.student = student
        self.is_repeat = is_repeat

        self.title("Результат генерации билета")
        self.geometry("560x420")
        self.minsize(480, 360)
        self.resizable(True, True)

        # Центрирование относительно родительского окна
        self._center_window()

        self._build_ui()

        # Привязка клавиши ESC: закрывает диалог, возвращая к главному окну
        self.bind("<Escape>", lambda event: self._close_dialog())

        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _center_window(self) -> None:
        """Центрирует окно поверх родителя."""
        self.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()

        w = 560
        h = 420
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Построение элементов интерфейса окна результата."""
        main_frame = ttk.Frame(self, padding="20 20 20 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Главный заголовок: «Ваш билет № N»
        header_text = f"Ваш билет № {self.ticket.number}"
        header_lbl = ttk.Label(
            main_frame,
            text=header_text,
            font=("Segoe UI", 18, "bold"),
            foreground="#1B365D",
            anchor="center",
        )
        header_lbl.pack(pady=(0, 6), fill=tk.X)

        # Подзаголовок: Студент и группа
        student_lbl = ttk.Label(
            main_frame,
            text=f"Студент: {self.student.full_name}   |   Группа: {self.student.group}",
            font=("Segoe UI", 10),
            foreground="#4A5568",
            anchor="center",
        )
        student_lbl.pack(pady=(0, 10), fill=tk.X)

        # Если это повторная генерация — выводим информационный бейдж
        if self.is_repeat:
            repeat_frame = tk.Frame(main_frame, bg="#FEF3C7", bd=1, relief=tk.SOLID)
            repeat_frame.pack(fill=tk.X, pady=(0, 12), ipady=4)
            repeat_lbl = tk.Label(
                repeat_frame,
                text="⚠️ Повторный запрос: билет выдан повторно из первой записи в журнале",
                bg="#FEF3C7",
                fg="#92400E",
                font=("Segoe UI", 9, "bold"),
            )
            repeat_lbl.pack()

        # Рамка со списком вопросов
        q_container = ttk.LabelFrame(main_frame, text="Вопросы экзаменационного билета", padding="12 10")
        q_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Холст с прокруткой для вопросов
        canvas = tk.Canvas(q_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(q_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Отображение вопросов билета (минимум 3 по ТЗ)
        for idx, question in enumerate(self.ticket.questions, start=1):
            q_box = ttk.Frame(scrollable_frame, padding="0 4 0 8")
            q_box.pack(fill=tk.X, expand=True)

            # Форматируем вопрос, чтобы номер выделялся
            clean_q = question
            q_text_lbl = ttk.Label(
                q_box,
                text=clean_q,
                font=("Segoe UI", 10),
                wraplength=460,
                justify="left",
            )
            q_text_lbl.pack(anchor="w")

        # Нижняя панель с кнопкой закрытия
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        hint_lbl = ttk.Label(
            bottom_frame,
            text="Нажмите ESC для возврата к выбору",
            font=("Segoe UI", 9, "italic"),
            foreground="#718096",
        )
        hint_lbl.pack(side=tk.LEFT)

        close_btn = ttk.Button(
            bottom_frame,
            text="Закрыть (ESC)",
            command=self._close_dialog,
        )
        close_btn.pack(side=tk.RIGHT)

    def _close_dialog(self) -> None:
        """Закрывает окно результата и передает фокус родителю."""
        self.grab_release()
        self.destroy()
        if self.parent:
            self.parent.focus_set()
