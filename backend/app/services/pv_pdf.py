from __future__ import annotations
"""
Génération du PV de commission NMA — PDF avec logo et détail complet.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Couleurs NMA
VERT_FONCE  = colors.HexColor("#1B5E20")
VERT_CLAIR  = colors.HexColor("#E8F5E9")
OR          = colors.HexColor("#F9A825")
GRIS_CLAIR  = colors.HexColor("#F5F5F5")
ROUGE       = colors.HexColor("#C62828")

LOGO_PATH = "/Users/damesady/developpement/Commerciaux/frontend/public/logo-nma.png"

ROLE_LABELS = {
    "RCR": "Responsable Commercial Régional",
    "SV": "Superviseur des Ventes",
    "COMMERCIAL": "Commercial",
    "ATC_BV": "Agent TC Bétail & Volaille",
    "ATC_FARINE": "Agent TC Farine",
    "RCE": "Responsable Commercial Export",
    "RESP_TECH_FP": "Resp. Technique Farine & Pâtes",
    "RESP_TECH_BV": "Resp. Technique Bétail & Volaille",
    "DV": "Directeur des Ventes",
    "DCMT": "Directeur Commercial Marketing Tech.",
}

MOIS_FR = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre",
}


def _fcfa(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", " ") + " FCFA"


def _pct(v) -> str:
    if v is None:
        return "-"
    return f"{float(v):.1f}%"


def generate_pv_pdf(bonus, employee, region_nom: str = "", periode: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle("titre", fontSize=13, textColor=VERT_FONCE,
                                 fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    sous_titre_style = ParagraphStyle("sous", fontSize=10, textColor=colors.grey,
                                      alignment=TA_CENTER, spaceAfter=2)
    section_style = ParagraphStyle("section", fontSize=10, textColor=colors.white,
                                   fontName="Helvetica-Bold", backColor=VERT_FONCE,
                                   leftIndent=6, spaceAfter=4, spaceBefore=10)
    label_style = ParagraphStyle("label", fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("value", fontSize=10, fontName="Helvetica-Bold")
    note_style  = ParagraphStyle("note", fontSize=8, textColor=colors.grey,
                                 alignment=TA_CENTER, spaceAfter=4)

    mois_annee = f"{MOIS_FR.get(periode[5:], '')} {periode[:4]}" if periode else ""
    nom_complet = f"{employee.prenom} {employee.nom}"
    role_label  = ROLE_LABELS.get(str(employee.type_poste.value if hasattr(employee.type_poste, 'value') else employee.type_poste), str(employee.type_poste))

    elements = []

    # ── En-tête ───────────────────────────────────────────────
    try:
        logo = Image(LOGO_PATH, width=3.5*cm, height=2*cm)
        logo.hAlign = "LEFT"
    except Exception:
        logo = Spacer(1, 2*cm)

    header_data = [[
        logo,
        [
            Paragraph("NOUVELLE MINOTERIE AFRICAINE", ParagraphStyle(
                "h1", fontSize=14, fontName="Helvetica-Bold", textColor=VERT_FONCE, alignment=TA_CENTER)),
            Paragraph("PROCÈS-VERBAL DE COMMISSION COMMERCIALE", ParagraphStyle(
                "h2", fontSize=11, fontName="Helvetica-Bold", textColor=OR, alignment=TA_CENTER)),
            Paragraph(f"Période : {mois_annee}", ParagraphStyle(
                "h3", fontSize=10, textColor=colors.grey, alignment=TA_CENTER)),
        ],
        Spacer(3.5*cm, 2*cm),
    ]]
    header_table = Table(header_data, colWidths=[3.5*cm, 10*cm, 3.5*cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=OR, spaceAfter=10))

    # ── Identité du commercial ─────────────────────────────────
    elements.append(Paragraph(" IDENTIFICATION DU COMMERCIAL", section_style))
    id_data = [
        ["Nom & Prénom", nom_complet, "Rôle", role_label],
        ["Zone / Région", region_nom or "-", "Période", mois_annee],
        ["Date d'édition", datetime.now().strftime("%d/%m/%Y"), "Statut prime", str(bonus.statut.value if hasattr(bonus.statut, 'value') else bonus.statut)],
    ]
    id_table = Table(id_data, colWidths=[4*cm, 6.5*cm, 3*cm, 3.5*cm])
    id_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GRIS_CLAIR]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(id_table)

    # ── Performance quantitative ───────────────────────────────
    elements.append(Paragraph(" PERFORMANCE QUANTITATIVE", section_style))

    taux = float(bonus.taux_atteinte_global or 0)
    taux_color = VERT_FONCE if taux >= 100 else (colors.HexColor("#1565C0") if taux >= 90 else ROUGE)

    perf_data = [
        ["Réalisé (T)", "Objectif (T)", "Taux d'atteinte", "Prime quantitative"],
        [
            f"{float(bonus.volume_realise):,.1f}".replace(",", " "),
            f"{float(bonus.volume_objectif):,.1f}".replace(",", " "),
            _pct(bonus.taux_atteinte_global),
            _fcfa(float(bonus.prime_quantitative)),
        ],
    ]
    if bonus.taux_atteinte_pates is not None:
        perf_data.append(["dont Pâtes (T)", "-", _pct(bonus.taux_atteinte_pates), ""])
    if bonus.taux_atteinte_autres is not None:
        perf_data.append(["dont Autres gammes (T)", "-", _pct(bonus.taux_atteinte_autres), ""])

    perf_table = Table(perf_data, colWidths=[4*cm, 4*cm, 4*cm, 5*cm])
    perf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERT_FONCE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLAIR]),
        ("TEXTCOLOR", (2, 1), (2, 1), taux_color),
        ("FONTNAME", (2, 1), (2, 1), "Helvetica-Bold"),
        ("FONTNAME", (3, 1), (3, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(perf_table)

    # ── Critères qualitatifs ───────────────────────────────────
    elements.append(Paragraph(" CRITÈRES QUALITATIFS", section_style))

    elig = bool(bonus.qualitative_eligible)
    elig_text = "ELIGIBLE (taux >= 90%)" if elig else "NON ELIGIBLE (taux < 90%)"
    elig_color = VERT_FONCE if elig else ROUGE
    elig_hex = elig_color.hexval()[2:]
    elements.append(Paragraph(
        f'<font color="#{elig_hex}"><b>{elig_text}</b></font>',
        ParagraphStyle("elig", fontSize=9, spaceAfter=6, alignment=TA_CENTER)
    ))

    qual_data = [["Critère", "Réalisé", "Seuil requis", "Éligible", "Montant max", "Accordé"]]
    for c in bonus.qual_details:
        qual_data.append([
            Paragraph(c.critere_libelle, ParagraphStyle("crit", fontSize=8)),
            c.valeur_atteinte or "-",
            c.seuil_requis or "-",
            "OUI" if c.eligible else "NON",
            _fcfa(float(c.montant_max)),
            _fcfa(float(c.montant_accorde)),
        ])
    qual_data.append(["", "", "", "", "TOTAL QUAL.", _fcfa(float(bonus.prime_qualitative))])

    qual_table = Table(qual_data, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
    style_qual = [
        ("BACKGROUND", (0, 0), (-1, 0), VERT_FONCE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIS_CLAIR]),
        ("BACKGROUND", (0, -1), (-1, -1), VERT_CLAIR),
        ("FONTNAME", (4, -1), (-1, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]
    for i, c in enumerate(bonus.qual_details, start=1):
        col = VERT_FONCE if c.eligible else ROUGE
        style_qual.append(("TEXTCOLOR", (3, i), (3, i), col))
        style_qual.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
    qual_table.setStyle(TableStyle(style_qual))
    elements.append(qual_table)

    # ── Récapitulatif financier ────────────────────────────────
    elements.append(Paragraph(" RÉCAPITULATIF FINANCIER", section_style))

    recap_data = [
        ["Commission fixe de suivi", _fcfa(float(bonus.prime_suivi_fixe))],
        ["Commission quantitative", _fcfa(float(bonus.prime_quantitative))],
        ["Commission qualitative", _fcfa(float(bonus.prime_qualitative))],
    ]
    if float(bonus.commission_nouvelles_affaires) > 0:
        recap_data.append(["Commission nouvelles affaires (0.5%)",
                            _fcfa(float(bonus.commission_nouvelles_affaires))])
    recap_data.append(["TOTAL COMMISSION DU MOIS", _fcfa(float(bonus.total))])

    recap_table = Table(recap_data, colWidths=[12*cm, 5*cm])
    style_recap = [
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -2), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -2), [colors.white, GRIS_CLAIR]),
        ("BACKGROUND", (0, -1), (-1, -1), VERT_FONCE),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, OR),
    ]
    recap_table.setStyle(TableStyle(style_recap))
    elements.append(recap_table)

    # ── Signatures ────────────────────────────────────────────
    elements.append(Spacer(1, 1*cm))
    sig_data = [[
        Paragraph("Le Commercial\n\n\n\n_______________________\n" + nom_complet,
                  ParagraphStyle("sig", fontSize=9, alignment=TA_CENTER)),
        Paragraph("Le Responsable Hiérarchique\n\n\n\n_______________________\n" + (region_nom or ""),
                  ParagraphStyle("sig", fontSize=9, alignment=TA_CENTER)),
        Paragraph("La Direction Commerciale\n\n\n\n_______________________\n",
                  ParagraphStyle("sig", fontSize=9, alignment=TA_CENTER)),
    ]]
    sig_table = Table(sig_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elements.append(Paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — NMA Gestion des Primes 2026 — Confidentiel",
        note_style
    ))

    doc.build(elements)
    return buf.getvalue()
