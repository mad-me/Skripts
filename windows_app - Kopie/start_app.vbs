Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Aktueller Ordner
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Pfade definieren
venvPath = currentDir & "\.venv"
scriptPath = currentDir & "\src\main.py"
requirementsPath = currentDir & "\requirements.txt"

' Prüfen ob Virtual Environment existiert
If Not fso.FolderExists(venvPath) Then
    ' Virtual Environment erstellen
    WshShell.Run "python -m venv " & venvPath, 0, True
End If

' Aktivierung und Skript-Ausführung in einem Befehl
cmd = "cmd /c """ & venvPath & "\Scripts\activate.bat"" && "

' Requirements installieren falls vorhanden
If fso.FileExists(requirementsPath) Then
    cmd = cmd & "pip install -r requirements.txt && "
End If

' Python-Skript ausführen
cmd = cmd & "python """ & scriptPath & """"

' Ausführen ohne CMD-Fenster (0 = versteckt, False = nicht warten)
WshShell.Run cmd, 0, False