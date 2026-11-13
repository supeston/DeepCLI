Option Explicit

Dim shell, fso, procEnv
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Function Q(text)
    Q = Chr(34) & text & Chr(34)
End Function

Function ResolveAppDir()
    Dim scriptDir, parentDir, desktopDir, localAppData
    scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
    If fso.FileExists(scriptDir & "\deepx\launcher.py") Then
        ResolveAppDir = scriptDir
        Exit Function
    End If

    parentDir = fso.GetParentFolderName(scriptDir)
    If parentDir <> "" And fso.FileExists(parentDir & "\deepx\launcher.py") Then
        ResolveAppDir = parentDir
        Exit Function
    End If

    desktopDir = shell.SpecialFolders("Desktop")
    If fso.FileExists(desktopDir & "\DEEPX CLI (DEEPSEEK)\deepx\launcher.py") Then
        ResolveAppDir = desktopDir & "\DEEPX CLI (DEEPSEEK)"
        Exit Function
    End If
    If fso.FileExists(desktopDir & "\DEEPX\deepx\launcher.py") Then
        ResolveAppDir = desktopDir & "\DEEPX"
        Exit Function
    End If

    localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    If fso.FileExists(localAppData & "\DeepX\app\deepx\launcher.py") Then
        ResolveAppDir = localAppData & "\DeepX\app"
        Exit Function
    End If

    ' Bootstrap download if launched from standalone VBS without local repo
    Dim targetDir, zipFile, repoUrl
    targetDir = desktopDir & "\DEEPX"
    If Not fso.FolderExists(targetDir) Then
        fso.CreateFolder targetDir
    End If
    zipFile = shell.ExpandEnvironmentStrings("%TEMP%") & "\DeepCLI_main.zip"
    repoUrl = "https://github.com/supeston/DeepCLI/archive/refs/heads/main.zip"
    shell.Run "curl.exe -fSL -o " & Q(zipFile) & " " & Q(repoUrl), 0, True
    If fso.FileExists(zipFile) Then
        shell.Run "tar.exe -xf " & Q(zipFile) & " -C " & Q(targetDir) & " --strip-components=1", 0, True
        On Error Resume Next
        fso.DeleteFile zipFile, True
        On Error GoTo 0
    End If
    ResolveAppDir = targetDir
End Function

Dim appDir
appDir = ResolveAppDir()
If Not fso.FolderExists(appDir) Then
    MsgBox "DEEPX directory could not be found or initialized: " & appDir, vbCritical, "DEEPX LAUNCHER"
    WScript.Quit 1
End If

shell.CurrentDirectory = appDir

Set procEnv = shell.Environment("PROCESS")
procEnv("PYTHONUTF8") = "1"
procEnv("PYTHONDONTWRITEBYTECODE") = "1"
procEnv("PYTHONPATH") = appDir

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

Dim hasVenv
hasVenv = False

Function FindOrInstallPythonPrefix()
    Dim localAppData, venvPy
    localAppData = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    venvPy = appDir & "\.venv\Scripts\python.exe"
    If fso.FileExists(venvPy) Then
        hasVenv = True
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

Dim pyPrefix, launcherScript
pyPrefix = FindOrInstallPythonPrefix()
If pyPrefix = "" Then
    MsgBox "Python 3.10+ is required for DEEPX AGENT and automatic installation failed." & vbCrLf & "Install Python 3.11+ from https://www.python.org/downloads/ and try again.", vbCritical, "DEEPX LAUNCHER"
    WScript.Quit 1
End If

launcherScript = appDir & "\deepx\launcher.py"
If Not fso.FileExists(launcherScript) Then
    MsgBox "Launcher script not found at: " & launcherScript, vbCritical, "DEEPX LAUNCHER"
    WScript.Quit 1
End If

On Error Resume Next
If hasVenv Then
    ' Hidden bootstrap verifies/cleans zombie WindowsTerminal, spawns visible WT or classic console, and brings window to front
    shell.Run pyPrefix & " -u " & Q(launcherScript) & " --bootstrap", 0, False
    If Err.Number <> 0 Then
        Err.Clear
        shell.Run pyPrefix & " -u " & Q(launcherScript) & " --no-relaunch", 1, False
    End If
Else
    ' First-time setup: open visible window immediately so user sees installation progress
    shell.Run pyPrefix & " -u " & Q(launcherScript), 1, False
End If
On Error GoTo 0
