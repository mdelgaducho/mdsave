<#
.SYNOPSIS
MDsave - Windows Native Universal Installer (PowerShell)
.DESCRIPTION
Instala y configura MDsave en entornos Windows nativos (PowerShell / CMD),
instalando extractores de Python, configurando lanzadores y anadiendo al PATH.
#>

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "  __  __ ____    ____                    " -ForegroundColor Cyan
Write-Host " |  \/  |  _ \  / ___|  __ ___   _____   " -ForegroundColor Cyan
Write-Host " | |\/| | | | | \___ \ / _` \ \ / / _ \  " -ForegroundColor Cyan
Write-Host " | |  | | |_| |  ___) | (_| |\ V /  __/  " -ForegroundColor Cyan
Write-Host " |_|  |_|____/  |____/ \__,_| \_/ \___|  " -ForegroundColor Cyan
Write-Host "       Instalador MDsave para Windows    " -ForegroundColor Cyan
Write-Host ""
Write-Host "Descargador Multimedia Pro para Reels, TikToks, Shorts, Fotos y Audios`n"

# 1. Rutas de instalacion
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseInstallDir = Join-Path $env:LOCALAPPDATA "mdsave"
$BinDir = Join-Path $BaseInstallDir "bin"

Write-Host "=== 1. Rutas de Instalacion ===" -ForegroundColor Yellow
Write-Host "[+] Directorio de aplicacion : $BaseInstallDir"
Write-Host "[+] Directorio de comandos   : $BinDir"

if (-not (Test-Path $BaseInstallDir)) { New-Item -ItemType Directory -Path $BaseInstallDir -Force | Out-Null }
if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }

# 2. Verificar Python 3
Write-Host "`n=== 2. Verificacion de Python ===" -ForegroundColor Yellow
$PythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" }
             elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             else { $null }

if (-not $PythonCmd) {
    Write-Host "[!] Python no encontrado. Intentando instalar via winget..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        $PythonCmd = "python"
    } else {
        Write-Host "[X] No se pudo encontrar Python 3." -ForegroundColor Red
        Write-Host "Por favor instala Python 3 desde https://www.python.org/ y marca 'Add Python to PATH'."
        exit 1
    }
}

Write-Host "[✓] Python detectado: $PythonCmd" -ForegroundColor Green

# 3. Verificar FFmpeg
Write-Host "`n=== 3. Verificacion de FFmpeg ===" -ForegroundColor Yellow
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "[✓] FFmpeg detectado correctamente." -ForegroundColor Green
} else {
    Write-Host "[!] FFmpeg no encontrado en PATH." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[+] Instalando FFmpeg via winget..." -ForegroundColor Cyan
        winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "    Se recomienda instalar FFmpeg para la extraccion de audio en MP3 y union de video/audio."
        Write-Host "    Puedes descargarlo desde: https://www.gyan.dev/ffmpeg/builds/"
    }
}

# 4. Instalar librerias de Python
Write-Host "`n=== 4. Instalacion de Extractores y Librerias ===" -ForegroundColor Yellow
$packages = @("yt-dlp", "gallery-dl", "parth-dl", "requests", "instaloader")
Write-Host "[+] Instalando dependencias: $($packages -join ' ')..." -ForegroundColor Cyan

if ($PythonCmd -eq "py") {
    & py -3 -m pip install --upgrade $packages
} else {
    & $PythonCmd -m pip install --upgrade $packages
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] Librerias instaladas con exito." -ForegroundColor Green
} else {
    Write-Host "[!] Advertencia: pip finalizo con advertencias o error. Verifica la conexion." -ForegroundColor Yellow
}

# 5. Copiar archivos y crear lanzadores
Write-Host "`n=== 5. Despliegue de Archivos y Lanzadores ===" -ForegroundColor Yellow
Copy-Item (Join-Path $SourceDir "mdsave.py") (Join-Path $BaseInstallDir "mdsave.py") -Force
if (Test-Path (Join-Path $SourceDir "README.md")) {
    Copy-Item (Join-Path $SourceDir "README.md") (Join-Path $BaseInstallDir "README.md") -Force
}

# Lanzador .cmd (para CMD)
$CmdLauncher = Join-Path $BinDir "mdsave.cmd"
@"
@echo off
setlocal
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_BIN=python"
    goto :run
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_BIN=py -3"
    goto :run
)
set "PY_BIN=python3"
:run
%PY_BIN% "$BaseInstallDir\mdsave.py" %*
exit /b %ERRORLEVEL%
"@ | Set-Content -Path $CmdLauncher -Encoding ASCII

# Lanzador .ps1 (para PowerShell)
$PsLauncher = Join-Path $BinDir "mdsave.ps1"
@"
`$ErrorActionPreference = "Stop"
`$PythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" }
              elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" }
              else { "python3" }
if (`$PythonCmd -eq "py") {
    & py -3 "$BaseInstallDir\mdsave.py" @args
} else {
    & `$PythonCmd "$BaseInstallDir\mdsave.py" @args
}
exit `$LASTEXITCODE
"@ | Set-Content -Path $PsLauncher -Encoding UTF8

Write-Host "[✓] Lanzadores mdsave.cmd y mdsave.ps1 generados en: $BinDir" -ForegroundColor Green

# 6. Configurar PATH en Windows
Write-Host "`n=== 6. Configuracion del PATH ===" -ForegroundColor Yellow
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    $newPath = if ($userPath) { $userPath.TrimEnd(";") + ";$BinDir" } else { $BinDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path += ";$BinDir"
    Write-Host "[✓] '$BinDir' anadido exitosamente a la variable de entorno PATH del usuario." -ForegroundColor Green
} else {
    Write-Host "[✓] '$BinDir' ya se encontraba en el PATH." -ForegroundColor Green
}

# 7. Crear carpetas de descargas predeterminadas
$DownloadBase = Join-Path $env:USERPROFILE "Downloads\MDsave"
$Folders = @("Videos", "Imagenes", "Audios")
foreach ($f in $Folders) {
    $target = Join-Path $DownloadBase $f
    if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target -Force | Out-Null }
}
Write-Host "[✓] Carpetas organizadas creadas en: $DownloadBase" -ForegroundColor Green

# 8. Verificacion
Write-Host "`n=== 7. Verificacion de Instalacion ===" -ForegroundColor Yellow
try {
    & $CmdLauncher --help | Select-Object -First 10
    Write-Host "`n[✓] ¡Instalacion completada con exito en Windows!" -ForegroundColor Green
} catch {
    Write-Host "[!] Verificacion manual requerida." -ForegroundColor Yellow
}

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "  ¡MDsave esta listo para usar desde cualquier terminal!        " -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Green
Write-Host "Ejemplos de comandos disponibles:" -ForegroundColor Cyan
Write-Host "  mdsave                                 Abre el menu interactivo"
Write-Host "  mdsave <URL>                           Descarga automatica en maxima calidad"
Write-Host "  mdsave -v <URL>                        Fuerza descarga en Video (4K/1080p)"
Write-Host "  mdsave -a <URL>                        Extrae solo Audio en MP3 (320 kbps)"
Write-Host "  mdsave -i <URL>                        Fuerza descarga de Imagen o Carrusel"
Write-Host "  mdsave @usuario                        Foto de perfil de Instagram en 1080x1080 HD"
Write-Host "  mdsave --set-cookie <tu_sessionid>     Desbloquea contenido 18+/privado"
Write-Host "`nNota: Si acabas de instalarlo, reinicia tu terminal CMD o PowerShell para recargar el PATH.`n"
