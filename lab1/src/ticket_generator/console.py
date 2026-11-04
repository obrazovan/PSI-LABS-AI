"""
Модуль консольного ввода/вывода с поддержкой перехвата клавиши ESC.
"""

from __future__ import annotations
import sys
from typing import Protocol, TextIO


class ConsoleIO(Protocol):
    """Интерфейс для консольного ввода/вывода."""

    def show_startup_hint(self) -> None:
        """Выводит подсказку при запуске: 'Для выхода нажмите ESC.'."""
        ...

    def read_name(self, prompt: str) -> str | None:
        """
        Запрашивает строку (фамилию или имя).

        - Пробелы по краям обрезаются.
        - Пустая строка не принимается (запрос повторяется).
        - Нажатие клавиши ESC возвращает None (сигнал к выходу).
        """
        ...

    def print(self, message: str) -> None:
        """Выводит сообщение в консоль."""
        ...


class WindowsConsoleIO:
    """
    Реализация консольного ввода для Windows с использованием msvcrt.

    Поддерживает:
    - Моментальный перехват ESC (код 27 / \x1b).
    - Корректную обработку клавиши Backspace (удаление символа с экрана и из буфера).
    - Полноценную поддержку Unicode (включая русские буквы) через getwch().
    - Игнорирование служебных клавиш (стрелки, F-клавиши).
    - Повторный запрос при пустом вводе.
    """

    def __init__(self, stdout: TextIO | None = None) -> None:
        self.stdout = stdout or sys.stdout

    def show_startup_hint(self) -> None:
        self.stdout.write("Для выхода нажмите ESC.\n")
        self.stdout.flush()

    def print(self, message: str) -> None:
        self.stdout.write(f"{message}\n")
        self.stdout.flush()

    def read_name(self, prompt: str) -> str | None:
        import msvcrt

        while True:
            self.stdout.write(prompt)
            self.stdout.flush()

            buffer: list[str] = []

            while True:
                ch = msvcrt.getwch()

                # Нажатие клавиши ESC -> сигнал к завершению программы
                if ch == "\x1b":
                    self.stdout.write("\n")
                    self.stdout.flush()
                    return None

                # Нажатие Ctrl+C
                if ch == "\x03":
                    self.stdout.write("\n")
                    self.stdout.flush()
                    raise KeyboardInterrupt()

                # Нажатие Enter
                if ch in ("\r", "\n"):
                    self.stdout.write("\n")
                    self.stdout.flush()
                    entered_text = "".join(buffer).strip()
                    if not entered_text:
                        # Пустая строка не принимается — повторяем запрос
                        break
                    return entered_text

                # Нажатие Backspace
                if ch in ("\x08", "\x7f"):
                    if buffer:
                        buffer.pop()
                        # Стираем символ на экране: шаг назад, пробел, шаг назад
                        self.stdout.write("\b \b")
                        self.stdout.flush()
                    continue

                # Служебные двухбайтовые клавиши (стрелки, Home, End и т.д.)
                if ch in ("\x00", "\xe0"):
                    # Считываем второй скан-код служебной клавиши
                    msvcrt.getwch()
                    continue

                # Обычный печатный символ (включая кириллицу)
                if ch >= " ":
                    buffer.append(ch)
                    self.stdout.write(ch)
                    self.stdout.flush()


class StreamConsoleIO:
    """
    Реализация ввода/вывода через стандартные потоки (для тестов или систем без msvcrt).
    """

    def __init__(self, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout

    def show_startup_hint(self) -> None:
        self.stdout.write("Для выхода нажмите ESC.\n")
        self.stdout.flush()

    def print(self, message: str) -> None:
        self.stdout.write(f"{message}\n")
        self.stdout.flush()

    def read_name(self, prompt: str) -> str | None:
        while True:
            self.stdout.write(prompt)
            self.stdout.flush()

            line = self.stdin.readline()
            if not line:  # EOF / закрыт поток
                return None

            # Если в поток отправлен ESC-код (\x1b) или специальный маркер выхода
            if "\x1b" in line or line.strip().upper() == "ESC":
                return None

            cleaned = line.strip()
            if not cleaned:
                # Пустая строка — повторяем запрос
                continue

            return cleaned


def get_console_io() -> ConsoleIO:
    """Фабрика для создания оптимальной реализации ConsoleIO для текущей среды."""
    if sys.platform == "win32" and sys.stdin.isatty():
        try:
            import msvcrt  # noqa: F401
            return WindowsConsoleIO()
        except ImportError:
            pass

    return StreamConsoleIO()
