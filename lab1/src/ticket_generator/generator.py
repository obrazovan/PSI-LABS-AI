"""
Генераторы номеров экзаменационных билетов.
"""

from __future__ import annotations

import random
from typing import Sequence

from .ports import TicketGenerator


class RandomTicketGenerator:
    """
    Генератор случайных номеров билетов в заданном диапазоне.

    По умолчанию генерирует номера от 1 до 20 включительно согласно ТЗ.
    """

    def __init__(self, min_ticket: int = 1, max_ticket: int = 20, seed: int | None = None) -> None:
        if (
            not isinstance(min_ticket, int)
            or isinstance(min_ticket, bool)
            or not isinstance(max_ticket, int)
            or isinstance(max_ticket, bool)
        ):
            raise TypeError("Границы диапазона билетов должны быть целыми числами")
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
        ticket_list = list(tickets)
        if not ticket_list:
            raise ValueError("Список билетов не может быть пустым")
        for ticket in ticket_list:
            if not isinstance(ticket, int) or isinstance(ticket, bool):
                raise TypeError("Номера билетов должны быть целыми числами")
            if ticket <= 0:
                raise ValueError("Номер билета должен быть больше 0")

        self._tickets = ticket_list
        self._index = 0

    def generate(self) -> int:
        """Возвращает следующий предопределенный положительный номер билета."""
        ticket = self._tickets[self._index % len(self._tickets)]
        self._index += 1
        return ticket


__all__ = [
    "TicketGenerator",
    "RandomTicketGenerator",
    "FixedTicketGenerator",
]
