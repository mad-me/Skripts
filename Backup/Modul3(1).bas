Attribute VB_Name = "Modul3"
' Prüft, ob ein Worksheet im Workbook existiert
Private Function WorksheetExists(wb As Workbook, sheetName As String) As Boolean
    Dim sht As Worksheet
    On Error Resume Next
    Set sht = wb.Worksheets(sheetName)
    WorksheetExists = Not sht Is Nothing
    On Error GoTo 0
End Function

' Hilfsfunktion: True, wenn mindestens 2 Wort-Tokens im RowName vorkommen
Public Function MatchesAtLeastTwo(tokens As Variant, rowName As String) As Boolean
    Dim rowParts() As String, matchCount As Long
    Dim j As Long, k As Long

    ' In einzelne Wörter splitten
    rowParts = Split(Trim(rowName), " ")
    matchCount = 0

    ' Über alle Tokens und Wortteile iterieren
    For j = LBound(tokens) To UBound(tokens)
        For k = LBound(rowParts) To UBound(rowParts)
            If StrComp(tokens(j), rowParts(k), vbTextCompare) = 0 Then
                matchCount = matchCount + 1
                Exit For
            End If
        Next k
        ' Sobald zwei Übereinstimmungen gefunden wurden, True zurückgeben
        If matchCount >= 2 Then
            MatchesAtLeastTwo = True
            Exit Function
        End If
    Next j

    ' Weniger als zwei Matches: False
    MatchesAtLeastTwo = False
End Function


