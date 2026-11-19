from datetime import datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from src.models import AppConfig, InvoiceItem


def format_decimal_de(value: Decimal) -> str:
    return f"{value:.2f}".replace(".", ",")


def generate_invoice_pdf(
    output_path: Path,
    billing_month: str,
    items: list[InvoiceItem],
    invoice_number: int,
    config: AppConfig,
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    font_regular = "Times-Roman"
    font_bold = "Times-Bold"

    # 1. Sender
    x_sender = 12 * cm
    y = height - 2.5 * cm
    pdf.setFont(font_regular, 10)
    pdf.drawString(x_sender, y, config.sender.name)
    pdf.drawString(x_sender, y - 0.5 * cm, config.sender.street)
    pdf.drawString(x_sender, y - 1.0 * cm, config.sender.city)

    # 2. Client
    x_receiver = 2 * cm
    y_receiver = height - 2.5 * cm
    pdf.setFont(font_bold, 11)
    for line in config.client.address_lines:
        pdf.drawString(x_receiver, y_receiver, line.strip())
        y_receiver -= 0.5 * cm

    # 3. Metadata
    y_meta = height - 6.0 * cm
    pdf.setFont(font_regular, 11)
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    invoice_code = f"RE-{now.year}-{invoice_number:03d}"

    pdf.drawRightString(width - 2 * cm, y_meta, f"Datum: {date_str}")
    pdf.drawRightString(width - 2 * cm, y_meta - 0.6 * cm, f"Rechnungs-Nr.: {invoice_code}")

    # 4. Title & Intro
    pdf.setFont(font_bold, 18)
    pdf.drawString(2 * cm, y_meta - 1.5 * cm, "Rechnung")

    y_text = y_meta - 3.0 * cm
    pdf.setFont(font_regular, 11)
    pdf.drawString(2 * cm, y_text, "Sehr geehrte Damen und Herren,")
    pdf.drawString(
        2 * cm,
        y_text - 0.8 * cm,
        "vereinbarungsgemäß lasse ich Ihnen diese Rechnung für die geleistete",
    )
    pdf.drawString(
        2 * cm,
        y_text - 1.3 * cm,
        f"Prüfungsaufsicht für den {billing_month} zukommen:",
    )

    # 5. Table Header
    col_x = [2 * cm, 5.7 * cm, 8.2 * cm, 10.0 * cm, 13.0 * cm, 17.0 * cm]
    y_table = y_text - 2.5 * cm
    row_height = 0.8 * cm

    pdf.setFont(font_bold, 10)
    pdf.setLineWidth(0.5)
    headers = ("Veranstaltungsnr.", "Datum", "Summe", "Honorar-Satz", "Honorarsumme")
    for idx, title in enumerate(headers):
        pdf.drawString(col_x[idx] + 0.1 * cm, y_table + 0.2 * cm, title)

    pdf.rect(2 * cm, y_table, 15 * cm, row_height, stroke=1, fill=0)
    for x in col_x[1:-1]:
        pdf.line(x, y_table, x, y_table + row_height)

    y_table -= row_height
    pdf.setFont(font_regular, 10)
    total_amount = Decimal("0.00")

    for item in items:
        row_sum = item.total
        total_amount += row_sum

        pdf.drawString(col_x[0] + 0.1 * cm, y_table + 0.2 * cm, item.event_id)
        pdf.drawString(col_x[1] + 0.1 * cm, y_table + 0.2 * cm, item.date)
        pdf.drawString(col_x[2] + 0.1 * cm, y_table + 0.2 * cm, format_decimal_de(item.quantity))
        pdf.drawString(
            col_x[3] + 0.1 * cm,
            y_table + 0.2 * cm,
            f"{format_decimal_de(item.rate)} €",
        )
        pdf.drawRightString(
            col_x[5] - 0.2 * cm,
            y_table + 0.2 * cm,
            f"{format_decimal_de(row_sum)} €",
        )

        pdf.rect(2 * cm, y_table, 15 * cm, row_height, stroke=1, fill=0)
        for x in col_x[1:-1]:
            pdf.line(x, y_table, x, y_table + row_height)

        y_table -= row_height
        if y_table < 4 * cm:
            pdf.showPage()
            y_table = height - 3 * cm
            pdf.setFont(font_regular, 10)

    # 6. Total & Footer
    y_table -= 0.5 * cm
    pdf.setFont(font_bold, 12)
    pdf.drawRightString(
        col_x[5],
        y_table,
        f"Rechnungsbetrag: {format_decimal_de(total_amount)} €",
    )
    pdf.line(col_x[5] - 5 * cm, y_table - 0.1 * cm, col_x[5], y_table - 0.1 * cm)

    y_footer = y_table - 2.5 * cm
    if y_footer < 3 * cm:
        pdf.showPage()
        y_footer = height - 4 * cm

    pdf.setFont(font_regular, 10)
    pdf.drawString(
        2 * cm,
        y_footer,
        "In dieser Rechnung ist gemäß § 19 (1) UStG (Kleinunternehmer)",
    )
    pdf.drawString(2 * cm, y_footer - 0.5 * cm, "keine Umsatzsteuer enthalten.")
    pdf.drawString(
        2 * cm,
        y_footer - 1.5 * cm,
        "Bitte überweisen Sie den Rechnungsbetrag ohne Abzug bis zum",
    )
    pdf.drawString(
        2 * cm,
        y_footer - 2.0 * cm,
        "nächstmöglichen Zeitpunkt auf das unten genannte Konto.",
    )
    pdf.drawString(2 * cm, y_footer - 3.5 * cm, "Freundliche Grüße,")
    pdf.drawString(2 * cm, y_footer - 4.5 * cm, config.sender.name)

    y_bottom = 2 * cm
    pdf.setFont(font_bold, 10)
    pdf.drawString(2 * cm, y_bottom + 0.5 * cm, f"Bank: {config.sender.bank}")
    pdf.drawString(2 * cm, y_bottom, f"IBAN: {config.sender.iban}")
    pdf.drawString(12 * cm, y_bottom, f"Steuernummer: {config.sender.tax_id}")

    pdf.save()
