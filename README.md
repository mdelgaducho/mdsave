# 🚀 MDsave

> **Descargador Multimedia Pro para Reels, TikToks, Shorts, Fotos, Carruseles y Audio en Máxima Calidad.**

**MDsave** es una herramienta de línea de comandos (CLI) ligera, rápida y multiplataforma diseñada para descargar contenido multimedia desde las principales redes sociales (Instagram, TikTok, YouTube, X/Twitter, Pinterest, Threads, Facebook y enlaces directos). 

MDsave prioriza siempre la **máxima resolución y tasa de bits disponible** (4K, 1440p, 1080p 60 FPS, resolución original para imágenes y audio MP3 a 320 kbps), organizando automáticamente tus archivos en carpetas dedicadas por categoría (`Videos/`, `Imagenes/`, `Audios/`).

---

## 🌟 Características Principales

- 🎬 **Videos y Reels en Máxima Calidad**: Descarga videos en la mejor resolución posible (hasta 4K/60fps) sin marcas de agua.
- 🖼️ **Fotos y Carruseles Completos**: Extrae fotos individuales, publicaciones múltiples (carruseles) y fotos de perfil en resolución original (`orig` / 1080x1080 HD).
- 🎵 **Extracción de Audio**: Convierte y extrae el audio de cualquier video en formato MP3 de alta fidelidad (320 kbps).
- 🔒 **Soporte de Contenido Restringido**: Compatible con publicaciones de Instagram con restricción de edad (+18) o cuentas privadas mediante cookies o sesión rápida (`sessionid`).
- 📁 **Organización Automática**: Clasifica automáticamente las descargas según su tipo en directorios dedicados.
- ⚡ **Modo Doble**: Menú interactivo visual amigable o comandos directos rápidos por terminal.
- 📦 **Descargas por Lotes**: Procesa listas masivas de URLs desde un archivo de texto.

---

## 📱 Plataformas Soportadas

| Plataforma | Videos / Reels | Fotos / Carruseles | Solo Audio (MP3) | Calidad de Descarga |
| :--- | :---: | :---: | :---: | :--- |
| **Instagram** | ✅ (Públicos y Restringidos) | ✅ (Fotos, Carruseles y Perfil HD) | ✅ | Original / 1080x1080 HD / 4K |
| **TikTok** | ✅ (Sin marca de agua) | ✅ (Fotos y Slideshows) | ✅ | Máxima disponible (HD) |
| **YouTube** | ✅ (Shorts y Videos) | ✅ (Miniaturas en máxima resolución) | ✅ | Hasta 4K / 60 FPS |
| **Facebook** | ✅ (Reels y Videos) | ❌ | ✅ | HD disponible |
| **X / Twitter** | ✅ | ✅ | ✅ | Resolución original (`orig`) |
| **Pinterest** | ✅ | ✅ | ✅ | Imagen original sin comprimir |
| **Threads** | ✅ | ✅ | ✅ | Máxima resolución |
| **Enlaces Directos** | ✅ (.mp4, .webm, etc.) | ✅ (.jpg, .png, etc.) | ✅ | Archivo fuente 100% original |

---

## 📦 Guía de Instalación Paso a Paso

MDsave es compatible con **Linux**, **Android (Termux)**, **Windows** y **macOS**. Puedes optar por la instalación automatizada mediante scripts incluidos o realizar la configuración manual.

### Requisitos Previos Generales
- **Python 3.8** o superior.
- **FFmpeg** (requerido para unir video y audio en máxima resolución y para convertir a MP3).
- **Git** (para clonar el repositorio).

---

### 🐧 1. Instalación en Linux (Ubuntu, Debian, Fedora, Arch, etc.)

#### Opción A: Instalador Automático (Recomendado)
El instalador detecta el gestor de paquetes de tu distribución (`apt`, `dnf`, `pacman`), instala `ffmpeg`, `python3-pip`, las librerías necesarias y enlaza `mdsave` a tu `PATH`.

1. Clona el repositorio y entra al directorio:
   ```bash
   git clone https://github.com/mdelgaducho/mdsave.git
   cd mdsave
   ```
2. Otorga permisos de ejecución y corre el instalador:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. Reinicia tu terminal o recarga tu shell:
   ```bash
   source ~/.bashrc   # o source ~/.zshrc
   ```

