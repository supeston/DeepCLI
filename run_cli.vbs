Option Explicit

Dim shell, fso, procEnv
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim appDir
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir

Set procEnv = shell.Environment("PROCESS")
procEnv("PYTHONUTF8") = "1"
procEnv("PYTHONDONTWRITEBYTECODE") = "1"
procEnv("PYTHONPATH") = appDir

Function Q(text)
    Q = Chr(34) & text & Chr(34)
End Function

Function IsWindows11()
    On Error Resume Next
    Dim buildStr
    buildStr = shell.RegRead("HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\CurrentBuildNumber")
    If Err.Number = 0 And IsNumeric(buildStr) Then
        IsWindows11 = (CLng(buildStr) >= 22000)
    Else
        IsWindows11 = False
    End If
    Err.Clear
    On Error GoTo 0
End Function

Function CheckPythonPrefix(prefix)
    On Error Resume Next
    Dim rc
    rc = shell.Run(prefix & " -c ""import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)""", 0, True)
    If Err.Number = 0 And rc = 0 Then
        CheckPythonPrefix = True
    Else
        CheckPythonPrefix = False
    End If
    Err.Clear
    On Error GoTo 0
End Function

Function FindOrInstallPythonPrefix()
    Dim localAppData, venvPy
    localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    venvPy = appDir & "\.venv\Scripts\python.exe"
    If fso.FileExists(venvPy) Then
        FindOrInstallPythonPrefix = Q(venvPy)
        Exit Function
    End If

    Dim directPaths(3), idx
    directPaths(0) = localAppData & "\Programs\Python\Python312\python.exe"
    directPaths(1) = localAppData & "\Programs\Python\Python311\python.exe"
    directPaths(2) = localAppData & "\Programs\Python\Python310\python.exe"
    directPaths(3) = shell.ExpandEnvironmentStrings("%ProgramFiles%") & "\Python311\python.exe"

    For idx = 0 To UBound(directPaths)
        If fso.FileExists(directPaths(idx)) Then
            If CheckPythonPrefix(Q(directPaths(idx))) Then
                FindOrInstallPythonPrefix = Q(directPaths(idx))
                Exit Function
            End If
        End If
    Next

    Dim commandCandidates(3)
    commandCandidates(0) = "py -3.12"
    commandCandidates(1) = "py -3.11"
    commandCandidates(2) = "py -3"
    commandCandidates(3) = "python"

    For idx = 0 To UBound(commandCandidates)
        If CheckPythonPrefix(commandCandidates(idx)) Then
            FindOrInstallPythonPrefix = commandCandidates(idx)
            Exit Function
        End If
    Next

    ' Install Python 3.11.9 silently if absent
    Dim tempDir, pyInstaller, dlCmd, instRc, installedPy
    tempDir = shell.ExpandEnvironmentStrings("%TEMP%")
    pyInstaller = tempDir & "\deepx_python_3119.exe"
    dlCmd = "curl.exe -fSL -o " & Q(pyInstaller) & " https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    shell.Run dlCmd, 0, True

    If fso.FileExists(pyInstaller) Then
        instRc = shell.Run(Q(pyInstaller) & " /quiet InstallAllUsers=0 PrependPath=1 Include_test=0", 1, True)
        On Error Resume Next
        fso.DeleteFile pyInstaller, True
        On Error GoTo 0
        installedPy = localAppData & "\Programs\Python\Python311\python.exe"
        If instRc = 0 And fso.FileExists(installedPy) Then
            FindOrInstallPythonPrefix = Q(installedPy)
            Exit Function
        End If
    End If

    FindOrInstallPythonPrefix = ""
End Function

Function FindWindowsTerminalPath()
    Dim localAppData, wtAlias, rc
    localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    wtAlias = localAppData & "\Microsoft\WindowsApps\wt.exe"
    If fso.FileExists(wtAlias) Then
        FindWindowsTerminalPath = wtAlias
        Exit Function
    End If

    On Error Resume Next
    rc = shell.Run("where /q wt.exe", 0, True)
    If Err.Number = 0 And rc = 0 Then
        FindWindowsTerminalPath = "wt.exe"
    Else
        FindWindowsTerminalPath = ""
    End If
    Err.Clear
    On Error GoTo 0
End Function

Dim pyPrefix, launcherScript
pyPrefix = FindOrInstallPythonPrefix()
If pyPrefix = "" Then
    MsgBox "Python 3.10+ is required for DEEPX AGENT and automatic installation failed." & vbCrLf & "Install Python 3.11+ from https://www.python.org/downloads/ and try again.", vbCritical, "DEEPX LAUNCHER"
    WScript.Quit 1
End If

launcherScript = appDir & "\deepx\launcher.py"
Dim win11, wtPath, wtLaunchCmd, classicCmd
win11 = IsWindows11()
wtPath = FindWindowsTerminalPath()

' Force launch inside Windows Terminal on Windows 11 or whenever WT is installed
If win11 Or wtPath <> "" Then
    Dim targetWt
    If wtPath <> "" Then
        targetWt = wtPath
    Else
        targetWt = "wt.exe"
    End If

    wtLaunchCmd = Q(targetWt) & " -w new --size 116,34 new-tab --title ""DEEPX LAUNCHER"" -d " & Q(appDir) & " " & pyPrefix & " -u " & Q(launcherScript) & " --in-wt"
    On Error Resume Next
    shell.Run wtLaunchCmd, 1, False
    If Err.Number = 0 Then
        WScript.Quit 0
    End If
    Err.Clear
    If win11 And targetWt <> "wt.exe" Then
        shell.Run "wt.exe -w new --size 116,34 new-tab --title ""DEEPX LAUNCHER"" -d " & Q(appDir) & " " & pyPrefix & " -u " & Q(launcherScript) & " --in-wt", 1, False
        If Err.Number = 0 Then
            WScript.Quit 0
        End If
        Err.Clear
    End If
    On Error GoTo 0
End If

' Fallback to classic Windows Console ONLY when not Windows 11 and WT is absent/unavailable
classicCmd = pyPrefix & " -u " & Q(launcherScript) & " --no-relaunch"
shell.Run classicCmd, 1, False
