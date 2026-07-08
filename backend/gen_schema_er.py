"""
Génère un diagramme ER PDF avec graphviz — flèches de relations visibles.
Usage : python gen_schema_er.py
"""
import subprocess, os

OUTPUT_DOT = "schema_bd_nma.dot"
OUTPUT_PDF = "schema_bd_nma.pdf"

# Couleurs NMA par groupe
COLORS = {
    "geo":     {"bg": "#1B5E20", "fg": "white", "border": "#4CAF50"},
    "emp":     {"bg": "#2E7D32", "fg": "white", "border": "#81C784"},
    "ventes":  {"bg": "#00695C", "fg": "white", "border": "#4DB6AC"},
    "obj":     {"bg": "#1565C0", "fg": "white", "border": "#64B5F6"},
    "primes":  {"bg": "#E65100", "fg": "white", "border": "#FFCC80"},
    "crm":     {"bg": "#4527A0", "fg": "white", "border": "#B39DDB"},
    "sys":     {"bg": "#37474F", "fg": "white", "border": "#90A4AE"},
    "auth":    {"bg": "#455A64", "fg": "white", "border": "#B0BEC5"},
}

def color(group, part):
    return COLORS[group][part]

def table_node(name, group, columns):
    """
    columns = list of (col_name, col_type, role)
    role = "PK" | "FK" | ""
    """
    c = COLORS[group]
    rows = []
    rows.append(f'<TR><TD COLSPAN="3" BGCOLOR="{c["bg"]}" ALIGN="CENTER">'
                f'<FONT COLOR="{c["fg"]}" POINT-SIZE="11"><B>{name}</B></FONT></TD></TR>')

    for col_name, col_type, role in columns:
        if role == "PK":
            icon = "🔑"
            name_color = "#C62828"
            bold_open  = "<B>"
            bold_close = "</B>"
        elif role == "FK":
            icon = "⤷"
            name_color = "#1565C0"
            bold_open  = "<I>"
            bold_close = "</I>"
        else:
            icon = " "
            name_color = "#212121"
            bold_open  = ""
            bold_close = ""

        rows.append(
            f'<TR>'
            f'<TD ALIGN="LEFT" WIDTH="14"><FONT POINT-SIZE="9">{icon}</FONT></TD>'
            f'<TD ALIGN="LEFT" PORT="{col_name}">'
            f'<FONT COLOR="{name_color}" POINT-SIZE="9">{bold_open}{col_name}{bold_close}</FONT></TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="#607D8B" POINT-SIZE="8"><I>{col_type}</I></FONT></TD>'
            f'</TR>'
        )

    label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">' + \
            "".join(rows) + '</TABLE>>'
    return f'  {name} [label={label} color="{c["border"]}"]'


