"""
Pytest fixtures для тестов генератора экзаменационных билетов.
"""

from __future__ import annotations
import tempfile
from pathlib import Path
from typing import Iterator, List
import pytest

from ticket_generator.models import StudentRecord


@pytest.fixture
def tmp_excel_path() -> Iterator[Path]:
    """Создает путь к временному файлу Excel и удаляет его после теста."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "test_journal.xlsx"
        yield file_path
        if file_path.exists():
            file_path.unlink()


@pytest.fixture
def sample_record() -> StudentRecord:
    """Возвращает тестовую запись студента."""
    return StudentRecord(
        last_name="Иванов",
        first_name="Иван",
        ticket_number=7,
        timestamp="2026-11-04 12:00:00",
    )


class MockConsoleIO:
    """Мок консольного ввода-вывода для детерминированного тестирования."""

    def __init__(self, inputs: List[str | None]) -> None:
        self.inputs = list(inputs)
        self.output_messages: list[str] = []
        self.prompts: list[str] = []
        self.startup_hint_shown = False

    def show_startup_hint(self) -> None:
        self.startup_hint_shown = True
        self.output_messages.append("Для выхода нажмите ESC.")

    def print(self, message: str) -> None:
        self.output_messages.append(message)

    def read_name(self, prompt: str) -> str | None:
        self.prompts.append(prompt)
        if not self.inputs:
            return None  # По умолчанию завершаем ввод, если список пуст

        val = self.inputs.pop(0)
        # Имитация повтора при пустом вводе
        while val is not None and not val.strip():
            self.prompts.append(prompt)
            if not self.inputs:
                return None
            val = self.inputs.pop(0)

        if val is None:
            return None

        return val.strip()


@pytest.fixture
def mock_console_factory():
    """Фабрика для создания мок-консоли с заданными вводами."""
    def _create(inputs: list[str | None]) -> MockConsoleIO:
        return MockConsoleIO(inputs)
    return _create
