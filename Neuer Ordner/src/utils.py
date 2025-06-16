import unicodedata
import re

def normalize_token(text: str) -> str:
    text = unicodedata.normalize("NFKC", text.strip().lower())
    text = re.sub(r"[^a-zäöüß ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def extrahiere_ziffernfolge(text: str) -> str:
    return re.sub(r"\D", "", text or "")

# Matching-Logik, float-Parsing, etc.
