QUELLEN_MAP = {
    "umsatz_bolt": "Bolt",
    "umsatz_uber": "Uber",
    "umsatz_40100": "Taxi",
    "umsatz_31300": "Taxi",
}

def setze_indexnamen(df):
    df = df.copy()
    indexnamen = []

    for idx, row in df.iterrows():
        if str(idx) in ["Summe", "Abrechnung"]:
            indexnamen.append(str(idx))
        elif "quelle" in df.columns and row["quelle"] in QUELLEN_MAP:
            indexnamen.append(QUELLEN_MAP[row["quelle"]])
        else:
            indexnamen.append(str(idx))

    df["Index"] = indexnamen
    return df

def parse_kw(kw_text: str, aktuelle_kw: int) -> int | None:
    import re
    kw_text = kw_text.strip().lower()

    if kw_text == "letzte woche":
        return aktuelle_kw - 1
    elif kw_text == "vorletzte woche":
        return aktuelle_kw - 2
    else:
        match = re.search(r"\d+", kw_text)
        if match:
            return int(match.group())
    return None
