"""
Точка входа для запуска модуля: python -m ticket_generator
"""

import argparse
import sys
from pathlib import Path

# Обеспечиваем корректное отображение кириллицы в консоли Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .app import TicketApp
from .storage import ExcelJournalStorage
from .generator import RandomTicketGenerator
from .console import get_console_io


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Генератор экзаменационных билетов с сохранением в Excel (Лабораторная работа №1)"
    )
    parser.add_argument(
        "--file",
        "-f",
        default="journal.xlsx",
        help="Путь к файлу журнала Excel (по умолчанию: journal.xlsx)",
    )
    parser.add_argument(
        "--min-ticket",
        type=int,
        default=1,
        help="Минимальный номер билета (по умолчанию: 1)",
    )
    parser.add_argument(
        "--max-ticket",
        type=int,
        default=20,
        help="Максимальный номер билета (по умолчанию: 20)",
    )

    args = parser.parse_args()

    storage = ExcelJournalStorage(file_path=args.file)
    generator = RandomTicketGenerator(min_ticket=args.min_ticket, max_ticket=args.max_ticket)
    console = get_console_io()

    app = TicketApp(storage=storage, generator=generator, console=console)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
