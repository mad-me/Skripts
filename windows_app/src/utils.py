import pandas as pd
import unicodedata
from typing import List
import sqlite3

def normalize_token(text: str) -> str:
    return unicodedata.normalize("NFKC", text.strip().lower())

def filtere_fahrer_daten(conn: sqlite3.Connection, tabelle: str, fahrer: str, kalenderwoche: int) -> pd.DataFrame:
    """Liefert gefilterte Daten aus umsatz_uber oder umsatz_bolt nach Fahrer und KW."""
    where = ["CAST(kalenderwoche AS TEXT) = ?"]
    params: List[str] = [str(kalenderwoche)]

    tokens = [normalize_token(t) for t in fahrer.split()]
    token_clauses = []

    for token in tokens:
        token_clauses.append("LOWER(Driver) LIKE ?")
        params.append(f"%{token}%")

    if len(token_clauses) >= 2:
        where.append("( " + " OR ".join(token_clauses) + " )")

    query = f"""
        SELECT *, '{tabelle}' AS quelle
        FROM {tabelle}
        WHERE {' AND '.join(where)}
    """

    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"[WARN] Fehler beim Abfragen von {tabelle}: {e}")
        return pd.DataFrame()
