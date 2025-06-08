import pandas as pd
from utils import normalize_token

def filtere_fahrer_daten(conn, tabelle: str, fahrer: str, kw: int) -> pd.DataFrame:
    """
    Filtert Einträge aus der gegebenen Tabelle (umsatz_uber oder umsatz_bolt),
    bei denen die KW und der Fahrername (per Token-Match) passen.
    Mindestens zwei Tokens müssen exakt als ganze Wörter im Driver-Feld vorkommen.
    """

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabelle})")
    spalten = [row[1] for row in cursor.fetchall()]

    where = ["CAST(kalenderwoche AS TEXT) = ?"]
    params = [str(kw)]

    # Match-Logik auf Token-Ebene
    tokens = [normalize_token(t) for t in fahrer.split() if normalize_token(t)]
    token_clauses = []

    for token in tokens:
        # Exakter Wortvergleich mit eingebetteten Leerzeichen
        token_clauses.append("( ' ' || LOWER(Driver) || ' ' LIKE ? )")
        params.append(f"% {token} %")

    if len(token_clauses) >= 2:
        where.append("( " + " + ".join(token_clauses) + " ) >= 2")
    else:
        print("⚠️ Zu wenig gültige Tokens für exakte Übereinstimmung.")
        return pd.DataFrame()

    query = f"""
        SELECT *, '{tabelle}' AS quelle
        FROM {tabelle}
        WHERE {' AND '.join(where)}
    """

    print("[DEBUG] Eingabe-Fahrer:", fahrer)
    print("[DEBUG] Tokens:", tokens)
    print("[DEBUG] SQL WHERE:", " AND ".join(where))
    print("[DEBUG] SQL Params:", params)

    return pd.read_sql_query(query, conn, params=params)
