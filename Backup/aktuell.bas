Attribute VB_Name = "Modul3"
Option Explicit

' Prüft, ob mindestens zwei Tokens im RowName vorkommen
Public Function MatchesAtLeastTwo(tokens As Variant, rowName As String) As Boolean
    Dim rowParts() As String, matchCount As Long
    Dim j As Long, k As Long
    rowParts = Split(Trim(rowName), " ")
    matchCount = 0
    For j = LBound(tokens) To UBound(tokens)
        For k = LBound(rowParts) To UBound(rowParts)
            If StrComp(tokens(j), rowParts(k), vbTextCompare) = 0 Then
                matchCount = matchCount + 1
                Exit For
            End If
        Next k
        If matchCount >= 2 Then
            MatchesAtLeastTwo = True
            Exit Function
        End If
    Next j
    MatchesAtLeastTwo = False
End Function

Public Sub fill()
    Dim basePath As String, weekFolder As String
    Dim fileUber As String, fileBolt As String, fullPayroll As String
    Dim fullUber As String, fullBolt As String
    Dim file40100 As String, full40100 As String
    Dim fileFunk As String, fullFunk As String
    Dim wbUber As Workbook, wbBolt As Workbook, wbPayroll As Workbook
    Dim wb40100 As Workbook, wbFunk As Workbook
    Dim wsUber As Worksheet, wsBolt As Worksheet, wsPayroll As Worksheet
    Dim ws40100 As Worksheet, wsFunk As Worksheet, wsDest As Worksheet
    Dim wsDriver As Worksheet, wsVeh As Worksheet, sht As Worksheet
    Dim nameOrig As String, nameTokens As Variant
    Dim dt As Date, dtCalc As Date, dtPrevMonth As Date
    Dim KW As Integer, mondays As Long
    Dim lastRow As Long, i As Long, r As Long
    Dim valUber As Double, valBolt As Double, valPayroll As Double
    Dim val40100 As Double, valFunk As Double, kredWert As Double, versWert As Double
    Dim rawDriverValue As Double
    Dim pwd As String, errStep As String
    Dim resp As VbMsgBoxResult, respHours As Variant, entryEinsteiger As Variant
    Dim targetName As String, activeName As String
    Dim substr3 As String, matchFound As Boolean
    Dim hdr As Range, colVK As Long, colKredit As Long, colVers As Long
    Dim summary As String

    On Error GoTo ErrHandler

    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.EnableEvents = False

    ' === Initial Setup ===
    errStep = "Initialisierung"
    basePath = "D:\Abrechnung\Umsätze\Uber Bolt\Excel\"
    Set wsDest = ActiveSheet
    pwd = "220281"

    nameOrig = Trim(wsDest.Range("F9").Value)
    If nameOrig = "" Then
        MsgBox "Kein Name in F9!", vbCritical
        GoTo CleanUp
    End If
    nameTokens = Split(nameOrig, " ")
    wsDest.Unprotect Password:=pwd

    dt = wsDest.Range("A3").Value
    If Not IsDate(dt) Then
        MsgBox "Ungültiges Datum in A3!", vbCritical
        GoTo CleanUp
    End If

    dtCalc = dt - 7
    KW = DatePart("ww", dtCalc, vbMonday, vbFirstFourDays)
    weekFolder = "KW" & KW & "\"
    If Dir(basePath & weekFolder, vbDirectory) = "" Then
        MsgBox "Ordner nicht gefunden: " & weekFolder, vbCritical
        GoTo CleanUp
    End If

    ' === Uber ===
    errStep = "Uber B3"
    fileUber = Dir(basePath & weekFolder & "Uber_KW" & KW & "*.xlsx")
    If fileUber = "" Then MsgBox "Uber-Datei nicht gefunden!", vbCritical: GoTo CleanUp
    fullUber = basePath & weekFolder & fileUber
    Set wbUber = Workbooks.Open(fullUber, ReadOnly:=True, UpdateLinks:=0)
    Set wsUber = wbUber.Sheets(1)
    lastRow = wsUber.Cells(wsUber.Rows.count, "A").End(xlUp).Row
    valUber = 0
    For i = 1 To lastRow
        If MatchesAtLeastTwo(nameTokens, wsUber.Cells(i, "A").Value) Then
            valUber = wsUber.Cells(i, "B").Value
            wsDest.Range("B9").Value = wsUber.Cells(i, "C").Value ' ?? Uber-Wert in B9
            Exit For
        End If
    Next i
    wbUber.Close SaveChanges:=False
    wsDest.Range("B3").Value = valUber

    ' === Bolt ===
    errStep = "Bolt C3"
    fileBolt = Dir(basePath & weekFolder & "Bolt_KW" & KW & "*.xlsx")
    If fileBolt = "" Then MsgBox "Bolt-Datei nicht gefunden!", vbCritical: GoTo CleanUp
    fullBolt = basePath & weekFolder & fileBolt
    Set wbBolt = Workbooks.Open(fullBolt, ReadOnly:=True, UpdateLinks:=0)
    Set wsBolt = wbBolt.Sheets(1)
    lastRow = wsBolt.Cells(wsBolt.Rows.count, "A").End(xlUp).Row
    valBolt = 0
    For i = 1 To lastRow
        If MatchesAtLeastTwo(nameTokens, wsBolt.Cells(i, "A").Value) Then
            valBolt = wsBolt.Cells(i, "B").Value
            wsDest.Range("C9").Value = wsBolt.Cells(i, "C").Value ' ?? Bolt-Wert in C9
            Exit For
        End If
    Next i
    wbBolt.Close SaveChanges:=False
    wsDest.Range("C3").Value = valBolt

    ' === Gehalt / J3 ===
    errStep = "Payroll J3"
    dtPrevMonth = DateAdd("m", -1, dt)
    fullPayroll = "D:\Abrechnung\Gehaltsabrechnung\Excel\Abrechnungen_" & _
                  Format(Month(dtPrevMonth), "00") & "_" & Year(dtPrevMonth) & ".xlsx"
    If Dir(fullPayroll) = "" Then
        MsgBox "Payroll-Datei nicht gefunden!", vbCritical
        GoTo CleanUp
    End If
    Set wbPayroll = Workbooks.Open(fullPayroll, ReadOnly:=True, UpdateLinks:=0)
    Set wsPayroll = wbPayroll.Sheets(1)
    lastRow = wsPayroll.Cells(wsPayroll.Rows.count, "A").End(xlUp).Row
    valPayroll = 0
    For i = 1 To lastRow
        If MatchesAtLeastTwo(nameTokens, wsPayroll.Cells(i, "A").Value) Then
            valPayroll = wsPayroll.Cells(i, "E").Value
            Exit For
        End If
    Next i
    wbPayroll.Close SaveChanges:=False

    mondays = 0
    For dtCalc = DateSerial(Year(dt), Month(dt), 1) To DateSerial(Year(dt), Month(dt) + 1, 0)
        If Weekday(dtCalc, vbMonday) = 1 Then mondays = mondays + 1
    Next dtCalc

    If valPayroll <> 0 Then
        wsDest.Range("J3").Value = valPayroll / IIf(mondays > 0, mondays, 1)
    Else
        respHours = InputBox("Kein Gehaltswert gefunden." & vbCrLf & _
                             "Bitte gemeldete Stunden eingeben:", "Stundenerfassung")
        If IsNumeric(respHours) Then
            Set wsDriver = ThisWorkbook.Sheets("driver")
            wsDriver.Range("X22").Value = CDbl(respHours)
            rawDriverValue = wsDriver.Range("AA34").Value
            wsDest.Range("J3").Value = rawDriverValue / IIf(mondays > 0, mondays, 1)
        Else
            MsgBox "Ungültige Eingabe. J3 wird auf 0 gesetzt.", vbExclamation
            wsDest.Range("J3").Value = 0
        End If
    End If

    ' === 40100 ===
