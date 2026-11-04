"""
Unit-тесты для модуля generator.py.
"""

import pytest
from ticket_generator.generator import RandomTicketGenerator, FixedTicketGenerator


class TestRandomTicketGenerator:
    def test_default_range_is_one_to_twenty(self):
        generator = RandomTicketGenerator()
        assert generator.min_ticket == 1
        assert generator.max_ticket == 20

        generated_numbers = {generator.generate() for _ in range(500)}

        # Все числа должны строго лежать в диапазоне [1, 20]
        assert all(1 <= num <= 20 for num in generated_numbers)
        # В выборке из 500 запусков должны встретиться все или почти все билеты от 1 до 20
        assert len(generated_numbers) >= 18
        assert 1 in generated_numbers
        assert 20 in generated_numbers

    def test_custom_range(self):
        generator = RandomTicketGenerator(min_ticket=5, max_ticket=10)
        for _ in range(100):
            num = generator.generate()
            assert 5 <= num <= 10

    def test_invalid_parameters_raise_error(self):
        with pytest.raises(ValueError, match="не может быть больше"):
            RandomTicketGenerator(min_ticket=20, max_ticket=10)

        with pytest.raises(ValueError, match="больше 0"):
            RandomTicketGenerator(min_ticket=0, max_ticket=20)

    def test_reproducible_with_seed(self):
        gen1 = RandomTicketGenerator(seed=42)
        gen2 = RandomTicketGenerator(seed=42)

        sequence1 = [gen1.generate() for _ in range(20)]
        sequence2 = [gen2.generate() for _ in range(20)]

        assert sequence1 == sequence2


class TestFixedTicketGenerator:
    def test_returns_sequence_in_loop(self):
        generator = FixedTicketGenerator([7, 14, 21])
        assert generator.generate() == 7
        assert generator.generate() == 14
        assert generator.generate() == 21
        assert generator.generate() == 7

    def test_empty_sequence_raises_error(self):
        with pytest.raises(ValueError, match="не может быть пустым"):
            FixedTicketGenerator([])
