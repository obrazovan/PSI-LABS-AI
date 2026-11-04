"""
Ticket Generator Application.

Пакет для генерации экзаменационных билетов и ведения журнала в формате Excel.
"""

from .models import StudentRecord
from .generator import TicketGenerator, RandomTicketGenerator
from .storage import ExcelJournalStorage
from .console import ConsoleIO, get_console_io
from .app import TicketApp

__all__ = [
    "StudentRecord",
    "TicketGenerator",
    "RandomTicketGenerator",
    "ExcelJournalStorage",
    "ConsoleIO",
    "get_console_io",
    "TicketApp",
]
