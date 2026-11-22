"""
Маршрутизатор HTTP-запросов веб-интерфейса (SRP).

Отвечает исключительно за разбор HTTP-запросов, сериализацию JSON
и отдачу статических файлов, делегируя бизнес-логику TicketServiceProtocol.
"""

from __future__ import annotations
import json
import logging
import threading
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..exceptions import NoTicketsAvailableError, StorageLockedError
from ..models import Student, InitializationReport
from ..ports import TicketServiceProtocol

logger = logging.getLogger(__name__)


class TicketWebRouter:
    """Маршрутизатор веб-запросов и API."""

    def __init__(
        self,
        service: TicketServiceProtocol,
        static_dir: Path | None = None,
    ) -> None:
        self.service = service
        self.static_dir = static_dir or (Path(__file__).parent / "static")
        self._io_lock = threading.Lock()

    def handle(
        self,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> tuple[int, dict[str, str], bytes]:
        """
        Обрабатывает входящий запрос. Потокобезопасно сериализует операции с Excel.
        """
        with self._io_lock:
            import gc
            was_gc = gc.isenabled()
            if was_gc:
                gc.disable()
            try:
                return self._handle_unlocked(method, path, body)
            finally:
                if was_gc:
                    gc.enable()

    def _handle_unlocked(
        self,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> tuple[int, dict[str, str], bytes]:
        parsed = urlparse(path)
        route_path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if method == "GET":
                if route_path in ("/", "/index.html"):
                    return self._serve_static_file("index.html", "text/html; charset=utf-8")
                if route_path == "/styles.css":
                    return self._serve_static_file("styles.css", "text/css; charset=utf-8")
                if route_path == "/app.js":
                    return self._serve_static_file("app.js", "application/javascript; charset=utf-8")
                if route_path == "/api/init":
                    return self._handle_init()
                if route_path == "/api/groups":
                    return self._handle_groups()
                if route_path == "/api/students":
                    return self._handle_students(query)
                if route_path == "/api/history":
                    return self._handle_history()

            elif method == "POST":
                if route_path == "/api/generate":
                    return self._handle_generate(body)

            return self._json_response(404, {"status": "error", "message": "Маршрут не найден"})

        except Exception as exc:
            logger.exception("Ошибка при обработке запроса %s %s: %s", method, path, exc)
            return self._json_response(500, {"status": "error", "message": str(exc)})

    def _serve_static_file(
        self,
        filename: str,
        content_type: str,
    ) -> tuple[int, dict[str, str], bytes]:
        file_path = self.static_dir / filename
        if not file_path.exists() or not file_path.is_file():
            return self._json_response(404, {"status": "error", "message": f"Файл {filename} не найден"})

        content = file_path.read_bytes()
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
            "Cache-Control": "no-cache",
        }
        return 200, headers, content

    def _handle_init(self) -> tuple[int, dict[str, str], bytes]:
        try:
            report = self.service.initialize()
            groups = self.service.get_groups()
            return self._json_response(
                200,
                {
                    "status": "ok",
                    "ready": report.is_ready,
                    "missing_sources": list(report.missing_sources),
                    "groups_count": report.groups_count,
                    "tickets_count": report.tickets_count,
                    "groups": groups,
                },
            )
        except StorageLockedError as exc:
            return self._json_response(
                423,
                {"status": "error", "error_type": "storage_locked", "message": str(exc)},
            )

    def _handle_groups(self) -> tuple[int, dict[str, str], bytes]:
        groups = self.service.get_groups()
        return self._json_response(200, {"status": "ok", "groups": groups})

    def _handle_students(self, query: dict[str, list[str]]) -> tuple[int, dict[str, str], bytes]:
        group_list = query.get("group")
        if not group_list or not group_list[0].strip():
            return self._json_response(400, {"status": "error", "message": "Параметр 'group' обязателен"})

        group = group_list[0].strip()
        students = self.service.get_students(group)
        student_data = [
            {
                "group": s.group,
                "last_name": s.last_name,
                "first_name": s.first_name,
                "full_name": s.full_name,
            }
            for s in students
        ]
        return self._json_response(
            200,
            {
                "status": "ok",
                "group": group,
                "count": len(student_data),
                "students": student_data,
            },
        )

    def _handle_generate(self, body: bytes) -> tuple[int, dict[str, str], bytes]:
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            return self._json_response(400, {"status": "error", "message": "Некорректный JSON в теле запроса"})

        group = str(payload.get("group") or "").strip()
        last_name = str(payload.get("last_name") or "").strip()
        first_name = str(payload.get("first_name") or "").strip()

        if not group or not last_name or not first_name:
            return self._json_response(
                400,
                {
                    "status": "error",
                    "message": "Поля 'group', 'last_name' и 'first_name' обязательны для заполнения",
                },
            )

        try:
            student = Student(group=group, last_name=last_name, first_name=first_name)
            ticket, result = self.service.assign_ticket(student)
            return self._json_response(
                200,
                {
                    "status": "ok",
                    "ticket": {
                        "number": ticket.number,
                        "questions": list(ticket.questions),
                    },
                    "result": {
                        "group": result.group,
                        "last_name": result.last_name,
                        "first_name": result.first_name,
                        "full_name": student.full_name,
                        "ticket_number": result.ticket_number,
                        "is_repeat": result.is_repeat,
                        "repeat_str": result.repeat_str,
                        "timestamp": result.timestamp,
                    },
                },
            )
        except NoTicketsAvailableError as exc:
            return self._json_response(
                409,
                {"status": "error", "error_type": "no_tickets", "message": str(exc)},
            )
        except StorageLockedError as exc:
            return self._json_response(
                423,
                {"status": "error", "error_type": "storage_locked", "message": str(exc)},
            )
        except Exception as exc:
            return self._json_response(500, {"status": "error", "message": str(exc)})

    def _handle_history(self) -> tuple[int, dict[str, str], bytes]:
        storage = getattr(self.service, "storage", None)
        if storage and hasattr(storage, "read_all_rows"):
            try:
                raw_rows = storage.read_all_rows()
                history = []
                for row in raw_rows[1:]:
                    if len(row) >= 6:
                        history.append(
                            {
                                "group": row[0],
                                "last_name": row[1],
                                "first_name": row[2],
                                "ticket_number": row[3],
                                "timestamp": row[4],
                                "repeat_str": row[5],
                            }
                        )
                return self._json_response(200, {"status": "ok", "history": history})
            except Exception as exc:
                logger.warning("Не удалось прочитать историю: %s", exc)

        return self._json_response(200, {"status": "ok", "history": []})

    def _json_response(
        self,
        status_code: int,
        data: dict[str, Any],
    ) -> tuple[int, dict[str, str], bytes]:
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(content)),
            "Cache-Control": "no-cache",
        }
        return status_code, headers, content
