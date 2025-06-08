' Hilfsfunktion: True, wenn mindestens 2 Wort-Tokens im RowName vorkommen
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
    Dim basePath        As String
    Dim weekFolder      As String
    Dim fileUber        As String, fileBolt   As String, fullPayroll As String
    Dim fullUber        As String, fullBolt   As String
    Dim file40100       As String, full40100  As String
    Dim fileFunk        As String, fullFunk   As String
    Dim wbUber          As Workbook
    Dim wbBolt          As Workbook
    Dim wbPayroll       As Workbook
    Dim wb40100         As Workbook
    Dim wbFunk          As Workbook
    Dim wsUber          As Worksheet
    Dim wsBolt          As Worksheet
    Dim wsPayroll       As Worksheet
    Dim ws40100         As Worksheet
    Dim wsFunk          As Worksheet
    Dim wsDest          As Worksheet
    Dim wsDriver        As Worksheet
    Dim wsVers          As Worksheet         ' Versicherungen-Sheet
    Dim sht             As Worksheet
    Dim nameOrig        As String
    Dim nameTokens      As Variant
    Dim dt              As Date
    Dim dtCalc          As Date
    Dim dtPrevMonth     As Date
    Dim KW              As Integer
    Dim lastRow         As Long
    Dim i               As Long
    Dim valUber         As Double
    Dim valBolt         As Double
    Dim valPayroll      As Double
    Dim val40100        As Double
    Dim valFunk         As Double
    Dim mondays         As Long
    Dim pwd             As String
    Dim errStep         As String
    Dim resp            As VbMsgBoxResult
    Dim respHours       As Variant
    Dim rawDriverValue  As Double
    Dim entryEinsteiger As Variant
    Dim targetName      As String
    Dim lastVers        As Long               ' für Versicherungen
    Dim rowVers         As Long               ' für Versicherungen
    Dim valVers         As Double             ' Versicherungswert
    Dim substr3         As String             ' 3-Zeichen-Substring
    Dim matchFound      As Boolean            ' Flag, wenn Match

    On Error GoTo ErrHandler

    ' Hintergrund-Modus
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.EnableEvents = False

    ' --- Initialisierung ---
    errStep = "Init"
    basePath = "D:\Abrechnung\Umsätze\Uber Bolt\Excel\"
    Set wsDest = ActiveSheet
    pwd = "220281"
    nameOrig = Trim(wsDest.Range("F9").Value)
    If nameOrig = "" Then
        MsgBox "Kein Name in F9!", vbCritical
        GoTo CleanUp
    End If
    nameTokens = Split(nameOrig, " ")

    ' Blattschutz aufheben
    errStep = "Unprotect"
    wsDest.Unprotect Password:=pwd

    ' Datum aus A3
    errStep = "Read Date"
    dt = wsDest.Range("A3").Value
    If Not IsDate(dt) Then
        MsgBox "Ungültiges Datum in A3!", vbCritical
        GoTo CleanUp
    End If

    ' KW berechnen (Datum -7 Tage)
    errStep = "Calc KW"
    dtCalc = dt - 7
    KW = DatePart("ww", dtCalc, vbMonday, vbFirstFourDays)
    weekFolder = "KW" & KW & "\"
    If Dir(basePath & weekFolder, vbDirectory) = "" Then
        MsgBox "Ordner nicht gefunden: " & weekFolder, vbCritical
        GoTo CleanUp
    End If

    ' --- Uber ? B3 ---
    errStep = "Uber B3"
    fileUber = Dir(basePath & weekFolder & "Uber_KW" & KW & "*.xlsx")
    If fileUber = "" Then
        MsgBox "Uber-Datei nicht gefunden!", vbCritical
        GoTo CleanUp
    End If
    fullUber = basePath & weekFolder & fileUber
    Set wbUber = Workbooks.Open(fileName:=fullUber, ReadOnly:=True, UpdateLinks:=0)
    wbUber.Windows(1).Visible = False
    Set wsUber = wbUber.Sheets(1)
    lastRow = wsUber.Cells(wsUber.Rows.count, "A").End(xlUp).Row
    valUber = 0
    For i = 1 To lastRow
        If MatchesAtLeastTwo(nameTokens, wsUber.Cells(i, "A").Value) Then
            valUber = wsUber.Cells(i, "B").Value
            Exit For
        End If
    Next i
    wbUber.Close SaveChanges:=False
    wsDest.Range("B3").Value = valUber

    ' --- Bolt ? C3 ---
    errStep = "Bolt C3"
    fileBolt = Dir(basePath & weekFolder & "Bolt_KW" & KW & "*.xlsx")
    If fileBolt = "" Then
        MsgBox "Bolt-Datei nicht gefunden!", vbCritical
        GoTo CleanUp
    End If
    fullBolt = basePath & weekFolder & fileBolt
    Set wbBolt = Workbooks.Open(fileName:=fullBolt, ReadOnly:=True, UpdateLinks:=0)
    wbBolt.Windows(1).Visible = False
    Set wsBolt = wbBolt.Sheets(1)
    lastRow = wsBolt.Cells(wsBolt.Rows.count, "A").End(xlUp).Row
    valBolt = 0
    For i = 1 To lastRow
        If MatchesAtLeastTwo(nameTokens, wsBolt.Cells(i, "A").Value) Then
            valBolt = wsBolt.Cells(i, "B").Value
            Exit For
        End If
    Next i
    wbBolt.Close SaveChanges:=False
    wsDest.Range("C3").Value = valBolt

    ' --- Gehalt ? J3 (Vormonat) ---
    errStep = "Payroll J3"
    dtPrevMonth = DateAdd("m", -1, dt)
    fullPayroll = "D:\Abrechnung\Gehaltsabrechnung\Excel\Abrechnungen_" & _
                  Format(Month(dtPrevMonth), "00") & "_" & Year(dtPrevMonth) & ".xlsx"
    If Dir(fullPayroll) = "" Then
        MsgBox "Payroll-Datei nicht gefunden!", vbCritical
        GoTo CleanUp
    End If
    Set wbPayroll = Workbooks.Open(fileName:=fullPayroll, ReadOnly:=True, UpdateLinks:=0)
    wbPayroll.Windows(1).Visible = False
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

    ' Montage zählen
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

    ' --- 40100 ? D3 (trim + Ja/Nein + Eingabe-Fallback) ---
    errStep = "40100 D3"
    file40100 = Dir("D:\Abrechnung\Umsätze\40100\Excel\40100_KW" & KW & "*.xlsx")
    wsDest.Range("D3").Value = 0
    If file40100 <> "" Then
        full40100 = "D:\Abrechnung\Umsätze\40100\Excel\" & file40100
        Set wb40100 = Workbooks.Open(fileName:=full40100, ReadOnly:=True, UpdateLinks:=0)
        wb40100.Windows(1).Visible = False
        targetName = Trim(wsDest.Name)
        Set ws40100 = Nothing
        For Each sht In wb40100.Worksheets
            If Trim(sht.Name) = targetName Then
                Set ws40100 = sht
                Exit For
            End If
        Next sht

        If MsgBox("Gab es Einsteiger?", vbYesNo + vbQuestion, "Einsteiger") = vbYes Then
            entryEinsteiger = InputBox("Bitte Anzahl Einsteiger eingeben:", "Einsteiger")
            If IsNumeric(entryEinsteiger) Then
                wsDest.Range("D3").Value = CDbl(entryEinsteiger)
            Else
                MsgBox "Ungültige Eingabe – D3 bleibt 0", vbExclamation
            End If
        Else
            If Not ws40100 Is Nothing Then
                wsDest.Range("D3").Value = ws40100.Range("L3").Value
            Else
                MsgBox "Kein Blatt '" & targetName & "' in " & file40100, vbExclamation
            End If
        End If

        wb40100.Close SaveChanges:=False
    Else
        MsgBox "Keine 40100-Datei für KW" & KW & " gefunden!", vbExclamation
    End If

    ' --- Funk ? I3 (erstes Blatt, Name trimmed) ---
    errStep = "Funk I3"
    fileFunk = "Rechnung_Funk_" & Format(Month(dtPrevMonth), "00") & "-" & Year(dtPrevMonth) & ".xlsx"
    fullFunk = "D:\Abrechnung\Funk\Rechnungen\" & fileFunk
    valFunk = 0
    If Dir(fullFunk) <> "" Then
        Set wbFunk = Workbooks.Open(fileName:=fullFunk, ReadOnly:=True, UpdateLinks:=0)
        wbFunk.Windows(1).Visible = False
        Set wsFunk = wbFunk.Sheets(1)
        lastRow = wsFunk.Cells(wsFunk.Rows.count, "A").End(xlUp).Row
        For i = 1 To lastRow
            If StrComp(Trim(wsFunk.Cells(i, "A").Value), Trim(wsDest.Name), vbTextCompare) = 0 Then
                valFunk = wsFunk.Cells(i, "C").Value
                Exit For
            End If
        Next i
        wbFunk.Close SaveChanges:=False
    End If
    wsDest.Range("I3").Value = IIf(mondays > 0, valFunk / mondays, 0)

    ' --- 70 ÷ Montage ? H3 ---
    errStep = "Calc H3"
    wsDest.Range("H3").Value = IIf(mondays > 0, 70 / mondays, 0)
        ' --- Fahrzeug-Block ? F3 & G3 (Verkehrskennzeichen 3-Zeichen-Match) ---
    errStep = "Fahrzeug-Block"
    Dim wsVeh       As Worksheet
    Dim hdr         As Range
    Dim colVK       As Long, colKredit As Long, colVers As Long
    Dim lastVeh     As Long, r As Long
    Dim activeName  As String
    Dim kredWert    As Double, versWert As Double
    
    Set wsVeh = ThisWorkbook.Sheets("vehicles")
    activeName = Trim(wsDest.Name)
    
    ' 1) Spalten ermitteln
    For Each hdr In wsVeh.Rows(1).Cells
        Select Case Trim(hdr.Value)
            Case "Verkehrskennzeichen": colVK = hdr.Column
            Case "Kredit":              colKredit = hdr.Column
            Case "Versicherung":        colVers = hdr.Column
        End Select
    Next hdr
    
    If colVK = 0 Or colKredit = 0 Or colVers = 0 Then
        MsgBox "Spalten 'Verkehrskennzeichen', 'Kredit' oder 'Versicherung' nicht gefunden!", vbCritical
        wsDest.Range("F3,G3").Value = 0
        GoTo AfterVehicle
    End If
    
    ' 2) Suche nach 3-Zeichen-Substring
    lastVeh = wsVeh.Cells(wsVeh.Rows.count, colVK).End(xlUp).Row
    matchFound = False
    For r = 2 To lastVeh
        For i = 1 To Len(activeName) - 2
            substr3 = Mid(activeName, i, 3)
            If InStr(1, wsVeh.Cells(r, colVK).Value, substr3, vbTextCompare) > 0 Then
                matchFound = True
                Exit For
            End If
        Next i
        If matchFound Then Exit For
    Next r
    
    If Not matchFound Then
        MsgBox "Fahrzeug nicht gefunden", vbExclamation
        wsDest.Range("F3,G3").Value = 0
        GoTo AfterVehicle
    End If
    
    ' 3) Werte auslesen und durch Montage teilen
    kredWert = wsVeh.Cells(r, colKredit).Value
    versWert = wsVeh.Cells(r, colVers).Value
    
    wsDest.Range("F3").Value = IIf(IsNumeric(kredWert), kredWert / IIf(mondays > 0, mondays, 1), 0)
    wsDest.Range("G3").Value = IIf(IsNumeric(versWert), versWert / IIf(mondays > 0, mondays, 1), 0)
    
