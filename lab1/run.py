#!/usr/bin/env python3
"""
Скрипт прямого запуска консольного приложения Лабораторной работы №1.

Использование:
    python run.py
    python run.py --file my_journal.xlsx
"""

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

# Добавляем каталог src в sys.path для корректного импорта пакета
base_dir = Path(__file__).resolve().parent
src_dir = base_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ticket_generator.__main__ import main

if __name__ == "__main__":
    # По умолчанию сохраняем journal.xlsx в каталоге lab1
    default_journal = base_dir / "journal.xlsx"
    sys.exit(main(default_file=default_journal))
