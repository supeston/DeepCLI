[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [switch]$Launch
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$RepoUrl = "https://github.com/supeston/DeepCLI.git"
$ArchiveUrl = "https://github.com/supeston/DeepCLI/archive/refs/heads/main.zip"
$PythonInstallerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DEEPX AGENT - System Installer for Windows" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

function Resolve-TargetDir {
    param([string]$Requested)
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        return $Requested
    }
    if (-not [string]::IsNullOrWhiteSpace($env:DEEPX_HOME)) {
        return $env:DEEPX_HOME
    }
    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "deepx\install.py"))) {
        return $PSScriptRoot
    }
    if (Test-Path (Join-Path (Get-Location).Path "deepx\install.py")) {
        return (Get-Location).Path
    }
    return (Join-Path $env:LOCALAPPDATA "DeepX\app")
}

function Find-Python310Plus {
    $candidates = @(
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("py", "-3.10"),
        @("py", "-3"),
        @("python"),
        @("python3"),
        @((Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe")),
        @((Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe")),
        @((Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\python.exe"))
    )

    foreach ($spec in $candidates) {
        $exe = $spec[0]
        $extra = @()
        if ($spec.Length -gt 1) {
            $extra = $spec[1..($spec.Length - 1)]
        }
        try {
            if ($exe -like "*\*" -and -not (Test-Path $exe)) {
                continue
            }
            $probe = & $exe @extra -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $resolved = & $exe @extra -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
                    return $resolved.Trim()
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

function Ensure-Python {
    $py = Find-Python310Plus
    if ($py) {
        Write-Host "[+] Found Python: $py" -ForegroundColor Green
        return $py
    }

    Write-Host "[!] Python 3.10+ not found. Installing Python 3.11.9..." -ForegroundColor Yellow
    $installer = Join-Path $env:TEMP "deepx_python_3119.exe"
    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        & curl.exe -fSL -o $installer $PythonInstallerUrl
    } else {
        (New-Object System.Net.WebClient).DownloadFile($PythonInstallerUrl, $installer)
    }

    if (-not (Test-Path $installer)) {
        throw "Failed to download Python 3.11.9 installer."
    }

    $proc = Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait -PassThru
    Remove-Item $installer -Force -ErrorAction SilentlyContinue
    if ($proc.ExitCode -ne 0) {
        throw "Python installer exited with code $($proc.ExitCode)."
    }

    $defaultPy = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
    if (Test-Path $defaultPy) {
        return $defaultPy
    }
    $py = Find-Python310Plus
    if (-not $py) {
        throw "Python was installed, but executable could not be located. Reopen terminal and retry."
    }
    return $py
}

function Sync-Repository {
    param([string]$TargetDir)
    $parent = Split-Path -Parent $TargetDir
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $hasLocalFiles = Test-Path (Join-Path $TargetDir "deepx\install.py")
    $hasGitRepo = Test-Path (Join-Path $TargetDir ".git")
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue

    if ($hasLocalFiles -and -not $hasGitRepo -and ($TargetDir -ne (Join-Path $env:LOCALAPPDATA "DeepX\app"))) {
        Write-Host "[i] Using existing local workspace: $TargetDir" -ForegroundColor DarkCyan
        return
    }

    if ($gitCmd -and $hasGitRepo) {
        Write-Host "[>] Updating existing repository via git..." -ForegroundColor Cyan
        & git -C $TargetDir pull --ff-only
        return
    }

    if ($gitCmd -and -not $hasLocalFiles) {
        Write-Host "[>] Cloning DEEPX CLI into $TargetDir..." -ForegroundColor Cyan
        & git clone --depth 1 $RepoUrl $TargetDir
        return
    }

    Write-Host "[>] Downloading DEEPX CLI archive..." -ForegroundColor Cyan
    $tmpRoot = Join-Path $env:TEMP ("deepx_install_" + [Guid]::NewGuid().ToString("N"))
    $zipFile = Join-Path $tmpRoot "deepcli.zip"
    $extractDir = Join-Path $tmpRoot "extracted"
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    try {
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe -fSL -o $zipFile $ArchiveUrl
        } else {
            (New-Object System.Net.WebClient).DownloadFile($ArchiveUrl, $zipFile)
        }
        Expand-Archive -Path $zipFile -DestinationPath $extractDir -Force
        $sourceRoot = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
        if (-not $sourceRoot) {
            throw "Downloaded archive had no root folder."
        }
        if (-not (Test-Path $TargetDir)) {
            New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
        }
        $preserve = @(".env", ".env.local", ".venv", "venv", ".git", ".deepx", "state.json", "vds_profiles.json")
        Get-ChildItem -Path $sourceRoot.FullName -Force | ForEach-Object {
            if ($preserve -contains $_.Name -and (Test-Path (Join-Path $TargetDir $_.Name))) {
                return
            }
            $dest = Join-Path $TargetDir $_.Name
            if ($_.PSIsContainer) {
                Copy-Item -Path $_.FullName -Destination $TargetDir -Recurse -Force
            } else {
                Copy-Item -Path $_.FullName -Destination $dest -Force
            }
        }
    } finally {
        Remove-Item -Path $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$TargetDir = Resolve-TargetDir -Requested $InstallDir
Sync-Repository -TargetDir $TargetDir
$PythonExe = Ensure-Python

$InstallScript = Join-Path $TargetDir "deepx\install.py"
if (-not (Test-Path $InstallScript)) {
    throw "Installer script not found at $InstallScript"
}

Write-Host "[>] Running environment setup..." -ForegroundColor Cyan
& $PythonExe $InstallScript
if ($LASTEXITCODE -ne 0) {
    throw "DEEPX environment installation failed with exit code $LASTEXITCODE"
}

$BinDir = Join-Path $env:LOCALAPPDATA "DeepX\bin"
if ((Test-Path $BinDir) -and ($env:Path -notlike "*$BinDir*")) {
    $env:Path = "$BinDir;$env:Path"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  DEEPX AGENT READY" -ForegroundColor Green
Write-Host "  App dir : $TargetDir" -ForegroundColor Gray
Write-Host "  Command : deepx  (works from any terminal)" -ForegroundColor White
Write-Host "  Launcher: run_cli.vbs" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

if ($Launch) {
    $DeepxCmd = Join-Path $BinDir "deepx.cmd"
    if (Test-Path $DeepxCmd) {
        & $DeepxCmd
    }
}