#### Opción B: Instalación Manual
1. Instala Python y FFmpeg:
   - **Debian / Ubuntu**: `sudo apt update && sudo apt install -y python3 python3-pip ffmpeg`
   - **Fedora**: `sudo dnf install -y python3 python3-pip ffmpeg`
   - **Arch Linux**: `sudo pacman -S python python-pip ffmpeg`
2. Instala los extractores de dependencias:
   ```bash
   pip3 install --break-system-packages -U yt-dlp gallery-dl parth-dl
   ```
3. Crea un enlace simbólico al script en `/usr/local/bin` o `~/.local/bin`:
   ```bash
   chmod +x mdsave
   mkdir -p ~/.local/bin
   ln -sf "$(pwd)/mdsave" ~/.local/bin/mdsave
   ```

---

### 📱 2. Instalación en Android (Termux)

MDsave está completamente optimizado para Android a través de **Termux**.

1. Abre Termux y concede acceso al almacenamiento interno:
   ```bash
   termux-setup-storage
   ```
2. Actualiza los paquetes del sistema e instala las dependencias base:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python ffmpeg git -y
   ```
3. Clona el repositorio y accede a él:
   ```bash
   git clone https://github.com/mdelgaducho/mdsave.git
   cd mdsave
   ```
4. Ejecuta el instalador automático:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
5. ¡Listo! Puedes invocar la herramienta escribiendo `mdsave` desde cualquier ubicación. Los archivos se guardarán directamente en tu carpeta accesible de Android: `/storage/emulated/0/Download/MDsave/`.

---

### 🪟 3. Instalación en Windows

#### Requisitos en Windows:
- Tener instalado **Python 3** (marcar la casilla **"Add python.exe to PATH"** durante la instalación).
- Tener instalado **FFmpeg** y agregado al PATH (o instalado vía `winget install Gyan.FFmpeg` o `choco install ffmpeg`).

#### Opción A: Instalación Automática con PowerShell
1. Abre **PowerShell** en la carpeta donde descargaste/clonaste el proyecto.
2. Permite la ejecución de scripts locales y corre el instalador:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install.ps1
   ```
3. El instalador configurará los ejecutables `.cmd` y `.ps1` y los agregará al PATH del usuario. Cierra y vuelve a abrir PowerShell.

#### Opción B: Con Git Bash / WSL
Si usas Git Bash o WSL:
```bash
chmod +x install.sh
./install.sh
```

#### Opción C: Instalación Manual en Windows
1. Instala las dependencias vía consola (CMD o PowerShell):
   ```cmd
   pip install -U yt-dlp gallery-dl parth-dl
   ```
2. Agrega la carpeta del proyecto a tus **Variables de entorno del sistema (PATH)** para poder ejecutar `mdsave` desde cualquier ventana de CMD o PowerShell.

---

### 🍎 4. Instalación en macOS

1. Instala Homebrew si no lo tienes, luego instala Python y FFmpeg:
   ```bash
   brew install python ffmpeg git
   ```
2. Clona el repositorio:
   ```bash
   git clone https://github.com/mdelgaducho/mdsave.git
   cd mdsave
   ```
3. Corre el instalador universal:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
4. Recarga la configuración de tu terminal:
   ```bash
   source ~/.zshrc
   ```

---

## ⚡ Modos de Uso

