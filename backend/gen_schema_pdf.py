"""
Génère un schéma PDF de la base de données NMA Primes.
Usage : python gen_schema_pdf.py
"""
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT = "schema_bd_nma.pdf"

# ── Palette NMA ───────────────────────────────────────────────────────────────
C_VERT_FONCE  = colors.HexColor("#1B5E20")
C_VERT_MID    = colors.HexColor("#2E7D32")
C_VERT_CLAIR  = colors.HexColor("#E8F5E9")
C_OR          = colors.HexColor("#F9A825")
C_GRIS        = colors.HexColor("#F5F5F5")
C_GRIS_MED    = colors.HexColor("#ECEFF1")
C_BLANC       = colors.white
C_NOIR        = colors.HexColor("#212121")
C_GRIS_TEXTE  = colors.HexColor("#546E7A")
C_FK          = colors.HexColor("#1565C0")
C_PK          = colors.HexColor("#B71C1C")

# ── Définition des tables ─────────────────────────────────────────────────────
TABLES = {
    "regions": {
        "color": C_VERT_MID,
        "cols": [
            ("id",   "INTEGER", "PK", None),
            ("nom",  "VARCHAR(100)", "", None),
            ("type", "VARCHAR(9)",   "", None),
        ]
    },
    "zones": {
        "color": C_VERT_MID,
        "cols": [
            ("id",              "INTEGER",    "PK", None),
            ("code",            "VARCHAR(10)","",   None),
            ("nom",             "VARCHAR(50)","",   None),
            ("superviseur_id",  "INTEGER",    "FK", "employees.id"),
            ("responsable_id",  "INTEGER",    "FK", "employees.id"),
        ]
    },
    "employees": {
        "color": C_VERT_FONCE,
        "cols": [
            ("id",          "INTEGER",     "PK", None),
            ("nom",         "VARCHAR(100)","",   None),
            ("prenom",      "VARCHAR(100)","",   None),
            ("email",       "VARCHAR(200)","",   None),
            ("type_poste",  "VARCHAR(12)", "",   None),
            ("region_id",   "INTEGER",     "FK", "regions.id"),
            ("zone_id",     "INTEGER",     "FK", "zones.id"),
            ("secteur",     "VARCHAR(100)","",   None),
            ("actif",       "BOOLEAN",     "",   None),
            ("sap_code",    "VARCHAR(50)", "",   None),
            ("sf_id",       "VARCHAR(50)", "",   None),
        ]
    },
    "users": {
        "color": colors.HexColor("#37474F"),
        "cols": [
            ("id",               "INTEGER",     "PK", None),
            ("email",            "VARCHAR(200)","",   None),
            ("hashed_password",  "VARCHAR(300)","",   None),
            ("nom",              "VARCHAR(150)","",   None),
            ("role",             "VARCHAR(50)", "",   None),
            ("actif",            "BOOLEAN",     "",   None),
        ]
    },
    "objectives": {
        "color": colors.HexColor("#1565C0"),
        "cols": [
            ("id",               "INTEGER",     "PK", None),
            ("employee_id",      "INTEGER",     "FK", "employees.id"),
            ("periode",          "VARCHAR(7)",  "",   None),
            ("gamme",            "VARCHAR(17)", "",   None),
            ("objectif_volume",  "NUMERIC(15,2)","",  None),
            ("objectif_ca",      "NUMERIC(15,2)","",  None),
        ]
    },
    "sales_forecasts": {
        "color": colors.HexColor("#1565C0"),
        "cols": [
            ("id",           "INTEGER",      "PK", None),
            ("employee_id",  "INTEGER",      "FK", "employees.id"),
            ("periode",      "VARCHAR(7)",   "",   None),
            ("gamme",        "VARCHAR(17)",  "",   None),
            ("volume_prevu", "NUMERIC(15,2)","",   None),
            ("ca_prevu",     "NUMERIC(15,2)","",   None),
        ]
    },
    "sales_data": {
        "color": colors.HexColor("#00695C"),
        "cols": [
            ("id",                  "INTEGER",      "PK", None),
            ("source_id",           "VARCHAR(50)",  "",   None),
            ("employee_id",         "INTEGER",      "FK", "employees.id"),
            ("client_id",           "INTEGER",      "FK", "clients.id"),
            ("client_code",         "VARCHAR(50)",  "",   None),
            ("gamme",               "VARCHAR(17)",  "",   None),
            ("volume",              "NUMERIC(15,3)","",   None),
            ("montant_ht",          "NUMERIC(15,2)","",   None),
            ("montant_recouvre",    "NUMERIC(15,2)","",   None),
            ("statut_recouvrement", "VARCHAR(10)",  "",   None),
            ("date_facture",        "DATETIME",     "",   None),
            ("periode",             "VARCHAR(7)",   "",   None),
        ]
    },
    "clients": {
        "color": colors.HexColor("#00695C"),
        "cols": [
            ("id",               "INTEGER",     "PK", None),
            ("code_sap",         "VARCHAR(50)", "",   None),
            ("nom",              "VARCHAR(200)","",   None),
            ("region_id",        "INTEGER",     "FK", "regions.id"),
            ("u_secteur",        "VARCHAR(15)", "",   None),
            ("gamme_principale", "VARCHAR(17)", "",   None),
            ("date_ouverture",   "DATE",        "",   None),
            ("actif",            "BOOLEAN",     "",   None),
        ]
    },
    "client_portfolios": {
        "color": colors.HexColor("#00695C"),
        "cols": [
            ("id",          "INTEGER","PK", None),
            ("employee_id", "INTEGER","FK", "employees.id"),
            ("client_id",   "INTEGER","FK", "clients.id"),
            ("annee",       "INTEGER","",   None),
        ]
    },
    "bonus_periods": {
        "color": C_OR,
        "cols": [
            ("id",               "INTEGER",     "PK", None),
            ("periode",          "VARCHAR(7)",  "",   None),
            ("statut",           "VARCHAR(13)", "",   None),
            ("date_calcul",      "DATETIME",    "",   None),
            ("valide_par",       "VARCHAR(100)","",   None),
            ("date_validation",  "DATETIME",    "",   None),
        ]
    },
    "bonuses": {
        "color": C_OR,
        "cols": [
            ("id",                          "INTEGER",      "PK", None),
            ("employee_id",                 "INTEGER",      "FK", "employees.id"),
            ("period_id",                   "INTEGER",      "FK", "bonus_periods.id"),
            ("taux_atteinte_global",        "NUMERIC(5,2)", "",   None),
            ("volume_realise",              "NUMERIC(12,2)","",   None),
            ("volume_objectif",             "NUMERIC(12,2)","",   None),
            ("nb_visites",                  "INTEGER",      "",   None),
            ("prime_suivi_fixe",            "NUMERIC(12,2)","",   None),
            ("prime_quantitative",          "NUMERIC(12,2)","",   None),
            ("prime_qualitative",           "NUMERIC(12,2)","",   None),
            ("commission_nouvelles_affaires","NUMERIC(12,2)","",  None),
            ("total",                       "NUMERIC(12,2)","",   None),
            ("qualitative_eligible",        "BOOLEAN",      "",   None),
            ("detail_json",                 "JSON",         "",   None),
            ("statut",                      "VARCHAR(13)",  "",   None),
            ("calcule_le",                  "DATETIME",     "",   None),
        ]
    },
    "bonus_qual_details": {
        "color": C_OR,
        "cols": [
            ("id",              "INTEGER",      "PK", None),
            ("bonus_id",        "INTEGER",      "FK", "bonuses.id"),
            ("critere_code",    "VARCHAR(50)",  "",   None),
            ("critere_libelle", "VARCHAR(200)", "",   None),
            ("valeur_atteinte", "VARCHAR(100)", "",   None),
            ("seuil_requis",    "VARCHAR(100)", "",   None),
            ("montant_max",     "NUMERIC(10,2)","",   None),
            ("montant_accorde", "NUMERIC(10,2)","",   None),
            ("eligible",        "BOOLEAN",      "",   None),
        ]
    },
    "manual_criteria": {
        "color": colors.HexColor("#6A1B9A"),
        "cols": [
            ("id",           "INTEGER",     "PK", None),
            ("employee_id",  "INTEGER",     "FK", "employees.id"),
            ("periode",      "VARCHAR(7)",  "",   None),
            ("critere_code", "VARCHAR(50)", "",   None),
            ("valeur",       "BOOLEAN",     "",   None),
            ("saisi_par",    "VARCHAR(100)","",   None),
            ("saisi_le",     "DATETIME",    "",   None),
        ]
    },
    "visits_data": {
        "color": colors.HexColor("#4527A0"),
        "cols": [
            ("id",                "INTEGER",     "PK", None),
            ("sf_id",             "VARCHAR(50)", "",   None),
            ("employee_id",       "INTEGER",     "FK", "employees.id"),
            ("client_code",       "VARCHAR(50)", "",   None),
            ("type_visite",       "VARCHAR(11)", "",   None),
            ("date_visite",       "DATETIME",    "",   None),
            ("commande_saisie",   "BOOLEAN",     "",   None),
            ("visite_saisie_crm", "BOOLEAN",     "",   None),
            ("periode",           "VARCHAR(7)",  "",   None),
        ]
    },
    "sync_logs": {
        "color": colors.HexColor("#455A64"),
        "cols": [
            ("id",         "INTEGER",      "PK", None),
            ("source",     "VARCHAR(10)",  "",   None),
            ("periode",    "VARCHAR(7)",   "",   None),
            ("started_at", "DATETIME",     "",   None),
            ("statut",     "VARCHAR(8)",   "",   None),
            ("nb_records", "INTEGER",      "",   None),
            ("message",    "VARCHAR(1000)","",   None),
        ]
    },
}