errStep = "40100 D3"
file40100 = Dir("D:\Abrechnung\Umsätze\40100\Excel\40100_KW" & KW & "*.xlsx")
wsDest.Range("D3").Value = 0

If file40100 <> "" Then
    full40100 = "D:\Abrechnung\Umsätze\40100\Excel\" & file40100

    ' Arbeitsmappe im Hintergrund öffnen
    Set wb40100 = Workbooks.Open(full40100, ReadOnly:=True, UpdateLinks:=0)
    wb40100.Windows(1).Visible = False ' Sichtbarkeit unterdrücken

    targetName = Trim(wsDest.Name)
    Set ws40100 = Nothing

    For Each sht In wb40100.Worksheets
        If Trim(sht.Name) = targetName Then
            Set ws40100 = sht
            Exit For
        End If
    Next sht

    If Not ws40100 Is Nothing Then
        ' Zwischenspeichern, um Fokusverschiebung zu vermeiden
        Dim d3Wert As Variant, d8Wert As Variant

        ' D3: Einsteiger abfragen oder aus L3 übernehmen
        If MsgBox("Gab es Einsteiger?", vbYesNo + vbQuestion, "Einsteiger") = vbYes Then
            entryEinsteiger = InputBox("Bitte Anzahl Einsteiger eingeben:", "Einsteiger")
            If IsNumeric(entryEinsteiger) Then
                d3Wert = CDbl(entryEinsteiger)
            Else
                MsgBox "Ungültige Eingabe – D3 bleibt 0", vbExclamation
                d3Wert = 0
            End If
        Else
            d3Wert = ws40100.Range("L3").Value
        End If

        ' D8: immer aus E3
        d8Wert = ws40100.Range("E3").Value

        ' Werte auf Zielblatt übertragen (nach Schließen!)
        wb40100.Close SaveChanges:=False

        wsDest.Range("D3").Value = d3Wert
        wsDest.Range("D8").Value = d8Wert
    Else
        wb40100.Close SaveChanges:=False
        MsgBox "Kein passendes Blatt in der 40100-Datei gefunden!", vbExclamation
    End If
