Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Aktueller Ordner
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Pfade definieren
venvPath = currentDir & "\.venv"
scriptPath = currentDir & "\src\main.py"
requirementsPath = currentDir & "\requirements.txt"
pythonExe = venvPath & "\Scripts\python.exe"

' Debug: Pfade anzeigen
'MsgBox "Current Dir: " & currentDir & vbCrLf & "Script Path: " & scriptPath & vbCrLf & "VEnv Path: " & venvPath

' Prüfen ob Python installiert ist
On Error Resume Next
WshShell.Run "python --version", 0, True
If Err.Number <> 0 Then
    MsgBox "Python ist nicht installiert oder nicht im PATH gefunden!", vbCritical, "Fehler"
    WScript.Quit
End If
On Error GoTo 0

' Prüfen ob main.py existiert
If Not fso.FileExists(scriptPath) Then
    MsgBox "main.py nicht gefunden in: " & scriptPath, vbCritical, "Fehler"
    WScript.Quit
End If

' Prüfen ob Virtual Environment existiert
If Not fso.FolderExists(venvPath) Then
    ' Virtual Environment erstellen
    result = WshShell.Run("python -m venv """ & venvPath & """", 0, True)
    If result <> 0 Then
        MsgBox "Fehler beim Erstellen des Virtual Environments", vbCritical, "Fehler"
        WScript.Quit
    End If
End If

' Aktivierung und Skript-Ausführung
cmd = """" & pythonExe & """ """ & scriptPath & """"

' Requirements installieren falls vorhanden (separat)
If fso.FileExists(requirementsPath) Then
    pipCmd = """" & venvPath & "\Scripts\pip.exe"" install -r """ & requirementsPath & """"
    WshShell.Run pipCmd, 0, True
End If

' Python-Skript ausführen (unsichtbar)
WshShell.Run cmd, 0, False