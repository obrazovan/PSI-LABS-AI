"""
Ticket Generator Application.

Пакет для генерации экзаменационных билетов и ведения журнала в формате Excel.
"""

from .app import TicketApp
from .console import (
    ConsoleLockRetryHandler,
    StreamConsoleIO,
    WindowsConsoleIO,
    get_console_io,
)
from .generator import FixedTicketGenerator, RandomTicketGenerator
from .models import StudentRecord
from .ports import (
    ConsoleInput,
    ConsoleIO,
    ConsoleOutput,
    JournalReader,
    JournalStorage,
    JournalWriter,
    LockRetryHandler,
    RecordRowMapper,
    StorageError,
    StorageLockedError,
    TicketGenerator,
)
from .storage import (
    DefaultExcelSheetStyler,
    ExcelJournalStorage,
    ExcelSheetStyler,
    FileLockedError,
    StudentRecordRowMapper,
)

__all__ = [
    "StudentRecord",
    "StorageError",
    "StorageLockedError",
    "TicketGenerator",
    "ConsoleOutput",
    "ConsoleInput",
    "ConsoleIO",
    "JournalWriter",
    "JournalReader",
    "JournalStorage",
    "RecordRowMapper",
    "LockRetryHandler",
    "RandomTicketGenerator",
    "FixedTicketGenerator",
    "ExcelSheetStyler",
    "DefaultExcelSheetStyler",
    "StudentRecordRowMapper",
    "ExcelJournalStorage",
    "FileLockedError",
    "WindowsConsoleIO",
    "StreamConsoleIO",
    "ConsoleLockRetryHandler",
    "get_console_io",
    "TicketApp",
]
