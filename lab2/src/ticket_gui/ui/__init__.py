"""
UI компоненты для приложения генерации билетов.
"""

from .main_window import MainWindow
from .presenters import TkAlertNotifier, TkFileLockHandler, TkResultPresenter
from .result_dialog import ResultDialog

__all__ = [
    "MainWindow",
    "ResultDialog",
    "TkAlertNotifier",
    "TkFileLockHandler",
    "TkResultPresenter",
]
