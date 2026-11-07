"""
Ticket Generator UI Application (Лабораторная работа №2).
"""

from .models import Student, Ticket, ExamResult
from .parsers import ExcelStudentReader, DocxTicketParser
from .storage import ResultJournalStorage
from .service import TicketService

__all__ = [
    "Student",
    "Ticket",
    "ExamResult",
    "ExcelStudentReader",
    "DocxTicketParser",
    "ResultJournalStorage",
    "TicketService",
]
