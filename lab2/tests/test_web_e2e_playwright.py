"""
End-to-End (E2E) тесты веб-интерфейса с использованием Playwright.

Спроектированы по паттерну Page Object Model (POM) в соответствии с SOLID и Clean Code.
"""

from __future__ import annotations
from pathlib import Path
from typing import Iterator
import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from ticket_gui.service import TicketService
from ticket_gui.web.server import TicketWebServer


class TicketPageObject:
    """
    Page Object Model (POM) для веб-интерфейса генератора билетов (SRP).
    Инкапсулирует локаторы и взаимодействия с веб-страницей.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

        # Селекторы элементов
        self.group_select = page.locator("#groupSelect")
        self.student_select = page.locator("#studentSelect")
        self.generate_btn = page.locator("#generateBtn")
        self.empty_group_note = page.locator("#emptyGroupNote")
        self.status_text = page.locator("#statusText")
        self.theme_toggle = page.locator("#themeToggle")

        self.modal = page.locator("#resultModal")
        self.modal_ticket_title = page.locator("#modalTicketNumber")
        self.modal_student_name = page.locator("#modalStudentName")
        self.modal_repeat_banner = page.locator("#modalRepeatBanner")
        self.modal_questions = page.locator(".question-card")
        self.modal_close_btn = page.locator("#modalCloseBtn")

    def open(self) -> None:
        self.page.goto(self.base_url)
        self.page.wait_for_selector("#groupSelect")

    def select_group(self, group_name: str) -> None:
        self.group_select.select_option(label=group_name)
        # Ожидаем завершения запроса студентов
        self.page.wait_for_timeout(300)

    def select_student_by_text(self, full_name: str) -> None:
        self.student_select.select_option(label=full_name)
        self.page.wait_for_timeout(100)

    def click_generate(self) -> None:
        self.generate_btn.click()
        self.modal.wait_for(state="visible", timeout=3000)

    def close_modal_via_esc(self) -> None:
        self.page.keyboard.press("Escape")
        self.modal.wait_for(state="hidden", timeout=3000)

    def is_modal_visible(self) -> bool:
        return self.modal.is_visible()

    def get_modal_ticket_text(self) -> str:
        return self.modal_ticket_title.inner_text().strip()

    def get_questions_count(self) -> int:
        return self.modal_questions.count()

    def is_repeat_banner_visible(self) -> bool:
        return self.modal_repeat_banner.is_visible()

    def is_generate_enabled(self) -> bool:
        return self.generate_btn.is_enabled()

    def is_empty_note_visible(self) -> bool:
        return self.empty_group_note.is_visible()

    def toggle_theme(self) -> None:
        self.theme_toggle.click()

    def get_html_theme(self) -> str:
        return self.page.locator("html").get_attribute("data-theme") or ""


@pytest.fixture(scope="module")
def playwright_instance():
    """
    Запуск и остановка сессии Playwright.
    Защита от CPython 3.14 GC гонки с greenlet stack swapping на Windows.
    """
    import gc
    was_enabled = gc.isenabled()
    if was_enabled:
        gc.disable()
    try:
        with sync_playwright() as p:
            yield p
    finally:
        if was_enabled:
            gc.enable()
            gc.collect()


@pytest.fixture(scope="module")
def browser(playwright_instance) -> Iterator[Browser]:
    """Запуск headless браузера Chromium."""
    b = playwright_instance.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture
def web_server(ticket_service: TicketService) -> Iterator[str]:
    """Запускает веб-сервер на случайном свободном порту (port=0) на время теста."""
    ticket_service.initialize()
    server = TicketWebServer(service=ticket_service, host="127.0.0.1", port=0)
    base_url = server.start_background()
    yield base_url
    server.stop()


class TestWebPlaywrightE2E:
    def test_page_loads_and_displays_groups(self, browser: Browser, web_server: str):
        page = browser.new_page()
        app = TicketPageObject(page, web_server)
        app.open()

        # Проверяем заполнение списка групп
        options = page.locator("#groupSelect option").all_inner_texts()
        assert any("ИВТ-21" in opt for opt in options)
        assert any("ПИ-22" in opt for opt in options)
        assert any("ПУСТАЯ-00" in opt for opt in options)

        # Кнопка генерации неактивна
        assert not app.is_generate_enabled()
        page.close()

    def test_empty_group_disables_button_and_shows_warning(self, browser: Browser, web_server: str):
        page = browser.new_page()
        app = TicketPageObject(page, web_server)
        app.open()

        app.select_group("ПУСТАЯ-00")
        assert not app.is_generate_enabled()
        assert app.is_empty_note_visible()
        page.close()

    def test_full_ticket_generation_flow_and_modal_esc(self, browser: Browser, web_server: str):
        page = browser.new_page()
        app = TicketPageObject(page, web_server)
        app.open()

        # 1. Выбираем группу
        app.select_group("ИВТ-21")
        assert not app.is_generate_enabled()

        # 2. Выбираем студента
        app.select_student_by_text("Иванов Иван")
        assert app.is_generate_enabled()

        # 3. Нажимаем генерацию
        app.click_generate()
        assert app.is_modal_visible()

        # 4. Проверяем номер билета и 3 вопроса
        ticket_text = app.get_modal_ticket_text()
        assert "Ваш билет №" in ticket_text
        assert app.get_questions_count() == 3
        assert not app.is_repeat_banner_visible()

        # 5. Закрываем модальное окно клавишей ESC (требование ТЗ)
        app.close_modal_via_esc()
        assert not app.is_modal_visible()

        page.close()

    def test_idempotence_repeat_generation_shows_same_ticket_and_repeat_banner(
        self, browser: Browser, web_server: str
    ):
        page = browser.new_page()
        app = TicketPageObject(page, web_server)
        app.open()

        # Первая генерация для Петрова
        app.select_group("ИВТ-21")
        app.select_student_by_text("Петров Петр")
        app.click_generate()

        first_ticket_text = app.get_modal_ticket_text()
        assert not app.is_repeat_banner_visible()
        app.close_modal_via_esc()

        # Повторная генерация для того же студента
        app.click_generate()
        second_ticket_text = app.get_modal_ticket_text()

        # Идемпотентность: тот же номер билета
        assert second_ticket_text == first_ticket_text
        # Должен отобразиться бейдж повторной сдачи
        assert app.is_repeat_banner_visible()

        app.close_modal_via_esc()
        page.close()

    def test_theme_toggle_works(self, browser: Browser, web_server: str):
        page = browser.new_page()
        app = TicketPageObject(page, web_server)
        app.open()

        initial_theme = app.get_html_theme()
        app.toggle_theme()
        toggled_theme = app.get_html_theme()

        assert initial_theme != toggled_theme
        assert toggled_theme in ("dark", "light")
        page.close()