### 1. Menú Interactivo (Fácil y Guiado)
Simplemente escribe en tu terminal:
```bash
mdsave
```
Se desplegará la interfaz visual interactiva:
```text
  __  __ ____    ____                    
 |  \/  |  _ \  / ___|  __ ___   _____   
 | |\/| | | | | \___ \ / _` \ \ / / _ \  
 | |  | | |_| |  ___) | (_| |\ V /  __/  
 |_|  |_|____/  |____/ \__,_| \_/ \___|  
        Descargador Multimedia Pro

 🎬 Videos:   ~/Downloads/MDsave/Videos/
 🖼️  Imágenes: ~/Downloads/MDsave/Imagenes/
 🎵 Audios:   ~/Downloads/MDsave/Audios/
 🌟 Calidad:  MÁXIMA DISPONIBLE (4K / Full HD / Original / 320k)
 🔑 Sesión:   ACTIVA (Descarga de contenido restringido habilitada)
────────────────────────────────────────────────────────────────────
  MENÚ PRINCIPAL
  [1] 🚀 Descarga Rápida (Video o Imagen - Detección automática)
  [2] 🎬 Descargar Videos (Reels, TikToks, Shorts - Máxima Calidad)
  [3] 🖼️  Descargar Imágenes o Carruseles (Fotos / Perfiles IG - Máxima Calidad)
  [4] 🎵 Descargar solo Audio (MP3 - 320 kbps)
  [5] 📦 Descarga por Lotes (Múltiples enlaces a la vez)
  [6] 📁 Ver archivos guardados
  [7] ⚙️  Configuración y Autenticación
  [8] 🔄 Actualizar extractores (yt-dlp, gallery-dl, parth-dl)
  [0] 🚪 Salir
```

---

### 2. Atajos Rápidos por Línea de Comandos (CLI)

```bash
# 🚀 Descarga automática inteligente (detecta si es video o imagen)
mdsave "https://www.instagram.com/reel/DfqowGcTzHY/"

# 🖼️ Descargar foto de perfil de Instagram en HD (1080x1080)
mdsave "https://www.instagram.com/nasa/"
mdsave @nasa

# 🎬 Forzar descarga de Video en Máxima Calidad (4K / 1080p)
mdsave -v "https://www.instagram.com/reel/..."

# 🖼️ Forzar descarga de Imagen o Carrusel completo en calidad original
mdsave -i "https://www.instagram.com/p/..."

# 🎵 Extraer solo el Audio en MP3 (320 kbps)
mdsave -a "https://www.tiktok.com/@usuario/video/..."

# 📦 Descarga masiva por lotes desde un archivo de texto
mdsave -b enlaces.txt

# 🔑 Configurar tu cookie de sesión de Instagram para contenido +18 o privado
mdsave --set-cookie "678912345%3Asometoken"
```

---

## 🔒 Descarga de Contenido Restringido (+18 o Privado)

Si un Reel o video de Instagram requiere inicio de sesión por restricciones de edad o privacidad (*"This content isn't available to everyone"*):

1. **Atajo rápido en terminal**:
   ```bash
   mdsave --set-cookie <tu_sessionid>
   ```
2. **Detección automática de `cookies.txt`**:
   Puedes colocar tu archivo `cookies.txt` exportado con extensiones como *Get cookies.txt locally* o *Cookie-Editor* en la carpeta de MDsave o en tu carpeta de descargas, y la herramienta lo detectará automáticamente.

### ¿Cómo obtener tu `sessionid` de Instagram en 1 minuto?
- **Desde la computadora (Chrome / Edge / Firefox)**:
  1. Abre `instagram.com` con tu cuenta activa.
  2. Presiona `F12` > pestaña **Aplicación** (o Almacenamiento) > **Cookies** > `https://www.instagram.com`.
  3. Copia el valor de la cookie llamada `sessionid`.
- **Desde el móvil**:
  1. En Kiwi Browser o Firefox Android, inicia sesión en `instagram.com`.
  2. Usa la extensión `Cookie-Editor` para copiar el valor de `sessionid`.

---

## 📂 Estructura de Salida de Archivos

MDsave organiza automáticamente tus archivos descargados:
```text
MDsave/
├── Videos/     <- Reels, TikToks, Shorts y videos en .mp4 (4K / 1080p)
├── Imagenes/   <- Fotos individuales, carruseles y avatares en resolución original
└── Audios/     <- Pistas de audio extraídas en .mp3 (320 kbps)
```
- **En Android (Termux)**: `/storage/emulated/0/Download/MDsave/`
- **En Linux / macOS**: `~/Downloads/MDsave/` o `~/Descargas/MDsave/`
- **En Windows**: `%USERPROFILE%\Downloads\MDsave\`

---

## 🔄 Actualización de Extractores

Las plataformas sociales actualizan constantemente sus algoritmos. Para asegurar el funcionamiento continuo:
- Puedes usar la **Opción [8]** en el menú de `mdsave`.
- O ejecutar manualmente:
  ```bash
  pip install --break-system-packages -U yt-dlp gallery-dl parth-dl
  ```

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
