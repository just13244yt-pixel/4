import curses
import os
import shutil
import sys
import time
import json
import psutil
import platform
from datetime import datetime, timedelta
import subprocess

def boot_animation(stdscr):
    h, w = stdscr.getmaxyx()
    boot_msg = "BOOTING JUST-OS..."
    stdscr.addstr(h//2, (w - len(boot_msg))//2, boot_msg, curses.color_pair(1))
    stdscr.refresh()
    time.sleep(2)

# --- SYSTEM-CHECK ---
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# --- CONFIG & PERSISTENCE ---
DATA_FILE = "just_os_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if "cfg" not in data: data["cfg"] = {}
                if "padding" not in data["cfg"]: data["cfg"]["padding"] = 6
                if "notes" not in data: data["notes"] = []
                if "username" not in data["cfg"]: data["cfg"]["username"] = "User"
                if "theme" not in data["cfg"]: data["cfg"]["theme"] = "default"
                # Vollständige Farbcodes sicherstellen
                keys = ["border", "text", "logo", "bg", "sel_bg", "sel_txt", "taskbar_bg", "taskbar_txt"]
                defaults = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_BLUE,
                            curses.COLOR_BLACK, curses.COLOR_CYAN, curses.COLOR_BLACK,
                            curses.COLOR_BLACK, curses.COLOR_WHITE]
                for k, d in zip(keys, defaults):
                    if k not in data["cfg"]: data["cfg"][k] = d
                return data
        except:
            pass
    return {"notes": [], "cfg": {
        "border": curses.COLOR_BLUE, "text": curses.COLOR_CYAN, "logo": curses.COLOR_BLUE,
        "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN, "sel_txt": curses.COLOR_BLACK,
        "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_WHITE,
        "padding": 6,
        "username": "User",
        "theme": "default"
    }}

user_data = load_data()
cfg = user_data["cfg"]

def save_data():
    user_data["cfg"] = cfg
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=4)

# --- THEMES ---
themes = {
    "default": {
        "border": curses.COLOR_BLUE, "text": curses.COLOR_CYAN, "logo": curses.COLOR_BLUE,
        "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN, "sel_txt": curses.COLOR_BLACK,
        "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_WHITE
    },
    "dark_green": {
        "border": curses.COLOR_GREEN, "text": curses.COLOR_WHITE, "logo": curses.COLOR_GREEN,
        "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_GREEN, "sel_txt": curses.COLOR_BLACK,
        "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_GREEN
    },
    "light_blue": {
        "border": curses.COLOR_CYAN, "text": curses.COLOR_BLACK, "logo": curses.COLOR_BLUE,
        "bg": curses.COLOR_WHITE, "sel_bg": curses.COLOR_BLUE, "sel_txt": curses.COLOR_WHITE,
        "taskbar_bg": curses.COLOR_BLUE, "taskbar_txt": curses.COLOR_WHITE
    }
}

def apply_theme(theme_name):
    if theme_name in themes:
        for key, value in themes[theme_name].items():
            cfg[key] = value
    apply_colors()

