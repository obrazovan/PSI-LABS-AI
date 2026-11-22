"""
Точка входа запуска приложения: python -m ticket_gui
Выполняет роль Composition Root — связывает конкретные реализации и абстракции.
Поддерживает как десктопный GUI (Tkinter), так и современный веб-интерфейс (--web).
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
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .parsers import DocxTicketParser, ExcelStudentReader
from .service import RandomTicketSelector, TicketService
from .storage import DelegatingLockHandler, ResultJournalStorage
from .ui.main_window import MainWindow
from .ui.presenters import TkFileLockHandler


def main(default_base_dir: Path | None = None) -> int:
    base = default_base_dir or Path.cwd()

    parser = argparse.ArgumentParser(
        description="Генератор экзаменационных билетов (Лабораторная №2) — Desktop GUI & Modern Web"
    )
    parser.add_argument(
        "--web",
        "-w",
        action="store_true",
        help="Запустить современный веб-интерфейс вместо десктопного GUI",
    )
    parser.add_argument(
        "--browser",
        "-b",
        action="store_true",
        help="Для веб-режима: автоматически открыть страницу в браузере через Playwright",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Порт для веб-сервера (по умолчанию: 8000)",
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

    # Если запрошен веб-режим
    if args.web:
        from .web import PlaywrightBrowserRunner, TicketWebServer

        student_reader = ExcelStudentReader(file_path=args.students)
        ticket_parser = DocxTicketParser(file_path=args.tickets)
        storage = ResultJournalStorage(file_path=args.results)

        service = TicketService(
            student_reader=student_reader,
            ticket_parser=ticket_parser,
            storage=storage,
            ticket_selector=RandomTicketSelector(),
        )

        server = TicketWebServer(service=service, host="127.0.0.1", port=args.port)
        print("\n" + "=" * 68)
        print("🎓 ГЕНЕРАТОР ЭКЗАМЕНАЦИОННЫХ БИЛЕТОВ — WEB EDITION")
        print(f"🚀 Веб-интерфейс доступен по адресу: {server.base_url}")
        print("=" * 68 + "\n")

        if args.browser:
            server.start_background()
            runner = PlaywrightBrowserRunner(headless=False)
            try:
                runner.open_url(server.base_url)
            finally:
                server.stop()
            return 0

        print("Нажмите Ctrl+C для остановки сервера.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")
        return 0

    # Десктопный режим Tkinter по умолчанию
    lock_handler = DelegatingLockHandler()
    student_reader = ExcelStudentReader(file_path=args.students)
    ticket_parser = DocxTicketParser(file_path=args.tickets)
    storage = ResultJournalStorage(file_path=args.results, lock_handler=lock_handler)

    service = TicketService(
        student_reader=student_reader,
        ticket_parser=ticket_parser,
        storage=storage,
        ticket_selector=RandomTicketSelector(),
    )

    app = MainWindow(service=service, auto_initialize=False)
    lock_handler.attach(TkFileLockHandler(parent=app))
    app.initialize()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
