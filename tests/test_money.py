from decimal import Decimal
import unittest

from taxbot.errors import MoneyError
from taxbot.money import Money


class MoneyTests(unittest.TestCase):
    def test_decimal_round_trip_is_exact(self) -> None:
        money = Money.from_decimal("1234.50", "pkr")
        self.assertEqual(money.minor, 123450)
        self.assertEqual(money.currency, "PKR")
        self.assertEqual(money.as_decimal_string(), "1234.50")

    def test_float_and_excess_precision_are_rejected(self) -> None:
        with self.assertRaises(MoneyError):
            Money.from_decimal(0.1, "PKR")
        with self.assertRaises(MoneyError):
            Money.from_decimal(Decimal("1.001"), "PKR")

    def test_negative_and_unknown_currency_are_rejected(self) -> None:
        with self.assertRaises(MoneyError):
            Money.from_decimal("-1", "PKR")
        with self.assertRaises(MoneyError):
            Money.from_decimal("1", "XYZ")


if __name__ == "__main__":
    unittest.main()
