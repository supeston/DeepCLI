Option Explicit

Dim shell, fso, folder, quote, command, argument, argsStr, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

folder = fso.GetParentFolderName(WScript.ScriptFullName)
quote = Chr(34)

argsStr = ""
For Each argument In WScript.Arguments
    argsStr = argsStr & " " & quote & Replace(argument, quote, quote & quote) & quote
Next

command = "wt.exe -w new --size 110,30 new-tab --title " & quote & "DEEPX AGENT" & quote & _
          " -d " & quote & folder & quote & _
          " cmd.exe /d /s /c " & quote & quote & folder & "\start.bat" & quote & argsStr & quote

On Error Resume Next
result = shell.Run(command, 1, False)

If Err.Number <> 0 Then
    Err.Clear
    shell.Run "cmd.exe /d /s /c " & quote & quote & folder & "\start.bat" & quote & argsStr & quote, 1, False
End If
On Error GoTo 0
