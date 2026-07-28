Option Explicit

Dim shell, fso, folder, quote, command, argument
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

folder = fso.GetParentFolderName(WScript.ScriptFullName)
quote = Chr(34)
command = "wt.exe -w new --size 110,30 new-tab --title " & quote & "DEEPX AGENT" & quote & _
          " -d " & quote & folder & quote & _
          " cmd.exe /d /c python " & quote & folder & "\deep_cli.py" & quote

For Each argument In WScript.Arguments
    command = command & " " & quote & Replace(argument, quote, quote & quote) & quote
Next

shell.Run command, 1, False
