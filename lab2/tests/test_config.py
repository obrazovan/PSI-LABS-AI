"""
Тесты конфигурационного модуля AppConfig.
"""

import os
from pathlib import Path
from unittest.mock import patch
import pytest

from ticket_gui.config import AppConfig


class TestAppConfig:
    def test_default_config(self):
        config = AppConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.log_level == "INFO"
        assert config.auto_browser is False
        assert config.students_path == Path("students.xlsx")
        assert config.tickets_path == Path("tickets.docx")
        assert config.results_path == Path("results.xlsx")

    def test_from_env_variables(self, tmp_path: Path):
        env = {
            "APP_HOST": "0.0.0.0",
            "APP_PORT": "9090",
            "APP_LOG_LEVEL": "DEBUG",
            "APP_AUTO_BROWSER": "true",
            "APP_STUDENTS_FILE": str(tmp_path / "custom_students.xlsx"),
            "APP_TICKETS_FILE": str(tmp_path / "custom_tickets.docx"),
            "APP_RESULTS_FILE": str(tmp_path / "custom_results.xlsx"),
        }
        with patch.dict(os.environ, env, clear=False):
            config = AppConfig.from_env_or_args(base_dir=tmp_path)
            assert config.host == "0.0.0.0"
            assert config.port == 9090
            assert config.log_level == "DEBUG"
            assert config.auto_browser is True
            assert config.students_path == (tmp_path / "custom_students.xlsx").resolve()
            assert config.tickets_path == (tmp_path / "custom_tickets.docx").resolve()
            assert config.results_path == (tmp_path / "custom_results.xlsx").resolve()

    def test_cli_args_override_env(self, tmp_path: Path):
        class MockArgs:
            host = "192.168.1.100"
            port = 8888
            students = str(tmp_path / "cli_students.xlsx")
            tickets = str(tmp_path / "cli_tickets.docx")
            results = str(tmp_path / "cli_results.xlsx")
            log_level = "WARNING"
            browser = True

        env = {"APP_HOST": "0.0.0.0", "APP_PORT": "9090"}
        with patch.dict(os.environ, env, clear=False):
            config = AppConfig.from_env_or_args(args=MockArgs(), base_dir=tmp_path)
            assert config.host == "192.168.1.100"
            assert config.port == 8888
            assert config.log_level == "WARNING"
            assert config.auto_browser is True
            assert config.students_path == (tmp_path / "cli_students.xlsx").resolve()