# ── Définition des tables ─────────────────────────────────────────────────────
TABLES = {
    "regions": ("geo", [
        ("id",   "INTEGER", "PK"),
        ("nom",  "VARCHAR(100)", ""),
        ("type", "VARCHAR(9)", ""),
    ]),
    "zones": ("geo", [
        ("id",             "INTEGER",    "PK"),
        ("code",           "VARCHAR(10)",""),
        ("nom",            "VARCHAR(50)",""),
        ("superviseur_id", "INTEGER",    "FK"),
        ("responsable_id", "INTEGER",    "FK"),
    ]),
    "employees": ("emp", [
        ("id",         "INTEGER",     "PK"),
        ("nom",        "VARCHAR(100)",""),
        ("prenom",     "VARCHAR(100)",""),
        ("type_poste", "VARCHAR(12)", ""),
        ("region_id",  "INTEGER",     "FK"),
        ("zone_id",    "INTEGER",     "FK"),
        ("actif",      "BOOLEAN",     ""),
        ("sap_code",   "VARCHAR(50)", ""),
        ("sf_id",      "VARCHAR(50)", ""),
    ]),
    "users": ("auth", [
        ("id",              "INTEGER",     "PK"),
        ("email",           "VARCHAR(200)",""),
        ("hashed_password", "VARCHAR(300)",""),
        ("nom",             "VARCHAR(150)",""),
        ("role",            "VARCHAR(50)", ""),
        ("actif",           "BOOLEAN",     ""),
    ]),
    "objectives": ("obj", [
        ("id",              "INTEGER",      "PK"),
        ("employee_id",     "INTEGER",      "FK"),
        ("periode",         "VARCHAR(7)",   ""),
        ("gamme",           "VARCHAR(17)",  ""),
        ("objectif_volume", "NUMERIC(15,2)",""),
        ("objectif_ca",     "NUMERIC(15,2)",""),
    ]),
    "sales_forecasts": ("obj", [
        ("id",           "INTEGER",      "PK"),
        ("employee_id",  "INTEGER",      "FK"),
        ("periode",      "VARCHAR(7)",   ""),
        ("gamme",        "VARCHAR(17)",  ""),
        ("volume_prevu", "NUMERIC(15,2)",""),
        ("ca_prevu",     "NUMERIC(15,2)",""),
    ]),
    "sales_data": ("ventes", [
        ("id",               "INTEGER",      "PK"),
        ("employee_id",      "INTEGER",      "FK"),
        ("client_id",        "INTEGER",      "FK"),
        ("gamme",            "VARCHAR(17)",  ""),
        ("volume",           "NUMERIC(15,3)",""),
        ("montant_ht",       "NUMERIC(15,2)",""),
        ("montant_recouvre", "NUMERIC(15,2)",""),
        ("date_facture",     "DATETIME",     ""),
        ("periode",          "VARCHAR(7)",   ""),
    ]),
    "clients": ("ventes", [
        ("id",               "INTEGER",     "PK"),
        ("code_sap",         "VARCHAR(50)", ""),
        ("nom",              "VARCHAR(200)",""),
        ("region_id",        "INTEGER",     "FK"),
        ("gamme_principale", "VARCHAR(17)", ""),
        ("date_ouverture",   "DATE",        ""),
        ("actif",            "BOOLEAN",     ""),
    ]),
    "client_portfolios": ("ventes", [
        ("id",          "INTEGER","PK"),
        ("employee_id", "INTEGER","FK"),
        ("client_id",   "INTEGER","FK"),
        ("annee",       "INTEGER",""),
    ]),
    "client_monthly_sales": ("ventes", [
        ("id",               "INTEGER",      "PK"),
        ("employee_id",      "INTEGER",      "FK"),
        ("client_code",      "VARCHAR(50)",  ""),
        ("periode",          "VARCHAR(7)",   ""),
        ("montant_ca",       "NUMERIC(15,2)",""),
        ("montant_recouvre", "NUMERIC(15,2)",""),
    ]),
    "bonus_periods": ("primes", [
        ("id",              "INTEGER",    "PK"),
        ("periode",         "VARCHAR(7)", ""),
        ("statut",          "VARCHAR(13)",""),
        ("date_calcul",     "DATETIME",   ""),
        ("valide_par",      "VARCHAR(100)",""),
        ("date_validation", "DATETIME",   ""),
    ]),
    "bonuses": ("primes", [
        ("id",                           "INTEGER",      "PK"),
        ("employee_id",                  "INTEGER",      "FK"),
        ("period_id",                    "INTEGER",      "FK"),
        ("taux_atteinte_global",         "NUMERIC(5,2)", ""),
        ("volume_realise",               "NUMERIC(12,2)",""),
        ("volume_objectif",              "NUMERIC(12,2)",""),
        ("nb_visites",                   "INTEGER",      ""),
        ("prime_suivi_fixe",             "NUMERIC(12,2)",""),
        ("prime_quantitative",           "NUMERIC(12,2)",""),
        ("prime_qualitative",            "NUMERIC(12,2)",""),
        ("commission_nouvelles_affaires","NUMERIC(12,2)",""),
        ("total",                        "NUMERIC(12,2)",""),
        ("qualitative_eligible",         "BOOLEAN",      ""),
        ("statut",                       "VARCHAR(13)",  ""),
        ("calcule_le",                   "DATETIME",     ""),
    ]),
    "bonus_qual_details": ("primes", [
        ("id",              "INTEGER",      "PK"),
        ("bonus_id",        "INTEGER",      "FK"),
        ("critere_code",    "VARCHAR(50)",  ""),
        ("valeur_atteinte", "VARCHAR(100)", ""),
        ("seuil_requis",    "VARCHAR(100)", ""),
        ("montant_max",     "NUMERIC(10,2)",""),
        ("montant_accorde", "NUMERIC(10,2)",""),
        ("eligible",        "BOOLEAN",      ""),
    ]),
    "manual_criteria": ("crm", [
        ("id",           "INTEGER",     "PK"),
        ("employee_id",  "INTEGER",     "FK"),
        ("periode",      "VARCHAR(7)",  ""),
        ("critere_code", "VARCHAR(50)", ""),
        ("valeur",       "BOOLEAN",     ""),
        ("saisi_par",    "VARCHAR(100)",""),
    ]),
    "visits_data": ("crm", [
        ("id",                "INTEGER",     "PK"),
        ("sf_id",             "VARCHAR(50)", ""),
        ("employee_id",       "INTEGER",     "FK"),
        ("client_code",       "VARCHAR(50)", ""),
        ("type_visite",       "VARCHAR(11)", ""),
        ("date_visite",       "DATETIME",    ""),
        ("commande_saisie",   "BOOLEAN",     ""),
        ("visite_saisie_crm", "BOOLEAN",     ""),
        ("periode",           "VARCHAR(7)",  ""),
    ]),
    "sync_logs": ("sys", [
        ("id",         "INTEGER",      "PK"),
        ("source",     "VARCHAR(10)",  ""),
        ("periode",    "VARCHAR(7)",   ""),
        ("started_at", "DATETIME",     ""),
        ("statut",     "VARCHAR(8)",   ""),
        ("nb_records", "INTEGER",      ""),
        ("message",    "VARCHAR(1000)",""),
    ]),
}

