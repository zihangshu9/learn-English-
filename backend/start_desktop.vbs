Option Explicit

Dim shell, fileSystem, backendDir, pythonExe, launcher, command
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

backendDir = fileSystem.GetParentFolderName(WScript.ScriptFullName)
pythonExe = backendDir & "\.venv\Scripts\python.exe"
launcher = backendDir & "\run_desktop.py"
command = Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & launcher & Chr(34)

shell.Run command, 0, False