# --- MASSIVE BEFEHLSDATENBANK (ÜBER 50 EINTRÄGE) ---
CMD_LIST = [
    ("ls -la", "Linux: Alle Dateien inkl. versteckter anzeigen"),
    ("dir /attr", "Windows: Verzeichnisinhalt mit Attributen"),
    ("cd ..", "Universal: Ein Verzeichnis nach oben wechseln"),
    ("chmod +x", "Linux: Datei ausführbar machen"),
    ("sudo su", "Linux: Zum Root-Benutzer wechseln"),
    ("ip a", "Linux: IP-Adressen & Interfaces anzeigen"),
    ("ipconfig /all", "Windows: Komplette Netzwerk-Konfiguration"),
    ("rm -rf", "Linux: Löscht Verzeichnisse rekursiv (Vorsicht!)"),
    ("del /f /s", "Windows: Dateien erzwingen zu löschen"),
    ("mkdir -p", "Universal: Ganze Ordner-Pfade erstellen"),
    ("touch", "Universal: Neue leere Datei anlegen"),
    ("cat", "Linux: Dateiinhalt im Terminal ausgeben"),
    ("type", "Windows: Dateiinhalt im Terminal ausgeben"),
    ("nano", "Linux: Beliebter Terminal-Texteditor"),
    ("notepad", "Windows: Standard Editor öffnen"),
    ("top", "Linux: Systemprozesse in Echtzeit"),
    ("htop", "Linux: Verbesserter bunter Taskmanager"),
    ("tasklist", "Windows: Alle laufenden Prozesse auflisten"),
    ("df -h", "Linux: Festplattenplatz (menschlich lesbar)"),
    ("free -m", "Linux: RAM-Auslastung in Megabyte"),
    ("ping -c 4", "Linux: Verbindung prüfen (4 Pakete)"),
    ("ping -n 4", "Windows: Verbindung prüfen (4 Pakete)"),
    ("nmap -sV", "Netzwerk-Scan: Dienste & Versionen finden"),
    ("airmon-ng", "Linux: WLAN-Monitor-Mode aktivieren"),
    ("airodump-ng", "Linux: WLAN-Netzwerke in der Nähe scannen"),
    ("iwconfig", "Linux: WLAN-Schnittstellen konfigurieren"),
    ("wget -c", "Universal: Download fortsetzen"),
    ("curl -I", "HTTP-Header einer Webseite prüfen"),
    ("apt update", "Linux: Paketlisten aktualisieren"),
    ("apt upgrade", "Linux: Alle Programme aktualisieren"),
    ("winget search", "Windows: Nach Software suchen"),
    ("whoami", "Aktuellen Benutzernamen anzeigen"),
    ("uptime -p", "System-Laufzeit schön anzeigen"),
    ("history -c", "Befehlsverlauf im Terminal löschen"),
    ("reboot", "System sofort neu starten"),
    ("shutdown -h now", "System sofort herunterfahren"),
    ("grep -ri", "Linux: Text in Dateien suchen (case-insensitive)"),
    ("findstr /s", "Windows: Text in Unterverzeichnissen suchen"),
    ("tar -xzvf", "Linux: .tar.gz Archiv entpacken"),
    ("zip -r", "Universal: Dateien in ZIP komprimieren"),
    ("unzip", "Universal: ZIP-Dateien entpacken"),
    ("ssh user@host", "Sichere Remote-Verbindung herstellen"),
    ("scp file user@host:", "Dateien sicher über SSH kopieren"),
    ("systemctl start", "Linux: System-Dienst starten"),
    ("systemctl status", "Linux: Status eines Dienstes prüfen"),
    ("journalctl -xe", "Linux: Letzte Systemfehler anzeigen"),
    ("lsblk", "Linux: Alle Festplatten & Partitionen"),
    ("ps aux", "Linux: Detaillierte Prozessliste"),
    ("kill -9 [PID]", "Linux: Prozess sofort abschießen"),
    ("taskkill /F /PID", "Windows: Prozess sofort beenden"),
    ("netstat -tuln", "Linux: Alle hörenden Ports anzeigen"),
    ("nslookup", "DNS-Einträge einer Domain prüfen"),
    ("chown", "Linux: Dateibesitzer ändern"),
    ("passwd", "Passwort des aktuellen Users ändern")
]

HACK_PAGES = [
    {"n": "WIRELESS", "t": ["aircrack-ng", "wifite", "reaver", "bully", "fluxion", "wifipumpkin3", "eaphammer"]},
    {"n": "PASSWORDS", "t": ["hashcat", "john", "hydra", "medusa", "crunch", "cupp", "hash-id"]},
    {"n": "NETWORK", "t": ["nmap", "bettercap", "wireshark", "netdiscover", "fping", "hping3", "masscan"]},
    {"n": "EXPLOIT", "t": ["msfconsole", "sqlmap", "commix", "searchsploit", "beef-xss", "metasploit"]},
    {"n": "SNIFFING", "t": ["tcpdump", "ettercap", "mitmproxy", "responser", "evil-trust"]}
]

# --- UI LOGIK & FARBEN ---

def apply_colors():
    curses.start_color()
    curses.init_pair(1, cfg["logo"], cfg["bg"])
    curses.init_pair(2, cfg["border"], cfg["bg"])
    curses.init_pair(3, cfg["text"], cfg["bg"])
    curses.init_pair(4, curses.COLOR_GREEN, cfg["bg"])
    curses.init_pair(5, curses.COLOR_RED, cfg["bg"])
    curses.init_pair(6, curses.COLOR_YELLOW, cfg["bg"])
    curses.init_pair(7, cfg["sel_txt"], cfg["sel_bg"])
    curses.init_pair(8, cfg["taskbar_txt"], cfg["taskbar_bg"])

