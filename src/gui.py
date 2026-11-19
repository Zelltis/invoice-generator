from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.config import ConfigRepository
from src.models import ClientInfo, InvoiceItem, SenderInfo
from src.parser import parse_email_snippet
from src.pdf_generator import generate_invoice_pdf


class InvoiceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Rechnungs-Generator")
        self.root.geometry("760x780")

        self.repo = ConfigRepository()
        self.is_first_run = not self.repo.config_path.exists()
        self.config = self.repo.load()
        self.items: list[InvoiceItem] = []

        self._build_ui()

        if self.is_first_run:
            self.notebook.select(self.tab_settings)

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_invoice = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_invoice, text="  1. Rechnung erstellen  ")
        self.notebook.add(self.tab_settings, text="  2. Stammdaten & Empfänger  ")

        self._build_invoice_tab()
        self._build_settings_tab()

    # ==========================================================
    # TAB 1: RECHNUNG ERSTELLEN
    # ==========================================================
    def _build_invoice_tab(self) -> None:
        # Top Bar
        frame_top = ttk.LabelFrame(self.tab_invoice, text="Rechnungskopf")
        frame_top.pack(fill="x", padx=8, pady=6)

        ttk.Label(frame_top, text="Leistungsmonat (z. B. Januar 2026):").pack(
            side="left", padx=5, pady=6
        )
        self.entry_month = ttk.Entry(frame_top, width=28)
        self.entry_month.pack(side="left", padx=5, pady=6)

        ttk.Button(
            frame_top,
            text="Stammdaten ändern →",
            command=self.open_settings_tab,
        ).pack(side="right", padx=6, pady=6)

        # Schnell-Import
        frame_import = ttk.LabelFrame(self.tab_invoice, text="Schnell-Import aus E-Mail")
        frame_import.pack(fill="x", padx=8, pady=6)

        ttk.Label(
            frame_import,
            text="E-Mail-Auszug einfügen (z. B. '...am 8.1.2026 findet LID-102... statt'):",
        ).pack(anchor="w", padx=5)

        self.text_import = tk.Text(frame_import, height=3, width=60)
        self.text_import.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            frame_import,
            text="Daten aus Text übernehmen",
            command=self.parse_input_text,
        ).pack(anchor="e", padx=5, pady=4)

        # Positionen eingeben
        frame_items = ttk.LabelFrame(self.tab_invoice, text="Position hinzufügen")
        frame_items.pack(fill="x", padx=8, pady=6)

        ttk.Label(frame_items, text="V-Nr.").grid(row=0, column=0, padx=4)
        self.entry_vnr = ttk.Entry(frame_items, width=16)
        self.entry_vnr.grid(row=1, column=0, padx=4, pady=4)

        ttk.Label(frame_items, text="Datum").grid(row=0, column=1, padx=4)
        self.entry_date = ttk.Entry(frame_items, width=14)
        self.entry_date.grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(frame_items, text="Menge / Std.").grid(row=0, column=2, padx=4)
        self.entry_qty = ttk.Entry(frame_items, width=12)
        self.entry_qty.grid(row=1, column=2, padx=4, pady=4)

        ttk.Label(frame_items, text="Satz (€)").grid(row=0, column=3, padx=4)
        self.entry_rate = ttk.Entry(frame_items, width=12)
        self.entry_rate.grid(row=1, column=3, padx=4, pady=4)

        ttk.Button(frame_items, text="Hinzufügen", command=self.add_item).grid(
            row=1, column=4, padx=10, pady=4
        )

        # Tabelle
        cols = ("vnr", "date", "qty", "rate", "total")
        self.tree = ttk.Treeview(self.tab_invoice, columns=cols, show="headings", height=8)
        for col, title, width in [
            ("vnr", "V-Nr.", 140),
            ("date", "Datum", 100),
            ("qty", "Menge", 80),
            ("rate", "Satz (€)", 80),
            ("total", "Gesamt (€)", 90),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width)

        self.tree.pack(fill="both", expand=True, padx=8, pady=6)

        # Tabellen-Aktionen
        frame_list_actions = ttk.Frame(self.tab_invoice)
        frame_list_actions.pack(fill="x", padx=8, pady=4)

        ttk.Button(
            frame_list_actions,
            text="Zeile in Eingabe kopieren",
            command=self.copy_to_input,
        ).pack(side="left")
        ttk.Button(
            frame_list_actions,
            text="Markierte Zeile löschen",
            command=self.delete_item,
        ).pack(side="right")

        # Footer
        frame_actions = ttk.Frame(self.tab_invoice)
        frame_actions.pack(fill="x", padx=8, pady=12)

        ttk.Label(frame_actions, text="Nächste Rechnungs-Nr.:").pack(side="left")
        self.entry_next_num = ttk.Entry(frame_actions, width=6)
        self.entry_next_num.pack(side="left", padx=5)
        self.entry_next_num.insert(0, str(self.config.last_number + 1))

        ttk.Button(frame_actions, text="PDF erstellen", command=self.generate).pack(
            side="right"
        )

    # ==========================================================
    # TAB 2: STAMMDATEN & EMPFÄNGER (EDITIEREN / NEU EINTRAGEN)
    # ==========================================================
    def _build_settings_tab(self) -> None:
        info_text = (
            "Hier kannst du deine eigenen Absenderdaten, Bankverbindung sowie die "
            "Empfängeradresse jederzeit bearbeiten oder komplett neu eintragen."
        )
        ttk.Label(
            self.tab_settings,
            text=info_text,
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        frame_sender = ttk.LabelFrame(
            self.tab_settings, text="Eigene Stammdaten (Absender)", padding=10
        )
        frame_sender.pack(fill="x", pady=6)
        frame_sender.columnconfigure(1, weight=1)

        fields = [
            ("Name:", self.config.sender.name),
            ("Straße & Hausnr.:", self.config.sender.street),
            ("PLZ & Ort:", self.config.sender.city),
            ("Bank:", self.config.sender.bank),
            ("IBAN:", self.config.sender.iban),
            ("Steuernummer:", self.config.sender.tax_id),
        ]
        self.settings_entries: dict[str, ttk.Entry] = {}

        for row, (label, val) in enumerate(fields):
            ttk.Label(frame_sender, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame_sender)
            entry.insert(0, val)
            entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))
            self.settings_entries[label] = entry

        frame_client = ttk.LabelFrame(
            self.tab_settings, text="Empfängeradresse (Rechnungsempfänger)", padding=10
        )
        frame_client.pack(fill="both", expand=True, pady=6)

        self.client_text = tk.Text(frame_client, height=6)
        self.client_text.insert("1.0", "\n".join(self.config.client.address_lines))
        self.client_text.pack(fill="both", expand=True)

        frame_settings_btns = ttk.Frame(self.tab_settings)
        frame_settings_btns.pack(fill="x", pady=(10, 0))

        ttk.Button(
            frame_settings_btns,
            text="Felder leeren (Neu eintragen)",
            command=self.clear_settings_fields,
        ).pack(side="left")

        ttk.Button(
            frame_settings_btns,
            text="Stammdaten speichern & übernehmen",
            command=self.save_settings_from_tab,
        ).pack(side="right")

    def open_settings_tab(self) -> None:
        self._load_settings_into_fields()
        self.notebook.select(self.tab_settings)

    def _load_settings_into_fields(self) -> None:
        mapping = {
            "Name:": self.config.sender.name,
            "Straße & Hausnr.:": self.config.sender.street,
            "PLZ & Ort:": self.config.sender.city,
            "Bank:": self.config.sender.bank,
            "IBAN:": self.config.sender.iban,
            "Steuernummer:": self.config.sender.tax_id,
        }
        for label, value in mapping.items():
            entry = self.settings_entries[label]
            entry.delete(0, "end")
            entry.insert(0, value)

        self.client_text.delete("1.0", "end")
        self.client_text.insert("1.0", "\n".join(self.config.client.address_lines))

    def clear_settings_fields(self) -> None:
        for entry in self.settings_entries.values():
            entry.delete(0, "end")
        self.client_text.delete("1.0", "end")
        self.settings_entries["Name:"].focus()

    def save_settings_from_tab(self) -> None:
        name = self.settings_entries["Name:"].get().strip()
        if not name:
            messagebox.showwarning(
                "Fehlende Angabe", "Bitte mindestens deinen Namen als Absender eintragen."
            )
            return

        self.config.sender = SenderInfo(
            name=name,
            street=self.settings_entries["Straße & Hausnr.:"].get().strip(),
            city=self.settings_entries["PLZ & Ort:"].get().strip(),
            bank=self.settings_entries["Bank:"].get().strip(),
            iban=self.settings_entries["IBAN:"].get().strip(),
            tax_id=self.settings_entries["Steuernummer:"].get().strip(),
        )
        raw_lines = self.client_text.get("1.0", "end").splitlines()
        self.config.client = ClientInfo(
            address_lines=[line.strip() for line in raw_lines if line.strip()]
        )
        self.repo.save(self.config)

        messagebox.showinfo(
            "Gespeichert",
            "Deine Stammdaten wurden gespeichert und werden ab sofort für alle Rechnungen genutzt.",
        )
        if self.is_first_run:
            self.is_first_run = False
            self.notebook.select(self.tab_invoice)

    # ==========================================================
    # LOGIK RECHNUNGSPOSITIONEN & PDF
    # ==========================================================
    def parse_input_text(self) -> None:
        parsed = parse_email_snippet(self.text_import.get("1.0", "end"))
        if parsed.billing_month:
            self.entry_month.delete(0, "end")
            self.entry_month.insert(0, parsed.billing_month)

        self.entry_vnr.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_rate.delete(0, "end")

        if parsed.event_id:
            self.entry_vnr.insert(0, parsed.event_id)
        if parsed.date_str:
            self.entry_date.insert(0, parsed.date_str)
        if parsed.rate is not None:
            self.entry_rate.insert(0, f"{parsed.rate:.2f}")

        self.entry_qty.focus()
        self.entry_qty.select_range(0, "end")

    def add_item(self) -> None:
        vnr = self.entry_vnr.get().strip()
        date_val = self.entry_date.get().strip()
        raw_qty = self.entry_qty.get().strip().replace(",", ".")
        raw_rate = self.entry_rate.get().strip().replace(",", ".")

        if not (vnr and date_val and raw_qty and raw_rate):
            return

        try:
            item = InvoiceItem(
                event_id=vnr,
                date=date_val,
                quantity=Decimal(raw_qty),
                rate=Decimal(raw_rate),
            )
        except InvalidOperation:
            messagebox.showerror("Fehler", "Bitte gültige Zahlen für Menge und Satz eingeben.")
            return

        self.items.append(item)
        self.tree.insert(
            "",
            "end",
            values=(
                item.event_id,
                item.date,
                f"{item.quantity:.2f}",
                f"{item.rate:.2f}",
                f"{item.total:.2f}",
            ),
        )
        self.entry_vnr.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_qty.delete(0, "end")
        self.entry_vnr.focus()

    def delete_item(self) -> None:
        selected = self.tree.selection()
        if selected:
            idx = self.tree.index(selected[0])
            del self.items[idx]
            self.tree.delete(selected[0])

    def copy_to_input(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Bitte zuerst eine Zeile auswählen.")
            return

        values = self.tree.item(selected[0])["values"]
        for entry, val in zip(
            (self.entry_vnr, self.entry_date, self.entry_qty, self.entry_rate),
            values[:4],
            strict=False,
        ):
            entry.delete(0, "end")
            entry.insert(0, str(val))

    def generate(self) -> None:
        month = self.entry_month.get().strip()
        if not month or not self.items:
            messagebox.showwarning(
                "Fehlende Daten", "Bitte Leistungsmonat und mindestens eine Position angeben."
            )
            return

        try:
            invoice_num = int(self.entry_next_num.get())
        except ValueError:
            messagebox.showerror("Fehler", "Rechnungsnummer muss eine ganze Zahl sein.")
            return

        clean_month = month.replace(" ", "_")
        default_name = f"Rechnung_RE-{datetime.now().year}-{invoice_num:03d}_{clean_month}.pdf"
        selected_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF-Dokument", "*.pdf")],
        )

        if not selected_path:
            return

        try:
            generate_invoice_pdf(
                output_path=Path(selected_path),
                billing_month=month,
                items=self.items,
                invoice_number=invoice_num,
                config=self.config,
            )
            self.config.last_number = invoice_num
            self.config.year = datetime.now().year
            self.repo.save(self.config)

            messagebox.showinfo("Erfolg", f"Rechnung Nr. {invoice_num} wurde gespeichert.")
            self.entry_next_num.delete(0, "end")
            self.entry_next_num.insert(0, str(invoice_num + 1))
        except Exception as exc:
            messagebox.showerror("Fehler", f"PDF konnte nicht erstellt werden:\n{exc}")
