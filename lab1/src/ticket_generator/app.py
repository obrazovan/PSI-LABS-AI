"""
Главный координатор приложения (Application Controller).
"""

from __future__ import annotations
import sys
from .models import StudentRecord
from .generator import TicketGenerator, RandomTicketGenerator
from .storage import ExcelJournalStorage, FileLockedError
from .console import ConsoleIO, get_console_io


class TicketApp:
    """
    Основное приложение генератора экзаменационных билетов.

    Связывает консольный интерфейс, логику генерации билетов и хранилище Excel.
    """

    def __init__(
        self,
        storage: ExcelJournalStorage | None = None,
        generator: TicketGenerator | None = None,
        console: ConsoleIO | None = None,
    ) -> None:
        self.storage = storage or ExcelJournalStorage()
        self.generator = generator or RandomTicketGenerator()
        self.console = console or get_console_io()

    def run(self) -> int:
        """
        Запускает основной цикл приложения.

        Шаги:
        1. При запуске выводится подсказка: 'Для выхода нажмите ESC.'
        2. Приложение запрашивает 'Last name: ' — подтверждается Enter.
        3. Приложение запрашивает 'First name: ' — подтверждается Enter.
        4. Генерируется номер билета от 1 до 20.
        5. Номер выводится в консоль: 'Билет № <номер>.'
        6. Запись немедленно дописывается в Excel-файл.
        7. Цикл повторяется до нажатия ESC.
        """
        try:
            # Инициализация хранилища (создание файла с шапкой при необходимости)
            self.storage.ensure_initialized()
        except FileLockedError as exc:
            self.console.print(f"Ошибка при инициализации: {exc}")
            return 1

        # Шаг 1: Подсказка при запуске
        self.console.show_startup_hint()
        self.console.print(f"Файл журнала: {self.storage.file_path.resolve()}\n")

        try:
            while True:
                # Шаг 2: Запрос фамилии
                last_name = self.console.read_name("Last name: ")
                if last_name is None:
                    # Нажата клавиша ESC на шаге ввода фамилии
                    break

                # Шаг 3: Запрос имени
                first_name = self.console.read_name("First name: ")
                if first_name is None:
                    # Нажата клавиша ESC на шаге ввода имени
                    break

                # Шаг 4: Генерация номера билета
                ticket_number = self.generator.generate()

                # Шаг 5: Вывод номера билета в консоль
                self.console.print(f"Билет № {ticket_number}.")

                # Шаг 6: Сохранение записи в Excel
                record = StudentRecord(
                    last_name=last_name,
                    first_name=first_name,
                    ticket_number=ticket_number,
                )

                try:
                    self.storage.append_record(record)
                except FileLockedError as exc:
                    self.console.print(f"\n[Ошибка сохранения] {exc}")
                    # Предлагаем пользователю продолжить или выйти
                    continue

        except KeyboardInterrupt:
            self.console.print("\nПрограмма прервана пользователем.")
            return 0

        self.console.print("Работа программы завершена.")
        return 0
