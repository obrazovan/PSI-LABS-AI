#!/usr/bin/env python3
"""
Скрипт прямого запуска веб-интерфейса генератора экзаменационных билетов.

Использование:
    python run_web.py
    python run_web.py --browser              # Автоматический запуск в окне браузера через Playwright
    python run_web.py --port 8080            # Запуск на порту 8080
    python run_web.py --help
"""

from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

# Обеспечиваем корректное отображение кириллицы
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

base_dir = Path(__file__).resolve().parent
src_dir = base_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Если скрипт вызван через глобальный Python, в котором нет playwright,
# но рядом есть проектный .venv с установленным playwright — автоматически
# перезапускаем скрипт через интерпретатор из .venv
venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
    try:
        import playwright  # noqa: F401
    except ImportError:
        res = subprocess.run([str(venv_python), *sys.argv])
        sys.exit(res.returncode)

from ticket_gui.config import AppConfig
from ticket_gui.logging_config import setup_logging
from ticket_gui.parsers import DocxTicketParser, ExcelStudentReader
from ticket_gui.service import RandomTicketSelector, TicketService
from ticket_gui.storage import DelegatingLockHandler, ResultJournalStorage
from ticket_gui.web import PlaywrightBrowserRunner, TicketWebServer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Современный веб-интерфейс генератора экзаменационных билетов (Web Edition)"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Хост сервера (по умолчанию: 127.0.0.1 или переменная APP_HOST)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=None,
        help="Порт сервера (по умолчанию: 8000 или переменная APP_PORT)",
    )
    parser.add_argument(
        "--browser",
        "-b",
        action="store_true",
        default=None,
        help="Автоматически запустить и открыть страницу в браузере через Playwright",
    )
    parser.add_argument(
        "--students",
        "-s",
        default=None,
        help="Путь к файлу со списком студентов (по умолчанию: students.xlsx)",
    )
    parser.add_argument(
        "--tickets",
        "-t",
        default=None,
        help="Путь к файлу со списком билетов (по умолчанию: tickets.docx)",
    )
    parser.add_argument(
        "--results",
        "-r",
        default=None,
        help="Путь к журналу результатов (по умолчанию: results.xlsx)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Уровень логирования (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args()
    config = AppConfig.from_env_or_args(args=args, base_dir=base_dir)
    logger = setup_logging(level=config.log_level)

    # Composition Root для веб-приложения на основе AppConfig (SOLID / DIP)
    student_reader = ExcelStudentReader(file_path=config.students_path)
    ticket_parser = DocxTicketParser(file_path=config.tickets_path)
    storage = ResultJournalStorage(file_path=config.results_path)

    service = TicketService(
        student_reader=student_reader,
        ticket_parser=ticket_parser,
        storage=storage,
        ticket_selector=RandomTicketSelector(),
    )
    init_report = service.initialize()

    server = TicketWebServer(service=service, host=config.host, port=config.port)

    print("\n" + "=" * 68)
    print("🎓 ГЕНЕРАТОР ЭКЗАМЕНАЦИОННЫХ БИЛЕТОВ — WEB EDITION")
    print(f"🚀 Веб-интерфейс доступен по адресу: {server.base_url}")
    if init_report.is_ready:
        print(f"✅ Успешно загружено: групп — {init_report.groups_count}, билетов — {init_report.tickets_count}")
    else:
        print(f"⚠️ Предупреждение: отсутствуют источники: {', '.join(init_report.missing_sources)}")
    print("=" * 68 + "\n")

    if config.auto_browser:
        server.start_background()
        runner = PlaywrightBrowserRunner(headless=False)
        print("🌐 Запуск браузера через Playwright...")
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


if __name__ == "__main__":
    sys.exit(main())
