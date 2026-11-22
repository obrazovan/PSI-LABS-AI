"""
Модуль консольного ввода/вывода с поддержкой перехвата клавиши ESC.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence, TextIO

from .ports import ConsoleIO, ConsoleInput, ConsoleOutput, LockRetryHandler

_TRIM_CHARS = " \t\r\n\ufeff"


def configure_utf8_stdio() -> None:
    """Настраивает UTF-8 кодировку для стандартных потоков ввода/вывода."""
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


class _BaseConsoleIO:
    """Общая реализация консольного вывода для всех консольных адаптеров."""

    def __init__(self, stdout: TextIO | None = None) -> None:
        self.stdout = stdout or sys.stdout

    def show_startup_hint(self) -> None:
        """Выводит стартовую подсказку пользователю."""
        self.print("Для выхода нажмите ESC.")

    def print(self, message: str) -> None:
        """Выводит сообщение в консоль."""
        self.stdout.write(f"{message}\n")
        self.stdout.flush()


class WindowsConsoleIO(_BaseConsoleIO):
    """
    Реализация консольного ввода для Windows с использованием msvcrt.

    Поддерживает:
    - Моментальный перехват ESC (код 27 / \x1b).
    - Корректную обработку клавиши Backspace (удаление символа с экрана и из буфера).
    - Полноценную поддержку Unicode (включая русские буквы) через getwch().
    - Игнорирование служебных клавиш (стрелки, F-клавиши).
    - Повторный запрос при пустом вводе.
    """

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
                    entered_text = "".join(buffer).strip(_TRIM_CHARS)
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


class StreamConsoleIO(_BaseConsoleIO):
    """
    Реализация ввода/вывода через стандартные потоки (для тестов или систем без msvcrt).
    """

    def __init__(
        self,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        exit_tokens: Sequence[str] = ("ESC",),
    ) -> None:
        super().__init__(stdout=stdout)
        self.stdin = stdin or sys.stdin
        self._exit_tokens = {token.strip().upper() for token in exit_tokens if token.strip()}

    def read_name(self, prompt: str) -> str | None:
        while True:
            self.stdout.write(prompt)
            self.stdout.flush()

            line = self.stdin.readline()
            if not line:  # EOF / закрыт поток
                return None

            # Если в поток отправлен ESC-код (\x1b) или специальный текстовый маркер выхода
            cleaned = line.strip(_TRIM_CHARS)
            if "\x1b" in line or cleaned.upper() in self._exit_tokens:
                return None

            if not cleaned:
                # Пустая строка — повторяем запрос
                continue

            return cleaned


class ConsoleLockRetryHandler:
    """
    Консольный обработчик блокировки ресурса хранения.

    Информирует пользователя о блокировке (например, если файл открыт в Excel)
    и ожидает подтверждения повторной попытки или отмены.
    """

    def __init__(
        self,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        cancel_tokens: Sequence[str] = ("exit", "q", "quit"),
    ) -> None:
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self._cancel_tokens = {token.strip().lower() for token in cancel_tokens}

    def __call__(self, resource: Any, exception: Exception) -> bool:
        resource_name = resource.name if isinstance(resource, Path) else str(resource)
        msg = (
            f"\n[ВНИМАНИЕ] Файл '{resource_name}' открыт в Excel или заблокирован другой программой.\n"
            f"Пожалуйста, закройте файл в Excel и нажмите Enter для повторной попытки сохранения.\n"
            f"(Или введите 'exit'/'q' и нажмите Enter для отмены): "
        )
        self.stdout.write(msg)
        self.stdout.flush()

        try:
            line = self.stdin.readline()
            if not line:
                return False
            response = line.strip(_TRIM_CHARS).lower()
            return response not in self._cancel_tokens
        except (KeyboardInterrupt, EOFError):
            return False


def get_console_io(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> ConsoleIO:
    """Фабрика для создания оптимальной реализации ConsoleIO для текущей среды."""
    in_stream = stdin or sys.stdin
    out_stream = stdout or sys.stdout

    if sys.platform == "win32" and getattr(in_stream, "isatty", lambda: False)():
        try:
            import msvcrt  # noqa: F401
            return WindowsConsoleIO(stdout=out_stream)
        except ImportError:
            pass

    return StreamConsoleIO(stdin=in_stream, stdout=out_stream)


__all__ = [
    "ConsoleOutput",
    "ConsoleInput",
    "ConsoleIO",
    "LockRetryHandler",
    "WindowsConsoleIO",
    "StreamConsoleIO",
    "ConsoleLockRetryHandler",
    "configure_utf8_stdio",
    "get_console_io",
]
