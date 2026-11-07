"""
Модели данных предметной области для генератора билетов с UI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence, Any


@dataclass(frozen=True)
class Student:
    """
    Модель студента.

    Attributes:
        group: Название учебной группы.
        last_name: Фамилия студента.
        first_name: Имя студента.
    """

    group: str
    last_name: str
    first_name: str

    def __post_init__(self) -> None:
        if not isinstance(self.group, str) or not self.group.strip():
            raise ValueError("Название группы не может быть пустым")
        if not isinstance(self.last_name, str) or not self.last_name.strip():
            raise ValueError("Фамилия не может быть пустой")
        if not isinstance(self.first_name, str) or not self.first_name.strip():
            raise ValueError("Имя не может быть пустым")

        # Так как dataclass frozen=True, нормализуем значения через object.__setattr__
        object.__setattr__(self, "group", self.group.strip())
        object.__setattr__(self, "last_name", self.last_name.strip())
        object.__setattr__(self, "first_name", self.first_name.strip())

    @property
    def full_name(self) -> str:
        """Представление в формате 'Фамилия Имя' для UI."""
        return f"{self.last_name} {self.first_name}"

    @property
    def identity_key(self) -> tuple[str, str, str]:
        """Уникальный ключ для идентификации студента (без учета регистра)."""
        return (self.group.lower(), self.last_name.lower(), self.first_name.lower())


@dataclass(frozen=True)
class Ticket:
    """
    Модель экзаменационного билета.

    Attributes:
        number: Номер билета (целое положительное число).
        questions: Кортеж формулировок вопросов билета (минимум 3 вопроса).
    """

    number: int
    questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.number, int) or isinstance(self.number, bool) or self.number <= 0:
            raise ValueError(f"Некорректный номер билета: {self.number}")
        if len(self.questions) < 3:
            raise ValueError(f"Билет №{self.number} содержит меньше 3 вопросов ({len(self.questions)})")


@dataclass
class ExamResult:
    """
    Результат назначения экзаменационного билета.

    Attributes:
        group: Учебная группа.
        last_name: Фамилия.
        first_name: Имя.
        ticket_number: Назначенный номер билета.
        timestamp: Дата и время назначения (YYYY-MM-DD HH:MM:SS).
        is_repeat: Флаг повторной генерации (True -> 'да', False -> 'нет').
    """

    group: str
    last_name: str
    first_name: str
    ticket_number: int
    is_repeat: bool
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self) -> None:
        self.group = self.group.strip()
        self.last_name = self.last_name.strip()
        self.first_name = self.first_name.strip()

    @property
    def repeat_str(self) -> str:
        """Строковое представление признака повтора ('да' или 'нет')."""
        return "да" if self.is_repeat else "нет"

    def to_row(self) -> list[Any]:
        """Возвращает строку таблицы для записи в results.xlsx."""
        return [
            self.group,
            self.last_name,
            self.first_name,
            self.ticket_number,
            self.timestamp,
            self.repeat_str,
        ]
