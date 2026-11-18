#!/usr/bin/env python3
"""
MDsave - Descargador automatizado de Reels, TikToks, Shorts, Videos e Imágenes.
Diseñado para Android (Termux) y entornos Linux.
Configurado para descargar siempre con la MÁXIMA CALIDAD posible (Full HD / 4K / Original).
Soporte completo para contenido con restricción de audiencia / edad / privado en Instagram.
Rutas automáticas personalizadas:
  - Videos:   /storage/emulated/0/Download/MDsave/Videos/
  - Imágenes: /storage/emulated/0/Download/MDsave/Imagenes/
  - Audios:   /storage/emulated/0/Download/MDsave/Audios/
"""

import sys
import os
import re
import json
import time
import shutil
import subprocess
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple

# Verificación de dependencias externas
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import requests
except ImportError:
    requests = None

try:
    import parth_dl
except ImportError:
    parth_dl = None

try:
    import instaloader
except ImportError:
    instaloader = None

# Constantes de configuración
if os.path.isdir("/storage/emulated/0/Download"):
    BASE_DEFAULT_DIR = "/storage/emulated/0/Download/MDsave"
else:
    BASE_DEFAULT_DIR = os.path.expanduser("~/Downloads/MDsave")
FALLBACK_BASE_DIR = os.path.expanduser("~/Downloads/MDsave")
CONFIG_DIR = os.path.expanduser("~/.config/mdsave")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_COOKIE_FILE = os.path.join(CONFIG_DIR, "cookies.txt")

# Colores ANSI para terminal
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def cprint(text: str, color: str = "", bold: bool = False, end: str = "\n"):
    prefix = ""
    if bold:
        prefix += Style.BOLD
    if color:
        prefix += color
    print(f"{prefix}{text}{Style.RESET}", end=end)

def format_size(bytes_num: int) -> str:
    """Convierte bytes en formato legible (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_num) < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def sanitize_filename(name: str) -> str:
    """Elimina caracteres incompatibles con FAT32/Android."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean if clean else f"archivo_{int(time.time())}"

def optimize_media_url_for_max_quality(url: str) -> str:
    """Modifica parámetros de URL conocidos para solicitar la versión original sin comprimir."""
    if "twimg.com" in url:
        url = re.sub(r'name=[a-zA-Z0-9]+', 'name=orig', url)
    if "googleusercontent.com" in url or "ggpht.com" in url:
        url = re.sub(r'=s\d+.*', '=s0', url)
        url = re.sub(r'=w\d+.*', '=s0', url)
    return url

