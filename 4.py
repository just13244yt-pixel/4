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

# --- SYSTEM-CHECK ---
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def boot_animation(stdscr):
    try:
        h, w = stdscr.getmaxyx()
        boot_msg = "BOOTING JUST-OS..."
        x = max(0, (w - len(boot_msg))//2)
        y = max(0, h//2)
        stdscr.addstr(y, x, boot_msg, curses.color_pair(1))
        stdscr.refresh()
        time.sleep(2)
    except:
        pass

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
                if "games" not in data: data["games"] = []
                if "hack_tools_custom" not in data: data["hack_tools_custom"] = []
                if "username" not in data["cfg"]: data["cfg"]["username"] = "User"
                if "theme" not in data["cfg"]: data["cfg"]["theme"] = "default"
                keys = ["border", "text", "logo", "bg", "sel_bg", "sel_txt", "taskbar_bg", "taskbar_txt"]
                defaults = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_BLUE,
                            curses.COLOR_BLACK, curses.COLOR_CYAN, curses.COLOR_BLACK,
                            curses.COLOR_BLACK, curses.COLOR_WHITE]
                for k, d in zip(keys, defaults):
                    if k not in data["cfg"]: data["cfg"][k] = d
                return data
        except:
            pass
    return {
        "notes": [], 
        "games": [],
        "hack_tools_custom": [],
        "cfg": {
            "border": curses.COLOR_BLUE, "text": curses.COLOR_CYAN, "logo": curses.COLOR_BLUE,
            "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN, "sel_txt": curses.COLOR_BLACK,
            "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_WHITE,
            "padding": 6,
            "username": "User",
            "theme": "default"
        }
    }

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

# --- MASSIVE BEFEHLSDATENBANK ---
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

# Vordefinierte Hack-Tools
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
    try:
        h, w = stdscr.getmaxyx()
        if h < 3 or w < 10:
            return
        
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        try:
            stdscr.border(0, 0, 0, 0, 0, 0, 0, 0)
        except:
            pass
        
        if sidebar_width > 0 and sidebar_width < w - 5:
            try:
                stdscr.vline(0, sidebar_width, curses.ACS_VLINE, h - taskbar_height)
                stdscr.addch(0, sidebar_width, curses.ACS_TTEE)
                if taskbar_height > 0 and h - taskbar_height - 1 > 0:
                    stdscr.addch(h - taskbar_height - 1, sidebar_width, curses.ACS_BTEE)
                else:
                    if h - 1 > 0:
                        stdscr.addch(h - 1, sidebar_width, curses.ACS_BTEE)
            except:
                pass

        if taskbar_height > 0 and h - taskbar_height - 1 > 0:
            try:
                stdscr.hline(h - taskbar_height - 1, 0, curses.ACS_HLINE, w)
                stdscr.addch(h - taskbar_height - 1, 0, curses.ACS_LTEE)
                stdscr.addch(h - taskbar_height - 1, w - 1, curses.ACS_RTEE)
                if sidebar_width > 0:
                    stdscr.addch(h - taskbar_height - 1, sidebar_width, curses.ACS_PLUS)
            except:
                pass

        title_str = f" [ {title.upper()} ] "
        x_pos = max(sidebar_width + 1, (w + sidebar_width)//2 - len(title_str)//2)
        if x_pos >= 0 and x_pos < w - len(title_str):
            stdscr.addstr(0, x_pos, title_str)
        
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
    except:
        pass

def get_network_info():
    info = {"ssid": "N/A", "ip": "N/A", "signal": "N/A", "error": ""}
    if IS_LINUX:
        try:
            cmd = "nmcli -t -f active,ssid,signal,ip4.address device wifi list"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith("yes"):
                        parts = line.split(":")
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
                        break
        except:
            pass
    return info

def draw_sidebar(stdscr, sidebar_width, taskbar_height):
    try:
        h, w = stdscr.getmaxyx()
        if sidebar_width == 0 or sidebar_width >= w - 10: 
            return

        if h > 5:
            stdscr.addstr(2, 2, "SYSTEM", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(3, 2, f"CPU: {psutil.cpu_percent()}%", curses.color_pair(3))
            stdscr.addstr(4, 2, f"RAM: {psutil.virtual_memory().percent}%", curses.color_pair(3))
            if h > 6:
                uptime = int(time.time() - psutil.boot_time()) // 3600
                stdscr.addstr(5, 2, f"UPTIME: {uptime}h", curses.color_pair(3))

        if h > 10:
            stdscr.addstr(7, 2, "NETWORK", curses.color_pair(1) | curses.A_BOLD)
            net_info = get_network_info()
            stdscr.addstr(8, 2, f"SSID: {net_info['ssid']}", curses.color_pair(3))
            if h > 11:
                stdscr.addstr(9, 2, f"SIGNAL: {net_info['signal']}%", curses.color_pair(3))
            if h > 12:
                stdscr.addstr(10, 2, f"IP: {net_info['ip']}", curses.color_pair(3))
            if net_info["error"] and h > 13:
                stdscr.addstr(11, 2, f"Err: {net_info['error'][:sidebar_width-8]}", curses.color_pair(5))

        if h > 15:
            try:
                stdscr.hline(13, 1, curses.ACS_HLINE, sidebar_width - 2)
            except:
                pass

        if h - taskbar_height - 3 > 0:
            stdscr.addstr(h - taskbar_height - 3, 2, f"TIME: {datetime.now().strftime('%H:%M:%S')}", curses.color_pair(6))
    except:
        pass

def draw_taskbar(stdscr, taskbar_height, sidebar_width):
    try:
        h, w = stdscr.getmaxyx()
        if taskbar_height <= 0 or h <= taskbar_height:
            return

        taskbar_y = h - taskbar_height
        if taskbar_y < 0 or taskbar_y >= h:
            return

        stdscr.attron(curses.color_pair(8))
        
        try:
            stdscr.addstr(taskbar_y, 0, " " * w)
        except:
            for x in range(w):
                try:
                    stdscr.addch(taskbar_y, x, ' ')
                except:
                    pass

        quick_launch = ["[EXP]", "[CMD]", "[WIFI]", "[SET]"]
        x_pos = sidebar_width + cfg["padding"]
        for i, icon in enumerate(quick_launch):
            if x_pos + len(icon) < w:
                try:
                    stdscr.addstr(taskbar_y, x_pos, icon, curses.color_pair(8) | curses.A_BOLD)
                except:
                    pass
                x_pos += len(icon) + 2

        status_str = f" {cfg['username']}@JUST-OS "
        if x_pos + len(status_str) < w - 10:
            try:
                stdscr.addstr(taskbar_y, x_pos, status_str)
            except:
                pass

        time_str = datetime.now().strftime('%H:%M:%S')
        if w - len(time_str) - 2 > 0:
            try:
                stdscr.addstr(taskbar_y, w - len(time_str) - 2, time_str)
            except:
                pass

        stdscr.attroff(curses.color_pair(8))
    except:
        pass

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
                    if drive_type == 2:
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
                try:
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
                except:
                    pass
    return usb_drives

def copy_to_usb(stdscr, source_file, sidebar_width, taskbar_height):
    usb_drives = detect_usb_drives()
    if not usb_drives:
        try:
            stdscr.clear()
            draw_frame(stdscr, "KEINE USB-LAUFWERKE", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            if h//2 > 0 and h//2 + 2 < h:
                stdscr.addstr(h//2, content_start_x, "❌ Keine USB-Laufwerke gefunden!", curses.color_pair(5))
                stdscr.addstr(h//2 + 2, content_start_x, "Beliebige Taste zum Fortfahren...", curses.color_pair(3))
            stdscr.getch()
        except:
            pass
        return False
    
    sel = 0
    while True:
        try:
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
                if 7 + i < h - taskbar_height - 2:
                    stdscr.addstr(7 + i, content_start_x, f" > {name} ", attr)
            
            if 7 + len(usb_drives) + 1 < h - taskbar_height:
                stdscr.addstr(7 + len(usb_drives) + 1, content_start_x, "[ENTER] Kopieren | [Q] Abbrechen", curses.color_pair(6))
            
            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(usb_drives) - 1:
                sel += 1
            elif k in [10, 13]:
                dest_path = os.path.join(usb_drives[sel][0], os.path.basename(source_file))
                try:
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h - taskbar_height - 3, content_start_x, "⏳ Kopiere...", curses.color_pair(6))
                    stdscr.refresh()
                    
                    if os.path.isfile(source_file):
                        shutil.copy2(source_file, dest_path)
                    else:
                        shutil.copytree(source_file, dest_path)
                    
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h - taskbar_height - 3, content_start_x, "✓ Erfolgreich kopiert!     ", curses.color_pair(4))
                    stdscr.refresh()
                    time.sleep(1.5)
                    return True
                except Exception as e:
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h - taskbar_height - 3, content_start_x, f"❌ Fehler", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(2)
                    return False
            elif k == ord('q'):
                return False
        except:
            return False

# --- TERMINAL MODULE ---
def terminal_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "TERMINAL", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            content_width = w - sidebar_width - pad - 2

            if content_start_x >= w - 20:
                content_start_x = 2

            # Terminal-Header
            stdscr.addstr(3, content_start_x, "╔" + "═" * content_width + "╗", curses.color_pair(6))
            stdscr.addstr(4, content_start_x, f"║{' JUST-OS TERMINAL '.center(content_width)}║", curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(5, content_start_x, "╠" + "═" * content_width + "╣", curses.color_pair(6))
            
            # Terminal-Inhalt
            stdscr.addstr(7, content_start_x + 2, "Willkommen im JUST-OS Terminal!", curses.color_pair(4))
            stdscr.addstr(8, content_start_x + 2, "Gebe 'exit' ein um zum Hauptmenü zurückzukehren.", curses.color_pair(3))
            stdscr.addstr(10, content_start_x + 2, "$> ", curses.color_pair(6) | curses.A_BOLD)
            
            stdscr.addstr(h - taskbar_height - 2, content_start_x, "[ENTER] Befehl ausführen | [Q] ZURÜCK", curses.color_pair(6))

            # Befehl eingeben - ohne Timeout
            curses.echo()
            stdscr.timeout(-1)  # Blockierend warten
            try:
                stdscr.addstr(10, content_start_x + 5, " " * (content_width - 10))
                stdscr.move(10, content_start_x + 5)
                cmd = stdscr.getstr().decode().strip()
            except:
                cmd = ""
            stdscr.timeout(1000)  # Wieder zurück setzen
            curses.noecho()

            if cmd.lower() == "exit":
                break
            elif cmd:
                # Befehl ausführen
                curses.endwin()
                try:
                    if cmd.startswith("cd "):
                        try:
                            os.chdir(cmd[3:])
                            print(f"Verzeichnis gewechselt zu: {os.getcwd()}")
                        except:
                            print(f"Verzeichnis nicht gefunden: {cmd[3:]}")
                    else:
                        os.system(cmd)
                except:
                    pass
                print(f"\nBefehl '{cmd}' ausgeführt.")
                print("Beliebige Taste für JUST-OS Terminal...")
                try:
                    curses.getch()
                except:
                    pass
                stdscr.clear()
                apply_colors()
                curses.curs_set(0)
        except:
            break

# --- GAME MENU ---
def game_menu(stdscr):
    sel = 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "GAMES", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            games = user_data.get("games", [])
            
            # Überschrift
            stdscr.addstr(3, content_start_x, "INSTALLIERTE SPIELE:", curses.color_pair(1) | curses.A_BOLD)
            
            # Games anzeigen
            for i, game in enumerate(games):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 5 + i < h - taskbar_height - 8:
                    display = f" {i+1}. {game}"
                    stdscr.addstr(5 + i, content_start_x, display, attr)
            
            # Trennlinie
            if games:
                line_y = 5 + len(games) + 1
                if line_y < h - taskbar_height - 5:
                    stdscr.addstr(line_y, content_start_x, "─" * 30, curses.color_pair(6))
            
            # Menü-Einträge
            menu_y = max(5 + len(games) + 3, h - taskbar_height - 6)
            menu_items = ["[S] NEUES SPIEL", "[D] SPIEL LÖSCHEN", "ZURÜCK"]
            
            for i, item in enumerate(menu_items):
                attr = curses.color_pair(7) if (len(games) + i) == sel else curses.color_pair(6)
                if menu_y + i < h - taskbar_height - 2:
                    stdscr.addstr(menu_y + i, content_start_x, f" {item} ", attr)

            stdscr.addstr(h - taskbar_height - 2, content_start_x, "[ENTER] Spiel starten", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            total_items = len(games) + 3  # +3 für Menü-Einträge
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < total_items - 1:
                sel += 1
            elif k == ord('s'):
                # Neues Spiel hinzufügen
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                    stdscr.addstr(h-taskbar_height-3, content_start_x, "Spielname (z.B. nsnake): ")
                curses.echo()
                stdscr.timeout(-1)  # Blockierend warten
                try:
                    new_game = stdscr.getstr().decode().strip()
                    if new_game and new_game not in user_data["games"]:
                        user_data["games"].append(new_game)
                        save_data()
                except:
                    pass
                stdscr.timeout(1000)  # Wieder zurück setzen
                curses.noecho()
                sel = 0
            elif k == ord('d') and sel < len(games):
                # Spiel löschen
                game_to_delete = games[sel]
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                    stdscr.addstr(h-taskbar_height-3, content_start_x, f" '{game_to_delete}' löschen? (j/n): ", curses.color_pair(5))
                stdscr.timeout(-1)  # Blockierend warten
                if stdscr.getch() == ord('j'):
                    user_data["games"].pop(sel)
                    save_data()
                    if sel >= len(user_data["games"]):
                        sel = max(0, len(user_data["games"]) - 1)
                stdscr.timeout(1000)  # Wieder zurück setzen
            elif k in [10, 13]:
                if sel < len(games):
                    # Spiel starten
                    game_name = games[sel]
                    curses.endwin()
                    try:
                        print(f"\nStarte '{game_name}'...")
                        print("Zum Beenden des Spiels drücke Ctrl+C oder schließe das Spiel.")
                        print("-" * 40)
                        time.sleep(1)
                        os.system(game_name)
                    except:
                        pass
                    print(f"\nSpiel '{game_name}' beendet.")
                    print("Beliebige Taste für JUST-OS...")
                    try:
                        curses.getch()
                    except:
                        pass
                    stdscr.clear()
                    apply_colors()
                    curses.curs_set(0)
                elif sel == len(games) + 2:  # ZURÜCK
                    break
        except:
            break

# --- CUSTOM HACK TOOLS MENU ---
def custom_hack_tools_menu(stdscr):
    sel = 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "CUSTOM HACK TOOLS", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            # Vordefinierte Tools + Custom Tools
            all_tools = []
            for page in HACK_PAGES:
                all_tools.extend(page["t"])
            
            custom_tools = user_data.get("hack_tools_custom", [])
            
            # Überschrift für vordefinierte Tools
            stdscr.addstr(3, content_start_x, "VORDEFINIERTE TOOLS:", curses.color_pair(1) | curses.A_BOLD)
            
            # Vordefinierte Tools anzeigen
            for i, tool in enumerate(all_tools[:h-15]):  # Begrenzung für Bildschirm
                attr = curses.color_pair(3)
                if 5 + i < h - taskbar_height - 15:
                    display = f" {i+1}. {tool}"
                    stdscr.addstr(5 + i, content_start_x, display, attr)
            
            if custom_tools:
                # Trennlinie
                sep_y = 5 + min(len(all_tools), h-20) + 1
                if sep_y < h - taskbar_height - 10:
                    stdscr.addstr(sep_y, content_start_x, "─" * 30, curses.color_pair(6))
                
                # Überschrift für Custom Tools
                stdscr.addstr(sep_y + 1, content_start_x, "CUSTOM TOOLS:", curses.color_pair(1) | curses.A_BOLD)
                
                # Custom Tools anzeigen
                for i, tool in enumerate(custom_tools):
                    idx = i
                    attr = curses.color_pair(7) if (len(all_tools) + i) == sel else curses.color_pair(4)
                    if sep_y + 3 + i < h - taskbar_height - 5:
                        display = f" C{i+1}. {tool}"
                        stdscr.addstr(sep_y + 3 + i, content_start_x, display, attr)
            
            # Menü-Einträge
            menu_y = max(h - taskbar_height - 8, 5 + len(all_tools) + len(custom_tools) + 5)
            if menu_y < h - taskbar_height - 3:
                stdscr.addstr(menu_y, content_start_x, "─" * 30, curses.color_pair(6))
                menu_items = ["[S] NEUES TOOL", "[D] TOOL LÖSCHEN", "ZURÜCK"]
                
                for i, item in enumerate(menu_items):
                    attr = curses.color_pair(7) if (len(all_tools) + len(custom_tools) + i) == sel else curses.color_pair(6)
                    if menu_y + 1 + i < h - taskbar_height - 2:
                        stdscr.addstr(menu_y + 1 + i, content_start_x, f" {item} ", attr)

            stdscr.addstr(h - taskbar_height - 2, content_start_x, "[ENTER] Tool starten", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            total_items = len(all_tools) + len(custom_tools) + 3  # +3 für Menü-Einträge
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < total_items - 1:
                sel += 1
            elif k == ord('s'):
                # Neues Tool hinzufügen
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                    stdscr.addstr(h-taskbar_height-3, content_start_x, "Tool-Name: ")
                curses.echo()
                stdscr.timeout(-1)  # Blockierend warten
                try:
                    new_tool = stdscr.getstr().decode().strip()
                    if new_tool and new_tool not in user_data["hack_tools_custom"]:
                        user_data["hack_tools_custom"].append(new_tool)
                        save_data()
                except:
                    pass
                stdscr.timeout(1000)  # Wieder zurück setzen
                curses.noecho()
            elif k == ord('d'):
                # Tool löschen
                if sel < len(all_tools):
                    # Vordefiniertes Tool kann nicht gelöscht werden
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, "Vordefinierte Tools können nicht gelöscht werden!", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(1.5)
                elif sel < len(all_tools) + len(custom_tools):
                    custom_idx = sel - len(all_tools)
                    tool_to_delete = custom_tools[custom_idx]
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, f" '{tool_to_delete}' löschen? (j/n): ", curses.color_pair(5))
                    stdscr.timeout(-1)  # Blockierend warten
                    if stdscr.getch() == ord('j'):
                        user_data["hack_tools_custom"].pop(custom_idx)
                        save_data()
                        if sel >= len(all_tools) + len(user_data["hack_tools_custom"]):
                            sel = max(0, len(all_tools) + len(user_data["hack_tools_custom"]) - 1)
                    stdscr.timeout(1000)  # Wieder zurück setzen
            elif k in [10, 13]:
                if sel < len(all_tools):
                    # Vordefiniertes Tool starten
                    tool_name = all_tools[sel]
                elif sel < len(all_tools) + len(custom_tools):
                    # Custom Tool starten
                    tool_name = custom_tools[sel - len(all_tools)]
                elif sel == len(all_tools) + len(custom_tools) + 2:  # ZURÜCK
                    break
                else:
                    continue
                
                if tool_name not in ["[S] NEUES TOOL", "[D] TOOL LÖSCHEN", "ZURÜCK"]:
                    curses.endwin()
                    try:
                        print(f"\nStarte '{tool_name}'...")
                        print("-" * 40)
                        time.sleep(1)
                        os.system(tool_name)
                    except:
                        pass
                    print(f"\nTool '{tool_name}' beendet.")
                    print("Beliebige Taste für JUST-OS...")
                    try:
                        curses.getch()
                    except:
                        pass
                    stdscr.clear()
                    apply_colors()
                    curses.curs_set(0)
        except:
            break

# --- EXPLORER MIT KOPIEREN/EINFÜGEN ---
def explorer(stdscr):
    curr, sel, search_query = os.getcwd(), 0, ""
    clipboard = None
    clipboard_is_cut = False
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, f"EXPLORER: {os.path.basename(curr)}", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            content_height = h - taskbar_height - 8

            if content_start_x >= w - 20:
                content_start_x = 2

            try:
                all_items = [".. (ZURÜCK)"] + sorted(os.listdir(curr))
                items = [all_items[0]] + [i for i in all_items[1:] if search_query.lower() in i.lower()] if search_query else all_items
            except:
                items = [".. (ZURÜCK)"]
            
            if sel >= len(items): 
                sel = max(0, len(items)-1)

            # Status-Zeile mit Clipboard-Info
            status_line = "[N] NEW | [D] DEL | [F] SEARCH | [U] USB"
            if clipboard:
                status_line += f" | [V] EINFÜGEN ({os.path.basename(clipboard)})"
                if clipboard_is_cut:
                    status_line += " (AUSGESCHNITTEN)"
            else:
                status_line += " | [C] KOPIEREN"
            
            if h - taskbar_height - 2 > 0:
                stdscr.addstr(h-taskbar_height-2, content_start_x, status_line[:w-content_start_x-2], curses.color_pair(6))

            # Items anzeigen
            for i, item in enumerate(items[:content_height]):
                path = os.path.join(curr, item)
                is_dir = os.path.isdir(path)
                
                # Basis-Attribut
                if i == sel:
                    attr = curses.color_pair(7)
                else:
                    attr = curses.color_pair(6) if is_dir else curses.color_pair(3)
                
                # Markierung für kopierte Datei
                display_item = f" {'[DIR]' if is_dir else '     '} {item[:w-content_start_x-20]}"
                if clipboard and path == clipboard:
                    display_item = f" {'[DIR]' if is_dir else '     '} *{item[:w-content_start_x-21]}"
                
                if 4 + i < h - taskbar_height - 3:
                    stdscr.addstr(4 + i, content_start_x, display_item, attr)

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(items)-1:
                sel += 1
            elif k in [10, 13]:
                if items:
                    path = os.path.join(curr, items[sel])
                    if items[sel] == ".. (ZURÜCK)":
                        curr = os.path.dirname(curr)
                        sel = 0
                        search_query = ""
                    elif os.path.isdir(path):
                        curr = path
                        sel = 0
                        search_query = ""
            elif k == ord('c') and sel > 0 and items[sel] != ".. (ZURÜCK)":
                # Kopieren
                clipboard = os.path.join(curr, items[sel])
                clipboard_is_cut = False
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, f"✓ {items[sel]} kopiert", curses.color_pair(4))
                stdscr.refresh()
                time.sleep(1)
            elif k == ord('x') and sel > 0 and items[sel] != ".. (ZURÜCK)":
                # Ausschneiden
                clipboard = os.path.join(curr, items[sel])
                clipboard_is_cut = True
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, f"✓ {items[sel]} ausgeschnitten", curses.color_pair(6))
                stdscr.refresh()
                time.sleep(1)
            elif k == ord('v') and clipboard:
                # Einfügen
                dest_path = os.path.join(curr, os.path.basename(clipboard))
                try:
                    if os.path.exists(dest_path):
                        if h - taskbar_height - 3 > 0:
                            stdscr.addstr(h-taskbar_height-3, content_start_x, "Überschreiben? (j/n): ", curses.color_pair(5))
                        if stdscr.getch() == ord('j'):
                            if os.path.isdir(dest_path):
                                shutil.rmtree(dest_path)
                            else:
                                os.remove(dest_path)
                        else:
                            clipboard = None
                            continue
                    
                    if clipboard_is_cut:
                        # Verschieben
                        shutil.move(clipboard, curr)
                        if h - taskbar_height - 3 > 0:
                            stdscr.addstr(h-taskbar_height-3, content_start_x, f"✓ {os.path.basename(clipboard)} verschoben", curses.color_pair(4))
                        clipboard = None
                    else:
                        # Kopieren
                        if os.path.isdir(clipboard):
                            shutil.copytree(clipboard, dest_path)
                        else:
                            shutil.copy2(clipboard, dest_path)
                        if h - taskbar_height - 3 > 0:
                            stdscr.addstr(h-taskbar_height-3, content_start_x, f"✓ {os.path.basename(clipboard)} kopiert", curses.color_pair(4))
                except Exception as e:
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, f"❌ Fehler: {str(e)[:20]}", curses.color_pair(5))
                stdscr.refresh()
                time.sleep(1.5)
            elif k == ord('n'):
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                    stdscr.addstr(h-taskbar_height-3, content_start_x, "Name: ")
                curses.echo()
                stdscr.timeout(-1)  # Blockierend warten
                try:
                    name = stdscr.getstr().decode().strip()
                    if name:
                        with open(os.path.join(curr, name), 'w') as f:
                            f.write("")
                except:
                    pass
                stdscr.timeout(1000)  # Wieder zurück setzen
                curses.noecho()
            elif k == ord('d') and sel > 0 and items:
                name = items[sel]
                if name != ".. (ZURÜCK)":
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, f"{name} löschen? (j/n): ", curses.color_pair(5))
                    stdscr.timeout(-1)  # Blockierend warten
                    if stdscr.getch() == ord('j'):
                        path = os.path.join(curr, name)
                        try:
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            else:
                                os.remove(path)
                        except:
                            pass
                    stdscr.timeout(1000)  # Wieder zurück setzen
            elif k == ord('u') and sel > 0 and items:
                if items[sel] != ".. (ZURÜCK)":
                    source_path = os.path.join(curr, items[sel])
                    copy_to_usb(stdscr, source_path, sidebar_width, taskbar_height)
            elif k == ord('f'):
                if h - taskbar_height - 3 > 0:
                    stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                    stdscr.addstr(h-taskbar_height-3, content_start_x, "Suchen: ")
                curses.echo()
                stdscr.timeout(-1)  # Blockierend warten
                try:
                    search_query = stdscr.getstr().decode().strip()
                except:
                    search_query = ""
                stdscr.timeout(1000)  # Wieder zurück setzen
                curses.noecho()
                sel = 0
            elif k == ord('q'):
                break
        except:
            break

# --- WEITERE MODULE (unverändert) ---
def commands_view(stdscr):
    sel, offset = 0, 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "SYSTEM-BEFEHLE", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            max_r = h - taskbar_height - 6

            if content_start_x >= w - 20:
                content_start_x = 2

            for i, (c, d) in enumerate(CMD_LIST[offset:offset+max_r]):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 3 + i < h - taskbar_height - 2:
                    display = f"{c:<15} | {d[:w-content_start_x-25]}"
                    stdscr.addstr(3 + i, content_start_x, display, attr)

            if h - taskbar_height - 2 > 0:
                stdscr.addstr(h-taskbar_height-2, content_start_x, "[ENTER] Ausführen | [Q] ZURÜCK", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP]:
                if sel > 0:
                    sel -= 1
                elif offset > 0:
                    offset -= 1
                    sel = max_r - 1
            elif k in [ord('s'), curses.KEY_DOWN]:
                if sel < max_r - 1 and offset + sel < len(CMD_LIST) - 1:
                    sel += 1
                elif offset + max_r < len(CMD_LIST):
                    offset += 1
                    sel = 0
            elif k in [10, 13]:
                if CMD_LIST:
                    curses.endwin()
                    try:
                        os.system(CMD_LIST[offset+sel][0])
                    except:
                        pass
                    print("\nBeliebige Taste...")
                    try:
                        curses.getch()
                    except:
                        pass
                    stdscr.clear()
                    apply_colors()
                    curses.curs_set(0)
            elif k == ord('q'):
                break
        except:
            break

def hacking_tools(stdscr):
    sel_p, sel_t = 0, 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "HACK-TOOLS", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            x_pos = content_start_x
            for i, p in enumerate(HACK_PAGES):
                attr = curses.color_pair(7) if i == sel_p else curses.color_pair(6)
                if x_pos + len(p['n']) + 2 < w:
                    stdscr.addstr(3, x_pos, f" {p['n']} ", attr)
                    x_pos += len(p['n']) + 4

            tools = HACK_PAGES[sel_p]["t"]
            for i, t in enumerate(tools):
                attr = curses.color_pair(7) if i == sel_t else curses.color_pair(3)
                if 6 + i < h - taskbar_height - 2:
                    stdscr.addstr(6 + i, content_start_x + 5, f" > {t} ", attr)

            stdscr.addstr(h - taskbar_height - 2, content_start_x, "[C] CUSTOM TOOLS | [ENTER] Starten | [Q] ZURÜCK", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k == ord('c'):
                custom_hack_tools_menu(stdscr)
                stdscr.timeout(1000)
                apply_colors()
            elif k in [ord('a'), curses.KEY_LEFT] and sel_p > 0:
                sel_p -= 1
                sel_t = 0
            elif k in [ord('d'), curses.KEY_RIGHT] and sel_p < len(HACK_PAGES)-1:
                sel_p += 1
                sel_t = 0
            elif k in [ord('w'), curses.KEY_UP] and sel_t > 0:
                sel_t -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel_t < len(tools)-1:
                sel_t += 1
            elif k in [10, 13]:
                if tools:
                    curses.endwin()
                    try:
                        os.system(tools[sel_t])
                    except:
                        pass
                    print("\nBeliebige Taste...")
                    try:
                        curses.getch()
                    except:
                        pass
                    stdscr.clear()
                    apply_colors()
                    curses.curs_set(0)
            elif k == ord('q'):
                break
        except:
            break

def notes_menu(stdscr):
    sel = 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "NOTIZEN", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            notes = user_data["notes"]
            display_list = notes + ["---", "+ NEUE NOTIZ", "ALLE LÖSCHEN", "ZURÜCK"]

            for i, item in enumerate(display_list):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 4 + i < h - taskbar_height - 2:
                    display = f" > {item}" if len(str(item)) < w - content_start_x - 5 else f" > {str(item)[:w-content_start_x-10]}..."
                    stdscr.addstr(4 + i, content_start_x, display, attr)

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(display_list)-1:
                sel += 1
            elif k in [10, 13]:
                choice = display_list[sel]
                if choice == "ZURÜCK":
                    break
                elif choice == "ALLE LÖSCHEN":
                    user_data["notes"] = []
                    save_data()
                elif choice == "+ NEUE NOTIZ":
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, "Inhalt: ")
                    curses.echo()
                    stdscr.timeout(-1)  # Blockierend warten
                    try:
                        new = stdscr.getstr().decode()
                        if new:
                            user_data["notes"].append(new)
                            save_data()
                    except:
                        pass
                    stdscr.timeout(1000)  # Wieder zurück setzen
                    curses.noecho()
                elif choice != "---":
                    user_data["notes"].pop(sel)
                    save_data()
            elif k == ord('q'):
                break
        except:
            break

def settings_menu(stdscr):
    sel = 0
    colors = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE]
    names = ["BLAU", "CYAN", "GRÜN", "ROT", "GELB", "WEISS"]
    theme_names = list(themes.keys())
    sidebar_width = 30
    taskbar_height = 1

    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "EINSTELLUNGEN", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            opts = [
                f"RAHMEN-FARBE: {names[colors.index(cfg['border'])]}",
                f"TEXT-FARBE  : {names[colors.index(cfg['text'])]}",
                f"LOGO-FARBE  : {names[colors.index(cfg['logo'])]}",
                f"RAND-ABSTAND: {cfg['padding']}px",
                f"BENUTZERNAME: {cfg['username']}",
                f"THEME       : {cfg['theme'].upper()}",
                "KONFIGURATION SPEICHERN",
                "ZURÜCK"
            ]

            for i, o in enumerate(opts):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 4 + i * 2 < h - taskbar_height - 2:
                    stdscr.addstr(4 + i * 2, content_start_x, f" {o} ", attr)

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(opts)-1:
                sel += 1
            elif k in [10, 13]:
                if sel == 0:
                    cfg['border'] = colors[(colors.index(cfg['border'])+1)%len(colors)]
                elif sel == 1:
                    cfg['text'] = colors[(colors.index(cfg['text'])+1)%len(colors)]
                elif sel == 2:
                    cfg['logo'] = colors[(colors.index(cfg['logo'])+1)%len(colors)]
                elif sel == 3:
                    cfg['padding'] = 2 if cfg['padding'] >= 22 else cfg['padding']+4
                elif sel == 4:
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, "Neuer Name: ")
                    curses.echo()
                    stdscr.timeout(-1)  # Blockierend warten
                    try:
                        new_username = stdscr.getstr().decode()
                        if new_username:
                            cfg['username'] = new_username
                    except:
                        pass
                    stdscr.timeout(1000)  # Wieder zurück setzen
                    curses.noecho()
                elif sel == 5:
                    current_theme_idx = theme_names.index(cfg['theme'])
                    next_theme_idx = (current_theme_idx + 1) % len(theme_names)
                    cfg['theme'] = theme_names[next_theme_idx]
                    apply_theme(cfg['theme'])
                elif sel == 6:
                    save_data()
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, "GESPEICHERT!", curses.color_pair(4))
                    stdscr.refresh()
                    time.sleep(0.5)
                elif sel == 7:
                    break
                apply_colors()
            elif k == ord('q'):
                break
        except:
            break

