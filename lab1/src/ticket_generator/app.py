"""
Главный координатор приложения (Application Controller).
"""

from __future__ import annotations

from .models import StudentRecord
from .ports import ConsoleIO, JournalWriter, StorageError, TicketGenerator


class TicketApp:
    """
    Основное приложение генератора экзаменационных билетов.

    Зависит исключительно от абстракций (портов) и координирует сценарий
    ввода студента, генерации билета и сохранения записи в журнал.
    """

    def __init__(
        self,
        storage: JournalWriter,
        generator: TicketGenerator,
        console: ConsoleIO,
        storage_description: str | None = None,
    ) -> None:
        self.storage = storage
        self.generator = generator
        self.console = console
        self.storage_description = storage_description

    def run(self) -> int:
        """
        Запускает основной цикл приложения.

        Шаги:
        1. Инициализируется хранилище.
        2. Выводится подсказка: 'Для выхода нажмите ESC.'
        3. Запрашиваются 'Last name: ' и 'First name: ' до нажатия ESC.
        4. Генерируется номер билета и выводится: 'Билет № <номер>.'.
        5. Запись немедленно сохраняется в хранилище.
        """
        try:
            self.storage.ensure_initialized()
        except StorageError as exc:
            self.console.print(f"Ошибка при инициализации: {exc}")
            return 1

        self.console.show_startup_hint()
        if self.storage_description:
            self.console.print(f"{self.storage_description}\n")

        try:
            while self._process_single_student():
                pass
        except KeyboardInterrupt:
            self.console.print("\nПрограмма прервана пользователем.")
            return 0

        self.console.print("Работа программы завершена.")
        return 0

    def _process_single_student(self) -> bool:
        """Обрабатывает ввод одного студента. Возвращает False при сигнале выхода."""
        last_name = self.console.read_name("Last name: ")
        if last_name is None:
            return False

        first_name = self.console.read_name("First name: ")
        if first_name is None:
            return False

        ticket_number = self.generator.generate()
        record = StudentRecord(
            last_name=last_name,
            first_name=first_name,
            ticket_number=ticket_number,
        )

        self.console.print(f"Билет № {record.ticket_number}.")

        try:
            self.storage.append_record(record)
        except StorageError as exc:
            self.console.print(f"\n[Ошибка сохранения] {exc}")

        return True