def get_file_resolution(filepath: str) -> str:
    """Detecta la resolución del archivo de imagen o video."""
    if not os.path.isfile(filepath):
        return "Máxima calidad"
    try:
        res = subprocess.run(["file", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        m = re.search(r'(\d{2,5}\s*x\s*\d{2,5})', res.stdout)
        if m:
            return m.group(1).replace(" ", "")
    except Exception:
        pass
    return "Máxima calidad"

class ConfigManager:
    """Administra la configuración del usuario, directorios y cookies."""
    @staticmethod
    def load_config() -> Dict[str, Any]:
        defaults = {
            "base_dir": BASE_DEFAULT_DIR,
            "audio_format": "mp3",
            "audio_quality": "320",
            "video_quality": "best",
            "cookies_file": "",
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception:
                pass
        return defaults

    @staticmethod
    def save_config(config: Dict[str, Any]):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            cprint(f"[!] Error guardando configuración: {e}", Style.RED)

    @classmethod
    def get_base_dir(cls, config: Dict[str, Any]) -> str:
        base = config.get("base_dir", BASE_DEFAULT_DIR)
        try:
            os.makedirs(base, exist_ok=True)
            test_path = os.path.join(base, ".test_perm")
            with open(test_path, "w") as f:
                f.write("ok")
            os.remove(test_path)
            return base
        except Exception:
            fallback = FALLBACK_BASE_DIR
            os.makedirs(fallback, exist_ok=True)
            return fallback

    @classmethod
    def get_paths(cls, config: Dict[str, Any]) -> Tuple[str, str, str, str]:
        base = cls.get_base_dir(config)
        videos_dir = os.path.join(base, "Videos")
        imagenes_dir = os.path.join(base, "Imagenes")
        audios_dir = os.path.join(base, "Audios")

        for d in (videos_dir, imagenes_dir, audios_dir):
            os.makedirs(d, exist_ok=True)

        return base, videos_dir, imagenes_dir, audios_dir

    @classmethod
    def get_cookie_file(cls, config: Dict[str, Any]) -> Optional[str]:
        """Obtiene la ruta del archivo de cookies, buscándolo automáticamente si no está configurado."""
        cfg_cookie = config.get("cookies_file")
        if cfg_cookie and os.path.isfile(cfg_cookie) and os.path.getsize(cfg_cookie) > 10:
            return cfg_cookie

        base = cls.get_base_dir(config)
        candidates = [
            DEFAULT_COOKIE_FILE,
            os.path.join(base, "cookies.txt"),
            "/storage/emulated/0/Download/cookies.txt",
            "/storage/emulated/0/Download/MDsave/cookies.txt",
            os.path.expanduser("~/cookies.txt"),
            "cookies.txt",
        ]
        for c in candidates:
            if os.path.isfile(c) and os.path.getsize(c) > 10:
                return os.path.abspath(c)
        return None

    @classmethod
    def save_instagram_session(cls, sessionid: str, config: Dict[str, Any]) -> str:
        """Crea automáticamente un archivo Netscape cookies.txt a partir de un sessionid de Instagram."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        cookie_path = DEFAULT_COOKIE_FILE
        clean_sid = sessionid.strip()

        # Extraer ds_user_id si está presente en el sessionid
        user_id = ""
        if "%3A" in clean_sid:
            user_id = clean_sid.split("%3A")[0]
        elif ":" in clean_sid:
            user_id = clean_sid.split(":")[0]

        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\t{clean_sid}\n")
            if user_id and user_id.isdigit():
                f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tds_user_id\t{user_id}\n")

        config["cookies_file"] = cookie_path
        cls.save_config(config)
        return cookie_path


class PlatformDetector:
    """Detecta la plataforma y clasifica el contenido."""
    @staticmethod
    def clean_url(url: str) -> str:
        url = url.strip()
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1].strip()
        if url.startswith("@"):
            return f"https://www.instagram.com/{url[1:]}/"
        if not re.match(r'^[a-zA-Z]+://', url):
            url = "https://" + url
        return url

    @classmethod
    def identify(cls, raw_url: str) -> Tuple[str, str, str]:
        url = cls.clean_url(raw_url)
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()

        video_exts = ('.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv')
        image_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.avif')

        if any(path.endswith(ext) for ext in video_exts):
            return "Video Directo", "video", url
        if any(path.endswith(ext) for ext in image_exts):
            return "Imagen Directa", "image", url

        # Instagram
        if "instagram.com" in netloc or "instagr.am" in netloc:
            if "/reel/" in path or "/reels/" in path:
                return "Instagram Reel", "video", url
            elif "/p/" in path:
                return "Instagram Post / Carrusel", "mixed", url
            elif "/stories/" in path:
                return "Instagram Story", "mixed", url

            # Detección de perfil de Instagram (descarga de foto de perfil en 1080x1080 HD)
            raw_parts = [p for p in parsed.path.strip('/').split('/') if p]
            reserved_ig = {
                'p', 'reel', 'reels', 'tv', 'stories', 'explore', 'direct',
                'accounts', 'directory', 'developer', 'about', 'legal',
                'privacy', 'help', 'share', 'api', 'graphql', 'static'
            }
            if len(raw_parts) == 1 or (len(raw_parts) == 2 and raw_parts[1].lower() == 'avatar'):
                user_candidate = raw_parts[0].lstrip('@')
                if user_candidate.lower() not in reserved_ig and re.match(r'^[a-zA-Z0-9._]+$', user_candidate):
                    clean_profile_url = f"https://www.instagram.com/{user_candidate}/"
                    return f"Instagram (Foto de Perfil @{user_candidate})", "instagram_profile", clean_profile_url

            return "Instagram", "mixed", url

        # TikTok
        if "tiktok.com" in netloc or "vt.tiktok.com" in netloc or "vm.tiktok.com" in netloc:
            if "/photo/" in path:
                return "TikTok Fotos / Carrusel", "image", url
            return "TikTok", "video", url

        # YouTube
        if "youtube.com" in netloc or "youtu.be" in netloc:
            if "/shorts/" in path:
                return "YouTube Shorts", "video", url
            return "YouTube", "video", url

        # Facebook
        if "facebook.com" in netloc or "fb.watch" in netloc or "fb.com" in netloc:
            if "/reel/" in path or "/reels/" in path:
                return "Facebook Reel", "video", url
            return "Facebook", "video", url

        # X / Twitter
        if "twitter.com" in netloc or "x.com" in netloc:
            return "X (Twitter)", "mixed", url

        # Pinterest
        if "pinterest.com" in netloc or "pin.it" in netloc:
            return "Pinterest", "image", url

        # Threads
        if "threads.net" in netloc:
            return "Threads", "mixed", url

        # Reddit
        if "reddit.com" in netloc or "redd.it" in netloc:
            return "Reddit", "mixed", url

        return "Web / Desconocida", "mixed", url


class DownloaderEngine:
    """Motor integral de descargas con soporte para MÁXIMA CALIDAD y contenido restringido."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir, self.videos_dir, self.imagenes_dir, self.audios_dir = ConfigManager.get_paths(config)

    def _get_target_dir(self, media_type: str) -> str:
        if media_type == "image":
            os.makedirs(self.imagenes_dir, exist_ok=True)
            return self.imagenes_dir
        elif media_type == "audio":
            os.makedirs(self.audios_dir, exist_ok=True)
            return self.audios_dir
        else:
            os.makedirs(self.videos_dir, exist_ok=True)
            return self.videos_dir

    def _get_yt_dlp_opts(self, output_dir: str, mode: str = "video") -> Dict[str, Any]:
        cookies_file = ConfigManager.get_cookie_file(self.config)
        opts: Dict[str, Any] = {
            "outtmpl": os.path.join(output_dir, "%(title).80B [%(id)s].%(ext)s"),
            "windowsfilenames": True,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
        }

        if shutil.which("qjs"):
            opts["js_runtimes"] = {"quickjs": {}}
            opts["remote_components"] = ["ejs:github"]
        elif shutil.which("node"):
            opts["js_runtimes"] = {"node": {}}
            opts["remote_components"] = ["ejs:github"]

        if cookies_file and os.path.isfile(cookies_file):
            opts["cookiefile"] = cookies_file

        if mode == "audio":
            opts.update({
                "format": "bestaudio/best",
                "format_sort": ["abr", "asr", "channels"],
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.config.get("audio_format", "mp3"),
                    "preferredquality": self.config.get("audio_quality", "320"),
                }],
            })
        else:
            opts.update({
                "format": "bestvideo*+bestaudio/best",
                "format_sort": ["res", "fps", "hdr:12", "channels", "size", "br"],
                "merge_output_format": "mp4",
            })

        return opts

    def download_direct_media(self, url: str, media_type: str = "auto") -> Tuple[bool, List[str], str, Dict[str, str]]:
        if not requests:
            return False, [], "Módulo requests no disponible", {}

        try:
            url = optimize_media_url_for_max_quality(url)
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            content_type = ""
            try:
                head_resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                content_type = head_resp.headers.get("Content-Type", "").lower()
            except Exception:
                pass

            detected_type = media_type
            if detected_type == "auto":
                if "image/" in content_type:
                    detected_type = "image"
                elif "video/" in content_type:
                    detected_type = "video"
                elif any(url.lower().split("?")[0].endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    detected_type = "image"
                else:
                    detected_type = "video"

            output_dir = self._get_target_dir(detected_type)

            parsed = urllib.parse.urlparse(url)
            base_name = os.path.basename(parsed.path) or f"media_{int(time.time())}"
            name_part, ext_part = os.path.splitext(base_name)
            
            if not ext_part:
                if "image/jpeg" in content_type:
                    ext_part = ".jpg"
                elif "image/png" in content_type:
                    ext_part = ".png"
                elif "image/webp" in content_type:
                    ext_part = ".webp"
                elif "image/gif" in content_type:
                    ext_part = ".gif"
                elif "video/mp4" in content_type:
                    ext_part = ".mp4"
                elif detected_type == "image":
                    ext_part = ".jpg"
                else:
                    ext_part = ".mp4"

            safe_name = sanitize_filename(name_part)
            filename = f"{safe_name}{ext_part}"
            filepath = os.path.join(output_dir, filename)

            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(output_dir, f"{safe_name}_{counter}{ext_part}")
                counter += 1

            cprint(f"    [↓] Descargando {detected_type.upper()} en máxima calidad: {os.path.basename(filepath)}...", Style.CYAN)
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_len = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_len > 0:
                                percent = (downloaded / total_len) * 100
                                sys.stdout.write(f"\r        Progreso: {percent:5.1f}% ({format_size(downloaded)} / {format_size(total_len)})")
                                sys.stdout.flush()

            print()
            meta = {filepath: "Original"}
            return True, [filepath], "OK", meta
        except Exception as e:
            return False, [], str(e), {}

    def download_instagram_media(self, url: str, mode: str = "auto") -> Tuple[bool, List[str], str, Dict[str, str]]:
        if not parth_dl or not requests:
            return False, [], "Librerías parth_dl o requests no disponibles", {}

        try:
            cprint("    [🔍] Analizando publicación de Instagram...", Style.CYAN)
            info = parth_dl.get_info(url)
            if not info:
                return False, [], "No se obtuvo respuesta de Instagram", {}

            shortcode = info.get("id") or "ig_post"
            uploader = sanitize_filename(info.get("uploader") or "instagram")
            entries = info.get("entries", [])
            saved_files: List[str] = []
            file_meta: Dict[str, str] = {}

            if entries:
                is_carousel = len(entries) > 1
                cprint(f"    [✓] Publicación detectada: {'Carrusel con ' + str(len(entries)) + ' elementos' if is_carousel else '1 elemento'}", Style.GREEN)

                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                for idx, entry in enumerate(entries, 1):
                    kind = entry.get("kind", "image")
                    formats = entry.get("formats", [])
                    best_url = None
                    best_w, best_h = None, None

                    if formats:
                        def get_res(f):
                            w = f.get("width") or 0
                            h = f.get("height") or 0
                            return w * h
                        sorted_fmts = sorted(formats, key=get_res, reverse=True)
                        top_fmt = sorted_fmts[0]
                        best_url = top_fmt.get("url")
                        best_w = top_fmt.get("width")
                        best_h = top_fmt.get("height")

                    if not best_url:
                        best_url = entry.get("url")

                    if not best_url:
                        continue

                    if kind == "video" or (mode == "video" and "video" in str(entry)):
                        target_dir = self.videos_dir
                        ext = ".mp4"
                        tipo_label = "Video"
                    else:
                        target_dir = self.imagenes_dir
                        ext = ".jpg"
                        tipo_label = "Imagen"

                    if is_carousel:
                        fname = f"{uploader}_{shortcode}_slide_{idx}{ext}"
                    else:
                        fname = f"{uploader}_{shortcode}{ext}"

                    filepath = os.path.join(target_dir, fname)
                    res_info = f" ({best_w}x{best_h})" if best_w and best_h else " (Máxima calidad)"
                    cprint(f"    [↓] Descargando [{idx}/{len(entries)}] {tipo_label}: {fname}{res_info}...", Style.CYAN)

                    r = requests.get(best_url, headers=headers, timeout=30)
                    r.raise_for_status()
                    with open(filepath, "wb") as f:
                        f.write(r.content)

                    saved_files.append(filepath)
                    file_meta[filepath] = f"{best_w}x{best_h}" if best_w and best_h else "Original"

                if saved_files:
                    return True, saved_files, "OK", file_meta

            return False, [], "No se encontraron medios descargables en el post", {}
        except Exception as e:
            return False, [], f"Error extrayendo con Instagram: {e}", {}

    def download_instagram_profile_picture(self, target: str) -> Tuple[bool, List[str], str, Dict[str, str]]:
        """Descarga la foto de perfil de Instagram en su MÁXIMA RESOLUCIÓN disponible (1080x1080 HD)."""
        clean_target = target.strip().rstrip('/')
        parsed = urllib.parse.urlparse(clean_target)
        if parsed.netloc:
            parts = [p for p in parsed.path.strip('/').split('/') if p]
            username = parts[0].lstrip('@') if parts else ""
        else:
            username = clean_target.lstrip('@')

        if not username:
            return False, [], "No se pudo determinar el nombre de usuario de Instagram", {}

        os.makedirs(self.imagenes_dir, exist_ok=True)
        avatar_url = f"https://www.instagram.com/{username}/avatar/"
        cprint(f"    [🔍] Buscando foto de perfil en MÁXIMA CALIDAD (1080x1080 HD) para @{username}...", Style.CYAN)

        expected_filename = f"{username}_foto_perfil.jpg"
        expected_filepath = os.path.join(self.imagenes_dir, expected_filename)

        # 1. Estrategia Principal: gallery-dl (extrae hd_profile_pic_url_info en 1080x1080 HD)
        if shutil.which("gallery-dl"):
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                old_f = os.path.join(self.imagenes_dir, f"{username}_foto_perfil{ext}")
                if os.path.exists(old_f):
                    try:
                        os.remove(old_f)
                    except OSError:
                        pass

            cmd = [
                "gallery-dl",
                "-D", self.imagenes_dir,
                "-f", f"{username}_foto_perfil.{{extension}}",
                "--windows-filenames",
                "--no-part",
            ]
            cookies_file = ConfigManager.get_cookie_file(self.config)
            if cookies_file and os.path.isfile(cookies_file):
                cmd.extend(["--cookies", cookies_file])
            cmd.append(avatar_url)

            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                candidates = [
                    os.path.join(self.imagenes_dir, f"{username}_foto_perfil.jpg"),
                    os.path.join(self.imagenes_dir, f"{username}_foto_perfil.jpeg"),
                    os.path.join(self.imagenes_dir, f"{username}_foto_perfil.png"),
                    os.path.join(self.imagenes_dir, f"{username}_foto_perfil.webp"),
                ]
                saved = [f for f in candidates if os.path.isfile(f) and os.path.getsize(f) > 0]
                if saved:
                    res_str = get_file_resolution(saved[0])
                    cprint(f"    [✓] Foto de perfil HD descargada exitosamente: {os.path.basename(saved[0])} ({res_str})", Style.GREEN, bold=True)
                    return True, [saved[0]], "OK", {saved[0]: res_str}
            except Exception:
                pass

        # 2. Estrategia Secundaria: Instaloader
        if instaloader and requests:
            try:
                cprint("    [i] Intentando método secundario con Instaloader...", Style.YELLOW)
                L = instaloader.Instaloader()
                profile = instaloader.Profile.from_username(L.context, username)
                pic_url = getattr(profile, "profile_pic_url_hd", None) or profile.profile_pic_url
                if pic_url:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    r = requests.get(pic_url, headers=headers, timeout=20)
                    if r.status_code == 200 and len(r.content) > 0:
                        with open(expected_filepath, "wb") as f:
                            f.write(r.content)
                        res_str = get_file_resolution(expected_filepath)
                        cprint(f"    [✓] Foto de perfil descargada: {expected_filename} ({res_str})", Style.GREEN, bold=True)
                        return True, [expected_filepath], "OK", {expected_filepath: res_str}
            except Exception:
                pass

        # 3. Estrategia Terciaria: parth_dl
        if parth_dl and requests:
            try:
                from parth_dl.extractors import ProfilePictureExtractor
                pe = ProfilePictureExtractor()
                res = pe.extract(f"https://www.instagram.com/{username}/")
                if res and hasattr(res, "data"):
                    pic_url = getattr(res.data, "profile_pic_url_hd", None) or getattr(res.data, "profile_pic_url", None)
                    if pic_url:
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                        r = requests.get(pic_url, headers=headers, timeout=20)
                        if r.status_code == 200 and len(r.content) > 0:
                            with open(expected_filepath, "wb") as f:
                                f.write(r.content)
                            res_str = get_file_resolution(expected_filepath)
                            cprint(f"    [✓] Foto de perfil descargada: {expected_filename} ({res_str})", Style.GREEN, bold=True)
                            return True, [expected_filepath], "OK", {expected_filepath: res_str}
            except Exception:
                pass

        return False, [], f"No se pudo descargar la foto de perfil de @{username}. Verifica que el usuario exista o no sea privado.", {}

    def download_with_gallery_dl(self, url: str, output_dir: str) -> Tuple[bool, List[str], str, Dict[str, str]]:
        if not shutil.which("gallery-dl"):
            return False, [], "gallery-dl no está instalado", {}

        os.makedirs(output_dir, exist_ok=True)
        files_before = set(os.listdir(output_dir))
        cmd = [
            "gallery-dl",
            "-D", output_dir,
            "--windows-filenames",
            "--no-part",
        ]
        cookies_file = ConfigManager.get_cookie_file(self.config)
        if cookies_file and os.path.isfile(cookies_file):
            cmd.extend(["--cookies", cookies_file])
        cmd.append(url)

        try:
            cprint(f"    [↓] Descargando con gallery-dl en máxima calidad original...", Style.CYAN)
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            files_after = set(os.listdir(output_dir))
            new_files = [os.path.join(output_dir, f) for f in (files_after - files_before)]

            meta = {f: get_file_resolution(f) for f in new_files}
            if new_files:
                return True, new_files, "OK", meta
            elif proc.returncode == 0:
                return True, [], "Completado (archivos ya descargados)", {}
            else:
                err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Código {proc.returncode}"
                return False, [], err_msg, {}
        except Exception as e:
            return False, [], str(e), {}

    def download_with_yt_dlp(self, url: str, output_dir: str, mode: str = "video") -> Tuple[bool, List[str], str, Dict[str, str]]:
        if not yt_dlp:
            return False, [], "yt-dlp no está instalado", {}

        os.makedirs(output_dir, exist_ok=True)
        opts = self._get_yt_dlp_opts(output_dir, mode=mode)
        files_before = set(os.listdir(output_dir))
        extracted_res = ""

        def progress_hook(d):
            nonlocal extracted_res
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                eta = d.get("eta") or 0
                speed_str = f"{format_size(speed)}/s" if speed else "--"
                if total > 0:
                    percent = (downloaded / total) * 100
                    sys.stdout.write(f"\r        Descargando: {percent:5.1f}% | {format_size(downloaded)} / {format_size(total)} | {speed_str} | ETA: {eta}s  ")
                else:
                    sys.stdout.write(f"\r        Descargando: {format_size(downloaded)} | {speed_str}  ")
                sys.stdout.flush()
            elif d.get("status") == "finished":
                sys.stdout.write("\r        [✓] Descarga completa. Muxing en máxima calidad MP4...      \n")
                sys.stdout.flush()

        opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    if mode == "audio":
                        extracted_res = f"{self.config.get('audio_quality', '320')} kbps"
                    else:
                        extracted_res = info.get("resolution") or (f"{info.get('width')}x{info.get('height')}" if info.get('width') else "Mejor calidad")

            files_after = set(os.listdir(output_dir))
            new_files = [os.path.join(output_dir, f) for f in (files_after - files_before)]
            new_files = [f for f in new_files if not f.endswith((".part", ".ytdl"))]

            meta = {f: extracted_res or "Máxima" for f in new_files}
            if new_files:
                return True, new_files, "OK", meta
            return True, [], "Completado", {}
        except Exception as e:
            err_str = str(e)
            err_str = re.sub(r'ERROR:\s*', '', err_str)
            return False, [], err_str, {}

    def download(self, raw_url: str, mode: str = "auto") -> Tuple[bool, List[str], str, str, Dict[str, str]]:
        platform_name, media_hint, url = PlatformDetector.identify(raw_url)

        cprint(f"\n[+] URL: {url}", Style.WHITE, bold=True)
        cprint(f"[+] Plataforma: {platform_name} | Modo: {mode.upper()} (MÁXIMA CALIDAD)", Style.MAGENTA)

        # 1. Modo Audio únicamente
        if mode == "audio":
            cprint(f"[+] Destino: {self.audios_dir}/", Style.CYAN)
            success, files, msg, meta = self.download_with_yt_dlp(url, self.audios_dir, mode="audio")
            return success, files, platform_name, msg, meta

        # 2. Enlaces directos a archivos
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.mov', '.webm')):
            dest = self.imagenes_dir if any(path.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif')) else self.videos_dir
            cprint(f"[+] Destino: {dest}/", Style.CYAN)
            success, files, msg, meta = self.download_direct_media(url, media_type="image" if dest == self.imagenes_dir else "video")
            if success:
                return True, files, platform_name, msg, meta

        # 3. Instagram (Perfil, Reels, Posts, Carruseles de fotos)
        if "Instagram" in platform_name:
            if media_hint == "instagram_profile":
                cprint(f"[+] Destino: {self.imagenes_dir}/", Style.CYAN)
                success, files, msg, meta = self.download_instagram_profile_picture(url)
                return success, files, platform_name, msg, meta

            if "/reel/" in url or "/reels/" in url:
                cprint(f"[+] Destino: {self.videos_dir}/", Style.CYAN)
                success, files, msg, meta = self.download_with_yt_dlp(url, self.videos_dir, mode="video")
                if success and files:
                    return True, files, platform_name, "OK", meta

                # Fallback a parth_dl
                success_ig, files_ig, msg_ig, meta_ig = self.download_instagram_media(url, mode="video")
                if success_ig and files_ig:
                    return True, files_ig, platform_name, "OK", meta_ig
                return success, files, platform_name, msg, meta
            else:
                cprint(f"[+] Destino: {self.imagenes_dir}/", Style.CYAN)
                success_ig, files_ig, msg_ig, meta_ig = self.download_instagram_media(url, mode=mode)
                if success_ig and files_ig:
                    return True, files_ig, platform_name, "OK", meta_ig

                success_gdl, files_gdl, msg_gdl, meta_gdl = self.download_with_gallery_dl(url, self.imagenes_dir)
                if success_gdl and files_gdl:
                    return True, files_gdl, platform_name, "OK", meta_gdl

                success_ytdl, files_ytdl, msg_ytdl, meta_ytdl = self.download_with_yt_dlp(url, self.videos_dir, mode="video")
                if success_ytdl and files_ytdl:
                    return True, files_ytdl, platform_name, "OK", meta_ytdl

                return False, [], platform_name, msg_ig or msg_gdl, {}

        # 4. TikTok (Videos o Fotos)
        if "TikTok" in platform_name:
            if "/photo/" in url or mode == "image":
                cprint(f"[+] Destino: {self.imagenes_dir}/", Style.CYAN)
                success, files, msg, meta = self.download_with_gallery_dl(url, self.imagenes_dir)
                if success and files:
                    return True, files, platform_name, "OK", meta
                success_yt, files_yt, msg_yt, meta_yt = self.download_with_yt_dlp(url, self.videos_dir, mode="video")
                if success_yt and files_yt:
                    return True, files_yt, platform_name, "OK", meta_yt
                return success, files, platform_name, msg, meta
            else:
                cprint(f"[+] Destino: {self.videos_dir}/", Style.CYAN)
                success, files, msg, meta = self.download_with_yt_dlp(url, self.videos_dir, mode="video")
                return success, files, platform_name, msg, meta

        # 5. Pinterest o modo forzado de imagen
        if mode == "image" or "Pinterest" in platform_name:
            cprint(f"[+] Destino: {self.imagenes_dir}/", Style.CYAN)
            success_gdl, files_gdl, msg_gdl, meta_gdl = self.download_with_gallery_dl(url, self.imagenes_dir)
            if success_gdl and files_gdl:
                return True, files_gdl, platform_name, "OK", meta_gdl
            success_dir, files_dir, msg_dir, meta_dir = self.download_direct_media(url, media_type="image")
            if success_dir and files_dir:
                return True, files_dir, platform_name, "OK", meta_dir
            return False, [], platform_name, msg_gdl, {}

        # 6. Modo Auto / Videos generales (YouTube, Facebook, Twitter, etc.)
        cprint(f"[+] Destino: {self.videos_dir}/", Style.CYAN)
        cprint(f"    [↓] Descargando video con yt-dlp en máxima calidad...", Style.CYAN)
        success, files, msg, meta = self.download_with_yt_dlp(url, self.videos_dir, mode="video")
        if success and files:
            return True, files, platform_name, "OK", meta

        cprint(f"    [i] Comprobando si el contenido es una imagen o galería...", Style.YELLOW)
        success_gdl, files_gdl, msg_gdl, meta_gdl = self.download_with_gallery_dl(url, self.imagenes_dir)
        if success_gdl and files_gdl:
            return True, files_gdl, platform_name, "OK", meta_gdl

        success_dir, files_dir, msg_dir, meta_dir = self.download_direct_media(url, media_type="auto")
        if success_dir and files_dir:
            return True, files_dir, platform_name, "OK", meta_dir

        return False, [], platform_name, msg, {}


def is_audience_restricted_error(error_msg: str) -> bool:
    """Verifica si el error se debe a restricción de audiencia / edad / login requerido en Instagram."""
    low = error_msg.lower()
    return any(phrase in low for phrase in [
        "this content isn't available to everyone",
        "it can't be seen by certain audiences",
        "restricted video",
        "login_required",
        "login required",
        "only available for registered users",
        "unauthorized",
        "401",
    ])


class TerminalUI:
    """Interfaz gráfica interactiva de consola con navegación amigable y desbloqueo automático."""
    def __init__(self):
        self.config = ConfigManager.load_config()
        self.engine = DownloaderEngine(self.config)

    def print_banner(self):
        os.system("clear" if os.name == "posix" else "cls")
        banner = r"""
  __  __ ____    ____                    
 |  \/  |  _ \  / ___|  __ ___   _____   
 | |\/| | | | | \___ \ / _` \ \ / / _ \  
 | |  | | |_| |  ___) | (_| |\ V /  __/  
 |_|  |_|____/  |____/ \__,_| \_/ \___|  
        Descargador Multimedia Pro
"""
        cprint(banner, Style.CYAN, bold=True)
        base, v_dir, i_dir, a_dir = ConfigManager.get_paths(self.config)
        cookie_file = ConfigManager.get_cookie_file(self.config)
        cprint(f" 🎬 Videos:   {v_dir}/", Style.WHITE)
        cprint(f" 🖼️  Imágenes: {i_dir}/", Style.WHITE)
        cprint(f" 🎵 Audios:   {a_dir}/", Style.WHITE)
        cprint(" 🌟 Calidad:  MÁXIMA DISPONIBLE (4K / Full HD / Original / 320k)", Style.GREEN, bold=True)
        if cookie_file:
            cprint(" 🔑 Sesión:   ACTIVA (Descarga de contenido restringido/privado habilitada)", Style.YELLOW)
        else:
            cprint(" 🔓 Sesión:   Pública (Para contenido 18+/restringido usa Opción 7 > [3])", Style.DIM)
        print("─" * 68)

    def report_results(self, success: bool, files: List[str], platform: str, message: str, meta: Optional[Dict[str, str]] = None):
        print()
        if not meta:
            meta = {}
        if success:
            cprint("┌" + "─" * 66 + "┐", Style.GREEN)
            cprint("│  🎉 ¡DESCARGA COMPLETADA CON ÉXITO!                            │", Style.GREEN, bold=True)
            cprint("├" + "─" * 66 + "┤", Style.GREEN)
            cprint(f"│  Plataforma: {platform:<51}│", Style.WHITE)
            if files:
                cprint(f"│  Archivos guardados ({len(files)}):{' ':<42}│", Style.WHITE)
                for f in files:
                    fname = os.path.basename(f)
                    size_str = format_size(os.path.getsize(f)) if os.path.exists(f) else "N/A"
                    res_tag = f" | {meta.get(f)}" if meta.get(f) else ""
                    tag_str = f"({size_str}{res_tag})"
                    display_name = fname if len(fname) <= 36 else fname[:33] + "..."
                    cprint(f"│   • {display_name:<36} {tag_str:>25} │", Style.GREEN)
                cprint(f"│  Carpeta destino:{' ':<49}│", Style.WHITE)
                loc = os.path.dirname(files[0])
                display_loc = loc if len(loc) <= 62 else loc[:59] + "..."
                cprint(f"│   {display_loc:<62}│", Style.CYAN)
            else:
                cprint(f"│  {message:<64}│", Style.YELLOW)
            cprint("└" + "─" * 66 + "┘", Style.GREEN)
        else:
            cprint("┌" + "─" * 66 + "┐", Style.RED)
            cprint("│  ❌ NO SE PUDO DESCARGAR EL CONTENIDO                          │", Style.RED, bold=True)
            cprint("├" + "─" * 66 + "┤", Style.RED)
            cprint(f"│  Plataforma: {platform:<51}│", Style.WHITE)
            clean_msg = message.replace("\n", " ")[:54]
            cprint(f"│  Detalle: {clean_msg:<54}│", Style.RED)
            cprint("└" + "─" * 66 + "┘", Style.RED)

    def handle_restricted_content_prompt(self, raw_url: str, mode: str) -> bool:
        """Permite al usuario ingresar su sessionid en el acto y reintentar la descarga automáticamente."""
        print()
        cprint("┌" + "─" * 66 + "┐", Style.YELLOW)
        cprint("│  🔒 CONTENIDO CON RESTRICCIÓN DE AUDIENCIA / EDAD              │", Style.YELLOW, bold=True)
        cprint("├" + "─" * 66 + "┤", Style.YELLOW)
        cprint("│  Instagram no permite a usuarios anónimos descargar este post: │", Style.WHITE)
        cprint("│  \"This content isn't available to everyone\".                   │", Style.CYAN)
        cprint("│                                                                  │", Style.WHITE)
        cprint("│  Para descargarlo, solo necesitas pegar tu 'sessionid' una vez. │", Style.WHITE)
        cprint("└" + "─" * 66 + "┘", Style.YELLOW)

        print("\n  [1] Pegar 'sessionid' de Instagram ahora y DESCARGAR DE INMEDIATO")
        print("  [2] ¿Cómo obtengo mi sessionid? (Guía de 1 minuto)")
        print("  [0] Omitir y volver\n")

        sub = input(f"{Style.BOLD}Selecciona una opción [0-2]: {Style.RESET}").strip()
        if sub == "2":
            self.show_cookie_guide()
            sub = input(f"\n{Style.BOLD}¿Deseas pegar tu sessionid ahora? (S/n): {Style.RESET}").strip().lower()
            if sub not in ("s", "si", "y", "yes"):
                return False

        sid = input(f"\n{Style.BOLD}{Style.CYAN}Pega tu sessionid de Instagram aquí > {Style.RESET}").strip()
        if not sid:
            cprint("  [!] sessionid vacío. Operación cancelada.", Style.YELLOW)
            return False

        ConfigManager.save_instagram_session(sid, self.config)
        self.engine = DownloaderEngine(self.config)
        cprint("  [✓] ¡Sesión guardada con éxito! Reintentando descarga...", Style.GREEN, bold=True)
        time.sleep(1)

        # Reintentar la descarga automáticamente
        success, files, platform, msg, meta = self.engine.download(raw_url, mode=mode)
        self.report_results(success, files, platform, msg, meta)
        return True

    def show_cookie_guide(self):
        """Muestra instrucciones claras para extraer el sessionid desde el móvil o PC."""
        self.print_banner()
        cprint("  📖 CÓMO OBTENER TU 'SESSIONID' DE INSTAGRAM (1 MINUTO)", Style.YELLOW, bold=True)
        print("─" * 68)
        print("""
  El 'sessionid' es una clave que demuestra a Instagram que tienes permiso
  para ver contenido con restricción de edad (18+), sensible o privado.

  OPCIÓN 1: Desde el navegador en tu teléfono (Kiwi Browser o Firefox Android)
  1. Inicia sesión en https://www.instagram.com en tu navegador móvil.
  2. Instala la extensión gratuita 'Cookie-Editor' en Kiwi/Firefox.
  3. Abre Cookie-Editor en la pestaña de Instagram.
  4. Busca la cookie llamada 'sessionid' y copia su Valor (Value).
     (Es una serie de letras y números como: 678912345%3Aabc...)

  OPCIÓN 2: Desde cualquier computadora (Chrome, Edge, Brave o Firefox)
  1. Abre https://www.instagram.com con tu cuenta iniciada.
  2. Presiona [F12] (o clic derecho > 'Inspeccionar').
  3. Ve a la pestaña 'Aplicación' (Application) o 'Almacenamiento' (Storage).
  4. En el menú izquierdo, expande 'Cookies' y haz clic en 'https://www.instagram.com'.
  5. Haz doble clic en el campo 'Value' de 'sessionid' y cópialo.

  OPCIÓN 3: Archivo cookies.txt completo
  Si prefieres usar una extensión como 'Get cookies.txt locally':
  Exporta el archivo y guárdalo como:
    /storage/emulated/0/Download/MDsave/cookies.txt
  (MDsave lo detectará automáticamente sin que tengas que hacer nada).
""")
        input(f"{Style.DIM}Presiona [Enter] para continuar...{Style.RESET}")

    def loop_single_download(self, mode: str = "auto"):
        mode_titles = {
            "auto": "RÁPIDA (Video o Imagen - Detección Automática)",
            "video": "SOLO VIDEOS (Reels, TikToks, Shorts - Máxima Calidad)",
            "image": "SOLO IMÁGENES / CARRUSELES / PERFILES (Fotos - Máxima Calidad)",
            "audio": "SOLO AUDIO (MP3 - 320 kbps)",
        }
        title = mode_titles.get(mode, "RÁPIDA")

        while True:
            self.print_banner()
            cprint(f"  MODO: {title}", Style.YELLOW, bold=True)
            cprint("  (Pega el enlace a continuación. Escribe 'm' o pulsa Enter para volver al Menú)\n", Style.DIM)

            try:
                raw_url = input(f"{Style.BOLD}{Style.CYAN}🔗 Pega el enlace aquí > {Style.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not raw_url or raw_url.lower() in ("m", "menu", "salir", "exit", "q"):
                break

            success, files, platform, msg, meta = self.engine.download(raw_url, mode=mode)
            
            # Si falló por restricción de audiencia / edad, ofrecer desbloqueo inmediato
            if not success and is_audience_restricted_error(msg):
                handled = self.handle_restricted_content_prompt(raw_url, mode)
                if not handled:
                    self.report_results(success, files, platform, msg, meta)
            else:
                self.report_results(success, files, platform, msg, meta)

            print()
            input(f"{Style.DIM}Presiona [Enter] para continuar...{Style.RESET}")

    def batch_download(self):
        self.print_banner()
        cprint("  DESCARGA POR LOTES (Múltiples enlaces)", Style.YELLOW, bold=True)
        print("  [1] Ingresar / Pegar varios enlaces (separados por espacios o líneas)")
        print("  [2] Cargar enlaces desde un archivo de texto (.txt)")
        print("  [0] Volver al menú principal\n")

        sub_choice = input(f"{Style.BOLD}Selecciona una opción [0-2]: {Style.RESET}").strip()
        links = []

        if sub_choice == "1":
            print("\n  Pega tus enlaces (puedes pegar un bloque completo):")
            cprint("  (Escribe 'FIN' en una línea nueva o pulsa Enter dos veces para iniciar)\n", Style.DIM)
            lines = []
            while True:
                try:
                    line = input().strip()
                    if not line or line.upper() == "FIN":
                        break
                    lines.append(line)
                except (KeyboardInterrupt, EOFError):
                    break
            full_text = " ".join(lines)
            links = re.findall(r'https?://[^\s,;"\']+', full_text)

        elif sub_choice == "2":
            file_path = input("\n  Introduce la ruta del archivo .txt: ").strip()
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        links = re.findall(r'https?://[^\s,;"\']+', text)
                except Exception as e:
                    cprint(f"  [!] Error al leer archivo: {e}", Style.RED)
                    input("\nPresiona [Enter] para continuar...")
                    return
            else:
                cprint(f"  [!] Archivo no encontrado: '{file_path}'", Style.RED)
                input("\nPresiona [Enter] para continuar...")
                return
        else:
            return

        if not links:
            cprint("\n  [!] No se encontraron enlaces válidos.", Style.YELLOW)
            input("\nPresiona [Enter] para continuar...")
            return

        cprint(f"\n  [+] Se encontraron {len(links)} enlace(s).", Style.GREEN, bold=True)
        proceed = input("  ¿Deseas iniciar la descarga por lotes ahora? (S/n): ").strip().lower()
        if proceed in ("n", "no"):
            return

        success_count = 0
        fail_count = 0

        for i, link in enumerate(links, 1):
            cprint(f"\n═════════════════ Lote [{i}/{len(links)}] ═════════════════", Style.CYAN)
            success, files, platform, msg, meta = self.engine.download(link, mode="auto")
            if success:
                success_count += 1
                cprint(f"  [✓] Éxito: {platform}", Style.GREEN)
            else:
                fail_count += 1
                cprint(f"  [✗] Error: {msg}", Style.RED)

        cprint("\n══════════════════════════════════════════════════", Style.WHITE)
        cprint(f"  Resumen de descarga por lotes:", Style.WHITE, bold=True)
        cprint(f"    • Descargados con éxito: {success_count}", Style.GREEN)
        cprint(f"    • Errores / Omitidos:    {fail_count}", Style.RED if fail_count > 0 else Style.DIM)
        input("\nPresiona [Enter] para volver al menú...")

    def list_downloads(self):
        self.print_banner()
        base, v_dir, i_dir, a_dir = ConfigManager.get_paths(self.config)
        cprint("  EXPLORADOR DE ARCHIVOS EN MDSAVE\n", Style.YELLOW, bold=True)

        categories = [
            ("🎬 VIDEOS", v_dir),
            ("🖼️  IMÁGENES Y CARRUSELES", i_dir),
            ("🎵 AUDIOS", a_dir),
        ]

        total_all = 0
        for cat_name, cat_dir in categories:
            cprint(f"  {cat_name} ({cat_dir}/):", Style.CYAN, bold=True)
            if not os.path.exists(cat_dir):
                cprint("    (Carpeta no existe aún)", Style.DIM)
                print()
                continue

            files = []
            for fname in os.listdir(cat_dir):
                if fname.startswith("."):
                    continue
                fpath = os.path.join(cat_dir, fname)
                if os.path.isfile(fpath):
                    try:
                        stat = os.stat(fpath)
                        files.append({"name": fname, "size": stat.st_size, "mtime": stat.st_mtime})
                    except OSError:
                        continue

            if not files:
                cprint("    (Vacía - No hay descargas en esta categoría)", Style.DIM)
            else:
                files.sort(key=lambda x: x["mtime"], reverse=True)
                total_all += len(files)
                for item in files[:10]:
                    display_name = item["name"] if len(item["name"]) <= 40 else item["name"][:37] + "..."
                    size = format_size(item["size"])
                    date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(item["mtime"]))
                    print(f"    • {display_name:<40} | {size:>10} | {date_str}")
                if len(files) > 10:
                    cprint(f"      ... y {len(files) - 10} archivo(s) más.", Style.DIM)
            print()

        cprint(f"  Total de archivos multimedia: {total_all}", Style.GREEN, bold=True)
        input("\nPresiona [Enter] para volver al menú...")

    def settings_menu(self):
        while True:
            self.print_banner()
            cprint("  CONFIGURACIÓN DE MDSAVE", Style.YELLOW, bold=True)
            current_base = self.config.get("base_dir", BASE_DEFAULT_DIR)
            audio_fmt = self.config.get("audio_format", "mp3")
            audio_quality = self.config.get("audio_quality", "320")
            cookie_file = ConfigManager.get_cookie_file(self.config)
            cookie_status = f"ACTIVA ({cookie_file})" if cookie_file else "NO CONFIGURADA"

            print(f"  [1] Carpeta base: {current_base}")
            print(f"      -> Videos:   {current_base}/Videos/")
            print(f"      -> Imágenes: {current_base}/Imagenes/")
            print(f"      -> Audios:   {current_base}/Audios/")
            print(f"  [2] Formato de audio preferido: {audio_fmt.upper()} ({audio_quality} kbps)")
            print(f"  [3] Autenticación Instagram (Contenido 18+ / privado): {cookie_status}")
            print(f"  [4] Restablecer ajustes por defecto")
            print(f"  [0] Volver al menú principal\n")

            choice = input(f"{Style.BOLD}Elige una opción [0-4]: {Style.RESET}").strip()

            if choice == "1":
                cprint(f"\n  Carpeta base actual: {current_base}", Style.CYAN)
                new_dir = input("  Introduce la nueva ruta base absoluta (o pulsa Enter para cancelar): ").strip()
                if new_dir:
                    self.config["base_dir"] = new_dir
                    ConfigManager.save_config(self.config)
                    self.engine = DownloaderEngine(self.config)
                    cprint("  [✓] Rutas actualizadas correctamente.", Style.GREEN)
                    time.sleep(1)

            elif choice == "2":
                fmt = input("  Introduce formato de audio (mp3, m4a, wav, flac): ").strip().lower()
                if fmt in ["mp3", "m4a", "wav", "flac"]:
                    self.config["audio_format"] = fmt
                q = input("  Calidad de audio en kbps (320, 256, 192, 128) [Enter para 320]: ").strip()
                if q in ["320", "256", "192", "128"]:
                    self.config["audio_quality"] = q
                else:
                    self.config["audio_quality"] = "320"
                ConfigManager.save_config(self.config)
                cprint(f"  [✓] Audio configurado a {self.config['audio_format'].upper()} ({self.config['audio_quality']} kbps).", Style.GREEN)
                time.sleep(1)

            elif choice == "3":
                self.instagram_auth_submenu()

            elif choice == "4":
                self.config = {
                    "base_dir": BASE_DEFAULT_DIR,
                    "audio_format": "mp3",
                    "audio_quality": "320",
                    "video_quality": "best",
                    "cookies_file": "",
                }
                ConfigManager.save_config(self.config)
                self.engine = DownloaderEngine(self.config)
                cprint("  [✓] Ajustes restablecidos por defecto.", Style.GREEN)
                time.sleep(1)

            elif choice == "0":
                break

    def instagram_auth_submenu(self):
        """Submenú de autenticación para descargar contenido restringido o privado."""
        while True:
            self.print_banner()
            cprint("  GESTIÓN DE AUTENTICACIÓN (INSTAGRAM)", Style.YELLOW, bold=True)
            cookie_file = ConfigManager.get_cookie_file(self.config)
            print(f"  Estado actual: {'SESIÓN ACTIVA en ' + cookie_file if cookie_file else 'Sin sesión'}\n")
            print("  [1] Pegar 'sessionid' de Instagram (Recomendado y más rápido)")
            print("  [2] Indicar ruta de archivo cookies.txt existente")
            print("  [3] ¿Cómo obtener mi sessionid? (Guía paso a paso)")
            print("  [4] Desactivar sesión actual")
            print("  [0] Volver a Configuración\n")

            sub = input(f"{Style.BOLD}Elige una opción [0-4]: {Style.RESET}").strip()

            if sub == "1":
                cprint("\n  Pega el valor de tu cookie 'sessionid' de Instagram:", Style.CYAN)
                sid = input("  sessionid > ").strip()
                if sid:
                    path = ConfigManager.save_instagram_session(sid, self.config)
                    self.engine = DownloaderEngine(self.config)
                    cprint(f"  [✓] ¡Sesión configurada con éxito en {path}!", Style.GREEN, bold=True)
                    time.sleep(1.5)
            elif sub == "2":
                path = input("\n  Ruta absoluta del archivo cookies.txt: ").strip()
                if path and os.path.isfile(path):
                    self.config["cookies_file"] = os.path.abspath(path)
                    ConfigManager.save_config(self.config)
                    self.engine = DownloaderEngine(self.config)
                    cprint("  [✓] Archivo de cookies guardado.", Style.GREEN)
                else:
                    cprint("  [!] Archivo no encontrado.", Style.RED)
                time.sleep(1.5)
            elif sub == "3":
                self.show_cookie_guide()
            elif sub == "4":
                self.config["cookies_file"] = ""
                if os.path.isfile(DEFAULT_COOKIE_FILE):
                    try:
                        os.remove(DEFAULT_COOKIE_FILE)
                    except OSError:
                        pass
                ConfigManager.save_config(self.config)
                self.engine = DownloaderEngine(self.config)
                cprint("  [✓] Sesión desactivada.", Style.YELLOW)
                time.sleep(1.5)
            elif sub == "0":
                break

    def update_tools(self):
        self.print_banner()
        cprint("  ACTUALIZACIÓN DE EXTRACTORES", Style.YELLOW, bold=True)
        print("  Esta opción actualizará yt-dlp, gallery-dl y parth-dl.\n")

        confirm = input("  ¿Deseas buscar y aplicar actualizaciones ahora? (S/n): ").strip().lower()
        if confirm in ("n", "no"):
            return

        cprint("\n  [+] Actualizando dependencias via pip...", Style.CYAN)
        cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", "-U", "yt-dlp", "gallery-dl", "parth-dl", "requests", "instaloader"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0 and "--break-system-packages" in res.stderr:
                cmd = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "gallery-dl", "parth-dl", "requests", "instaloader"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                cprint("\n  [✓] ¡Extractores actualizados con éxito!", Style.GREEN, bold=True)
            else:
                cprint(f"\n  [!] Error: {res.stderr}", Style.RED)
        except Exception as e:
            cprint(f"\n  [!] Error ejecutando pip: {e}", Style.RED)

        input("\nPresiona [Enter] para continuar...")

    def run(self):
        while True:
            self.print_banner()
            cprint("  MENÚ PRINCIPAL", Style.YELLOW, bold=True)
            print("  [1] 🚀 Descarga Rápida (Video o Imagen - Detección automática)")
            print("  [2] 🎬 Descargar Videos (Reels, TikToks, Shorts - Máxima Calidad)")
            print("  [3] 🖼️  Descargar Imágenes o Carruseles (Fotos / Perfiles IG - Máxima Calidad)")
            print("  [4] 🎵 Descargar solo Audio (MP3 - 320 kbps)")
            print("  [5] 📦 Descarga por Lotes (Múltiples enlaces a la vez)")
            print("  [6] 📁 Ver archivos guardados (Videos / Imágenes / Audios)")
            print("  [7] ⚙️  Configuración y Autenticación")
            print("  [8] 🔄 Actualizar extractores (yt-dlp, gallery-dl, parth-dl)")
            print("  [0] 🚪 Salir\n")

            try:
                choice = input(f"{Style.BOLD}Selecciona una opción [0-8]: {Style.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if choice == "1":
                self.loop_single_download(mode="auto")
            elif choice == "2":
                self.loop_single_download(mode="video")
            elif choice == "3":
                self.loop_single_download(mode="image")
            elif choice == "4":
                self.loop_single_download(mode="audio")
            elif choice == "5":
                self.batch_download()
            elif choice == "6":
                self.list_downloads()
            elif choice == "7":
                self.settings_menu()
            elif choice == "8":
                self.update_tools()
            elif choice in ("0", "salir", "exit", "q"):
                cprint("\n  ¡Gracias por usar MDsave! Hasta pronto.\n", Style.CYAN, bold=True)
                break


def cli_direct_mode():
    import argparse
    parser = argparse.ArgumentParser(
        description="MDsave: Descargador automatizado de Reels, TikToks, Shorts, Fotos, Carruseles y Perfiles de Instagram en MÁXIMA CALIDAD.",
        epilog="Ejemplos:\n  mdsave https://www.instagram.com/reel/DfqowGcTzHY/\n  mdsave https://www.instagram.com/nasa/  (Foto de perfil HD)\n  mdsave @nasa\n  mdsave --set-cookie 123456%3Atoken\n  mdsave -a https://www.tiktok.com/@user/video/...\n  mdsave -b lista.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("url", nargs="?", help="URL del vídeo o imagen a descargar")
    parser.add_argument("-v", "--video", action="store_true", help="Forzar modo descarga de video")
    parser.add_argument("-i", "--image", action="store_true", help="Forzar modo descarga de imagen o carrusel")
    parser.add_argument("-a", "--audio", action="store_true", help="Descargar solo el audio en máxima calidad (320 kbps)")
    parser.add_argument("-b", "--batch", help="Ruta de un archivo de texto con múltiples enlaces a descargar")
    parser.add_argument("-d", "--dir", help="Directorio base personalizado para esta ejecución")
    parser.add_argument("--set-cookie", dest="set_cookie", help="Guardar 'sessionid' de Instagram para desbloquear contenido 18+/privado")
    parser.add_argument("--cookies", dest="cookies_file", help="Ruta de un archivo cookies.txt para esta ejecución")

    args = parser.parse_args()

    config = ConfigManager.load_config()

    if args.set_cookie:
        p = ConfigManager.save_instagram_session(args.set_cookie, config)
        cprint(f"[✓] sessionid de Instagram guardado exitosamente en: {p}", Style.GREEN, bold=True)
        cprint("Ahora puedes descargar cualquier contenido privado o restringido por edad.", Style.CYAN)
        return

    if args.cookies_file:
        config["cookies_file"] = os.path.abspath(args.cookies_file)

    if not args.url and not args.batch:
        ui = TerminalUI()
        ui.run()
        return

    if args.dir:
        config["base_dir"] = args.dir

    engine = DownloaderEngine(config)

    if args.batch:
        if not os.path.isfile(args.batch):
            cprint(f"[!] El archivo '{args.batch}' no existe.", Style.RED)
            sys.exit(1)
        with open(args.batch, "r", encoding="utf-8") as f:
            content = f.read()
        links = re.findall(r'https?://[^\s,;"\']+', content)
        cprint(f"[+] Procesando {len(links)} enlaces desde {args.batch}...", Style.CYAN)
        mode = "audio" if args.audio else ("image" if args.image else ("video" if args.video else "auto"))
        for link in links:
            engine.download(link, mode=mode)
        return

    if args.url:
        mode = "audio" if args.audio else ("image" if args.image else ("video" if args.video else "auto"))
        success, files, platform, msg, meta = engine.download(args.url, mode=mode)
        ui = TerminalUI()
        if not success and is_audience_restricted_error(msg):
            cprint("\n[!] Este contenido tiene restricción de audiencia / edad por parte de Instagram.", Style.YELLOW, bold=True)
            cprint("    Instagram requiere una sesión activa para entregar el video.", Style.WHITE)
            cprint("    Ejecuta: mdsave --set-cookie <tu_sessionid> para desbloquearlo de inmediato.", Style.CYAN, bold=True)
            cprint("    O abre 'mdsave' y ve a Configuración > [3] Autenticación de Instagram.", Style.WHITE)
        ui.report_results(success, files, platform, msg, meta)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        cli_direct_mode()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)