def get_wifi_networks():
    networks = []
    if IS_LINUX:
        try:
            cmd = "nmcli -t -f ssid,signal device wifi list"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2 and parts[0]:
                            networks.append((parts[0], parts[1]))
        except:
            pass
    return networks

def connect_to_wifi(ssid, password):
    if IS_LINUX:
        try:
            cmd = f"nmcli device wifi connect '{ssid}' password '{password}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, "Verbunden!"
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)
    return False, "Nur unter Linux verfügbar."

def wifi_menu(stdscr):
    sel = 0
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "WLAN-MANAGER", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            stdscr.addstr(4, content_start_x, "Verfügbare Netzwerke:", curses.color_pair(6))
            networks = get_wifi_networks()

            display_networks = [f"{ssid} ({signal}%)" for ssid, signal in networks if ssid]
            display_list = display_networks + ["---", "ZURÜCK"]

            for i, item in enumerate(display_list):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 6 + i < h - taskbar_height - 2:
                    stdscr.addstr(6 + i, content_start_x, f" > {item} ", attr)

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k in [ord('w'), curses.KEY_UP] and sel > 0:
                sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(display_list)-1:
                sel += 1
            elif k in [10, 13]:
                choice = display_list[sel]
                if choice == "ZURÜCK":
                    break
                elif choice != "---" and networks and sel < len(networks):
                    ssid_to_connect = networks[sel][0]
                    if h - taskbar_height - 3 > 0:
                        stdscr.addstr(h-taskbar_height-3, content_start_x, " " * (w - content_start_x - 2))
                        stdscr.addstr(h-taskbar_height-3, content_start_x, f"Passwort: ")
                    curses.echo()
                    stdscr.timeout(-1)  # Blockierend warten
                    try:
                        password = stdscr.getstr().decode()
                    except:
                        password = ""
                    stdscr.timeout(1000)  # Wieder zurück setzen
                    curses.noecho()

                    if h - taskbar_height - 4 > 0:
                        stdscr.addstr(h-taskbar_height-4, content_start_x, "Verbinde...", curses.color_pair(6))
                    stdscr.refresh()
                    success, message = connect_to_wifi(ssid_to_connect, password)
                    if h - taskbar_height - 4 > 0:
                        if success:
                            stdscr.addstr(h-taskbar_height-4, content_start_x, f"✓ {message}", curses.color_pair(4))
                        else:
                            stdscr.addstr(h-taskbar_height-4, content_start_x, f"❌ Fehler", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(2)
            elif k == ord('q'):
                break
        except:
            break

def dashboard_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "SYSTEM-DASHBOARD", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            cpu_percent = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net_io = psutil.net_io_counters()

            stdscr.addstr(4, content_start_x, f"CPU: {cpu_percent:.1f}%", curses.color_pair(3))
            stdscr.addstr(5, content_start_x, f"RAM: {ram.percent:.1f}% ({ram.used/1024**3:.1f}GB/{ram.total/1024**3:.1f}GB)", curses.color_pair(3))
            stdscr.addstr(6, content_start_x, f"DISK: {disk.percent:.1f}% ({disk.used/1024**3:.1f}GB/{disk.total/1024**3:.1f}GB)", curses.color_pair(3))
            stdscr.addstr(7, content_start_x, f"SENT: {net_io.bytes_sent/1024**2:.1f} MB", curses.color_pair(3))
            stdscr.addstr(8, content_start_x, f"RECV: {net_io.bytes_recv/1024**2:.1f} MB", curses.color_pair(3))

            if h - taskbar_height - 2 > 0:
                stdscr.addstr(h - taskbar_height - 2, content_start_x, "[Q] ZURÜCK", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k == ord('q'):
                break
        except:
            break

def office_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    current_date = datetime.now()
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "OFFICE-SUITE", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            content_width = w - sidebar_width - pad

            if content_start_x >= w - 20:
                content_start_x = 2

            month_year_str = current_date.strftime("%B %Y")
            x_pos = content_start_x + max(0, (content_width - len(month_year_str)) // 2)
            stdscr.addstr(4, x_pos, month_year_str, curses.color_pair(1) | curses.A_BOLD)

            weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            for i, day in enumerate(weekdays):
                if content_start_x + i * 4 < w - 5:
                    stdscr.addstr(6, content_start_x + i * 4, day, curses.color_pair(6))

            first_day = current_date.replace(day=1)
            start_weekday = first_day.weekday()
            day_x = content_start_x + start_weekday * 4
            day_y = 7

            for day_num in range(1, 32):
                try:
                    current_day = current_date.replace(day=day_num)
                except ValueError:
                    break

                attr = curses.color_pair(7) if current_day.date() == datetime.now().date() else curses.color_pair(3)
                if day_y < h - taskbar_height - 2 and day_x < w - 5:
                    stdscr.addstr(day_y, day_x, f"{day_num:2}", attr)

                day_x += 4
                if (start_weekday + day_num) % 7 == 0:
                    day_x = content_start_x
                    day_y += 1

            if h - taskbar_height - 2 > 0:
                stdscr.addstr(h - taskbar_height - 2, content_start_x, "[<] VORHER | [>] NÄCHSTER | [Q] BACK", curses.color_pair(6))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k == ord('q'):
                break
            elif k == curses.KEY_LEFT or k == ord('<'):
                current_date = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            elif k == curses.KEY_RIGHT or k == ord('>'):
                next_month = current_date.replace(day=1) + timedelta(days=32)
                current_date = next_month.replace(day=1)
        except:
            break

def media_menu(stdscr):
    sidebar_width = 30
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "MEDIA-CENTER", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            
            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad

            if content_start_x >= w - 20:
                content_start_x = 2

            if h//2 > 0:
                stdscr.addstr(h//2, content_start_x, "[KEINE MEDIEN GEFUNDEN]", curses.color_pair(6))
            if h//2 + 2 < h:
                stdscr.addstr(h//2 + 2, content_start_x, "[Q] ZURÜCK", curses.color_pair(3))

            stdscr.timeout(-1)  # Blockierend warten
            k = stdscr.getch()
            stdscr.timeout(1000)  # Wieder zurück setzen
            
            if k == ord('q'):
                break
        except:
            break

# --- MAIN ---

def main(stdscr):
    try:
        boot_animation(stdscr)
        apply_theme(cfg["theme"])
        curses.curs_set(0)

        h, w = stdscr.getmaxyx()
        if h < 20 or w < 60:
            stdscr.clear()
            stdscr.addstr(0, 0, "Terminal zu klein! Bitte vergrößern.", curses.color_pair(5))
            stdscr.refresh()
            time.sleep(3)

        sidebar_width = 30
        taskbar_height = 1

        menu = [
            {"n": "EXPLORER", "f": explorer},
            {"n": "COMMANDS", "f": commands_view},
            {"n": "TERMINAL", "f": terminal_menu},
            {"n": "HACK-TOOLS", "f": hacking_tools},
            {"n": "GAMES", "f": game_menu},
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
            try:
                stdscr.clear()
                draw_frame(stdscr, "JUST-OS V21 ULTIMATE", sidebar_width, taskbar_height)
                draw_sidebar(stdscr, sidebar_width, taskbar_height)
                draw_taskbar(stdscr, taskbar_height, sidebar_width)

                h, w = stdscr.getmaxyx()
                pad = cfg["padding"]
                content_start_x = sidebar_width + pad

                if content_start_x >= w - 20:
                    content_start_x = 2

                logo = [
                    "      ██╗██╗   ██╗███████╗████████╗",
                    "      ██║██║   ██║██╔════╝╚══██╔══╝",
                    "      ██║██║   ██║███████╗   ██║   ",
                    " ██   ██║██║   ██║╚════██║   ██║   ",
                    " ╚██████╔╝╚██████╔╝███████║   ██║   ",
                    "  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   "
                ]

                for i, line in enumerate(logo):
                    x_pos = max(content_start_x, (w + content_start_x)//2 - 20)
                    if 2 + i < h - 10 and x_pos >= 0:
                        stdscr.addstr(2 + i, x_pos, line, curses.color_pair(1))

                menu_start_y = 10
                for i, item in enumerate(menu):
                    attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                    if menu_start_y + i*2 < h - taskbar_height - 2:
                        stdscr.addstr(menu_start_y + i*2, content_start_x + 5, f" [ {item['n']:<12} ] ", attr)

                stdscr.timeout(-1)  # Blockierend warten im Hauptmenü
                k = stdscr.getch()
                stdscr.timeout(1000)  # Wieder zurück setzen
                
                if k in [ord('w'), curses.KEY_UP] and sel > 0:
                    sel -= 1
                elif k in [ord('s'), curses.KEY_DOWN] and sel < len(menu)-1:
                    sel += 1
                elif k in [10, 13]:
                    if menu[sel]["f"] == "exit":
                        break
                    menu[sel]["f"](stdscr)
                    apply_theme(cfg["theme"])
                elif k == ord("q"):
                    break
            except:
                continue

    except Exception as e:
        pass

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        save_data()
        print("\n[!] JUST-OS wurde sicher beendet. Daten wurden synchronisiert.")