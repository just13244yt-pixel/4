import curses
import os
import subprocess
import json
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.justos_config.json")

class JustOS:

    ASCII_TITLE = [
        "     ██╗██╗   ██╗███████╗████████╗ ██████╗ ███████╗",
        "     ██║██║   ██║██╔════╝╚══██╔══╝██╔═══██╗██╔════╝",
        "     ██║██║   ██║███████╗   ██║   ██║   ██║███████╗",
        "██   ██║██║   ██║╚════██║   ██║   ██║   ██║╚════██║",
        "╚█████╔╝╚██████╔╝███████║   ██║   ╚██████╔╝███████║",
        " ╚════╝  ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝ ╚══════╝"
    ]

    COLOR_LIST = [
        ("Schwarz", curses.COLOR_BLACK),
        ("Rot", curses.COLOR_RED),
        ("Grün", curses.COLOR_GREEN),
        ("Gelb", curses.COLOR_YELLOW),
        ("Blau", curses.COLOR_BLUE),
        ("Magenta", curses.COLOR_MAGENTA),
        ("Cyan", curses.COLOR_CYAN),
        ("Weiß", curses.COLOR_WHITE)
    ]

    def __init__(self, stdscr):

        # Prüfen ob Raspberry Pi Lite
        if not os.path.exists("/etc/os-release") or "raspbian" not in open("/etc/os-release").read().lower():
            print("JustOS läuft nur auf Raspberry Pi Lite!")
            exit()

        self.stdscr = stdscr
        self.current_menu = "main"
        self.selected_index = 0
        self.running = True

        self.user_name = "Justus"

        self.main_menu_items = [
            "Explorer",
            "Terminal",
            "Befehle",
            "Settings",
            "Neustart",
            "Shut Down"
        ]

        # Explorer
        self.explorer_path = os.path.abspath(os.path.expanduser("~"))
        self.explorer_files = []
        self.explorer_selected = 0
        self.search_query = ""

        # Commands
        self.custom_commands = []
        self.cmd_selected = 0

        # Settings
        self.settings_items = [
            "Titel Farbe",
            "Auswahl Farbe",
            "Status Farbe",
            "Ordner Farbe",
            "Zurück"
        ]
        self.settings_selected = 0

        self.colors = {
            "title": curses.COLOR_CYAN,
            "select": curses.COLOR_WHITE,
            "status": curses.COLOR_GREEN,
            "dir": curses.COLOR_YELLOW
        }

        self.load_config()

        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)

        curses.start_color()
        self.init_colors()

    # ---------------- JSON ----------------

    def save_config(self):
        data = {
            "user_name": self.user_name,
            "colors": self.colors,
            "commands": self.custom_commands
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(data, f, indent=4)
        except:
            pass

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH) as f:
                data = json.load(f)
            self.user_name = data.get("user_name", self.user_name)
            self.colors = data.get("colors", self.colors)
            self.custom_commands = data.get("commands", [])
        except:
            pass

    # ---------------- COLORS ----------------

    def init_colors(self):
        curses.init_pair(1, self.colors["title"], curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, self.colors["select"])
        curses.init_pair(3, self.colors["status"], curses.COLOR_BLACK)
        curses.init_pair(4, self.colors["dir"], curses.COLOR_BLACK)

    # ---------------- HEADER ----------------

    def draw_header(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        for i, line in enumerate(self.ASCII_TITLE):
            x = (w - len(line)) // 2
            self.stdscr.addstr(i, x, line)
        self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.hline(len(self.ASCII_TITLE)+1, 0, '-', w)

    def draw_footer(self):
        h, w = self.stdscr.getmaxyx()
        now = datetime.now().strftime("%H:%M:%S")
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(h-1, 0, self.user_name)
        self.stdscr.addstr(h-1, w-len(now)-1, now)
        self.stdscr.attroff(curses.color_pair(3))

    # ---------------- MAIN MENU ----------------

    def draw_main_menu(self):
        h, w = self.stdscr.getmaxyx()
        start_y = len(self.ASCII_TITLE)+3
        for i,item in enumerate(self.main_menu_items):
            x = (w-len(item))//2
            y = start_y + i
            if i == self.selected_index:
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y,x,item)
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y,x,item)

    # ---------------- EXPLORER ----------------

    def update_explorer_files(self):
        try:
            files = os.listdir(self.explorer_path)
            if self.search_query:
                files = [f for f in files if self.search_query.lower() in f.lower()]
            dirs = sorted([f for f in files if os.path.isdir(os.path.join(self.explorer_path, f))])
            files_only = sorted([f for f in files if os.path.isfile(os.path.join(self.explorer_path, f))])
            self.explorer_files = [".."] + dirs + files_only
        except:
            self.explorer_files = [".."]

    def draw_explorer(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(len(self.ASCII_TITLE)+2,2,f"Pfad: {self.explorer_path}")
        start = len(self.ASCII_TITLE)+4
        for i,file in enumerate(self.explorer_files):
            y = start+i
            full = os.path.join(self.explorer_path,file)
            if i == self.explorer_selected:
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y,2,file)
                self.stdscr.attroff(curses.color_pair(2))
            else:
                if os.path.isdir(full) or file=="..":
                    self.stdscr.attron(curses.color_pair(4))
                    self.stdscr.addstr(y,2,file)
                    self.stdscr.attroff(curses.color_pair(4))
                else:
                    self.stdscr.addstr(y,2,file)

    # ---------------- COMMANDS ----------------

    def draw_commands(self):
        y = len(self.ASCII_TITLE)+3
        self.stdscr.addstr(y,2,"Gespeicherte Befehle (b = hinzufügen)")

        if not self.custom_commands:
            self.stdscr.addstr(y+2,2,"Keine Befehle gespeichert")

        for i,cmd in enumerate(self.custom_commands):
            text = f"{cmd['name']} -> {cmd['cmd']}"
            if i == self.cmd_selected:
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y+2+i,2,text)
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y+2+i,2,text)

    def add_command(self):
        curses.echo()
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(10, 5, "Name des Befehls: ")
        name = self.stdscr.getstr(10, 25, 50).decode("utf-8")
        self.stdscr.addstr(12, 5, "Kommando: ")
        cmd = self.stdscr.getstr(12, 15, 100).decode("utf-8")
        curses.noecho()
        if name and cmd:
            self.custom_commands.append({"name": name, "cmd": cmd})
            self.save_config()

    # ---------------- SETTINGS ----------------

    def draw_settings(self):
        h,w = self.stdscr.getmaxyx()
        start = len(self.ASCII_TITLE)+3
        for i,item in enumerate(self.settings_items):
            x=(w-len(item))//2
            y=start+i
            if i==self.settings_selected:
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y,x,item)
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y,x,item)

    def choose_color(self):
        idx=0
        while True:
            self.stdscr.clear()
            self.draw_header()
            for i,(name,_) in enumerate(self.COLOR_LIST):
                if i==idx:
                    self.stdscr.attron(curses.color_pair(2))
                    self.stdscr.addstr(10+i,10,name)
                    self.stdscr.attroff(curses.color_pair(2))
                else:
                    self.stdscr.addstr(10+i,10,name)
            key=self.stdscr.getch()
            if key==curses.KEY_UP:
                idx=(idx-1)%len(self.COLOR_LIST)
            elif key==curses.KEY_DOWN:
                idx=(idx+1)%len(self.COLOR_LIST)
            elif key in [10,13]:
                return self.COLOR_LIST[idx][1]
            elif key==27:
                return None

    # ---------------- TERMINAL ----------------

    def open_terminal(self):
        curses.endwin()
        subprocess.run("/bin/bash")
        self.stdscr.clear()

    # ---------------- INPUT ----------------

    def handle_input(self,key):
        if key==27:
            self.current_menu="main"
            return

        if self.current_menu=="main":
            if key==curses.KEY_UP:
                self.selected_index=(self.selected_index-1)%len(self.main_menu_items)
            elif key==curses.KEY_DOWN:
                self.selected_index=(self.selected_index+1)%len(self.main_menu_items)
            elif key in [10,13]:
                item=self.main_menu_items[self.selected_index]
                if item=="Explorer":
                    self.current_menu="explorer"
                    self.update_explorer_files()
                elif item=="Terminal":
                    self.open_terminal()
                elif item=="Befehle":
                    self.current_menu="commands"
                elif item=="Settings":
                    self.current_menu="settings"
                elif item=="Neustart":
                    os.system("sudo reboot")
                elif item=="Shut Down":
                    os.system("sudo shutdown -h now")

        elif self.current_menu=="commands":
            if key==curses.KEY_UP:
                self.cmd_selected=(self.cmd_selected-1)%len(self.custom_commands) if self.custom_commands else 0
            elif key==curses.KEY_DOWN:
                self.cmd_selected=(self.cmd_selected+1)%len(self.custom_commands) if self.custom_commands else 0
            elif key in [10,13] and self.custom_commands:
                cmd=self.custom_commands[self.cmd_selected]["cmd"]
                curses.endwin()
                os.system(cmd)
                self.stdscr.clear()
            elif key in [ord('b'), ord('B')]:
                self.add_command()

        elif self.current_menu=="settings":
            if key==curses.KEY_UP:
                self.settings_selected=(self.settings_selected-1)%len(self.settings_items)
            elif key==curses.KEY_DOWN:
                self.settings_selected=(self.settings_selected+1)%len(self.settings_items)
            elif key in [10,13]:
                item=self.settings_items[self.settings_selected]
                if item=="Zurück":
                    self.current_menu="main"
                    return
                color=self.choose_color()
                if color is None:
                    return
                if item=="Titel Farbe":
                    self.colors["title"]=color
                elif item=="Auswahl Farbe":
                    self.colors["select"]=color
                elif item=="Status Farbe":
                    self.colors["status"]=color
                elif item=="Ordner Farbe":
                    self.colors["dir"]=color
                self.init_colors()
                self.save_config()

    # ---------------- LOOP ----------------

    def run(self):
        while self.running:
            try:
                self.stdscr.clear()
                self.draw_header()
                self.draw_footer()
                if self.current_menu=="main":
                    self.draw_main_menu()
                elif self.current_menu=="explorer":
                    self.draw_explorer()
                elif self.current_menu=="commands":
                    self.draw_commands()
                elif self.current_menu=="settings":
                    self.draw_settings()
                key=self.stdscr.getch()
                if key!=-1:
                    self.handle_input(key)
                self.stdscr.refresh()
            except curses.error:
                pass

if __name__=="__main__":
    curses.wrapper(lambda stdscr: JustOS(stdscr).run())