AfterVehicle:
    ' hier geht’s weiter mit Deinem Zusammenfassungs-PopUp…



    ' Blattschutz wieder aktivieren?
    resp = MsgBox("Blatt wieder schützen?", vbYesNo + vbQuestion, "Schutz aktivieren")
    If resp = vbYes Then wsDest.Protect Password:=pwd, UserInterfaceOnly:=True

          ' --- Zusammenfassungs-PopUp mit allen Werten (2 Dez., €) inkl. F3 ---
    Dim summary As String
    With wsDest
        summary = "Aktualisierte Werte:" & vbCrLf & _
                  "Uber : " & FormatCurrency(.Range("B3").Value, 2) & vbCrLf & _
                  "Bolt : " & FormatCurrency(.Range("C3").Value, 2) & vbCrLf & _
                  "40100: " & FormatCurrency(.Range("D3").Value, 2) & vbCrLf & _
                  "Kredit : " & FormatCurrency(.Range("F3").Value, 2) & vbCrLf & _
                  "Versicherung : " & FormatCurrency(.Range("G3").Value, 2) & vbCrLf & _
                  "Buchhaltung : " & FormatCurrency(.Range("H3").Value, 2) & vbCrLf & _
                  "Funk : " & FormatCurrency(.Range("I3").Value, 2) & vbCrLf & _
                  "Krankenkassa: " & FormatCurrency(.Range("J3").Value, 2)
    End With
    MsgBox summary, vbInformation, "Zusammenfassung"



CleanUp:
    ' Hintergrund-Modus zurücksetzen
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    Application.EnableEvents = True
    Exit Sub

ErrHandler:
    MsgBox "Fehler in Schritt: " & errStep & vbCrLf & Err.Description, vbCritical
    Resume CleanUp
End Sub