Public Sub fill()
    Dim wsDest        As Worksheet
    Dim wsUber        As Worksheet
    Dim wsBolt        As Worksheet
    Dim wsPayroll     As Worksheet
    Dim ws40100       As Worksheet
    Dim wsFunk        As Worksheet
    Dim wsDriver      As Worksheet
    Dim wsVeh         As Worksheet
    Dim nameTokens    As Variant
    Dim dt            As Date, dtCalc As Date
    Dim KW            As Integer
    Dim basePath      As String, weekFolder As String
    Dim fileUber      As String, fileBolt As String
    Dim fileBoltXLSX  As String, fileBoltXLSB As String
    Dim filePayroll   As String
    Dim file40100     As String
    Dim fileFunk      As String
    Dim mondays       As Long
    Dim errStep       As String
    Dim d             As Date, firstOfMonth As Date, lastOfMonth As Date
    Dim lastRow       As Long, i As Long, r As Long
    Dim valUber       As Double, valBolt As Double
    Dim valPayroll    As Double, val40100 As Double
    Dim valFunk       As Double, kredWert As Double, versWert As Double
    Dim colVK         As Long, colKredit As Long, colVers As Long
    Dim hdr           As Range
    Dim pwd           As String

    On Error GoTo ErrHandler
    errStep = "Init"

    ' Aktives Blatt verwenden
    Set wsDest = ActiveSheet

    ' Basisverzeichnis dynamisch vom Speicherort ableiten
    basePath = ThisWorkbook.Path & Application.PathSeparator & "Abrechnung" & Application.PathSeparator

    pwd = "DeinPasswort"

    ' Anwendung optimieren
    With Application
        .ScreenUpdating = False
        .Calculation = xlCalculationManual
        .EnableEvents = False
    End With

    ' Blattschutz aufheben
    errStep = "Unprotect"
    With wsDest: .Unprotect Password:=pwd: End With

    ' Datum & Name einlesen
    errStep = "Read Date/Name"
    With wsDest
        dt = .Range("A3").Value
        If Not IsDate(dt) Then Err.Raise vbObjectError + 1, , "Ungültiges Datum in A3"
        dtCalc = dt - 7
        KW = DatePart("ww", dtCalc, vbMonday, vbFirstFourDays)
        nameTokens = Split(.Range("F9").Value, " ")
    End With

    ' Anzahl Montage im Monat bestimmen
    firstOfMonth = DateSerial(Year(dt), Month(dt), 1)
    lastOfMonth = DateSerial(Year(dt), Month(dt) + 1, 0)
    For d = firstOfMonth To lastOfMonth
        If Weekday(d, vbMonday) = 1 Then mondays = mondays + 1
    Next d

    ' KW-Ordner definieren
    weekFolder = "KW" & KW & Application.PathSeparator
    errStep = "FolderCheck"
    If Dir(basePath & weekFolder, vbDirectory) = "" Then Err.Raise vbObjectError + 2, , "Ordner nicht gefunden: " & basePath & weekFolder

    ' Uber auslesen
    errStep = "Uber"
    fileUber = Dir(basePath & weekFolder & "Uber_KW" & KW & "*.xlsx")
    If fileUber = "" Then Err.Raise vbObjectError + 3, , "Keine Uber-Datei für KW " & KW
    Set wsUber = Workbooks.Open(basePath & weekFolder & fileUber, ReadOnly:=True, UpdateLinks:=0).Sheets(1)
    valUber = wsUber.Cells(2, "C").Value
    With wsDest: .Range("B9").Value = valUber: .Range("B9").NumberFormat = "#,##0.00": End With
    wsUber.Parent.Close SaveChanges:=False

    ' Bolt auslesen
    errStep = "Bolt"
    fileBoltXLSX = Dir(basePath & weekFolder & "Bolt_KW" & KW & "*.xlsx")
    If fileBoltXLSX <> "" Then fileBolt = fileBoltXLSX Else fileBolt = Dir(basePath & weekFolder & "Bolt_KW" & KW & "*.xlsb")
    If fileBolt = "" Then Err.Raise vbObjectError + 4, , "Keine Bolt-Datei für KW " & KW
    Set wsBolt = Workbooks.Open(basePath & weekFolder & fileBolt, ReadOnly:=True, UpdateLinks:=0).Sheets(1)
    valBolt = wsBolt.Cells(3, "C").Value
    With wsDest: .Range("C9").Value = valBolt: .Range("C9").NumberFormat = "#,##0.00": End With
    wsBolt.Parent.Close SaveChanges:=False

    ' Payroll auslesen
    errStep = "Payroll"
    filePayroll = Dir(basePath & weekFolder & "Payroll_KW" & KW & "*.xlsx")
    If filePayroll = "" Then Err.Raise vbObjectError + 5, , "Keine Payroll-Datei für KW " & KW
    Set wsPayroll = Workbooks.Open(basePath & weekFolder & filePayroll, ReadOnly:=True, UpdateLinks:=0).Sheets(1)
    valPayroll = wsPayroll.Cells(2, "C").Value
    With wsDest: .Range("D9").Value = valPayroll: .Range("D9").NumberFormat = "#,##0.00": End With
    wsPayroll.Parent.Close SaveChanges:=False

    ' Konto 40100 auslesen
    errStep = "40100"
    file40100 = Dir(basePath & weekFolder & "40100_KW" & KW & "*.xlsx")
    If file40100 = "" Then Err.Raise vbObjectError + 6, , "Keine 40100-Datei für KW " & KW
    Set ws40100 = Workbooks.Open(basePath & weekFolder & file40100, ReadOnly:=True, UpdateLinks:=0).Sheets(1)
    val40100 = ws40100.Cells(2, "C").Value
    With wsDest: .Range("E9").Value = val40100: .Range("E9").NumberFormat = "#,##0.00": End With
    ws40100.Parent.Close SaveChanges:=False

    ' Funk auslesen
    errStep = "Funk"
    fileFunk = Dir(basePath & weekFolder & "Funk_KW" & KW & "*.xlsx")
    If fileFunk = "" Then Err.Raise vbObjectError + 7, , "Keine Funk-Datei für KW " & KW
    Set wsFunk = Workbooks.Open(basePath & weekFolder & fileFunk, ReadOnly:=True, UpdateLinks:=0).Sheets(1)
    valFunk = wsFunk.Cells(2, "C").Value
    With wsDest: .Range("F9").Value = valFunk: .Range("F9").NumberFormat = "#,##0.00": End With
    wsFunk.Parent.Close SaveChanges:=False

    ' Fahrerwerte (driver)
    errStep = "Driver"
    If Not WorksheetExists(ThisWorkbook, "driver") Then Err.Raise vbObjectError + 8, , "Sheet 'driver' nicht gefunden"
    Set wsDriver = ThisWorkbook.Worksheets("driver")
    With wsDriver
        lastRow = .Cells(.Rows.count, "E").End(xlUp).Row
        For i = 1 To lastRow
            If MatchesAtLeastTwo(nameTokens, .Cells(i, "E").Value) Then
                kredWert = .Cells(i, "G").Value: Exit For
            End If
        Next i
        .Range("X22").Value = kredWert
    End With

    ' Fahrzeuge (vehicles)
    errStep = "Fahrzeug"
    If Not WorksheetExists(ThisWorkbook, "vehicles") Then Err.Raise vbObjectError + 9, , "Sheet 'vehicles' nicht gefunden"
    Set wsVeh = ThisWorkbook.Worksheets("vehicles")
    With wsVeh.Rows(1)
        For Each hdr In .Cells
            Select Case Trim(hdr.Value)
                Case "Verkehrskennzeichen": colVK = hdr.Column
                Case "Kredit":              colKredit = hdr.Column
                Case "Versicherung":        colVers = hdr.Column
            End Select
        Next hdr
    End With
    lastRow = wsVeh.Cells(wsVeh.Rows.count, colVK).End(xlUp).Row
    For r = 2 To lastRow
        If Left(wsVeh.Cells(r, colVK).Value, 3) = Left(wsDest.Name, 3) Then
            kredWert = wsVeh.Cells(r, colKredit).Value: versWert = wsVeh.Cells(r, colVers).Value: Exit For
        End If
    Next r
    With wsDest
        .Range("F3").Value = IIf(IsNumeric(kredWert), kredWert / mondays, 0)
        .Range("G3").Value = IIf(IsNumeric(versWert), versWert / mondays, 0)
    End With

    ' Formeln und Abschlussformatierungen
    With wsDest
        .Range("K3").FormulaLocal = _
            "=LET(Name;F9;Zeile;VERGLEICH(Name;driver!E:E;0);Kenn;INDEX(driver!H:H;Zeile);Basis;INDEX(driver!I:I;Zeile);Schwelle;INDEX(driver!J:J;Zeile);Summe;SUMME(B3:D3);" & _
            ""WENN(ISTFEHLER(Zeile);""Name nicht gefunden"";WENN(Kenn=""%"";(Summe-E3)/2;WENN(Kenn=""P"";(Summe-C3>Schwelle)*(Summe-C3-Schwelle)*0,1+Basis;Basis)))"
        .Range("K9").FormulaLocal = "=K3-E8"
        .Range("A8").Value = "Bankomat"
        .Range("A9").Value = "Bargeld"
        With .Range("A8:A9")
            .HorizontalAlignment = xlRight
            .VerticalAlignment = xlCenter
            .Font.Size = 9
        End With
        .Range("E8").FormulaLocal = "=SUMME(B8:D8)"
        .Range("E9").FormulaLocal = "=SUMME(B9:D9)"
        .Range("B8").FormulaLocal = "=B3-B9"
        .Range("C8").FormulaLocal = "=C3-C9"
    End With

    ' Anwendung zurücksetzen
    With Application
        .Calculation = xlCalculationAutomatic
        .ScreenUpdating = True
        .EnableEvents = True
    End With
    Exit Sub

ErrHandler:
    MsgBox "Fehler in Schritt " & errStep & ": " & Err.Number & " – " & Err.Description, vbCritical
    On Error Resume Next
    With Application
        .Calculation = xlCalculationAutomatic
        .ScreenUpdating = True
        .EnableEvents = True
    End With
End Sub


