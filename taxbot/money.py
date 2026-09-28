"""Exact-money primitives. Binary floating point is deliberately rejected."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import ClassVar

from .errors import MoneyError


@dataclass(frozen=True, slots=True)
class Money:
    minor: int
    currency: str

    SCALES: ClassVar[dict[str, int]] = {
        "PKR": 2,
        "USD": 2,
        "EUR": 2,
        "GBP": 2,
        "AED": 2,
        "SAR": 2,
    }

    def __post_init__(self) -> None:
        normalized = self.currency.upper()
        if normalized not in self.SCALES:
            raise MoneyError(f"Unsupported currency: {normalized}")
        if type(self.minor) is not int:
            raise MoneyError("Money minor units must be an integer")
        if self.minor < 0:
            raise MoneyError("Money amount must be non-negative; direction is separate")
        object.__setattr__(self, "currency", normalized)

    @classmethod
    def from_decimal(cls, amount: str | Decimal, currency: str) -> Money:
        if isinstance(amount, float):
            raise MoneyError("Binary floating point is not accepted")
        try:
            value = Decimal(amount)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise MoneyError("Invalid decimal amount") from exc
        if not value.is_finite() or value < 0:
            raise MoneyError("Amount must be finite and non-negative")
        normalized = currency.upper()
        if normalized not in cls.SCALES:
            raise MoneyError(f"Unsupported currency: {normalized}")
        scale = cls.SCALES[normalized]
        quantum = Decimal(1).scaleb(-scale)
        if value.quantize(quantum) != value:
            raise MoneyError(f"{normalized} supports at most {scale} decimal places")
        return cls(int(value.scaleb(scale)), normalized)

    @classmethod
    def from_minor(cls, minor: int, currency: str) -> Money:
        return cls(minor, currency)

    def as_decimal_string(self) -> str:
        scale = self.SCALES[self.currency]
        value = Decimal(self.minor).scaleb(-scale)
        return format(value, f".{scale}f")
