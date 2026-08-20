Option Explicit

Dim shell, fso, folder, quote, command, argument, innerCmd, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

folder = fso.GetParentFolderName(WScript.ScriptFullName)
quote = Chr(34)

' Если окружение .venv уже создано — запускаем DeepCLI, иначе запускаем автоматический установщик deepx\install.py
If fso.FileExists(folder & "\.venv\Scripts\python.exe") Then
    innerCmd = "set PYTHONDONTWRITEBYTECODE=1 & " & quote & folder & "\.venv\Scripts\python.exe" & quote & " " & quote & folder & "\deepx\deep_cli.py" & quote
Else
    innerCmd = "set PYTHONDONTWRITEBYTECODE=1 & python " & quote & folder & "\deepx\install.py" & quote & " && " & quote & folder & "\.venv\Scripts\python.exe" & quote & " " & quote & folder & "\deepx\deep_cli.py" & quote
End If

For Each argument In WScript.Arguments
    innerCmd = innerCmd & " " & quote & Replace(argument, quote, quote & quote) & quote
Next

command = "wt.exe -w new --size 110,30 new-tab --title " & quote & "DEEPX AGENT" & quote & _
          " -d " & quote & folder & quote & _
          " cmd.exe /d /c " & innerCmd

On Error Resume Next
result = shell.Run(command, 1, False)

' Фолбэк на стандартный cmd.exe, если Windows Terminal (wt.exe) не установлен
If Err.Number <> 0 Then
    Err.Clear
    shell.Run "cmd.exe /d /k " & innerCmd, 1, False
End If
On Error GoTo 0