# ── Relations (FK → PK) ───────────────────────────────────────────────────────
RELATIONS = [
    # employees
    ("employees", "region_id",       "regions",        "id"),
    ("employees", "zone_id",         "zones",          "id"),
    # zones
    ("zones",     "superviseur_id",  "employees",      "id"),
    ("zones",     "responsable_id",  "employees",      "id"),
    # objectives
    ("objectives","employee_id",     "employees",      "id"),
    # forecasts
    ("sales_forecasts","employee_id","employees",      "id"),
    # sales
    ("sales_data","employee_id",     "employees",      "id"),
    ("sales_data","client_id",       "clients",        "id"),
    # clients
    ("clients",   "region_id",       "regions",        "id"),
    # portfolios
    ("client_portfolios","employee_id","employees",    "id"),
    ("client_portfolios","client_id",  "clients",      "id"),
    # client monthly sales
    ("client_monthly_sales","employee_id","employees", "id"),
    # bonuses
    ("bonuses",   "employee_id",     "employees",      "id"),
    ("bonuses",   "period_id",       "bonus_periods",  "id"),
    # bonus qual details
    ("bonus_qual_details","bonus_id","bonuses",        "id"),
    # manual criteria
    ("manual_criteria","employee_id","employees",      "id"),
    # visits
    ("visits_data","employee_id",    "employees",      "id"),
]

# ── Groupes (subgraph) ────────────────────────────────────────────────────────
GROUPS = {
    "cluster_geo":    ("Référentiel géographique", "#E8F5E9", ["regions", "zones"]),
    "cluster_emp":    ("Employés & Utilisateurs",  "#F1F8E9", ["employees", "users"]),
    "cluster_obj":    ("Objectifs & Prévisions",   "#E3F2FD", ["objectives", "sales_forecasts"]),
    "cluster_ventes": ("Ventes SAP B1",            "#E0F2F1", ["sales_data","clients","client_portfolios","client_monthly_sales"]),
    "cluster_primes": ("Calcul des primes",        "#FFF3E0", ["bonus_periods","bonuses","bonus_qual_details"]),
    "cluster_crm":    ("CRM & Critères manuels",   "#EDE7F6", ["manual_criteria","visits_data"]),
    "cluster_sys":    ("Système",                  "#ECEFF1", ["sync_logs"]),
}


def build_dot():
    lines = [
        'digraph NMA_BD {',
        '  graph [',
        '    rankdir=LR',
        '    splines=ortho',
        '    nodesep=0.6',
        '    ranksep=1.2',
        '    fontname="Helvetica"',
        '    fontsize=12',
        '    label="Schéma Base de Données — NMA Gestion des Primes 2026"',
        '    labelloc=t',
        '    labeljust=c',
        '    bgcolor="#FAFAFA"',
        '  ]',
        '  node [shape=none margin=0 fontname="Helvetica"]',
        '  edge [fontname="Helvetica" fontsize=8 arrowhead=crow arrowtail=none dir=forward color="#607D8B"]',
        '',
    ]

    # Subgraphs
    for cluster_id, (label, bg, table_names) in GROUPS.items():
        lines.append(f'  subgraph {cluster_id} {{')
        lines.append(f'    graph [label="{label}" bgcolor="{bg}" style=rounded pencolor="#B0BEC5" penwidth=1.5 fontname="Helvetica-Bold" fontsize=10]')
        for tname in table_names:
            if tname in TABLES:
                group, cols = TABLES[tname]
                lines.append(table_node(tname, group, cols))
        lines.append('  }')
        lines.append('')

    # Relations
    lines.append('  // Relations')
    for src_table, src_col, dst_table, dst_col in RELATIONS:
        lines.append(f'  {src_table}:{src_col} -> {dst_table}:{dst_col} [tooltip="{src_table}.{src_col} → {dst_table}.{dst_col}"]')

    lines.append('}')
    return '\n'.join(lines)


def main():
    dot_src = build_dot()
    with open(OUTPUT_DOT, 'w') as f:
        f.write(dot_src)
    print(f"✓ DOT généré : {OUTPUT_DOT}")

    result = subprocess.run(
        ['dot', '-Tpdf', '-Gsize=20,14!', '-Gdpi=150', OUTPUT_DOT, '-o', OUTPUT_PDF],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Erreur graphviz:", result.stderr)
    else:
        print(f"✓ PDF généré  : {OUTPUT_PDF}")
        os.system(f"open {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
