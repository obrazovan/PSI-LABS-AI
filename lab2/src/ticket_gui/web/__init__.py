"""
Веб-интерфейс генератора билетов (Web UI Adapter).

Реализует веб-адаптер над ядром TicketServiceProtocol в соответствии
с принципами Clean Architecture и SOLID.
"""

from .router import TicketWebRouter
from .server import TicketWebServer
from .playwright_runner import PlaywrightBrowserRunner

__all__ = ["TicketWebRouter", "TicketWebServer", "PlaywrightBrowserRunner"]