def make_table_block(name, definition, styles):
    """Génère le bloc visuel d'une table."""
    color = definition["color"]
    cols  = definition["cols"]

    title_style = ParagraphStyle("title",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=C_BLANC, alignment=TA_CENTER)
    field_style = ParagraphStyle("field",
        fontName="Helvetica", fontSize=7.5,
        textColor=C_NOIR, leading=11)
    fk_style = ParagraphStyle("fk",
        fontName="Helvetica-Oblique", fontSize=7,
        textColor=C_FK, leading=11)
    pk_style = ParagraphStyle("pk",
        fontName="Helvetica-Bold", fontSize=7.5,
        textColor=C_PK, leading=11)

    rows = [[Paragraph(f"<b>{name}</b>", title_style), "", ""]]
    for col_name, col_type, role, fk_ref in cols:
        if role == "PK":
            label = Paragraph(f"🔑 {col_name}", pk_style)
        elif role == "FK":
            label = Paragraph(f"⤷ {col_name}", fk_style)
        else:
            label = Paragraph(col_name, field_style)

        type_p  = Paragraph(f"<i>{col_type}</i>",
                            ParagraphStyle("t", fontName="Helvetica-Oblique",
                                           fontSize=7, textColor=C_GRIS_TEXTE, leading=11))
        ref_p   = Paragraph(f"→ {fk_ref}" if fk_ref else "",
                            ParagraphStyle("r", fontName="Helvetica-Oblique",
                                           fontSize=6.5, textColor=C_FK, leading=10))
        rows.append([label, type_p, ref_p])

    col_widths = [4.2*cm, 2.8*cm, 3.2*cm]
    t = Table(rows, colWidths=col_widths, repeatRows=0)

    row_count = len(rows)
    style = TableStyle([
        # En-tête
        ("BACKGROUND",   (0, 0), (-1, 0), color),
        ("SPAN",         (0, 0), (-1, 0)),
        ("TOPPADDING",   (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 5),
        # Corps
        ("BACKGROUND",   (0, 1), (-1, -1), C_BLANC),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_BLANC, C_GRIS]),
        ("TOPPADDING",   (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Bordures
        ("BOX",          (0, 0), (-1, -1), 1.0, color),
        ("LINEBELOW",    (0, 0), (-1, 0),  1.0, color),
        ("LINEBEFORE",   (1, 1), (1, -1),  0.3, C_GRIS_MED),
        ("LINEBEFORE",   (2, 1), (2, -1),  0.3, C_GRIS_MED),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ])
    t.setStyle(style)
    return t


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=landscape(A3),
        leftMargin=1.2*cm, rightMargin=1.2*cm,
        topMargin=1.5*cm,  bottomMargin=1.2*cm,
    )

    styles = getSampleStyleSheet()

    title_s = ParagraphStyle("maintitle",
        fontName="Helvetica-Bold", fontSize=18,
        textColor=C_BLANC, alignment=TA_CENTER, spaceAfter=4)
    sub_s = ParagraphStyle("subtitle",
        fontName="Helvetica", fontSize=10,
        textColor=C_VERT_CLAIR, alignment=TA_CENTER)
    section_s = ParagraphStyle("section",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=C_BLANC, alignment=TA_LEFT,
        spaceBefore=10, spaceAfter=4)

    # ── En-tête ───────────────────────────────────────────────────────────────
    header_table = Table(
        [[Paragraph("SCHÉMA BASE DE DONNÉES — NMA GESTION DES PRIMES 2026", title_s)],
         [Paragraph("PostgreSQL · 17 tables · SQLAlchemy ORM · FastAPI backend", sub_s)]],
        colWidths=[38*cm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_VERT_FONCE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 2, C_OR),
    ]))

    # ── Légende ───────────────────────────────────────────────────────────────
    legend_data = [
        [Paragraph("<b>🔑 PK</b> Clé primaire", ParagraphStyle("l", fontSize=8, textColor=C_PK)),
         Paragraph("<b>⤷ FK</b> Clé étrangère", ParagraphStyle("l", fontSize=8, textColor=C_FK)),
         Paragraph("● Référentiel (vert)",    ParagraphStyle("l", fontSize=8, textColor=C_VERT_FONCE)),
         Paragraph("● Primes (or)",           ParagraphStyle("l", fontSize=8, textColor=C_OR)),
         Paragraph("● SAP / Ventes (teal)",   ParagraphStyle("l", fontSize=8, textColor=colors.HexColor("#00695C"))),
         Paragraph("● CRM / Visites (violet)",ParagraphStyle("l", fontSize=8, textColor=colors.HexColor("#4527A0"))),
         Paragraph("● Objectifs (bleu)",      ParagraphStyle("l", fontSize=8, textColor=colors.HexColor("#1565C0"))),
         Paragraph("● Système (gris)",        ParagraphStyle("l", fontSize=8, textColor=colors.HexColor("#455A64"))),
        ]
    ]
    legend = Table(legend_data, colWidths=[4.5*cm]*8)
    legend.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_GRIS_MED),
        ("BOX",           (0,0),(-1,-1), 0.5, colors.HexColor("#B0BEC5")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ]))

    def section_label(txt, color):
        t = Table([[Paragraph(f"  {txt}", ParagraphStyle("sl",
                   fontName="Helvetica-Bold", fontSize=8,
                   textColor=C_BLANC))]],
                   colWidths=[38*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), color),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        return t

    def row_of_tables(names):
        blocks = [make_table_block(n, TABLES[n], styles) for n in names]
        spacers = []
        for b in blocks:
            spacers.append(b)
            spacers.append(Spacer(0.4*cm, 1))
        row = Table([spacers], colWidths=None)
        row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
        return row

    # ── Construction ──────────────────────────────────────────────────────────
    story = [
        header_table,
        Spacer(1, 0.3*cm),
        legend,
        Spacer(1, 0.5*cm),

        section_label("RÉFÉRENTIEL GÉOGRAPHIQUE & EMPLOYÉS", C_VERT_FONCE),
        Spacer(1, 0.2*cm),
        row_of_tables(["regions", "zones", "employees", "users"]),
        Spacer(1, 0.5*cm),

        section_label("OBJECTIFS & VENTES (SAP B1)", colors.HexColor("#00695C")),
        Spacer(1, 0.2*cm),
        row_of_tables(["objectives", "sales_forecasts", "sales_data", "clients", "client_portfolios"]),
        Spacer(1, 0.5*cm),

        section_label("CALCUL DES PRIMES", C_OR),
        Spacer(1, 0.2*cm),
        row_of_tables(["bonus_periods", "bonuses", "bonus_qual_details", "manual_criteria"]),
        Spacer(1, 0.5*cm),

        section_label("CRM / VISITES TERRAIN (SALESFORCE) & LOGS", colors.HexColor("#4527A0")),
        Spacer(1, 0.2*cm),
        row_of_tables(["visits_data", "sync_logs"]),
    ]

    doc.build(story)
    print(f"✓ PDF généré : {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
