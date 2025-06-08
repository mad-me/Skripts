import subprocess
import shutil
from pathlib import Path

# === Konfiguration ===
SOURCE_DIR = Path(r"C:\EKK\Skripts\download\data\raw")
ARCHIVE_DIR = Path(r"C:\EKK\Skripts\import\data\archive")
SCRIPTS_DIR = Path(r"C:\EKK\Skripts\import\src")


def process_file(filepath: Path):
    filename = filepath.name

    # Schritt 1: Aggregation für 40100
    if "40100" in filename:
        try:
            subprocess.run(
                ["python", str(SCRIPTS_DIR / "aggregate_40100.py"), str(filepath)],
                check=True
            )
            print(f"✅ aggregation_40100.py erfolgreich für {filename}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Fehler bei Aggregation {filename}: {e}")
            return

    # Schritt 2: Datei verschieben
    try:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        target = ARCHIVE_DIR / filename
        shutil.move(str(filepath), str(target))
        print(f"📁 Verschiebe {filename} nach {ARCHIVE_DIR}")
    except Exception as e:
        print(f"❌ Fehler beim Verschieben der Datei {filename}: {e}")
        return

    # Schritt 3: Passendes Importskript
    if "40100" in filename:
        script_name = "import_40100.py"
    elif "Uber" in filename or "Bolt" in filename:
        script_name = "import_UberBolt.py"
    else:
        print(f"⚠️ Keine passende Plattform erkannt für: {filename}, überspringe Import.")
        return

    import_script = SCRIPTS_DIR / script_name
    if not import_script.exists():
        print(f"⚠️ Script nicht gefunden: {script_name}, überspringe.")
        return

    try:
        subprocess.run(["python", str(import_script)], check=True)
        print(f"✅ {script_name} ausgeführt für {filename}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Import mit {script_name}: {e}")


def main():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    files = list(SOURCE_DIR.glob("*.csv"))
    if not files:
        print("ℹ️ Keine CSV-Dateien im Rohdatenordner gefunden.")
        return

    print(f"🚀 Starte Verarbeitung von {len(files)} Datei(en)...")
    for f in files:
        process_file(f)

    print("✅ Verarbeitung abgeschlossen.")


if __name__ == "__main__":
    main()
