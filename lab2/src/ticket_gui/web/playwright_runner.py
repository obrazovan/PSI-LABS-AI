"""
Раннер автоматизации браузера с использованием Playwright (SRP / OCP).

Позволяет запускать веб-приложение в окне Chromium / Microsoft Edge
для пользователя или автоматических E2E-тестов.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PlaywrightBrowserRunner:
    """Управление запуском и сессией браузера через Playwright."""

    def __init__(
        self,
        headless: bool = False,
        preferred_channel: str | None = None,
    ) -> None:
        self.headless = headless
        self.preferred_channel = preferred_channel

    def open_url(self, url: str) -> None:
        """
        Запускает браузер через Playwright, открывает URL и ожидает закрытия пользователем.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            venv_python = Path.cwd() / ".venv" / "Scripts" / "python.exe"
            help_msg = (
                "\n" + "=" * 70 + "\n"
                "⚠️ Пакет 'playwright' не найден в текущем окружении Python.\n\n"
                "Решение 1: Активируйте виртуальное окружение:\n"
                "    .venv\\Scripts\\Activate.ps1   (в PowerShell)\n"
                "    .venv\\Scripts\\activate.bat   (в cmd)\n\n"
                "Решение 2: Запустите через Python из venv напрямую:\n"
                f"    \"{venv_python}\" run_web.py --browser\n\n"
                "Решение 3: Установите playwright в текущий интерпретатор:\n"
                "    pip install playwright && playwright install chromium\n"
                + "=" * 70 + "\n"
            )
            print(help_msg, file=sys.stderr)
            raise SystemExit(1) from exc

        with sync_playwright() as p:
            browser = None
            launch_attempts = [
                {"headless": self.headless},
                {"headless": self.headless, "channel": "msedge"},
                {"headless": self.headless, "channel": "chrome"},
            ]
            if self.preferred_channel:
                launch_attempts.insert(0, {"headless": self.headless, "channel": self.preferred_channel})

            for kwargs in launch_attempts:
                try:
                    browser = p.chromium.launch(**kwargs)
                    logger.info("Браузер Playwright запущен: %s", kwargs)
                    break
                except Exception as exc:
                    logger.debug("Не удалось запустить браузер с %s: %s", kwargs, exc)

            if browser is None:
                print(
                    "\n⚠️ Не удалось запустить Chromium через Playwright.\n"
                    "Попробуйте установить браузеры Playwright командой:\n"
                    "    playwright install chromium\n",
                    file=sys.stderr,
                )
                raise SystemExit(1)

            context = browser.new_context(viewport={"width": 1200, "height": 850})
            page = context.new_page()
            page.goto(url)

            if not self.headless:
                logger.info("Браузер открыт на %s. Закройте окно браузера или нажмите Ctrl+C для выхода.", url)
                try:
                    page.wait_for_event("close", timeout=0)
                except KeyboardInterrupt:
                    pass
                except Exception:
                    pass
                finally:
                    browser.close()
            else:
                browser.close()
