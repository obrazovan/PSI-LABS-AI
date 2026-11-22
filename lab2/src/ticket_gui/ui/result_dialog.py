"""
Диалоговое окно отображения результатов сгенерированного билета.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from ..models import Student, Ticket


class ResultDialog(tk.Toplevel):
    """
    Модальное окно с отображением номера билета и его вопросов.

    Требования ТЗ:
    - Показывает 'Ваш билет № N' и три вопроса билета.
    - Нажатие клавиши ESC закрывает окно результата и возвращает к выбору
      в основном окне, само приложение при этом не завершается.
    - Кнопка 'Закрыть (ESC)' всегда видна внизу окна без необходимости его растягивать.
    """

    def __init__(
        self,
        parent: tk.Misc,
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
        self.geometry("600x520")
        self.minsize(520, 440)
        self.resizable(True, True)

        self._build_ui()
        self._center_window()

        self.bind("<Escape>", lambda event: self._close_dialog())

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

        w = 600
        h = 520
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Построение элементов интерфейса окна результата."""
        main_frame = ttk.Frame(self, padding="20 16 20 16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Нижняя панель с кнопкой закрытия (упаковывается первой через side=BOTTOM)
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))

        hint_lbl = ttk.Label(
            bottom_frame,
            text="Нажмите ESC на клавиатуре для быстрого закрытия",
            font=("Segoe UI", 9, "italic"),
            foreground="#64748B",
        )
        hint_lbl.pack(side=tk.LEFT, pady=4)

        close_btn = ttk.Button(
            bottom_frame,
            text="Закрыть (ESC)",
            style="Accent.TButton",
            command=self._close_dialog,
        )
        close_btn.pack(side=tk.RIGHT)

        # Заголовок и информация о студенте
        header_lbl = ttk.Label(
            main_frame,
            text=f"Ваш билет № {self.ticket.number}",
            font=("Segoe UI", 18, "bold"),
            foreground="#1E3A8A",
            anchor="center",
        )
        header_lbl.pack(side=tk.TOP, pady=(0, 4), fill=tk.X)

        student_lbl = ttk.Label(
            main_frame,
            text=f"Студент: {self.student.full_name}   •   Группа: {self.student.group}",
            font=("Segoe UI", 10, "bold"),
            foreground="#475569",
            anchor="center",
        )
        student_lbl.pack(side=tk.TOP, pady=(0, 10), fill=tk.X)

        if self.is_repeat:
            repeat_frame = tk.Frame(main_frame, bg="#FEF3C7", bd=1, relief=tk.SOLID)
            repeat_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 12), ipady=5)
            repeat_lbl = tk.Label(
                repeat_frame,
                text="⚠️ Повторная сдача: выдан ранее назначенный билет (отмечено в журнале)",
                bg="#FEF3C7",
                fg="#92400E",
                font=("Segoe UI", 9, "bold"),
            )
            repeat_lbl.pack()

        # Карточки с вопросами билета
        q_container = ttk.LabelFrame(
            main_frame,
            text="Вопросы экзаменационного билета",
            padding="14 12",
        )
        q_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        for idx, question in enumerate(self.ticket.questions, start=1):
            q_card = tk.Frame(q_container, bg="#F1F5F9", bd=1, relief=tk.GROOVE)
            q_card.pack(fill=tk.X, pady=(0, 8), padx=2, ipady=6, ipadx=8)

            badge_frame = tk.Frame(q_card, bg="#E2E8F0")
            badge_frame.pack(anchor="w", padx=6, pady=(4, 2))

            badge_lbl = tk.Label(
                badge_frame,
                text=f"Вопрос {idx}",
                font=("Segoe UI", 8, "bold"),
                bg="#E2E8F0",
                fg="#334155",
                padx=6,
                pady=1,
            )
            badge_lbl.pack()

            q_text_lbl = tk.Label(
                q_card,
                text=question,
                font=("Segoe UI", 10),
                bg="#F1F5F9",
                fg="#0F172A",
                wraplength=500,
                justify="left",
                anchor="w",
            )
            q_text_lbl.pack(fill=tk.X, padx=8, pady=(2, 4))

    def _close_dialog(self) -> None:
        """Закрывает окно результата и передает фокус родителю."""
        self.grab_release()
        self.destroy()
        if self.parent:
            self.parent.focus_set()
