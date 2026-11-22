"""
Ticket Generator UI Application (Лабораторная работа №2).
"""

import os
import sys
from pathlib import Path

# Обеспечиваем гарантированное нахождение библиотек Tcl/Tk в Windows Python
for _base in (Path(sys.base_prefix) / "tcl", Path("C:/Python314/tcl")):
    if (_base / "tcl8.6").is_dir() and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = str(_base / "tcl8.6")
    if (_base / "tk8.6").is_dir() and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = str(_base / "tk8.6")

from .exceptions import NoTicketsAvailableError, SourceNotFoundError, StorageLockedError
from .models import ExamResult, InitializationReport, Student, Ticket
from .parsers import DocxTicketParser, ExcelStudentReader
from .ports import (
    AlertNotifierProtocol,
    JournalStylerProtocol,
    LockHandlerProtocol,
    ResultJournalReaderProtocol,
    ResultJournalWriterProtocol,
    ResultPresenterProtocol,
    ResultStorageProtocol,
    StudentReaderProtocol,
    TicketParserProtocol,
    TicketSelectionStrategyProtocol,
    TicketServiceProtocol,
)
from .service import RandomTicketSelector, TicketService
from .storage import (
    DelegatingLockHandler,
    ExcelJournalStyler,
    ResultJournalStorage,
)

__all__ = [
    "AlertNotifierProtocol",
    "DelegatingLockHandler",
    "DocxTicketParser",
    "ExamResult",
    "ExcelJournalStyler",
    "ExcelStudentReader",
    "InitializationReport",
    "JournalStylerProtocol",
    "LockHandlerProtocol",
    "NoTicketsAvailableError",
    "RandomTicketSelector",
    "ResultJournalReaderProtocol",
    "ResultJournalStorage",
    "ResultJournalWriterProtocol",
    "ResultPresenterProtocol",
    "ResultStorageProtocol",
    "SourceNotFoundError",
    "StorageLockedError",
    "Student",
    "StudentReaderProtocol",
    "Ticket",
    "TicketParserProtocol",
    "TicketSelectionStrategyProtocol",
    "TicketService",
    "TicketServiceProtocol",
]
