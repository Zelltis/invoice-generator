from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class InvoiceItem:
    event_id: str
    date: str
    quantity: Decimal
    rate: Decimal

    @property
    def total(self) -> Decimal:
        return (self.quantity * self.rate).quantize(Decimal("0.01"))


@dataclass
class SenderInfo:
    name: str = "Max Mustermann"
    street: str = "Musterstraße 1"
    city: str = "52062 Aachen"
    bank: str = "Musterbank"
    iban: str = "DE00000000000000000000"
    tax_id: str = "123/456/7890"


@dataclass
class ClientInfo:
    address_lines: list[str] = field(
        default_factory=lambda: [
            "Musterkunde GmbH",
            "Beispielweg 10",
            "52062 Aachen",
        ]
    )


@dataclass
class AppConfig:
    sender: SenderInfo = field(default_factory=SenderInfo)
    client: ClientInfo = field(default_factory=ClientInfo)
    year: int = 2026
    last_number: int = 0