Else
    MsgBox "Keine 40100-Datei für KW" & KW & " gefunden!", vbExclamation
End If

    ' === Fahrzeugdaten ===
    errStep = "Fahrzeugdaten"
    Set wsVeh = ThisWorkbook.Sheets("vehicles")
    activeName = Trim(wsDest.Name)
    For Each hdr In wsVeh.Rows(1).Cells
        Select Case Trim(hdr.Value)
            Case "Verkehrskennzeichen": colVK = hdr.Column
            Case "Kredit": colKredit = hdr.Column
            Case "Versicherung": colVers = hdr.Column
        End Select
    Next hdr

    If colVK = 0 Or colKredit = 0 Or colVers = 0 Then
        MsgBox "Fahrzeugdaten-Spalten fehlen!", vbCritical
        wsDest.Range("F3,G3").Value = 0
        GoTo AfterVehicle
    End If

    matchFound = False
    lastRow = wsVeh.Cells(wsVeh.Rows.count, colVK).End(xlUp).Row
    For r = 2 To lastRow
        For i = 1 To Len(activeName) - 2
            substr3 = Mid(activeName, i, 3)
            If InStr(1, wsVeh.Cells(r, colVK).Value, substr3, vbTextCompare) > 0 Then
                matchFound = True
                Exit For
            End If
        Next i
        If matchFound Then Exit For
    Next r

    If matchFound Then
        kredWert = wsVeh.Cells(r, colKredit).Value
        versWert = wsVeh.Cells(r, colVers).Value
        wsDest.Range("F3").Value = kredWert / IIf(mondays > 0, mondays, 1)
        wsDest.Range("G3").Value = versWert / IIf(mondays > 0, mondays, 1)
    Else
        MsgBox "Fahrzeug nicht gefunden!", vbExclamation
        wsDest.Range("F3,G3").Value = 0
    End If

