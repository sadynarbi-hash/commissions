from __future__ import annotations
"""
Génération du récapitulatif mensuel des commissions NMA — pour les RH.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

VERT_FONCE = colors.HexColor("#1B5E20")
VERT_CLAIR = colors.HexColor("#E8F5E9")
VERT_MID   = colors.HexColor("#388E3C")
OR         = colors.HexColor("#F9A825")
GRIS_CLAIR = colors.HexColor("#F5F5F5")
GRIS_MED   = colors.HexColor("#E0E0E0")

import os as _os
LOGO_PATH = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..', 'frontend', 'public', 'logo-nma.png'))

ROLE_LABELS = {
    "RCR":          "RCR",
    "SV":           "SV",
    "COMMERCIAL":   "Commercial",
    "ATC_BV":       "ATC BV",
    "ATC_FARINE":   "ATC Farine",
    "RCE":          "RCE",
    "RESP_TECH_FP": "Resp. Tech FP",
    "RESP_TECH_BV": "Resp. Tech BV",
    "DV":           "DV",
    "DCMT":         "DCMT",
}

MOIS_FR = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre",
}


def _fcfa(v: float) -> str:
    if v == 0:
        return "-"
    return f"{int(round(v)):,}".replace(",", " ")


def generate_recap_pdf(rows: list[dict], periode: str) -> bytes:
    """
    rows : liste de dicts avec les clés :
        nom, prenom, role, region, prime_suivi_fixe,
        prime_quantitative, prime_qualitative,
        commission_nouvelles_affaires, total
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.2*cm, bottomMargin=1.5*cm,
    )

    mois_annee = f"{MOIS_FR.get(periode[5:], '')} {periode[:4]}" if periode else ""

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", fontSize=8, leading=10)
    cell_bold  = ParagraphStyle("cellb", fontSize=8, fontName="Helvetica-Bold", leading=10)
    note_style = ParagraphStyle("note", fontSize=7, textColor=colors.grey,
                                alignment=TA_CENTER)

    elements = []

    # ── En-tête ────────────────────────────────────────────────────
    import os
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=3*cm, height=1.7*cm)
        logo.hAlign = "LEFT"
    else:
        logo = Spacer(3*cm, 1.7*cm)

    header_data = [[
        logo,
        [
            Paragraph("NOUVELLE MINOTERIE AFRICAINE", ParagraphStyle(
                "h1", fontSize=13, fontName="Helvetica-Bold",
                textColor=VERT_FONCE, alignment=TA_CENTER)),
            Paragraph("ÉTAT MENSUEL DES COMMISSIONS COMMERCIALES", ParagraphStyle(
                "h2", fontSize=10, fontName="Helvetica-Bold",
                textColor=OR, alignment=TA_CENTER)),
            Paragraph(f"Période : {mois_annee}", ParagraphStyle(
                "h3", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)),
        ],
        Paragraph(
            f"Édité le {datetime.now().strftime('%d/%m/%Y')}",
            ParagraphStyle("date", fontSize=8, textColor=colors.grey,
                           alignment=TA_RIGHT),
        ),
    ]]
    header_table = Table(header_data, colWidths=[3.5*cm, 18*cm, 4.5*cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=OR, spaceAfter=8))

    # ── Tableau principal ──────────────────────────────────────────
    headers = [
        "N°", "Nom & Prénom", "Rôle", "Zone",
        "Comm.\nfixe", "Comm.\nquantitative", "Comm.\nqualitative",
        "Comm.\nnouv. affaires", "TOTAL",
    ]
    col_w = [0.8*cm, 5.5*cm, 2.5*cm, 2.5*cm,
             2.5*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm]

    # Trier : par région puis par rôle
    role_order = ["RCR", "SV", "COMMERCIAL", "ATC_BV", "ATC_FARINE",
                  "RCE", "RESP_TECH_FP", "RESP_TECH_BV", "DV", "DCMT"]
    rows_sorted = sorted(
        rows,
        key=lambda r: (r.get("region", ""), role_order.index(r["role"]) if r["role"] in role_order else 99),
    )

    data = [headers]
    totaux = {"fixe": 0, "quant": 0, "qual": 0, "naff": 0, "total": 0}
    region_subtotals: dict[str, float] = {}
    current_region = None
    region_start_row = 1

    style_cmds = [
        # En-tête
        ("BACKGROUND",  (0, 0), (-1, 0), VERT_FONCE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",      (0, 0), (-1, 0), "MIDDLE"),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("VALIGN",      (0, 1), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLAIR]),
        ("ALIGN",       (4, 1), (-1, -1), "RIGHT"),
        ("PADDING",     (0, 0), (-1, -1), 4),
    ]

    for i, r in enumerate(rows_sorted, start=1):
        # Rupture de région → ligne de sous-total
        if r.get("region") != current_region and current_region is not None:
            sub = region_subtotals.get(current_region, 0)
            row_idx = len(data)
            data.append([
                "", Paragraph(f"Sous-total {current_region}", cell_bold),
                "", "", "", "", "", "",
                Paragraph(f"{int(sub):,}".replace(",", " "), cell_bold),
            ])
            style_cmds += [
                ("BACKGROUND", (0, row_idx), (-1, row_idx), VERT_CLAIR),
                ("SPAN",       (1, row_idx), (7, row_idx)),
            ]

        current_region = r.get("region", "")
        region_subtotals[current_region] = region_subtotals.get(current_region, 0) + r["total"]

        fixe  = r.get("prime_suivi_fixe", 0) or 0
        quant = r.get("prime_quantitative", 0) or 0
        qual  = r.get("prime_qualitative", 0) or 0
        naff  = r.get("commission_nouvelles_affaires", 0) or 0
        tot   = r.get("total", 0) or 0

        totaux["fixe"]  += fixe
        totaux["quant"] += quant
        totaux["qual"]  += qual
        totaux["naff"]  += naff
        totaux["total"] += tot

        data.append([
            str(i),
            Paragraph(f"{r['prenom']} {r['nom']}", cell_style),
            ROLE_LABELS.get(r["role"], r["role"]),
            r.get("region", "-"),
            _fcfa(fixe),
            _fcfa(quant),
            _fcfa(qual),
            _fcfa(naff),
            Paragraph(f"<b>{_fcfa(tot)}</b>", cell_bold),
        ])

    # Dernier sous-total de région
    if current_region:
        sub = region_subtotals.get(current_region, 0)
        row_idx = len(data)
        data.append([
            "", Paragraph(f"Sous-total {current_region}", cell_bold),
            "", "", "", "", "", "",
            Paragraph(f"{int(sub):,}".replace(",", " "), cell_bold),
        ])
        style_cmds += [
            ("BACKGROUND", (0, row_idx), (-1, row_idx), VERT_CLAIR),
            ("SPAN",       (1, row_idx), (7, row_idx)),
        ]

    # Ligne total général
    total_row = len(data)
    data.append([
        "",
        Paragraph("TOTAL GÉNÉRAL À DÉCAISSER", ParagraphStyle(
            "tot", fontSize=9, fontName="Helvetica-Bold", textColor=colors.white)),
        "", "",
        Paragraph(f"<b>{_fcfa(totaux['fixe'])}</b>",
                  ParagraphStyle("tf", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fcfa(totaux['quant'])}</b>",
                  ParagraphStyle("tq", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fcfa(totaux['qual'])}</b>",
                  ParagraphStyle("tql", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fcfa(totaux['naff'])}</b>",
                  ParagraphStyle("tn", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f"<b>{int(totaux['total']):,} FCFA</b>".replace(",", " "),
                  ParagraphStyle("tt", fontSize=10, fontName="Helvetica-Bold",
                                 textColor=OR, alignment=TA_RIGHT)),
    ])
    style_cmds += [
        ("BACKGROUND", (0, total_row), (-1, total_row), VERT_FONCE),
        ("SPAN",       (1, total_row), (3, total_row)),
        ("LINEABOVE",  (0, total_row), (-1, total_row), 2, OR),
        ("FONTSIZE",   (0, total_row), (-1, total_row), 9),
    ]

    table = Table(data, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    # ── Signatures ────────────────────────────────────────────────
    elements.append(Spacer(1, 0.8*cm))
    sig_data = [[
        Paragraph("Établi par la Direction Commerciale\n\n\n\n_________________________",
                  ParagraphStyle("s1", fontSize=9, alignment=TA_CENTER)),
        Paragraph("Vérifié par les Ressources Humaines\n\n\n\n_________________________",
                  ParagraphStyle("s2", fontSize=9, alignment=TA_CENTER)),
        Paragraph("Approuvé par la Direction Générale\n\n\n\n_________________________",
                  ParagraphStyle("s3", fontSize=9, alignment=TA_CENTER)),
    ]]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm, 8.5*cm])
    sig_table.setStyle(TableStyle([
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_table)

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    elements.append(Paragraph(
        f"Document confidentiel — NMA Gestion des Primes 2026 — "
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        note_style,
    ))

    doc.build(elements)
    return buf.getvalue()
