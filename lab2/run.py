#!/usr/bin/env python3
"""
Скрипт прямого запуска GUI приложения Лабораторной работы №2.

Использование:
    python run.py
    python run.py --students path/to/students.xlsx --tickets path/to/tickets.docx
"""

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

from ticket_gui.__main__ import main

if __name__ == "__main__":
    sys.exit(main(default_base_dir=base_dir))
