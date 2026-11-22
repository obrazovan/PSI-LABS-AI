"""
Тесты соответствия архитектуре SOLID: протоколы (ISP/DIP), расширяемость (OCP),
подстановка реализаций (LSP) и разделение ответственностей (SRP).
"""

from __future__ import annotations
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Sequence
import docx
import pytest

from ticket_gui.exceptions import NoTicketsAvailableError, StorageLockedError
from ticket_gui.models import ExamResult, InitializationReport, Student, Ticket
from ticket_gui.parsers import DocxTicketParser, ExcelStudentReader
from ticket_gui.ports import (
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
from ticket_gui.service import RandomTicketSelector, TicketService
from ticket_gui.storage import DelegatingLockHandler, ExcelJournalStyler, ResultJournalStorage
from ticket_gui.ui.main_window import MainWindow
from ticket_gui.ui.presenters import TkAlertNotifier, TkFileLockHandler, TkResultPresenter


class InMemoryStudentReader:
    """In-memory реализация StudentReaderProtocol без зависимости от Excel."""

    def __init__(
        self,
        data: dict[str, list[Student]] | None = None,
        available: bool = True,
    ) -> None:
        self._data = data or {}
        self._available = available

    @property
    def source_name(self) -> str:
        return "In-memory студенты"

    def is_available(self) -> bool:
        return self._available

    def load_groups(self) -> list[str]:
        return list(self._data.keys())

    def load_students_for_group(self, group_name: str) -> list[Student]:
        return list(self._data.get(group_name, []))


class InMemoryTicketParser:
    """In-memory реализация TicketParserProtocol без зависимости от Word."""

    def __init__(self, tickets: dict[int, Ticket] | None = None, available: bool = True) -> None:
        self._tickets = tickets or {}
        self._available = available

    @property
    def source_name(self) -> str:
        return "In-memory билеты"

    def is_available(self) -> bool:
        return self._available

    def parse_tickets(self) -> dict[int, Ticket]:
        return dict(self._tickets)


class InMemoryResultStorage:
    """In-memory реализация ResultStorageProtocol без файлов Excel."""

    def __init__(self) -> None:
        self.initialized = False
        self.records: list[ExamResult] = []

    def ensure_initialized(self) -> None:
        self.initialized = True

    def get_first_ticket_for_student(
        self,
        group: str,
        last_name: str,
        first_name: str,
    ) -> int | None:
        key = (group.strip().lower(), last_name.strip().lower(), first_name.strip().lower())
        for rec in self.records:
            rec_key = (rec.group.lower(), rec.last_name.lower(), rec.first_name.lower())
            if rec_key == key:
                return rec.ticket_number
        return None

    def append_result(self, result: ExamResult) -> None:
        self.records.append(result)


class MaxTicketSelector:
    """Альтернативная стратегия выбора билета (проверка OCP)."""

    def select_ticket_number(self, available_numbers: Sequence[int]) -> int:
        return max(available_numbers)


class FakeTicketService:
    """Минимальная реализация TicketServiceProtocol для изолированного теста UI (DIP/ISP)."""

    def __init__(
        self,
        report: InitializationReport,
        groups: list[str] | None = None,
        students_by_group: dict[str, list[Student]] | None = None,
        error_on_assign: Exception | None = None,
    ) -> None:
        self._report = report
        self._groups = groups or []
        self._students_by_group = students_by_group or {}
        self._error_on_assign = error_on_assign
        self.assigned_calls: list[Student] = []

    def initialize(self) -> InitializationReport:
        return self._report

    def get_groups(self) -> list[str]:
        return list(self._groups)

    def get_students(self, group: str) -> list[Student]:
        return list(self._students_by_group.get(group, []))

    def assign_ticket(self, student: Student) -> tuple[Ticket, ExamResult]:
        if self._error_on_assign is not None:
            raise self._error_on_assign
        self.assigned_calls.append(student)
        ticket = Ticket(number=5, questions=("Вопрос A", "Вопрос B", "Вопрос C"))
        result = ExamResult(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
            ticket_number=5,
            is_repeat=False,
        )
        return ticket, result


class SpyResultPresenter:
    """Шпион для ResultPresenterProtocol."""

    def __init__(self) -> None:
        self.shown: list[tuple[Ticket, Student, bool]] = []

    def show_result(self, ticket: Ticket, student: Student, is_repeat: bool) -> None:
        self.shown.append((ticket, student, is_repeat))


class SpyAlertNotifier:
    """Шпион для AlertNotifierProtocol."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, str]] = []
        self.errors: list[tuple[str, str]] = []

    def show_warning(self, title: str, message: str) -> None:
        self.warnings.append((title, message))

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))


class TestSolidArchitecture:
    def test_concrete_classes_satisfy_protocols(self, tmp_dir: Path):
        reader = ExcelStudentReader(tmp_dir / "s.xlsx")
        parser = DocxTicketParser(tmp_dir / "t.docx")
        storage = ResultJournalStorage(tmp_dir / "r.xlsx")
        selector = RandomTicketSelector(seed=1)
        styler = ExcelJournalStyler()
        lock_handler = DelegatingLockHandler()
        service = TicketService(reader, parser, storage, ticket_selector=selector)

        assert isinstance(reader, StudentReaderProtocol)
        assert isinstance(parser, TicketParserProtocol)
        assert isinstance(storage, ResultJournalReaderProtocol)
        assert isinstance(storage, ResultJournalWriterProtocol)
        assert isinstance(storage, ResultStorageProtocol)
        assert isinstance(selector, TicketSelectionStrategyProtocol)
        assert isinstance(styler, JournalStylerProtocol)
        assert isinstance(lock_handler, LockHandlerProtocol)
        assert isinstance(service, TicketServiceProtocol)

    def test_ui_adapters_satisfy_protocols(self):
        from unittest.mock import MagicMock

        mock_parent = MagicMock()
        assert isinstance(TkResultPresenter(mock_parent), ResultPresenterProtocol)
        assert isinstance(TkAlertNotifier(mock_parent), AlertNotifierProtocol)
        assert isinstance(TkFileLockHandler(mock_parent), LockHandlerProtocol)

    def test_ticket_service_works_with_pure_in_memory_protocols_and_custom_strategy(self):
        student = Student("ТИ-235", "Иванов", "Иван")
        reader = InMemoryStudentReader({"ТИ-235": [student]})
        parser = InMemoryTicketParser(
            {
                1: Ticket(1, ("В1", "В2", "В3")),
                10: Ticket(10, ("В4", "В5", "В6")),
            }
        )
        storage = InMemoryResultStorage()
        service = TicketService(
            student_reader=reader,
            ticket_parser=parser,
            storage=storage,
            ticket_selector=MaxTicketSelector(),
        )

        report = service.initialize()
        assert report.is_ready
        assert report.groups_count == 1
        assert report.tickets_count == 2
        assert storage.initialized is True

        ticket1, res1 = service.assign_ticket(student)
        assert ticket1.number == 10
        assert res1.is_repeat is False

        ticket2, res2 = service.assign_ticket(student)
        assert ticket2.number == 10
        assert res2.is_repeat is True
        assert len(storage.records) == 2

    def test_initialize_reports_missing_sources_cleanly(self):
        service = TicketService(
            student_reader=InMemoryStudentReader(available=False),
            ticket_parser=InMemoryTicketParser(available=False),
            storage=InMemoryResultStorage(),
        )

        report = service.initialize()
        assert not report.is_ready
        assert report.missing_sources == ("In-memory студенты", "In-memory билеты")

    def test_main_window_works_with_mocked_service_and_presenters(self):
        student = Student("ТИ-235", "Петров", "Петр")
        fake_service = FakeTicketService(
            report=InitializationReport(missing_sources=(), groups_count=1, tickets_count=3),
            groups=["ТИ-235"],
            students_by_group={"ТИ-235": [student]},
        )
        presenter = SpyResultPresenter()
        notifier = SpyAlertNotifier()

        app = MainWindow(
            service=fake_service,
            result_presenter=presenter,
            alert_notifier=notifier,
        )
        app.withdraw()
        try:
            assert list(app.group_combo["values"]) == ["ТИ-235"]
            app.group_combo.set("ТИ-235")
            app._on_group_selected()
            app.student_combo.current(0)
            app._on_student_selected()
            app._on_generate_clicked()

            assert len(fake_service.assigned_calls) == 1
            assert len(presenter.shown) == 1
            shown_ticket, shown_student, is_repeat = presenter.shown[0]
            assert shown_ticket.number == 5
            assert shown_student == student
            assert is_repeat is False
            assert notifier.warnings == []
            assert notifier.errors == []
        finally:
            app.destroy()

    def test_main_window_notifies_warning_on_missing_sources_and_error_on_lock(self):
        missing_service = FakeTicketService(
            report=InitializationReport(
                missing_sources=("students.xlsx",),
                groups_count=0,
                tickets_count=0,
            )
        )
        notifier = SpyAlertNotifier()
        app_missing = MainWindow(
            service=missing_service,
            result_presenter=SpyResultPresenter(),
            alert_notifier=notifier,
        )
        app_missing.withdraw()
        try:
            assert len(notifier.warnings) == 1
            assert "students.xlsx" in notifier.warnings[0][1]
        finally:
            app_missing.destroy()

        student = Student("ТИ-235", "Петров", "Петр")
        locked_service = FakeTicketService(
            report=InitializationReport(missing_sources=(), groups_count=1, tickets_count=1),
            groups=["ТИ-235"],
            students_by_group={"ТИ-235": [student]},
            error_on_assign=StorageLockedError("Файл занят"),
        )
        err_notifier = SpyAlertNotifier()
        app_locked = MainWindow(
            service=locked_service,
            result_presenter=SpyResultPresenter(),
            alert_notifier=err_notifier,
        )
        app_locked.withdraw()
        try:
            app_locked.group_combo.set("ТИ-235")
            app_locked._on_group_selected()
            app_locked.student_combo.current(0)
            app_locked._on_student_selected()
            app_locked._on_generate_clicked()

            assert len(err_notifier.errors) == 1
            assert err_notifier.errors[0][0] == "Ошибка сохранения"
        finally:
            app_locked.destroy()

    def test_exam_result_is_immutable(self):
        result = ExamResult("ТИ-235", "Иванов", "Иван", 3, False, "2026-11-11 10:00:00")
        with pytest.raises(FrozenInstanceError):
            result.ticket_number = 99  # type: ignore[misc]

    def test_delegating_lock_handler_behavior(self, tmp_dir: Path):
        handler = DelegatingLockHandler()
        path = tmp_dir / "results.xlsx"
        exc = PermissionError("Locked")

        assert handler(path, exc) is False
        handler.attach(lambda p, e: p == path and isinstance(e, PermissionError))
        assert handler(path, exc) is True

    def test_docx_parser_strips_question_prefixes_and_skips_bad_header(self, tmp_dir: Path):
        file_path = tmp_dir / "bad_header.docx"
        doc = docx.Document()
        doc.add_paragraph("Билет без номера")
        doc.add_paragraph("1. Лишний вопрос")
        doc.add_paragraph("Билет 2")
        doc.add_paragraph("1. Первый вопрос")
        doc.add_paragraph("2) Второй вопрос")
        doc.add_paragraph("3. Третий вопрос")
        doc.save(file_path)

        tickets = DocxTicketParser(file_path).parse_tickets()
        assert list(tickets.keys()) == [2]
        assert tickets[2].questions == ("Первый вопрос", "Второй вопрос", "Третий вопрос")

