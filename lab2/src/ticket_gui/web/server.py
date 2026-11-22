"""
HTTP-сервер веб-интерфейса (SRP).

Отвечает за жизненный цикл HTTP-сервера и передачу запросов в TicketWebRouter.
"""

from __future__ import annotations
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from ..ports import TicketServiceProtocol
from .router import TicketWebRouter

logger = logging.getLogger(__name__)


class _HttpHandler(BaseHTTPRequestHandler):
    """Внутренний обработчик HTTP, делегирующий запросы маршрутизатору."""

    router: TicketWebRouter

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self) -> None:
        status, headers, content = self.router.handle("GET", self.path)
        self._send_response(status, headers, content)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        status, headers, content = self.router.handle("POST", self.path, body)
        self._send_response(status, headers, content)

    def _send_response(self, status: int, headers: dict[str, str], content: bytes) -> None:
        try:
            self.close_connection = True
            self.send_response(status)
            for key, val in headers.items():
                self.send_header(key, val)
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)


class _SilentHTTPServer(HTTPServer):
    """HTTP-сервер с подавлением шума отключения сокетов при завершении."""

    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        # Подавляем исключения закрытия keep-alive сокетов клиентом при завершении теста/сервера
        pass


class TicketWebServer:
    """Управление веб-сервером приложения."""

    def __init__(
        self,
        service: TicketServiceProtocol,
        host: str = "127.0.0.1",
        port: int = 8000,
        router: TicketWebRouter | None = None,
    ) -> None:
        self.host = host
        self.requested_port = port
        self.router = router or TicketWebRouter(service=service)

        class CustomHandler(_HttpHandler):
            router = self.router

        self.server = _SilentHTTPServer((self.host, self.requested_port), CustomHandler)
        self._thread: threading.Thread | None = None

    @property
    def server_port(self) -> int:
        """Реальный порт сервера (актуально при port=0)."""
        return self.server.server_address[1]

    @property
    def base_url(self) -> str:
        """Базовый URL работающего веб-сервера."""
        return f"http://{self.host}:{self.server_port}"

    def serve_forever(self) -> None:
        """Запускает сервер в блокирующем режиме."""
        logger.info("Веб-сервер запущен: %s", self.base_url)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Остановка веб-сервера по сигналу прерывания.")
        finally:
            self.server.server_close()

    def start_background(self) -> str:
        """Запускает сервер в фоновом потоке (для тестов и авто-браузера)."""
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        return self.base_url

    def stop(self) -> None:
        """Останавливает сервер."""
        self.server.shutdown()
        self.server.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
