#!/usr/bin/env bash
# ==============================================================================
# MDsave - Universal Installer (Linux, Android Termux, macOS & Windows)
# ==============================================================================
# Instala MDsave, configura dependencias (Python, ffmpeg, extractores),
# despliega el launcher universal y anade el script al PATH del sistema.
# ==============================================================================

# Colores y formato
CLR_RESET="\033[0m"
CLR_BOLD="\033[1m"
CLR_GREEN="\033[92m"
CLR_BLUE="\033[94m"
CLR_CYAN="\033[96m"
CLR_YELLOW="\033[93m"
CLR_RED="\033[91m"
CLR_MAGENTA="\033[95m"

info()    { echo -e "${CLR_BLUE}[+]${CLR_RESET} $1"; }
success() { echo -e "${CLR_GREEN}[✓]${CLR_RESET} ${CLR_BOLD}$1${CLR_RESET}"; }
warn()    { echo -e "${CLR_YELLOW}[!]${CLR_RESET} $1"; }
err()     { echo -e "${CLR_RED}[✗] $1${CLR_RESET}" >&2; }
heading() { echo -e "\n${CLR_CYAN}${CLR_BOLD}=== $1 ===${CLR_RESET}"; }

banner() {
    echo -e "${CLR_CYAN}${CLR_BOLD}"
    cat << "EOF"
  __  __ ____    ____                    
 |  \/  |  _ \  / ___|  __ ___   _____   
 | |\/| | | | | \___ \ / _` \ \ / / _ \  
 | |  | | |_| |  ___) | (_| |\ V /  __/  
 |_|  |_|____/  |____/ \__,_| \_/ \___|  
       Instalador Universal de MDsave
EOF
    echo -e "${CLR_RESET}"
    echo -e "  Descargador Multimedia Pro para Reels, TikToks, Shorts, Fotos y Audio"
    echo -e "  Compatible con Linux, Android (Termux), Windows (Git Bash/WSL) y macOS\n"
}

# 1. Detectar entorno y arquitectura
detect_environment() {
    heading "Detección de Sistema y Entorno"
    
    OS_NAME="$(uname -s 2>/dev/null || echo "Unknown")"
    ARCH="$(uname -m 2>/dev/null || echo "Unknown")"
    IS_WINDOWS=false
    IS_WSL=false
    IS_TERMUX=false
    IS_MACOS=false
    IS_LINUX=false

    # Detección Termux
    if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
        IS_TERMUX=true
        PLATFORM="Android (Termux)"
    # Detección Windows (Git Bash, MSYS2, MINGW, Cygwin)
    elif [[ "$OS_NAME" =~ MINGW* ]] || [[ "$OS_NAME" =~ MSYS* ]] || [[ "$OS_NAME" =~ CYGWIN* ]]; then
        IS_WINDOWS=true
        PLATFORM="Windows ($OS_NAME)"
    # Detección macOS
    elif [ "$OS_NAME" = "Darwin" ]; then
        IS_MACOS=true
        PLATFORM="macOS"
    # Detección Linux / WSL
    elif [ "$OS_NAME" = "Linux" ]; then
        IS_LINUX=true
        if grep -qi "microsoft\|wsl" /proc/version 2>/dev/null; then
            IS_WSL=true
            PLATFORM="Linux (WSL - Windows Subsystem for Linux)"
        else
            PLATFORM="Linux"
        fi
    else
        PLATFORM="$OS_NAME ($ARCH)"
    fi

    info "Plataforma detectada: ${CLR_BOLD}$PLATFORM${CLR_RESET} ($ARCH)"
}

# 2. Configurar permisos y rutas de instalación
setup_install_paths() {
    heading "Configuración de Rutas de Instalación"
    
    SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ "$IS_TERMUX" = true ]; then
        INSTALL_DIR="${PREFIX:-/data/data/com.termux/files/usr}/share/mdsave"
        BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
        SUDO=""
    elif [ "$IS_WINDOWS" = true ]; then
        INSTALL_DIR="$HOME/.local/share/mdsave"
        BIN_DIR="$HOME/.local/bin"
        SUDO=""
    elif [ "$(id -u)" -eq 0 ]; then
        # Instalación global como root
        INSTALL_DIR="/usr/local/share/mdsave"
        BIN_DIR="/usr/local/bin"
        SUDO=""
    else
        # Usuario sin privilegios root
        if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
            INSTALL_DIR="/usr/local/share/mdsave"
            BIN_DIR="/usr/local/bin"
            SUDO="sudo"
        else
            # Fallback seguro a directorio local de usuario sin requerir sudo
            INSTALL_DIR="$HOME/.local/share/mdsave"
            BIN_DIR="$HOME/.local/bin"
            SUDO=""
            info "Instalando en modo usuario (${BIN_DIR}) para no requerir privilegios root."
        fi
    fi

    info "Directorio de la aplicación : $INSTALL_DIR"
    info "Directorio de ejecutables   : $BIN_DIR"
}

# 3. Detectar e instalar dependencias del sistema (Python, ffmpeg)
install_system_dependencies() {
    heading "Verificación de Herramientas del Sistema"

    # Verificar Python 3
    PYTHON_CMD=""
    for cmd in python3 python py; do
        if command -v "$cmd" >/dev/null 2>&1; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 and sys.version_info[1] >= 8 else 1)" 2>/dev/null; then
                PYTHON_CMD="$cmd"
                break
            fi
        fi
    done

    if [ -n "$PYTHON_CMD" ]; then
        PY_VER="$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null)"
        success "Python detectado: $PYTHON_CMD (v$PY_VER)"
    else
        warn "Python 3.8+ no encontrado. Intentando instalar automáticamente..."
        if [ "$IS_TERMUX" = true ]; then
            pkg update -y && pkg install -y python python-pip
        elif command -v apt-get >/dev/null 2>&1; then
            $SUDO apt-get update -y && $SUDO apt-get install -y python3 python3-pip
        elif command -v dnf >/dev/null 2>&1; then
            $SUDO dnf install -y python3 python3-pip
        elif command -v pacman >/dev/null 2>&1; then
            $SUDO pacman -Sy --noconfirm python python-pip
        elif command -v zypper >/dev/null 2>&1; then
            $SUDO zypper in -y python3 python3-pip
        elif command -v apk >/dev/null 2>&1; then
            $SUDO apk add --no-cache python3 py3-pip
        elif command -v brew >/dev/null 2>&1; then
            brew install python
        elif [ "$IS_WINDOWS" = true ]; then
            if command -v winget.exe >/dev/null 2>&1; then
                info "Instalando Python 3 via winget..."
                winget.exe install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
            else
                err "No se pudo instalar Python automáticamente en Windows."
                echo "Por favor instala Python 3 desde https://www.python.org/ y vuelve a ejecutar este instalador."
                exit 1
            fi
        fi

        # Re-verificar
        for cmd in python3 python; do
            if command -v "$cmd" >/dev/null 2>&1; then
                PYTHON_CMD="$cmd"
                break
            fi
        done
        [ -z "$PYTHON_CMD" ] && { err "No se pudo verificar Python 3."; exit 1; }
    fi

    # Verificar FFmpeg (esencial para combinar video/audio y extraer MP3 a 320 kbps)
    if command -v ffmpeg >/dev/null 2>&1; then
        success "FFmpeg detectado: $(command -v ffmpeg)"
    else
        warn "FFmpeg no encontrado. Instalando FFmpeg para soporte completo de audio y muxing..."
        if [ "$IS_TERMUX" = true ]; then
            pkg install -y ffmpeg
        elif command -v apt-get >/dev/null 2>&1; then
            $SUDO apt-get install -y ffmpeg
        elif command -v dnf >/dev/null 2>&1; then
            $SUDO dnf install -y ffmpeg
        elif command -v pacman >/dev/null 2>&1; then
            $SUDO pacman -Sy --noconfirm ffmpeg
        elif command -v zypper >/dev/null 2>&1; then
            $SUDO zypper in -y ffmpeg
        elif command -v apk >/dev/null 2>&1; then
            $SUDO apk add --no-cache ffmpeg
        elif command -v brew >/dev/null 2>&1; then
            brew install ffmpeg
        elif [ "$IS_WINDOWS" = true ]; then
            if command -v winget.exe >/dev/null 2>&1; then
                info "Instalando FFmpeg via winget..."
                winget.exe install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements || true
            else
                warn "FFmpeg no encontrado en Windows. Se recomienda instalar FFmpeg para soporte óptimo de audio."
            fi
        fi
    fi

    # Instalar motor de JavaScript opcional (quickjs o node) si está disponible en repositorios
    if ! command -v qjs >/dev/null 2>&1 && ! command -v node >/dev/null 2>&1; then
        if [ "$IS_TERMUX" = true ]; then
            pkg install -y quickjs >/dev/null 2>&1 || true
        elif command -v apt-get >/dev/null 2>&1; then
            $SUDO apt-get install -y quickjs >/dev/null 2>&1 || true
        fi
    fi
}

# 4. Instalar o actualizar dependencias de Python
install_python_dependencies() {
    heading "Instalación de Extractores y Librerías de Python"

    PACKAGES=("yt-dlp" "gallery-dl" "parth-dl" "requests" "instaloader")
    info "Instalando/actualizando paquetes: ${PACKAGES[*]}"

    # Intentar instalación con --break-system-packages (requerido en Debian 12+, Ubuntu 23+, Fedora)
    PIP_SUCCESS=false
    if $PYTHON_CMD -m pip install --break-system-packages -U "${PACKAGES[@]}" >/dev/null 2>&1; then
        PIP_SUCCESS=true
    elif $PYTHON_CMD -m pip install -U "${PACKAGES[@]}" >/dev/null 2>&1; then
        PIP_SUCCESS=true
    elif $PYTHON_CMD -m pip install --user --break-system-packages -U "${PACKAGES[@]}" >/dev/null 2>&1; then
        PIP_SUCCESS=true
    elif $PYTHON_CMD -m pip install --user -U "${PACKAGES[@]}" >/dev/null 2>&1; then
        PIP_SUCCESS=true
    fi

    if [ "$PIP_SUCCESS" = true ]; then
        success "Librerías multimedia de Python instaladas con éxito."
    else
        warn "La instalación automática de pip falló silenciosamente. Intentando con salida detallada..."
        $PYTHON_CMD -m pip install --user --break-system-packages -U "${PACKAGES[@]}" || \
        $PYTHON_CMD -m pip install --user -U "${PACKAGES[@]}" || \
        warn "Verifica tu instalación de pip si algún extractor no responde."
    fi
}

# 5. Desplegar archivos del programa
deploy_mdsave_files() {
    heading "Despliegue de MDsave"

    # Crear directorios de destino
    if [ -n "$SUDO" ]; then
        $SUDO mkdir -p "$INSTALL_DIR" "$BIN_DIR"
        $SUDO cp -f "$SRC_DIR/mdsave.py" "$INSTALL_DIR/mdsave.py"
        $SUDO cp -f "$SRC_DIR/README.md" "$INSTALL_DIR/README.md" 2>/dev/null || true
        $SUDO chmod 755 "$INSTALL_DIR/mdsave.py"
    else
        mkdir -p "$INSTALL_DIR" "$BIN_DIR"
        cp -f "$SRC_DIR/mdsave.py" "$INSTALL_DIR/mdsave.py"
        cp -f "$SRC_DIR/README.md" "$INSTALL_DIR/README.md" 2>/dev/null || true
        chmod 755 "$INSTALL_DIR/mdsave.py"
    fi
    success "Archivos base copiados a: $INSTALL_DIR"

    # Generar o copiar el ejecutable universal 'mdsave' en $BIN_DIR
    LAUNCHER_PATH="$BIN_DIR/mdsave"
    info "Creando ejecutable de terminal en: $LAUNCHER_PATH"

    cat << 'EOF' | if [ -n "$SUDO" ]; then $SUDO tee "$LAUNCHER_PATH" >/dev/null; else tee "$LAUNCHER_PATH" >/dev/null; fi
#!/usr/bin/env bash
# MDsave - Universal CLI Launcher

# 1. Resolver ruta del script principal
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

CANDIDATES=(
    "$SCRIPT_DIR/mdsave.py"
    "$SCRIPT_DIR/../share/mdsave/mdsave.py"
    "/usr/local/share/mdsave/mdsave.py"
    "/usr/share/mdsave/mdsave.py"
    "${PREFIX:-/data/data/com.termux/files/usr}/share/mdsave/mdsave.py"
    "$HOME/.local/share/mdsave/mdsave.py"
    "$HOME/.mdsave/mdsave.py"
)

if [ -n "$LOCALAPPDATA" ] && command -v cygpath >/dev/null 2>&1; then
    CANDIDATES+=("$(cygpath -u "$LOCALAPPDATA" 2>/dev/null)/mdsave/mdsave.py")
fi

REAL_SCRIPT=""
for candidate in "${CANDIDATES[@]}"; do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
        REAL_SCRIPT="$candidate"
        break
    fi
done

if [ -z "$REAL_SCRIPT" ]; then
    echo -e "\033[91m[!] Error: No se pudo localizar 'mdsave.py'.\033[0m" >&2
    echo "Reinstala MDsave ejecutando el instalador ./install.sh" >&2
    exit 1
fi

# 2. Detectar interprete de Python 3
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    if python -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)" >/dev/null 2>&1; then
        PYTHON_BIN="python"
    fi
elif command -v py >/dev/null 2>&1; then
    if py -3 -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
        PYTHON_BIN="py -3"
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo -e "\033[91m[!] Error: Python 3 no encontrado en el sistema.\033[0m" >&2
    exit 1
fi

# 3. Ejecutar preservando directorio de trabajo y respetando flags/argumentos de la CLI
exec $PYTHON_BIN "$REAL_SCRIPT" "$@"
EOF

    if [ -n "$SUDO" ]; then
        $SUDO chmod 755 "$LAUNCHER_PATH"
    else
        chmod 755 "$LAUNCHER_PATH"
    fi
    success "Lanzador universal bash instalado en: $LAUNCHER_PATH"

    # Si estamos en Windows (Git Bash / MSYS2 / WSL) o existen launchers de Windows, instalarlos también
    if [ "$IS_WINDOWS" = true ] || [ "$IS_WSL" = true ]; then
        # mdsave.cmd para Windows CMD
        if [ -f "$SRC_DIR/mdsave.cmd" ]; then
            cp -f "$SRC_DIR/mdsave.cmd" "$BIN_DIR/mdsave.cmd" 2>/dev/null || true
            chmod 755 "$BIN_DIR/mdsave.cmd" 2>/dev/null || true
            success "Lanzador para Windows CMD (mdsave.cmd) instalado."
        fi
        # mdsave.ps1 para PowerShell
        if [ -f "$SRC_DIR/mdsave.ps1" ]; then
            cp -f "$SRC_DIR/mdsave.ps1" "$BIN_DIR/mdsave.ps1" 2>/dev/null || true
            chmod 755 "$BIN_DIR/mdsave.ps1" 2>/dev/null || true
            success "Lanzador para PowerShell (mdsave.ps1) instalado."
        fi
    fi
}

# 6. Configurar PATH universal
configure_path() {
    heading "Configuración del PATH"

    PATH_UPDATED=false

    # Verificar si $BIN_DIR ya está en el PATH actual
    case ":$PATH:" in
        *":$BIN_DIR:"*)
            success "El directorio $BIN_DIR ya está en la variable PATH."
            ;;
        *)
            info "Añadiendo $BIN_DIR a tus archivos de perfil de shell..."
            SHELL_FILES=("$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zshrc")
            LINE_TO_ADD="export PATH=\"$BIN_DIR:\$PATH\""

            for sfile in "${SHELL_FILES[@]}"; do
                if [ -f "$sfile" ]; then
                    if ! grep -Fq "$BIN_DIR" "$sfile" 2>/dev/null; then
                        echo "" >> "$sfile"
                        echo "# MDsave CLI PATH" >> "$sfile"
                        echo "$LINE_TO_ADD" >> "$sfile"
                        info "  ✓ Actualizado: $sfile"
                        PATH_UPDATED=true
                    fi
                fi
            done

            # Si no existe ninguno, crear .bashrc
            if [ "$PATH_UPDATED" = false ]; then
                echo "$LINE_TO_ADD" >> "$HOME/.bashrc"
                info "  ✓ Creado: $HOME/.bashrc con PATH"
                PATH_UPDATED=true
            fi

            export PATH="$BIN_DIR:$PATH"
            ;;
    esac

    # En Windows, actualizar el PATH de usuario en el registro de Windows via PowerShell
    if [ "$IS_WINDOWS" = true ] && command -v powershell.exe >/dev/null 2>&1; then
        info "Configurando el PATH nativo de Windows (para CMD y PowerShell)..."
        WIN_BIN_PATH="$(cygpath -w "$BIN_DIR" 2>/dev/null || echo "$BIN_DIR")"
        powershell.exe -NoProfile -Command "
            try {
                \$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
                if (\$userPath -notlike '*$WIN_BIN_PATH*') {
                    [Environment]::SetEnvironmentVariable('Path', \$userPath.TrimEnd(';') + ';$WIN_BIN_PATH', 'User')
                    Write-Host '    ✓ PATH de Windows configurado exitosamente.'
                } else {
                    Write-Host '    ✓ PATH de Windows ya contiene el directorio.'
                }
            } catch {
                Write-Host '    ! No se pudo actualizar el registro de PATH de Windows.'
            }
        " 2>/dev/null || true
    fi
}

# 7. Crear directorios de descargas predeterminados
setup_download_folders() {
    heading "Verificación de Carpetas de Descarga"

    if [ "$IS_TERMUX" = true ] && [ -d "/storage/emulated/0/Download" ]; then
        BASE_DIR="/storage/emulated/0/Download/MDsave"
    else
        BASE_DIR="$HOME/Downloads/MDsave"
    fi

    mkdir -p "$BASE_DIR/Videos" "$BASE_DIR/Imagenes" "$BASE_DIR/Audios"
    success "Carpetas organizadas listas en: $BASE_DIR"
    echo -e "   ├── Videos/   (4K, 1440p, 1080p Full HD)"
    echo -e "   ├── Imagenes/ (Fotos y Carruseles en resolución original)"
    echo -e "   └── Audios/   (Pistas extraídas en MP3 a 320 kbps)"
}

# 8. Verificación final del comando CLI
verify_installation() {
    heading "Verificación Final de la Instalación"

    if [ -x "$BIN_DIR/mdsave" ]; then
        success "¡MDsave se ha instalado correctamente!"
        echo ""
        info "Probando llamada CLI: mdsave --help..."
        echo -e "${CLR_CYAN}------------------------------------------------------------${CLR_RESET}"
        "$BIN_DIR/mdsave" --help | head -n 12
        echo -e "${CLR_CYAN}------------------------------------------------------------${CLR_RESET}"
    else
        err "No se pudo encontrar el ejecutable en: $BIN_DIR/mdsave"
        exit 1
    fi
}

# Resumen de uso
print_summary() {
    echo -e "\n${CLR_GREEN}${CLR_BOLD}================================================================${CLR_RESET}"
    echo -e "${CLR_GREEN}${CLR_BOLD}       🎉 ¡MDsave quedó instalado y listo para usar!            ${CLR_RESET}"
    echo -e "${CLR_GREEN}${CLR_BOLD}================================================================${CLR_RESET}\n"
    
    echo -e "${CLR_BOLD}Formas de ejecución desde cualquier carpeta:${CLR_RESET}"
    echo -e "  ${CLR_CYAN}1. Modo Interactivo (Menú completo):${CLR_RESET}"
    echo -e "     ${CLR_BOLD}mdsave${CLR_RESET}\n"
    echo -e "  ${CLR_CYAN}2. Descarga Directa por CLI (Atajos rápidos):${CLR_RESET}"
    echo -e "     ${CLR_BOLD}mdsave <URL>${CLR_RESET}                  Detección automática en máxima calidad"
    echo -e "     ${CLR_BOLD}mdsave -v <URL>${CLR_RESET}               Forzar descarga de Video (4K/1080p)"
    echo -e "     ${CLR_BOLD}mdsave -i <URL>${CLR_RESET}               Forzar descarga de Imagen o Carrusel"
    echo -e "     ${CLR_BOLD}mdsave -a <URL>${CLR_RESET}               Extraer solo Audio en MP3 (320 kbps)"
    echo -e "     ${CLR_BOLD}mdsave @usuario${CLR_RESET}               Foto de perfil de Instagram en 1080x1080 HD"
    echo -e "     ${CLR_BOLD}mdsave --set-cookie <id>${CLR_RESET}      Desbloquear videos 18+/privados de Instagram"
    echo -e "     ${CLR_BOLD}mdsave -b enlaces.txt${CLR_RESET}        Descargar lista por lotes\n"

    if [ "$PATH_UPDATED" = true ]; then
        echo -e "${CLR_YELLOW}${CLR_BOLD}ℹ NOTA SOBRE EL PATH:${CLR_RESET}"
        echo -e "  Para que el comando 'mdsave' esté disponible en esta terminal actual, ejecuta:"
        echo -e "  ${CLR_GREEN}source ~/.bashrc${CLR_RESET}  (o abre una nueva ventana de terminal)\n"
    fi
}

# Ejecución principal
main() {
    banner
    detect_environment
    setup_install_paths
    install_system_dependencies
    install_python_dependencies
    deploy_mdsave_files
    configure_path
    setup_download_folders
    verify_installation
    print_summary
}

main "$@"
