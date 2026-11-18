<#
.SYNOPSIS
MDsave - Windows PowerShell Launcher
#>
$ErrorActionPreference = "Stop"

# 1. Resolve mdsave.py path
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Candidates = @(
    (Join-Path $ScriptDir "mdsave.py"),
    (Join-Path $env:LOCALAPPDATA "mdsave\mdsave.py"),
    (Join-Path $env:USERPROFILE ".local\share\mdsave\mdsave.py"),
    (Join-Path $env:USERPROFILE "mdsave\mdsave.py")
)

$RealScript = $null
foreach ($path in $Candidates) {
    if (Test-Path $path) {
        $RealScript = $path
        break
    }
}

if (-not $RealScript) {
    Write-Host "[!] Error: No se pudo encontrar mdsave.py" -ForegroundColor Red
    Write-Host "Ejecuta install.sh o install.ps1 para instalar MDsave."
    exit 1
}

# 2. Find Python interpreter
$PythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" }
             elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             else { $null }

if (-not $PythonCmd) {
    Write-Host "[!] Error: No se encontro Python 3 en PATH." -ForegroundColor Red
    Write-Host "Instala Python desde https://www.python.org/ y anadelo al PATH."
    exit 1
}

# 3. Execute preserving CLI arguments and current directory
if ($PythonCmd -eq "py") {
    & py -3 "$RealScript" @args
} else {
    & $PythonCmd "$RealScript" @args
}

exit $LASTEXITCODE
