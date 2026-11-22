"""
Точка входа для запуска модуля: python -m ticket_generator
"""

import argparse
import sys
from pathlib import Path

from .app import TicketApp
from .console import ConsoleLockRetryHandler, configure_utf8_stdio, get_console_io
from .generator import RandomTicketGenerator
from .storage import (
    DefaultExcelSheetStyler,
    ExcelJournalStorage,
    StudentRecordRowMapper,
)


def main(default_file: Path | str | None = None) -> int:
    """Точка сборки зависимостей (Composition Root) и запуска приложения."""
    configure_utf8_stdio()
    default_path = str(default_file) if default_file is not None else "journal.xlsx"

    parser = argparse.ArgumentParser(
        description="Генератор экзаменационных билетов с сохранением в Excel (Лабораторная работа №1)"
    )
    parser.add_argument(
        "--file",
        "-f",
        default=default_path,
        help=f"Путь к файлу журнала Excel (по умолчанию: {default_path})",
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

    storage = ExcelJournalStorage(
        file_path=args.file,
        lock_retry_handler=ConsoleLockRetryHandler(),
        mapper=StudentRecordRowMapper(),
        styler=DefaultExcelSheetStyler(),
    )
    generator = RandomTicketGenerator(min_ticket=args.min_ticket, max_ticket=args.max_ticket)
    console = get_console_io()

    app = TicketApp(
        storage=storage,
        generator=generator,
        console=console,
        storage_description=storage.describe(),
    )
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
