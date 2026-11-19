from datetime import datetime
import json
from pathlib import Path
import sys

from src.models import AppConfig, ClientInfo, SenderInfo


def get_base_dir() -> Path:
    """Resolve directory for config files (supports both script and PyInstaller EXE)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class ConfigRepository:
    def __init__(
        self,
        config_path: Path | None = None,
        example_path: Path | None = None,
    ) -> None:
        base_dir = get_base_dir()
        self.config_path = config_path or (base_dir / "config.json")
        self.example_path = example_path or (base_dir / "config.example.json")

    def load(self) -> AppConfig:
        source = self.config_path if self.config_path.exists() else self.example_path
        if not source.exists():
            return AppConfig(year=datetime.now().year, last_number=0)

        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppConfig(year=datetime.now().year, last_number=0)

        sender_data = raw.get("sender", {})
        client_data = raw.get("client", {})
        seq_data = raw.get("sequence", {})

        current_year = datetime.now().year
        stored_year = int(seq_data.get("year", current_year))
        last_number = int(seq_data.get("last_number", 0))

        return AppConfig(
            sender=SenderInfo(
                name=sender_data.get("name", ""),
                street=sender_data.get("street", ""),
                city=sender_data.get("city", ""),
                bank=sender_data.get("bank", ""),
                iban=sender_data.get("iban", ""),
                tax_id=sender_data.get("tax_id", ""),
            ),
            client=ClientInfo(
                address_lines=list(client_data.get("address_lines", []))
            ),
            year=current_year if stored_year != current_year else stored_year,
            last_number=last_number,
        )

    def save(self, config: AppConfig) -> None:
        payload = {
            "sender": {
                "name": config.sender.name,
                "street": config.sender.street,
                "city": config.sender.city,
                "bank": config.sender.bank,
                "iban": config.sender.iban,
                "tax_id": config.sender.tax_id,
            },
            "client": {
                "address_lines": config.client.address_lines,
            },
            "sequence": {
                "year": config.year,
                "last_number": config.last_number,
            },
        }
        self.config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