AfterVehicle:
    wsDest.Range("H3").Value = IIf(mondays > 0, 70 / mondays, 1)
    wsDest.Range("I3").Value = 0 ' Funk kommt ggf. später

    ' === Zusammenfassung ===
    With wsDest
        summary = "Aktualisierte Werte:" & vbCrLf & _
                  "Uber : " & FormatCurrency(.Range("B3").Value, 2) & vbCrLf & _
                  "Bolt : " & FormatCurrency(.Range("C3").Value, 2) & vbCrLf & _
                  "40100: " & FormatCurrency(.Range("D3").Value, 2) & vbCrLf & _
                  "Kredit : " & FormatCurrency(.Range("F3").Value, 2) & vbCrLf & _
                  "Versicherung : " & FormatCurrency(.Range("G3").Value, 2) & vbCrLf & _
                  "Buchhaltung : " & FormatCurrency(.Range("H3").Value, 2) & vbCrLf & _
                  "Krankenkassa: " & FormatCurrency(.Range("J3").Value, 2)
    End With
    MsgBox summary, vbInformation, "Zusammenfassung"

    resp = MsgBox("Blatt wieder schützen?", vbYesNo + vbQuestion, "Schutz aktivieren")
    If resp = vbYes Then wsDest.Protect Password:=pwd, UserInterfaceOnly:=True

   With wsDest
    ' === Texte einfügen und formatieren ===
    .Range("A8").Value = "Bankomat"
    .Range("A9").Value = "Bargeld"

    With .Range("A8:A9")
        .HorizontalAlignment = xlLeft
        .Font.Size = 9
    End With

    ' === Formeln für Zeilen 8 und 9 ===
    .Range("D9").Formula = "=D3-D8"
    .Range("C8").Formula = "=C3-C9"
    .Range("B8").Formula = "=B3-B9"
    .Range("E8").Formula = "=SUM(B8:D8)"
    .Range("E9").Formula = "=SUM(B9:D9)"

    ' === Formel für K3 (LET-Funktion mit Bedingungen) ===
    .Range("K3").FormulaLocal = _
        "=LET(Name;F9;" & _
        "Zeile;VERGLEICH(Name;driver!E:E;0);" & _
        "Kenn;INDEX(driver!H:H;Zeile);" & _
        "Schwelle;INDEX(driver!J:J;Zeile);" & _
        "Basis;INDEX(driver!I:I;Zeile);" & _
        "SumAll;SUMME(B3:D3);" & _
        "SumPC;SUMME(B3:C3);" & _
        "WENN(ISTFEHLER(Zeile);" & _
        """Name nicht gefunden"";" & _
        "WENN(Kenn=""%"";(SumAll-E3)/2;" & _
        "WENN(Kenn=""P"";" & _
        "WENN(SumPC>Schwelle;(SumPC-Schwelle)*0,1+Basis;Basis);" & _
        "0))))"

    ' === Formel für K9 ===
    .Range("K9").Formula = "=K3-E8"
End With

' === Funk-Wert in I3 aus externer Datei holen (Vormonat, Matching mit 3 Ziffern, geteilt durch Montage) ===
errStep = "Funk I3"

Dim fileFunkName As String, fullFunkPath As String
Dim originalName As String, cleanedName As String
Dim funkRow As Long
Dim dtFunk As Date, dtMonat As Date, dtEnde As Date
Dim montagsCount As Long

' Berechne Vormonat basierend auf A3
dtFunk = DateAdd("m", -1, wsDest.Range("A3").Value)

' Erstelle Dateinamen für Vormonat
fileFunkName = "Rechnung_Funk_" & Format(dtFunk, "MM-yyyy") & ".xlsx"
fullFunkPath = "D:\Abrechnung\Funk\Rechnungen\" & fileFunkName

If Dir(fullFunkPath) = "" Then
    MsgBox "Funk-Datei nicht gefunden: " & fileFunkName, vbExclamation
    wsDest.Range("I3").Value = 0
    GoTo SkipFunk
End If

Set wbFunk = Workbooks.Open(fullFunkPath, ReadOnly:=True, UpdateLinks:=0)
Set wsFunk = wbFunk.Sheets(1)

' Bereinige Blattnamen
originalName = Trim(wsDest.Name)
cleanedName = Replace(originalName, " ", "")
If Left(cleanedName, 1) = "W" Then cleanedName = Mid(cleanedName, 2)
If Right(cleanedName, 2) = "TX" Then cleanedName = Left(cleanedName, Len(cleanedName) - 2)

' Anzahl Montage im aktuellen Monat (nicht im Vormonat!)
dtMonat = DateSerial(Year(wsDest.Range("A3").Value), Month(wsDest.Range("A3").Value), 1)
dtEnde = DateSerial(Year(dtMonat), Month(dtMonat) + 1, 0)
montagsCount = 0
Do While dtMonat <= dtEnde
    If Weekday(dtMonat, vbMonday) = 1 Then montagsCount = montagsCount + 1
    dtMonat = dtMonat + 1
Loop
If montagsCount = 0 Then montagsCount = 1 ' Fallback

' Initialwert
wsDest.Range("I3").Value = 0

With wsFunk
    Dim lastFunkRow As Long
    Dim cmpName As String, cmpNameClean As String
    Dim numStr As String
    Dim rawFunkValue As Double
    lastFunkRow = .Cells(.Rows.count, "D").End(xlUp).Row

    For funkRow = 1 To lastFunkRow
        cmpName = Trim(.Cells(funkRow, "D").Value)
        cmpNameClean = Replace(cmpName, " ", "")
        If Left(cmpNameClean, 1) = "W" Then cmpNameClean = Mid(cmpNameClean, 2)
        If Right(cmpNameClean, 2) = "TX" Then cmpNameClean = Left(cmpNameClean, Len(cmpNameClean) - 2)

        If InStr(1, cmpNameClean, cleanedName, vbTextCompare) > 0 Or _
           InStr(1, cleanedName, cmpNameClean, vbTextCompare) > 0 Then

            For i = 1 To Len(cleanedName) - 2
                numStr = Mid(cleanedName, i, 3)
                If IsNumeric(numStr) Then
                    If InStr(1, cmpNameClean, numStr) > 0 Then
                        rawFunkValue = .Cells(funkRow, "C").Value
                        wsDest.Range("I3").Value = rawFunkValue / montagsCount
                        Exit For
                    End If
                End If
                Next i
                End If
            Next funkRow
        End With
        
        ' === E3: Fahrer-Ausgaben berechnen ===
    errStep = "E3 Fahrer-Ausgaben"
    
    Dim zeileDriver As Variant
    Dim ausgabeWert As Double, tankWert As Double, sonstigeWert As Double
    Dim geteilterFahrerWert As Double

    ' Werte initialisieren
    ausgabeWert = 0
    tankWert = 0
    sonstigeWert = 0
    geteilterFahrerWert = 0

    ' Fahrerblatt durchsuchen: Name aus F9 in Spalte E suchen
    zeileDriver = Application.Match(nameOrig, ThisWorkbook.Sheets("driver").Range("E:E"), 0)
    If Not IsError(zeileDriver) And zeileDriver > 0 Then
        ausgabeWert = ThisWorkbook.Sheets("driver").Cells(zeileDriver, "F").Value
        If mondays > 0 Then
            geteilterFahrerWert = ausgabeWert / mondays
        Else
            geteilterFahrerWert = ausgabeWert ' Fallback, sollte nie 0 sein
        End If
    End If

    ' Tankrechnung abfragen
    respHours = InputBox("Tankrechnung?", "Eingabe erforderlich")
    If IsNumeric(respHours) Then
        tankWert = CDbl(respHours)
    Else
        MsgBox "Ungültige Eingabe für Tankrechnung. Wert = 0", vbExclamation
    End If

    ' Sonstige Ausgaben optional abfragen
    If MsgBox("Gab es sonstige Ausgaben?", vbYesNo + vbQuestion, "Sonstiges") = vbYes Then
        entryEinsteiger = InputBox("Bitte Betrag für sonstige Ausgaben eingeben:", "Sonstige Ausgaben")
        If IsNumeric(entryEinsteiger) Then
            sonstigeWert = CDbl(entryEinsteiger)
        Else
            MsgBox "Ungültige Eingabe für sonstige Ausgaben. Wert = 0", vbExclamation
        End If
    End If

    ' Gesamtsumme berechnen und in E3 schreiben
    wsDest.Range("E3").Value = geteilterFahrerWert + tankWert + sonstigeWert
        
FoundMatch:
        wbFunk.Close SaveChanges:=False
        
SkipFunk:



CleanUp:
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    Application.EnableEvents = True
    Exit Sub

ErrHandler:
    MsgBox "Fehler in Schritt: " & errStep & vbCrLf & Err.Description, vbCritical
    Resume CleanUp
End Sub

