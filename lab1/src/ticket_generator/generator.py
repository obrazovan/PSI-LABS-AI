"""
Генераторы номеров экзаменационных билетов.
"""

from __future__ import annotations
import random
from typing import Protocol, Sequence


class TicketGenerator(Protocol):
    """Интерфейс генератора номеров билетов."""

    def generate(self) -> int:
        """Сгенерировать номер билета."""
        ...


class RandomTicketGenerator:
    """
    Генератор случайных номеров билетов в заданном диапазоне.

    По умолчанию генерирует номера от 1 до 20 включительно согласно ТЗ.
    """

    def __init__(self, min_ticket: int = 1, max_ticket: int = 20, seed: int | None = None) -> None:
        if min_ticket > max_ticket:
            raise ValueError(f"min_ticket ({min_ticket}) не может быть больше max_ticket ({max_ticket})")
        if min_ticket <= 0:
            raise ValueError("min_ticket должен быть больше 0")

        self.min_ticket = min_ticket
        self.max_ticket = max_ticket
        self._rng = random.Random(seed)

    def generate(self) -> int:
        """Возвращает случайное число в диапазоне [min_ticket, max_ticket]."""
        return self._rng.randint(self.min_ticket, self.max_ticket)


class FixedTicketGenerator:
    """Генератор фиксированных или предопределенных номеров (удобен для тестов)."""

    def __init__(self, tickets: Sequence[int]) -> None:
        if not tickets:
            raise ValueError("Список билетов не может быть пустым")
        self._tickets = list(tickets)
        self._index = 0

    def generate(self) -> int:
        ticket = self._tickets[self._index % len(self._tickets)]
        self._index += 1
        return ticket
