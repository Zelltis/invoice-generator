from decimal import Decimal
from pathlib import Path

from src.config import ConfigRepository
from src.models import AppConfig, ClientInfo, InvoiceItem, SenderInfo
from src.parser import parse_email_snippet


def test_parse_lid_snippet() -> None:
    snippet = "Hallo, am 8.1.2026 findet LID-2026-04 in Raum 12 statt."
    result = parse_email_snippet(snippet)

    assert result.date_str == "8.1.2026"
    assert result.billing_month == "Januar 2026"
    assert result.event_id == "LID-2026-04"
    assert result.rate == Decimal("25.00")


def test_parse_dtz_snippet() -> None:
    snippet = "Terminbestätigung DTZ_991 am 14.11.2026"
    result = parse_email_snippet(snippet)

    assert result.date_str == "14.11.2026"
    assert result.billing_month == "November 2026"
    assert result.event_id == "DTZ_991"
    assert result.rate == Decimal("80.00")


def test_parse_fallback_bracket_id() -> None:
    snippet = "Prüfung (4711) am 03.05.2026"
    result = parse_email_snippet(snippet)

    assert result.event_id == "4711"
    assert result.rate is None


def test_invoice_item_total_precision() -> None:
    item = InvoiceItem(
        event_id="LID-01",
        date="08.01.2026",
        quantity=Decimal("3.5"),
        rate=Decimal("25.00"),
    )
    assert item.total == Decimal("87.50")


def test_config_repository_roundtrip(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.json"
    repo = ConfigRepository(config_path=cfg_file, example_path=tmp_path / "missing.json")

    cfg = AppConfig(
        sender=SenderInfo(name="Test User", iban="DE1234"),
        client=ClientInfo(address_lines=["Kunde A", "Aachen"]),
        year=2026,
        last_number=7,
    )
    repo.save(cfg)

    loaded = repo.load()
    assert loaded.sender.name == "Test User"
    assert loaded.sender.iban == "DE1234"
    assert loaded.client.address_lines == ["Kunde A", "Aachen"]
    assert loaded.last_number == 7
