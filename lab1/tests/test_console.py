"""
Unit-тесты для модуля console.py.
"""

import io
from unittest.mock import patch
import pytest

from ticket_generator.console import StreamConsoleIO, WindowsConsoleIO


class TestStreamConsoleIO:
    def test_startup_hint(self):
        out = io.StringIO()
        console = StreamConsoleIO(stdout=out)
        console.show_startup_hint()
        assert "Для выхода нажмите ESC." in out.getvalue()

    def test_valid_input_with_trimming(self):
        in_stream = io.StringIO("   Иванов   \n")
        out_stream = io.StringIO()
        console = StreamConsoleIO(stdin=in_stream, stdout=out_stream)

        res = console.read_name("Last name: ")
        assert res == "Иванов"
        assert "Last name: " in out_stream.getvalue()

    def test_empty_string_reprompts(self):
        # Два пустых ввода (Enter), затем пробелы, затем валидное имя
        in_stream = io.StringIO("\n   \n   \nПетров\n")
        out_stream = io.StringIO()
        console = StreamConsoleIO(stdin=in_stream, stdout=out_stream)

        res = console.read_name("Last name: ")
        assert res == "Петров"
        # Проверяем, что запрос "Last name: " повторялся 4 раза
        assert out_stream.getvalue().count("Last name: ") == 4

    def test_esc_marker_returns_none(self):
        in_stream = io.StringIO("ESC\n")
        console = StreamConsoleIO(stdin=in_stream, stdout=io.StringIO())
        assert console.read_name("Last name: ") is None

    def test_esc_code_returns_none(self):
        in_stream = io.StringIO("\x1b\n")
        console = StreamConsoleIO(stdin=in_stream, stdout=io.StringIO())
        assert console.read_name("Last name: ") is None

    def test_eof_returns_none(self):
        in_stream = io.StringIO("")  # Сразу EOF
        console = StreamConsoleIO(stdin=in_stream, stdout=io.StringIO())
        assert console.read_name("Last name: ") is None


class TestWindowsConsoleIO:
    def test_esc_returns_none(self):
        out_stream = io.StringIO()
        console = WindowsConsoleIO(stdout=out_stream)

        with patch("msvcrt.getwch", side_effect=["\x1b"]):
            res = console.read_name("Last name: ")
            assert res is None

    def test_normal_typing_and_enter(self):
        out_stream = io.StringIO()
        console = WindowsConsoleIO(stdout=out_stream)

        # Ввод: 'И', 'в', 'а', 'н', '\r'
        keys = ["И", "в", "а", "н", "\r"]
        with patch("msvcrt.getwch", side_effect=keys):
            res = console.read_name("First name: ")
            assert res == "Иван"

    def test_backspace_handling(self):
        out_stream = io.StringIO()
        console = WindowsConsoleIO(stdout=out_stream)

        # Ввод: 'И', 'в', 'а', 'п', Backspace (\x08), 'н', Enter (\r)
        keys = ["И", "в", "а", "п", "\x08", "н", "\r"]
        with patch("msvcrt.getwch", side_effect=keys):
            res = console.read_name("First name: ")
            assert res == "Иван"
            assert "\b \b" in out_stream.getvalue()

    def test_empty_enter_reprompts(self):
        out_stream = io.StringIO()
        console = WindowsConsoleIO(stdout=out_stream)

        # Сначала Enter на пустом буфере, потом пробелы + Enter, потом 'А', '\r'
        keys = ["\r", " ", "\r", "А", "\r"]
        with patch("msvcrt.getwch", side_effect=keys):
            res = console.read_name("Name: ")
            assert res == "А"
            assert out_stream.getvalue().count("Name: ") == 3

    def test_special_key_consumption(self):
        out_stream = io.StringIO()
        console = WindowsConsoleIO(stdout=out_stream)

        # Стрелка влево (префикс \xe0, скан-код \x4b), затем 'Б', '\r'
        keys = ["\xe0", "\x4b", "Б", "\r"]
        with patch("msvcrt.getwch", side_effect=keys):
            res = console.read_name("Name: ")
            assert res == "Б"
