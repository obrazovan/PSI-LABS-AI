"""
Тесты маршрутизатора веб-интерфейса TicketWebRouter.
"""

from __future__ import annotations
import json
from pathlib import Path
import pytest

from ticket_gui.models import InitializationReport, Student, Ticket
from ticket_gui.ports import TicketServiceProtocol
from ticket_gui.web.router import TicketWebRouter


class FakeWebService:
    """Минимальный сервис для тестирования API веб-интерфейса."""

    def __init__(self) -> None:
        self.student = Student("ТИ-235", "Иванов", "Иван")

    def initialize(self) -> InitializationReport:
        return InitializationReport(missing_sources=(), groups_count=1, tickets_count=1)

    def get_groups(self) -> list[str]:
        return ["ТИ-235"]

    def get_students(self, group: str) -> list[Student]:
        if group == "ТИ-235":
            return [self.student]
        return []

    def assign_ticket(self, student: Student) -> tuple[Ticket, Any]:
        from ticket_gui.models import ExamResult

        ticket = Ticket(number=3, questions=("Вопрос 1", "Вопрос 2", "Вопрос 3"))
        result = ExamResult(
            group=student.group,
            last_name=student.last_name,
            first_name=student.first_name,
            ticket_number=3,
            is_repeat=False,
        )
        return ticket, result


class TestWebRouter:
    @pytest.fixture
    def router(self) -> TicketWebRouter:
        return TicketWebRouter(service=FakeWebService())

    def test_serve_index_html(self, router: TicketWebRouter):
        status, headers, content = router.handle("GET", "/")
        assert status == 200
        assert "text/html" in headers["Content-Type"]
        assert b"<!DOCTYPE html>" in content

    def test_serve_css_and_js(self, router: TicketWebRouter):
        status_css, headers_css, content_css = router.handle("GET", "/styles.css")
        assert status_css == 200
        assert "text/css" in headers_css["Content-Type"]
        assert len(content_css) > 0

        status_js, headers_js, content_js = router.handle("GET", "/app.js")
        assert status_js == 200
        assert "javascript" in headers_js["Content-Type"]
        assert len(content_js) > 0

    def test_api_init(self, router: TicketWebRouter):
        status, headers, content = router.handle("GET", "/api/init")
        assert status == 200
        data = json.loads(content.decode("utf-8"))
        assert data["status"] == "ok"
        assert data["ready"] is True
        assert data["groups"] == ["ТИ-235"]

    def test_api_students(self, router: TicketWebRouter):
        status, headers, content = router.handle("GET", "/api/students?group=%D0%A2%D0%98-235")
        assert status == 200
        data = json.loads(content.decode("utf-8"))
        assert data["status"] == "ok"
        assert len(data["students"]) == 1
        assert data["students"][0]["full_name"] == "Иванов Иван"

    def test_api_students_missing_group_returns_400(self, router: TicketWebRouter):
        status, _, content = router.handle("GET", "/api/students")
        assert status == 400

    def test_api_generate_success(self, router: TicketWebRouter):
        payload = {"group": "ТИ-235", "last_name": "Иванов", "first_name": "Иван"}
        body = json.dumps(payload).encode("utf-8")
        status, _, content = router.handle("POST", "/api/generate", body)
        assert status == 200
        data = json.loads(content.decode("utf-8"))
        assert data["status"] == "ok"
        assert data["ticket"]["number"] == 3
        assert len(data["ticket"]["questions"]) == 3
        assert data["result"]["ticket_number"] == 3

    def test_api_generate_missing_fields_returns_400(self, router: TicketWebRouter):
        payload = {"group": "ТИ-235"}
        body = json.dumps(payload).encode("utf-8")
        status, _, _ = router.handle("POST", "/api/generate", body)
        assert status == 400

    def test_unknown_route_returns_404(self, router: TicketWebRouter):
        status, _, _ = router.handle("GET", "/unknown/route")
        assert status == 404

