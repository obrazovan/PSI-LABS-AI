"""
Точка входа запуска приложения: python -m ticket_gui
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Обеспечиваем корректное отображение кириллицы в консоли Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .parsers import ExcelStudentReader, DocxTicketParser
from .storage import ResultJournalStorage
from .service import TicketService
from .ui.main_window import MainWindow


def main(default_base_dir: Path | None = None) -> int:
    base = default_base_dir or Path.cwd()

    parser = argparse.ArgumentParser(
        description="Генератор экзаменационных билетов с графическим интерфейсом (Лабораторная №2)"
    )
    parser.add_argument(
        "--students",
        "-s",
        default=str(base / "students.xlsx"),
        help="Путь к файлу со списком студентов (по умолчанию: students.xlsx)",
    )
    parser.add_argument(
        "--tickets",
        "-t",
        default=str(base / "tickets.docx"),
        help="Путь к файлу со списком билетов (по умолчанию: tickets.docx)",
    )
    parser.add_argument(
        "--results",
        "-r",
        default=str(base / "results.xlsx"),
        help="Путь к журналу результатов (по умолчанию: results.xlsx)",
    )

    args = parser.parse_args()

    student_reader = ExcelStudentReader(file_path=args.students)
    ticket_parser = DocxTicketParser(file_path=args.tickets)
    storage = ResultJournalStorage(file_path=args.results)

    service = TicketService(
        student_reader=student_reader,
        ticket_parser=ticket_parser,
        storage=storage,
    )

    app = MainWindow(service=service)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
