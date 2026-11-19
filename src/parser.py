import re
from dataclasses import dataclass
from decimal import Decimal

GERMAN_MONTHS: tuple[str, ...] = (
    "",
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)

EXAM_RATES: dict[str, Decimal] = {
    "LID": Decimal("25.00"),
    "DTZ": Decimal("80.00"),
}


@dataclass(frozen=True)
class ParsedEmailSnippet:
    event_id: str = ""
    date_str: str = ""
    billing_month: str = ""
    rate: Decimal | None = None


def parse_email_snippet(text: str) -> ParsedEmailSnippet:
    cleaned = text.strip()
    if not cleaned:
        return ParsedEmailSnippet()

    date_str = ""
    billing_month = ""
    date_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", cleaned)
    if date_match:
        day, month, year = date_match.groups()
        date_str = f"{day}.{month}.{year}"
        month_idx = int(month)
        if 1 <= month_idx <= 12:
            billing_month = f"{GERMAN_MONTHS[month_idx]} {year}"

    event_id = ""
    rate: Decimal | None = None
    upper_text = cleaned.upper()

    for exam_type, default_rate in EXAM_RATES.items():
        if exam_type in upper_text:
            rate = default_rate
            id_match = re.search(rf"({exam_type}[\w-]+)", cleaned, re.IGNORECASE)
            if id_match:
                event_id = id_match.group(1)
            break

    if not event_id:
        bracket_match = re.search(r"\((\d+)\)", cleaned)
        if bracket_match:
            event_id = bracket_match.group(1)

    return ParsedEmailSnippet(
        event_id=event_id,
        date_str=date_str,
        billing_month=billing_month,
        rate=rate,
    )
