from playwright.sync_api import sync_playwright
import os
from datetime import datetime

def download_bolt_csv(email, password, download_dir="downloads"):
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 1. Loginseite aufrufen
        page.goto("https://fleets.bolt.eu/login?tab=email_username")

        # Falls Cookie-Hinweis vorhanden ist, wegklicken (optional)
        try:
            page.click("text=Alle akzeptieren", timeout=5000)
        except:
            pass  # kein Cookie-Banner

        # Warte explizit auf das Emailfeld via ID oder sichtbar
        page.wait_for_selector('#email', timeout=20000)
        page.fill('#email', email)
        page.fill('input[type="password"]', password)

        # Flexibler Button-Selektor für Anmelden/Log in
        try:
            page.click('button:has-text("Anmelden")', timeout=5000)
        except:
            page.click('button:has-text("Log in")', timeout=5000)

        # 2. Warten bis Seite vollständig geladen ist (egal welche URL)
        page.wait_for_load_state("networkidle")

        # 3. Navigiere zum Reiter "Umsätze" oder "Reports"
        try:
            page.click("text=Umsätze", timeout=5000)
        except:
            page.click("text=Reports", timeout=5000)

        page.wait_for_timeout(3000)

        # 4. Datum auf "Letzte Woche" oder "Last week" umstellen
        try:
            page.click("text=Heute", timeout=5000)
        except:
            page.click("text=Today", timeout=5000)

        try:
            page.click("text=Letzte Woche", timeout=5000)
        except:
            page.click("text=Last week", timeout=5000)

        page.wait_for_timeout(3000)

        # 5. Download starten
        with page.expect_download() as download_info:
            page.click("text=Download")
        download = download_info.value

        # 6. Speichern unter KW-basiertem Namen
        today = datetime.today()
        kw = today.isocalendar().week
        filename = f"Umsätze_KW{kw}.csv"
        download_path = os.path.join(download_dir, filename)
        download.save_as(download_path)

        print(f"✅ CSV gespeichert unter: {download_path}")

        browser.close()

if __name__ == "__main__":
    download_bolt_csv(
        email="mahmouddiab2008@yahoo.com",
        password="Mahmoud220281",
        download_dir="D:/Neuer Ordner/Umsätze"
    )
