"""
Модели данных для приложения генератора экзаменационных билетов.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StudentRecord:
    """
    Запись о студенте и выданном экзаменационном билете.

    Attributes:
        last_name: Фамилия студента (строка, пробелы по краям удаляются).
        first_name: Имя студента (строка, пробелы по краям удаляются).
        ticket_number: Номер экзаменационного билета (1..20).
        timestamp: Дата и время формирования записи (строка формата 'YYYY-MM-DD HH:MM:SS').
    """

    last_name: str
    first_name: str
    ticket_number: int
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self) -> None:
        """Валидация и нормализация полей записи."""
        if not isinstance(self.last_name, str):
            raise TypeError("Фамилия должна быть строкой")
        if not isinstance(self.first_name, str):
            raise TypeError("Имя должно быть строкой")

        self.last_name = self.last_name.strip(" \t\r\n\ufeff")
        self.first_name = self.first_name.strip(" \t\r\n\ufeff")

        if not self.last_name:
            raise ValueError("Фамилия не может быть пустой")
        if not self.first_name:
            raise ValueError("Имя не может быть пустым")

        if not isinstance(self.ticket_number, int) or isinstance(self.ticket_number, bool):
            raise TypeError("Номер билета должен быть целым числом")
        if self.ticket_number <= 0:
            raise ValueError("Номер билета должен быть положительным числом")

    def to_row(self) -> list[Any]:
        """Возвращает строку таблицы для записи в Excel."""
        return [self.last_name, self.first_name, self.ticket_number, self.timestamp]
