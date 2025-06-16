import sqlite3
import datetime
import re
from utils import finde_kennzeichen_per_ziffernfolge, match_driver_tokens

class WochenberichtDialog:
    def __init__(
        self,
        db_path,
        df_numeric,
        fahrername,
        combo_drv=None,
        combo_fz=None,
        fahrzeug=None,
        montage=None,
        kw=None,
        year=None,
        tarif=None,
        pauschale=None,
        tank_input=None,
        einsteiger_input=None,
        garage=None,
    ):
        self.db_path = db_path
        self.montage = montage
        self.kw = kw
        self.year = year
        self.tarif = tarif
        self.pauschale = pauschale

        # Speichere ComboBox für Fallback im speichern()
        self.vehicle_cb = combo_fz

        print("[DEBUG] combo_fz beim Init:", combo_fz)
        print("[DEBUG] currentText():", combo_fz.currentText() if combo_fz else "None")

        # Hilfsfunktion für float-Konvertierung
        def safe_float(val):
            try:
                return float(str(val).replace(",", ".").replace("€", "").replace(" ", ""))
            except Exception:
                return 0.0

        # -- DRIVER bestimmen: String > ComboBox > None
        if fahrername is not None:
            self.driver = fahrername
        elif combo_drv is not None:
            self.driver = combo_drv.currentText().strip()
        else:
            self.driver = None

        # -- VEHICLE bestimmen: String > ComboBox > None
        if fahrzeug:
            initial_kennzeichen = fahrzeug.strip()
        elif combo_fz is not None:
            initial_kennzeichen = combo_fz.currentText().strip()
        else:
            initial_kennzeichen = None
        self.vehicle = None
        self.kredit = 0.0
        self.versicherung = 0.0

        # Verbindung zur DB und Vehicle-Details
        try:
            conn = sqlite3.connect(self.db_path)
            if initial_kennzeichen:
                found = finde_kennzeichen_per_ziffernfolge(initial_kennzeichen, conn)
                self.vehicle = found or initial_kennzeichen
                cur = conn.cursor()
                cur.execute(
                    "SELECT kredit, versicherung FROM fahrzeuge WHERE kennzeichen = ?",
                    (self.vehicle,)
                )
                row = cur.fetchone()
                if row:
                    self.kredit = safe_float(row[0])
                    self.versicherung = safe_float(row[1])
            # Fallback df_numeric
            if not self.vehicle:
                try:
                    self.vehicle = df_numeric.loc["Summe", "Fahrer/Fahrzeug"].strip()
                except Exception:
                    self.vehicle = None
        except Exception:
            try:
                self.vehicle = df_numeric.loc["Summe", "Fahrer/Fahrzeug"].strip()
            except Exception:
                self.vehicle = None
        finally:
            try:
                conn.close()
            except:
                pass

        # Fallback ComboBox wie beim DRIVER
        if not self.vehicle and self.vehicle_cb is not None:
            sel = self.vehicle_cb.currentText().strip()
            if sel:
                self.vehicle = sel

        # -- Gesamtumsatz (Turnover)
        self.turnover = safe_float(df_numeric.loc["Summe", "gesamtumsatz"])

        # -- Einsteiger
        self.einsteiger = safe_float(einsteiger_input or 0.0)

        # -- Running Cost (Tank)
        self.running_cost = safe_float(tank_input or 0.0)

        # -- Garage (pro Montag)
        self.garage = safe_float(garage)
        self.garage_pro_montag = (self.garage / self.montage) if self.montage else 0.0

        # -- Loan & Insurance (pro Montag)
        self.loan = (self.kredit / self.montage) if self.montage else 0.0
        self.insurance = (self.versicherung / self.montage) if self.montage else 0.0

        # -- Accounting (immer 70 / montage)
        self.accounting = 70.0 / self.montage if self.montage else 0.0

        # --- DISPONENT (Vormonat, sonst aktueller Monat) ---
        self.disponent = 0.0
        try:
            if self.year and self.kw and self.vehicle:
                dt = datetime.date.fromisocalendar(self.year, self.kw, 1)
                first_of_month = dt.replace(day=1)
                last_month = (first_of_month - datetime.timedelta(days=1))
                # Monat/Jahr für Vormonat und aktuellen Monat
                monat_jahr_vor = f"{last_month.month:02d}/{str(last_month.year)[-2:]}"
                monat_jahr_akt = f"{first_of_month.month:02d}/{str(first_of_month.year)[-2:]}"

                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()

                # Erst Vormonat versuchen
                cur.execute(
                    """
                    SELECT Brutto FROM funk_40100
                    WHERE verkehrskennzeichen = ? AND monat_jahr = ?
                    LIMIT 1
                    """,
                    (self.vehicle, monat_jahr_vor)
                )
                row = cur.fetchone()

                # Falls Vormonat kein Ergebnis: aktueller Monat
                if not row or row[0] is None:
                    cur.execute(
                        """
                        SELECT Brutto FROM funk_40100
                        WHERE verkehrskennzeichen = ? AND monat_jahr = ?
                        LIMIT 1
                        """,
                        (self.vehicle, monat_jahr_akt)
                    )
                    row = cur.fetchone()

                self.disponent = (safe_float(row[0]) / self.montage) if row and row[0] is not None else 0.0
        except Exception as e:
            print(f"[DEBUG] Fehler Disponent: {e}")
            self.disponent = 0.0

        # --- HEALTH INSURANCE (Vormonat, sonst aktueller Monat) ---
        self.health_insurance = 0.0
        try:
            if self.year and self.kw and self.driver:
                dt = datetime.date.fromisocalendar(self.year, self.kw, 1)
                first_of_month = dt.replace(day=1)
                last_month = (first_of_month - datetime.timedelta(days=1))
                monat_jahr_vor = f"{last_month.month:02d}/{str(last_month.year)[-2:]}"
                monat_jahr_akt = f"{first_of_month.month:02d}/{str(first_of_month.year)[-2:]}"

                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()

                netto = None

                # Erst im Vormonat suchen
                cur.execute(
                    """
                    SELECT netto FROM gehalt WHERE dienstnehmernummer = (
                        SELECT dienstnehmernummer FROM fahrer WHERE vorname || ' ' || nachname = ?
                    ) AND monat_jahr = ?
                    LIMIT 1
                    """,
                    (self.driver, monat_jahr_vor)
                )
                row = cur.fetchone()
                if row and row[0] is not None:
                    netto = safe_float(row[0])
                else:
                    # Fallback: Suche im aktuellen Monat
                    cur.execute(
                        """
                        SELECT netto FROM gehalt WHERE dienstnehmernummer = (
                            SELECT dienstnehmernummer FROM fahrer WHERE vorname || ' ' || nachname = ?
                        ) AND monat_jahr = ?
                        LIMIT 1
                        """,
                        (self.driver, monat_jahr_akt)
                    )
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        netto = safe_float(row[0])

                # Wenn immer noch kein Wert, zweiten Namens-Match-Ansatz (erst Vormonat, dann aktueller Monat)
                if netto is None:
                    # Vormonat
                    cur.execute(
                        "SELECT vorname, nachname, netto FROM gehalt WHERE monat_jahr = ?",
                        (monat_jahr_vor,)
                    )
                    for vn, nn, n in cur.fetchall():
                        if match_driver_tokens(self.driver.split(), vn, nn):
                            netto = safe_float(n)
                            break
                if netto is None:
                    # Aktueller Monat
                    cur.execute(
                        "SELECT vorname, nachname, netto FROM gehalt WHERE monat_jahr = ?",
                        (monat_jahr_akt,)
                    )
                    for vn, nn, n in cur.fetchall():
                        if match_driver_tokens(self.driver.split(), vn, nn):
                            netto = safe_float(n)
                            break

                if netto is None:
                    netto = 0.0

                if netto < 515:
                    self.health_insurance = 75.0 / self.montage if self.montage else 0.0
                else:
                    self.health_insurance = (netto * 14 / 12 * 0.51) / self.montage if self.montage else 0.0
        except Exception as e:
            print(f"[DEBUG] Fehler health_insurance: {e}")
            self.health_insurance = 0.0

        # -- Income
        if self.tarif == "%":
            self.income = (
                self.turnover + self.einsteiger
                - self.garage_pro_montag
                - self.running_cost
            ) / 2
        else:
            self.income = safe_float(self.pauschale) if self.pauschale else 0.0

        # -- Umsatzsteuer
        self.sales_volume_tax = self.turnover * 0.1

        # -- Vorsteuer
        self.input_tax = (self.disponent + self.running_cost) / 6.0

        # -- Untaxed Income
        self.untaxed_income = (
            self.income
            - self.loan
            - self.insurance
            - self.accounting
            - self.disponent
            - self.health_insurance
            - self.sales_volume_tax
            + self.input_tax
        )

    def speichern(self):
        print("[DEBUG] vehicle_cb:", self.vehicle_cb)
        print("[DEBUG] currentText:", self.vehicle_cb.currentText() if self.vehicle_cb else "None")

        # Fallback auf ComboBox unabhängig vom Index
        if not self.vehicle and self.vehicle_cb is not None:
            sel = self.vehicle_cb.currentText().strip()
            if sel:
                self.vehicle = sel

        if not self.vehicle:
            return False, "Kein Fahrzeug ausgewählt! Der Datensatz kann nicht gespeichert werden."

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            garage_wochenwert_halbiert = (self.garage / self.montage / 2) if self.montage else 0.0
            cursor.execute(
                """
                INSERT INTO internal (
                    driver, vehicle, turnover, einsteiger, running_cost, garage, loan,
                    insurance, accounting, disponent, health_insurance, income,
                    sales_volume_tax, input_tax, untaxed_income, week
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.driver,
                    self.vehicle,
                    self.turnover,
                    self.einsteiger,
                    self.running_cost,
                    garage_wochenwert_halbiert,
                    self.loan,
                    self.insurance,
                    self.accounting,
                    self.disponent,
                    self.health_insurance,
                    self.income,
                    self.sales_volume_tax,
                    self.input_tax,
                    self.untaxed_income,
                    self.kw
                )
            )
            conn.commit()
            conn.close()
            return True, "Abrechnung erfolgreich gespeichert!"
        except Exception as e:
            return False, f"Fehler beim Speichern:\n{e}"