def draw_frame(stdscr, title, sidebar_width=0, taskbar_height=0):
    h, w = stdscr.getmaxyx()
    # Draw subtle shadow
    shadow_char = curses.ACS_CKBOARD # A darker shade character
    stdscr.attron(curses.color_pair(1))
    for y in range(1, h - taskbar_height):
        if w > 1: stdscr.addch(y, w - 1, shadow_char)
    if h - taskbar_height > 1:
        for x in range(1, w - 1):
            stdscr.addch(h - taskbar_height - 1, x, shadow_char)
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
    stdscr.border(0, 0, 0, 0, 0, 0, 0, 0)
    if sidebar_width > 0:
        stdscr.vline(0, sidebar_width, curses.ACS_VLINE, h - taskbar_height)
        stdscr.addch(0, sidebar_width, curses.ACS_TTEE)
        if taskbar_height > 0:
            stdscr.addch(h - taskbar_height -1, sidebar_width, curses.ACS_BTEE)
        else:
            stdscr.addch(h-1, sidebar_width, curses.ACS_BTEE)

    if taskbar_height > 0:
        stdscr.hline(h - taskbar_height - 1, 0, curses.ACS_HLINE, w)
        stdscr.addch(h - taskbar_height - 1, 0, curses.ACS_LTEE)
        stdscr.addch(h - taskbar_height - 1, w - 1, curses.ACS_RTEE)
        if sidebar_width > 0:
            stdscr.addch(h - taskbar_height - 1, sidebar_width, curses.ACS_PLUS)

    title_str = f" [ {title.upper()} ] "
    stdscr.addstr(0, max(sidebar_width + 1, (w + sidebar_width)//2 - len(title_str)//2), titl    stdscr.attroff(curses.color_pair(1))ef get_network_info():
    info = {"ssid": "N/A", "ip": "N/A", "signal": "N/A", "error": ""}
    if IS_LINUX:
        try:
            # Get active connection details
            cmd = "nmcli -t -f active,ssid,signal,ip4.address device wifi list"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            found_active = False
            for line in lines:
                if line.startswith("yes"): # Active connection
                    parts = line.split(":")
                    # Ensure enough parts before accessing
                    if len(parts) > 1:
                        info["ssid"] = parts[1]
                    if len(parts) > 2:
                        info["signal"] = parts[2]
                    if len(parts) > 3:
                        ip_address_full = parts[3]
                        if '/' in ip_address_full:
                            info["ip"] = ip_address_full.split('/')[0]
                        else:
                            info["ip"] = ip_address_full
                    found_active = True
                    break
            
            if not found_active:
                info["error"] = "No active Wi-Fi connection found."
        except subprocess.CalledProcessError as e:
            info["error"] = f"nmcli error: {e.stderr.strip()}"
        except Exception as e:
            info["error"] = str(e)
    return info

def draw_sidebar(stdscr, sidebar_width, taskbar_height):
    h, w = stdscr.getmaxyx()
    if sidebar_width == 0: return

    # System Info
    stdscr.addstr(2, 2, "SYSTEM", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(3, 2, f"CPU: {psutil.cpu_percent()}%", curses.color_pair(3))
    stdscr.addstr(4, 2, f"RAM: {psutil.virtual_memory().percent}%", curses.color_pair(3))
    stdscr.addstr(5, 2, f"UPTIME: {int(time.time() - psutil.boot_time()) // 3600}h", curses.color_pair(3))

    # Network Info
    stdscr.addstr(7, 2, "NETWORK", curses.color_pair(1) | curses.A_BOLD)
    net_info = get_network_info()
    stdscr.addstr(8, 2, f"SSID: {net_info['ssid']}", curses.color_pair(3))
    stdscr.addstr(9, 2, f"SIGNAL: {net_info["signal"]}%", curses.color_pair(3))
    stdscr.addstr(10, 2, f"IP: {net_info["ip"]}", curses.color_pair(3))
    if net_info["error"]:
        stdscr.addstr(11, 2, f"Err: {net_info["error"][:sidebar_width-8]}", curses.color_pair(5))

    # Separator
    stdscr.hline(13, 1, curses.ACS_HLINE, sidebar_width - 2)

    # Live Clock
    stdscr.addstr(h - taskbar_height - 3, 2, f"TIME: {datetime.now().strftime(\"%H:%M:%S\")}", curses.color_pair(6))
def draw_taskbar(stdscr, taskbar_height, sidebar_width):
    h, w = stdscr.getmaxyx()
    if taskbar_height == 0: return

    taskbar_y = h - taskbar_height
    stdscr.attron(curses.color_pair(8))
    stdscr.addstr(taskbar_y, 0, " " * w)
    
    # User and System Status
    status_str = f" {cfg['username']}@JUST-OS "
    # Quick Launch Icons
    quick_launch_icons = [
        ("EXP", explorer),
        ("CMD", commands_view),
        ("WIFI", wifi_menu),
        ("SET", settings_menu)
    ]
    for i, (icon_name, func) in enumerate(quick_launch_icons):
        stdscr.addstr(taskbar_y, sidebar_width + cfg["padding"] + i * 6, f"[{icon_name}]", curses.color_pair(8) | curses.A_BOLD)

    # Handle quick launch clicks (this is a simplified approach, actual click detection is complex in curses)
    # For now, just display the icons.
    # The actual launching will be handled by keybindings in the main loop if needed.
    stdscr.addstr(taskbar_y, sidebar_width + cfg["padding"] + len(quick_launch_icons) * 6 + 3, status_str)

    # Time on right
    time_str = datetime.now().strftime('%H:%M:%S')
    stdscr.addstr(taskbar_y, w - len(time_str) - 2, time_str)
    stdscr.attroff(curses.color_pair(8))

# --- USB DETECTION HELPER ---
def detect_usb_drives():
    usb_drives = []
    if IS_WINDOWS:
        import string
        from ctypes import windll
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drive_type = windll.kernel32.GetDriveTypeW(drive_path)
                    if drive_type == 2:  # DRIVE_REMOVABLE
                        try:
                            size = psutil.disk_usage(drive_path)
                            name = f"USB ({letter}:) - {size.total // (1024**3)}GB"
                            usb_drives.append((drive_path, name))
                        except:
                            usb_drives.append((drive_path, f"USB ({letter}:)"))
            bitmask >>= 1
    elif IS_LINUX:
        mount_paths = ["/media", "/mnt", "/run/media"]
        for mount_path in mount_paths:
            if os.path.exists(mount_path):
                for user_dir in os.listdir(mount_path):
                    user_path = os.path.join(mount_path, user_dir)
                    if os.path.isdir(user_path):
                        for device in os.listdir(user_path):
                            device_path = os.path.join(user_path, device)
                            if os.path.isdir(device_path) and os.access(device_path, os.W_OK):
                                try:
                                    size = psutil.disk_usage(device_path)
                                    name = f"USB {device} - {size.total // (1024**3)}GB"
                                    usb_drives.append((device_path, name))
                                except:
                                    usb_drives.append((device_path, f"USB {device}"))
    return usb_drives

def copy_to_usb(stdscr, source_file, sidebar_width, taskbar_height):
    usb_drives = detect_usb_drives()
    if not usb_drives:
        stdscr.clear()
        draw_frame(stdscr, "KEINE USB-LAUFWERKE", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)
        h, w = stdscr.getmaxyx()
        content_start_x = sidebar_width + cfg["padding"]
        stdscr.addstr(h//2, content_start_x, "❌ Keine USB-Laufwerke gefunden!", curses.color_pair(5))
        stdscr.addstr(h//2 + 2, content_start_x, "Beliebige Taste zum Fortfahren...", curses.color_pair(3))
        stdscr.getch()
        return False
    sel = 0
    while True:
        stdscr.clear()
        draw_frame(stdscr, "USB-LAUFWERK WÄHLEN", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)
        h, w = stdscr.getmaxyx()
        pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        stdscr.addstr(3, content_start_x, f"Datei: {os.path.basename(source_file)}", curses.color_pair(6))
        stdscr.addstr(5, content_start_x, "Verfügbare USB-Laufwerke:", curses.color_pair(3))
        for i, (path, name) in enumerate(usb_drives):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(7 + i, content_start_x, f" > {name} ", attr)
        stdscr.addstr(7 + len(usb_drives) + 1, content_start_x, "[ENTER] Kopieren | [Q] Abbrechen", curses.color_pair(6))
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0:
            sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(usb_drives) - 1:
            sel += 1
        elif k in [10, 13]:
            dest_path = os.path.join(usb_drives[sel][0], os.path.basename(source_file))
            stdscr.addstr(h - taskbar_height - 3, content_start_x, "⏳ Kopiere...", curses.color_pair(6))
            stdscr.refresh()
            try:
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, dest_path)
                else:
                    shutil.copytree(source_file, dest_path)
                stdscr.addstr(h - taskbar_height - 3, content_start_x, "✓ Erfolgreich kopiert!     ", curses.color_pair(4))
                stdscr.refresh()
                time.sleep(1.5)
                return True
            except Exception as e:
                stdscr.addstr(h - taskbar_height - 3, content_start_x, f"❌ Fehler: {str(e)[:w-content_start_x-10]}", curses.color_pair(5))
                stdscr.refresh()
                time.sleep(2)
                return False
        elif k == ord('q'):
            return False

# --- MODULES ---

def explorer(stdscr):
    curr, sel, search_query = os.getcwd(), 0, ""
    clipboard = None # For cut/copy/paste
    stdscr.timeout(1000)
    sidebar_width = 30
    taskbar_height = 1
    while True:
        stdscr.clear()
        draw_frame(stdscr, f"EXPLORER: {curr}", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx()
        pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        content_height = h - taskbar_height - 1 # Adjust for taskbar and frame

        stdscr.addstr(h-taskbar_height-2, content_start_x, "[N] NEW | [D] DEL | [E] EDIT | [F] SEARCH | [U] USB-COPY | [C] CUT/MOVE | [V] PASTE | [Q] BACK", curses.color_pair(6))

        try:
            all_items = [".. (ZURÜCK)"] + sorted(os.listdir(curr))
            items = [all_items[0]] + [i for i in all_items[1:] if search_query.lower() in i.lower()] if search_query else all_items
        except: items = [".. (ZURÜCK)"]
        
        if sel >= len(items): sel = max(0, len(items)-1)

        for i, item in enumerate(items[:content_height-10]): # Adjust for taskbar and bottom status line
            path = os.path.join(curr, item); is_dir = os.path.isdir(path)
            attr = curses.color_pair(7) if i == sel else (curses.color_pair(6) if is_dir else curses.color_pair(3))
            display_item = f" {'[ORDNER]' if is_dir else '        '} {item[:w-content_start_x-30]} "
            stdscr.addstr(4+i, content_start_x, display_item, attr)
            
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(items)-1: sel += 1
        elif k in [10, 13]:
            path = os.path.join(curr, items[sel])
            if items[sel] == ".. (ZURÜCK)": curr = os.path.dirname(curr); sel = 0; search_query = ""
            elif os.path.isdir(path): curr = path; sel = 0; search_query = ""
        elif k == ord('e') and sel > 0:
            path = os.path.join(curr, items[sel])
            if not os.path.isdir(path):
                curses.endwin()
                subprocess.call(["notepad" if IS_WINDOWS else "nano", path])
                stdscr.clear(); apply_colors(); curses.curs_set(0)
        elif k == ord('n'):
            stdscr.addstr(h-taskbar_height-3, content_start_x, "Name der neuen Datei: "); curses.echo()
            name = stdscr.getstr().decode(); curses.noecho()
            if name: open(os.path.join(curr, name), 'a').close()
        elif k == ord('d') and sel > 0:
            name = items[sel]
            stdscr.addstr(h-taskbar_height-3, content_start_x, f"{name} löschen? (y/n): ", curses.color_pair(5))
            if stdscr.getch() == ord('y'):
                path = os.path.join(curr, name)
                try:
                    if os.path.isdir(path): shutil.rmtree(path)
                    else: os.remove(path)
                except: pass
        elif k == ord('u') and sel > 0:
            if items[sel] != ".. (ZURÜCK)":
                source_path = os.path.join(curr, items[sel])
                copy_to_usb(stdscr, source_path, sidebar_width, taskbar_height)
        elif k == ord('c') and sel > 0: # Cut/Move
            clipboard = os.path.join(curr, items[sel])
            stdscr.addstr(h-taskbar_height-3, content_start_x, f"'{items[sel]}' in Zwischenablage kopiert. Navigieren und [V] zum Einfügen.", curses.color_pair(6))
        elif k == ord('v') and clipboard: # Paste
            try:
                dest_path = os.path.join(curr, os.path.basename(clipboard))
                if os.path.isdir(clipboard):
                    shutil.move(clipboard, dest_path)
                else:
                    shutil.move(clipboard, dest_path)
                clipboard = None
                stdscr.addstr(h-taskbar_height-3, content_start_x, "Datei/Ordner erfolgreich verschoben.", curses.color_pair(4))
            except Exception as e:
                stdscr.addstr(h-taskbar_height-3, content_start_x, f"Fehler beim Verschieben: {str(e)}", curses.color_pair(5))
            stdscr.refresh(); time.sleep(1.5)
        elif k == ord('f'):
            stdscr.addstr(h-taskbar_height-3, content_start_x, "Suchen nach: "); curses.echo()
            search_query = stdscr.getstr().decode(); curses.noecho(); sel = 0
        elif k == ord('q'): break

def commands_view(stdscr):
    sel, offset = 0, 0
    stdscr.timeout(1000)
    sidebar_width = 30
    taskbar_height = 1
    while True:
        stdscr.clear()
        draw_frame(stdscr, "SYSTEM-BEFEHLE", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); max_r, pad = h - taskbar_height - 6, cfg["padding"]
        content_start_x = sidebar_width + pad

        for i, (c, d) in enumerate(CMD_LIST[offset:offset+max_r]):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(3+i, content_start_x, f"{c:<22} | {d[:w-content_start_x-30]}", attr)
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP]:
            if sel > 0: sel -= 1
            elif offset > 0: offset -= 1
        elif k in [ord('s'), curses.KEY_DOWN]:
            if sel < max_r - 1: sel += 1
            elif offset+max_r < len(CMD_LIST): offset += 1
        elif k == ord('q'): break

def hacking_tools(stdscr):
    if not IS_LINUX:
        stdscr.clear(); draw_frame(stdscr, "ZUGRIFF VERWEIGERT")
        h, w = stdscr.getmaxyx()
        stdscr.addstr(10, cfg["padding"], "HACKING TOOLS SIND NUR UNTER LINUX VERFÜGBAR.", curses.color_pair(5))
        stdscr.addstr(12, cfg["padding"], "BELIEBIGE TASTE ZUM ZURÜCKKEHREN...", curses.color_pair(3))
        stdscr.getch(); return
    
    p_idx, sel = 0, 0
    stdscr.timeout(1000)
    sidebar_width = 30
    taskbar_height = 1
    while True:
        stdscr.clear()
        page = HACK_PAGES[p_idx]
        draw_frame(stdscr, f"TOOLS: {page['n']}", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx()
        items, pad = page['t'] + ["ZURÜCK"], cfg["padding"]
        content_start_x = sidebar_width + pad

        stdscr.addstr(h-taskbar_height-2, content_start_x, "STEUERUNG: [A/D] KATEGORIE | [W/S] AUSWAHL | [ENTER] START", curses.color_pair(6))
        for i, item in enumerate(items):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(6+i, content_start_x, f" [#] {item.upper()} ", attr)
        k = stdscr.getch()
        if k in [ord('d'), curses.KEY_RIGHT]: p_idx = (p_idx+1)%len(HACK_PAGES); sel=0
        elif k in [ord('a'), curses.KEY_LEFT]: p_idx = (p_idx-1)%len(HACK_PAGES); sel=0
        elif k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(items)-1: sel += 1
        elif k == 10:
            if items[sel] == "ZURÜCK": break
            curses.endwin()
            subprocess.call([items[sel]])
            stdscr.clear(); apply_colors(); curses.curs_set(0)
        elif k == ord('q'): break

def notes_menu(stdscr):
    sel = 0
    stdscr.timeout(1000)
    sidebar_width = 30
    taskbar_height = 1
    while True:
        stdscr.clear()
        draw_frame(stdscr, "NOTIZEN & INFOS", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad

        notes = user_data["notes"]
        display_list = notes + ["---", "+ NEUE NOTIZ", "ALLE LÖSCHEN", "ZURÜCK"]
        
        for i, item in enumerate(display_list):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(4+i, content_start_x, f" > {item} ", attr)
            
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(display_list)-1: sel += 1
        elif k in [10, 13]:
            choice = display_list[sel]
            if choice == "ZURÜCK": break
            elif choice == "ALLE LÖSCHEN": 
                user_data["notes"] = []; save_data()
            elif choice == "+ NEUE NOTIZ":
                stdscr.addstr(h-taskbar_height-3, content_start_x, "Inhalt: "); curses.echo()
                new = stdscr.getstr().decode(); curses.noecho()
                if new: user_data["notes"].append(new); save_data()
            elif choice != "---":
                user_data["notes"].pop(sel); save_data()
        elif k == ord('q'): break

def settings_menu(stdscr):
    sel = 0
    stdscr.timeout(1000)
    colors = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE]
    names = ["BLAU", "CYAN", "GRÜN", "ROT", "GELB", "WEISS"]
    theme_names = list(themes.keys())

    sidebar_width = 30
    taskbar_height = 1

    while True:
        stdscr.clear()
        draw_frame(stdscr, "EINSTELLUNGEN", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad

        opts = [f"RAHMEN-FARBE: {names[colors.index(cfg['border'])]}",
                f"TEXT-FARBE  : {names[colors.index(cfg['text'])]}",
                f"LOGO-FARBE  : {names[colors.index(cfg['logo'])]}",
                f"RAND-ABSTAND: {cfg['padding']}px",
                f"BENUTZERNAME: {cfg['username']}",
                f"THEME       : {cfg['theme'].upper()}",
                "KONFIGURATION SPEICHERN", "ZURÜCK"]
        
        for i, o in enumerate(opts):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(4+i*2, content_start_x, f" {o} ", attr)
            
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(opts)-1: sel += 1
        elif k in [10, 13]:
            if sel == 0: cfg['border'] = colors[(colors.index(cfg['border'])+1)%len(colors)]
            elif sel == 1: cfg['text'] = colors[(colors.index(cfg['text'])+1)%len(colors)]
            elif sel == 2: cfg['logo'] = colors[(colors.index(cfg['logo'])+1)%len(colors)]
            elif sel == 3: cfg['padding'] = 2 if cfg['padding'] >= 22 else cfg['padding']+4
            elif sel == 4: # Change Username
                stdscr.addstr(h-taskbar_height-3, content_start_x, "Neuer Benutzername: "); curses.echo()
                new_username = stdscr.getstr().decode(); curses.noecho()
                if new_username: cfg['username'] = new_username
            elif sel == 5: # Change Theme
                current_theme_idx = theme_names.index(cfg['theme'])
                next_theme_idx = (current_theme_idx + 1) % len(theme_names)
                cfg['theme'] = theme_names[next_theme_idx]
                apply_theme(cfg['theme'])
            elif sel == 6: 
                save_data()
                stdscr.addstr(h-taskbar_height-3, content_start_x, "GESPEICHERT!", curses.color_pair(4))
                stdscr.refresh(); time.sleep(0.5)
            elif sel == 7: break
            apply_colors()
        elif k == ord('q'): break

def get_wifi_networks():
    networks = []
    try:
        cmd = "nmcli -t -f ssid,signal device wifi list"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            parts = line.split(':')
            if len(parts) >= 2:
                ssid = parts[0]
                signal = parts[1]
                networks.append((ssid, signal))
        networks.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0, reverse=True)
    except Exception as e:
        networks.append((f"Error: {str(e)}", "0"))
    return networks

def connect_to_wifi(stdscr, ssid, password, sidebar_width, taskbar_height):
    try:
        # Deactivate existing connection if any
        subprocess.run("nmcli device disconnect wlan0", shell=True, capture_output=True, text=True)
        
        # Remove existing connection for this SSID if it exists
        subprocess.run(f"nmcli connection delete \"{ssid}\"", shell=True, capture_output=True, text=True)

        # Create and activate new connection
        cmd = f"nmcli device wifi connect \"{ssid}\" password \"{password}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        if "successfully activated" in result.stdout:
            return True, "Verbunden!"
        else:
            return False, result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except Exception as e:
        return False, str(e)

def wifi_menu(stdscr):
    if not IS_LINUX:
        stdscr.clear(); draw_frame(stdscr, "ZUGRIFF VERWEIGERT")
        h, w = stdscr.getmaxyx()
        stdscr.addstr(10, cfg["padding"], "WLAN-FUNKTIONEN SIND NUR UNTER LINUX VERFÜGBAR.", curses.color_pair(5))
        stdscr.addstr(12, cfg["padding"], "BELIEBIGE TASTE ZUM ZURÜCKKEHREN...", curses.color_pair(3))
        stdscr.getch(); return

    sel = 0
    stdscr.timeout(1000)
    sidebar_width = 30
    taskbar_height = 1
    while True:
        stdscr.clear()
        draw_frame(stdscr, "WLAN-MANAGER", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad

        stdscr.addstr(4, content_start_x, "Verfügbare WLAN-Netzwerke:", curses.color_pair(6))
        networks = get_wifi_networks()

        display_networks = [f"{ssid} ({signal}%)" for ssid, signal in networks]
        display_list = display_networks + ["---", "ZURÜCK"]

        for i, item in enumerate(display_list):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(6+i, content_start_x, f" > {item} ", attr)

        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(display_list)-1: sel += 1
        elif k in [10, 13]:
            choice = display_list[sel]
            if choice == "ZURÜCK": break
            elif choice != "---":
                ssid_to_connect = networks[sel][0]
                stdscr.addstr(h-taskbar_height-3, content_start_x, f"Passwort für {ssid_to_connect}: "); curses.echo()
                password = stdscr.getstr().decode(); curses.noecho()
                
                stdscr.addstr(h-taskbar_height-4, content_start_x, "Verbinde...", curses.color_pair(6))
                stdscr.refresh()
                success, message = connect_to_wifi(stdscr, ssid_to_connect, password, sidebar_width, taskbar_height)
                if success:
                    stdscr.addstr(h-taskbar_height-4, content_start_x, f"✓ {message}", curses.color_pair(4))
                else:
                    stdscr.addstr(h-taskbar_height-4, content_start_x, f"❌ {message}", curses.color_pair(5))
                stdscr.refresh(); time.sleep(2)
        elif k == ord('q'): break

# --- NEW MODULES (PLACEHOLDERS) ---def dashboard_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    stdscr.timeout(1000)
    while True:
        stdscr.clear()
        draw_frame(stdscr, "SYSTEM-DASHBOARD", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        content_width = w - sidebar_width - pad

        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=0.5) # Increased interval for lower resource usage on RPi Zero W
        stdscr.addstr(4, content_start_x, f"CPU-Auslastung: {cpu_percent:.1f}%", curses.color_pair(3))
        # RAM Usage
        ram = psutil.virtual_memory()
        stdscr.addstr(5, content_start_x, f"RAM-Auslastung: {ram.percent:.1f}% ({ram.used / (1024**3):.1f}GB / {ram.total / (1024**3):.1f}GB)", curses.color_pair(3))
        # Disk Usage
        disk = psutil.disk_usage(\"/\")
        stdscr.addstr(6, content_start_x, f"Festplatte (Root): {disk.percent:.1f}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)", curses.color_pair(3))
        # Network Stats (simple)
        net_io = psutil.net_io_counters()
        stdscr.addstr(7, content_start_x, f"Netzwerk (Gesendet): {net_io.bytes_sent / (1024**2):.1f} MB", curses.color_pair(3))
        stdscr.addstr(8, content_start_x, f"Netzwerk (Empfangen): {net_io.bytes_recv / (1024**2):.1f} MB", curses.color_pair(3))

        stdscr.addstr(h - taskbar_height - 2, content_start_x, "[Q] ZURÜCK", curses.color_pair(6))
        k = stdscr.getch()
        if k == ord(\'q\'): breadef office_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    stdscr.timeout(1000)
    current_date = datetime.now()
    while True:
        stdscr.clear()
        draw_frame(stdscr, "OFFICE-SUITE", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        content_width = w - sidebar_width - pad

        # Display current month and year
        month_year_str = current_date.strftime(\"%B %Y\")
        stdscr.addstr(4, content_start_x + (content_width - len(month_year_str)) // 2, month_year_str, curses.color_pair(1) | curses.A_BOLD)

        # Display weekdays
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for i, day in enumerate(weekdays):
            stdscr.addstr(6, content_start_x + i * 4, day, curses.color_pair(6))

        # Display days of the month
        first_day_of_month = current_date.replace(day=1)
        start_weekday = first_day_of_month.weekday() # Monday is 0

        # Calculate where to start drawing days
        day_x = content_start_x + start_weekday * 4
        day_y = 7

        for day_num in range(1, 32): # Max days in a month
            try:
                current_day = current_date.replace(day=day_num)
            except ValueError: # Day does not exist in this month
                break

            attr = curses.color_pair(3)
            if current_day.date() == datetime.now().date():
                attr = curses.color_pair(7) # Highlight today

            stdscr.addstr(day_y, day_x, f"{day_num:2}", attr)

            day_x += 4
            if (start_weekday + day_num) % 7 == 0:
                day_x = content_start_x
                day_y += 1
        
        stdscr.addstr(h - taskbar_height - 2, content_start_x, "[<] VORHERIGER MONAT | [>] NÄCHSTER MONAT | [Q] ZURÜCK", curses.color_pair(6))
        k = stdscr.getch()
        if k == ord(\\'q\\'): break
        elif k == curses.KEY_LEFT or k == ord(\\'<\\'):
            current_date = current_date.replace(day=1) - timedelta(days=1)
        elif k == curses.KEY_RIGHT or k == ord(\\'\\'>\\'):
            current_date = current_date.replace(day=1) + timedelta(days=32) # Go to next month, then set day to 1
            current_date = current_date.replace(day=1)
def media_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    stdscr.timeout(1000)
    while True:
        stdscr.clear()
        draw_frame(stdscr, "MEDIA-CENTER", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)
        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        stdscr.addstr(h//2, content_start_x, "[MEDIA-CENTER: KEINE MEDIEN GEFUNDEN]", curses.color_pair(6))
        stdscr.addstr(h//2 + 2, content_start_x, "[Q] ZURÜCK", curses.color_pair(3))
        k = stdscr.getch()
        if k == ord(\'q\'): break
# --- MAIN ---

def main(stdscr):
    boot_animation(stdscr)
    apply_theme(cfg["theme"])
    curses.curs_set(0); stdscr.timeout(1000)

    # Check terminal size for Raspberry Pi Zero W
    h, w = stdscr.getmaxyx()
    if h < 24 or w < 80:
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal zu klein! Mindestens 24 Zeilen und 80 Spalten benötigt.", curses.color_pair(5))
        stdscr.addstr(1, 0, "Bitte Terminalgröße anpassen und neu starten.", curses.color_pair(5))
        stdscr.refresh()
        time.sleep(5) # Give user time to read
        sys.exit(0) # Exit gracefully
    
    sidebar_width = 30
    taskbar_height = 1

    menu = [
        {"n": "EXPLORER", "f": explorer},
        {"n": "COMMANDS", "f": commands_view},
        {"n": "HACK-TOOLS", "f": hacking_tools},
        {"n": "NOTIZEN", "f": notes_menu},
        {"n": "WLAN-MANAGER", "f": wifi_menu},
        {"n": "DASHBOARD", "f": dashboard_menu},
        {"n": "OFFICE", "f": office_menu},
        {"n": "MEDIA", "f": media_menu},
        {"n": "SETTINGS", "f": settings_menu},
        {"n": "POWER-OFF", "f": "exit"}
    ]
    sel = 0
    while True:
        stdscr.clear()
        draw_frame(stdscr, "JUST-OS V21 ULTIMATE", sidebar_width, taskbar_height)
        draw_sidebar(stdscr, sidebar_width, taskbar_height)
        draw_taskbar(stdscr, taskbar_height, sidebar_width)

        h, w = stdscr.getmaxyx(); pad = cfg["padding"]
        content_start_x = sidebar_width + pad
        
        logo = [
       "      ██╗██╗   ██╗███████╗████████╗",
            "      ██║██║   ██║██╔════╝╚══██╔══╝",
            "      ██║██║   ██║███████╗   ██║   ",
            " ██   ██║██║   ██║╚════██║   ██║   ",
            " ╚██████╔╝╚██████╔╝███████║   ██║   ",
            "  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   "
        ]
        for i, line in enumerate(logo):
            stdscr.addstr(2+i, max(content_start_x, (w + content_start_x)//2-20), line, curses.color_pair(1))
        
        # Calculate starting y-position for menu items to center them vertically
        menu_start_y = (h - taskbar_height - len(logo) - len(menu) * 2) // 2 + len(logo) + 2
        if menu_start_y < 10: menu_start_y = 10 # Ensure it doesn't overlap with logo

        for i, item in enumerate(menu):
            attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
            stdscr.addstr(menu_start_y + i*2, content_start_x + 10, f" [ {item["n"]:<12} ] ", attr)
            
        k = stdscr.getch()
        if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
        elif k in [ord('s'), curses.KEY_DOWN] and sel < len(menu)-1: sel += 1
        elif k in [10, 13]:
            if menu[sel]["f"] == "exit": break
            menu[sel]["f"](stdscr); stdscr.timeout(1000)
            apply_theme(cfg["theme"]) # Reapply theme in case settings changed
        elif k == ord("d") or k == curses.KEY_RIGHT: # Go to WLAN menu directly
            wifi_menu(stdscr); stdscr.timeout(1000)
            apply_theme(cfg["theme"])
        elif k == ord("1"): # Quick launch Explorer
            explorer(stdscr); stdscr.timeout(1000); apply_theme(cfg["theme"])
        elif k == ord("2"): # Quick launch Commands
            commands_view(stdscr); stdscr.timeout(1000); apply_theme(cfg["theme"])
        elif k == ord("3"): # Quick launch WLAN Manager
            wifi_menu(stdscr); stdscr.timeout(1000); apply_theme(cfg["theme"])
        elif k == ord("4"): # Quick launch Settings
            settings_menu(stdscr); stdscr.timeout(1000); apply_theme(cfg["theme"])
        elif k == ord("q"): break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        save_data()
        print("\n[!] JUST-OS wurde sicher beendet. Daten wurden synchronisiert.")
