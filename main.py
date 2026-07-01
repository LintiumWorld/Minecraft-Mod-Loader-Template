"""
╔══════════════════════════════════════════════════════════════╗
║           УНИВЕРСАЛЬНЫЙ ЗАГРУЗЧИК МОДОВ MINECRAFT          ║
║                      версия 1.0.0                           ║
║                                                            ║
║  КАК ИСПОЛЬЗОВАТЬ:                                         ║
║  1. Поменяй настройки в секции КОНФИГУРАЦИЯ ниже          ║
║  2. Установи Python и библиотеки:                          ║
║     pip install requests                                    ║
║  3. Установи Nuitka: pip install nuitka                    ║
║  4. Собери EXE:                                            ║
║     nuitka --onefile --windows-disable-console              ║
║            --windows-icon-from-ico=icon.ico                 ║
║            --lto=yes --output-dir=build main.py             ║
║  5. Загрузи EXE и свой mods_list.json куда угодно          ║
║                                                            ║
║  ВСЁ! Твой установщик готов.                               ║
╚══════════════════════════════════════════════════════════════╝
"""

import json, os, sys, requests, zipfile, io, time, subprocess, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# ╔══════════════════════════════════════════════════════════╗
# ║                КОНФИГУРАЦИЯ - МЕНЯЙ ТУТ!               ║
# ╚══════════════════════════════════════════════════════════╝

PROJECT_NAME = "My Mod Pack"
PROJECT_NAME_SHORT = "MMP"

MODS_LIST_URL = "https://raw.githubusercontent.com/ТВОЙ_ЮЗЕР/ТВОЯ_РЕПА/main/mods_list.json"

VERSION = "1.0.0"
AUTHOR = "Твоё Имя"
GITHUB_REPO = "ТВОЙ_ЮЗЕР/ТВОЯ_РЕПА"

MC_VERSION = "1.21.1"
MC_LOADER = "NeoForge"
MC_LOADER_VERSION = "последняя версия"

SETTINGS_FILE = f"{PROJECT_NAME_SHORT.lower()}_settings.json"

ACCENT_HEX = "#ffcc00"

BG_DARK = "#0d0d0d"
CARD_DARK = "#1a1a1a"
FG_DARK = "#ffffff"
BG_LIGHT = "#f5f5f5"
CARD_LIGHT = "#ffffff"
FG_LIGHT = "#1a1a1a"

REQUIREMENTS_RU = f"""ПЕРЕД УСТАНОВКОЙ УБЕДИСЬ:

У тебя должен быть установлен Minecraft {MC_VERSION}
с загрузчиком {MC_LOADER} ({MC_LOADER_VERSION}).

Эта сборка НЕ включает установщик версии.
Если {MC_LOADER} не установлен — ничего не заработает."""

REQUIREMENTS_EN = f"""BEFORE INSTALLING:

You must have Minecraft {MC_VERSION}
with {MC_LOADER} ({MC_LOADER_VERSION}) installed.

This pack does NOT include the version installer.
If {MC_LOADER} is not installed, nothing will work."""

ABOUT_RU = f"""{PROJECT_NAME} - Установщик сборки

Версия: {VERSION}
Разработчик: {AUTHOR}
GitHub: {GITHUB_REPO}"""

ABOUT_EN = f"""{PROJECT_NAME} - Setup

Version: {VERSION}
Developer: {AUTHOR}
GitHub: {GITHUB_REPO}"""

# ╔══════════════════════════════════════════════════════════╗
# ║              КОНЕЦ КОНФИГУРАЦИИ - ДАЛЬШЕ КОД           ║
# ╚══════════════════════════════════════════════════════════╝

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

def darken(hex_color, factor=0.8):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(int(r*factor), int(g*factor), int(b*factor))

def lighten(hex_color, factor=1.2):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(min(255, int(r*factor)), min(255, int(g*factor)), min(255, int(b*factor)))

ACCENT_COLOR = ACCENT_HEX
ACCENT_DARK = darken(ACCENT_HEX)
BUTTON_BG = ACCENT_HEX
BUTTON_FG = "#000000" if sum(hex_to_rgb(ACCENT_HEX)) > 380 else "#ffffff"
BUTTON_HOVER = lighten(ACCENT_HEX, 1.1)
SUCCESS_COLOR = ACCENT_HEX
ERROR_COLOR = "#ff4444"
WARNING_COLOR = ACCENT_HEX if sum(hex_to_rgb(ACCENT_HEX)) > 380 else "#ff8800"
BORDER_COLOR = ACCENT_HEX
PULSE_COLOR = lighten(ACCENT_HEX, 1.3)

current_theme = "dark"
current_lang = "ru"

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"last_folder": "", "theme": "dark", "lang": "ru"}

def save_settings(s):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False)
    except:
        pass

def clear_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
    except:
        pass

def select_folder(initial=""):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title=f"Выбери папку для установки {PROJECT_NAME}", initialdir=initial) if initial and os.path.exists(initial) else filedialog.askdirectory(title=f"Выбери папку для установки {PROJECT_NAME}")
    root.destroy()
    return folder

def get_free_space(path):
    try:
        p = path if os.path.exists(path) else os.path.dirname(path)
        if os.path.exists(p):
            s = os.statvfs(p)
            return s.f_frsize * s.f_bavail
    except:
        pass
    return -1

def format_size(b):
    if b < 0: return "???"
    for u in ['Б','КБ','МБ','ГБ']:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} ТБ"

def download_file(url, dest_path, progress_cb, size_cb):
    try:
        r = requests.get(url, stream=True, timeout=30)
        total = int(r.headers.get('content-length', 0))
        dl = 0
        lt = time.time()
        ld = 0
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                dl += len(chunk)
                size_cb(len(chunk))
                if time.time() - lt > 0.3 and total > 0:
                    speed = (dl - ld) / (time.time() - lt) if (time.time() - lt) > 0 else 0
                    progress_cb(dl, total, speed)
                    lt = time.time()
                    ld = dl
        return True, None
    except Exception as e:
        return False, str(e)

def download_and_extract(url, dest_folder, extract_to, progress_cb, size_cb):
    try:
        target = dest_folder if extract_to == "root" else os.path.join(dest_folder, extract_to)
        os.makedirs(target, exist_ok=True)
        
        r = requests.get(url, stream=True, timeout=60)
        total = int(r.headers.get('content-length', 0))
        dl = 0
        lt = time.time()
        ld = 0
        data = io.BytesIO()
        
        for chunk in r.iter_content(chunk_size=65536):
            data.write(chunk)
            dl += len(chunk)
            size_cb(len(chunk))
            if time.time() - lt > 0.3 and total > 0:
                speed = (dl - ld) / (time.time() - lt) if (time.time() - lt) > 0 else 0
                progress_cb(dl, total, speed)
                lt = time.time()
                ld = dl
        
        progress_cb(total, total, 0)
        
        with zipfile.ZipFile(data, 'r') as z:
            fl = z.namelist()
            for i, f in enumerate(fl):
                z.extract(f, target)
                if fl:
                    progress_cb(int((i+1)/len(fl)*total), total, 0)
        
        return True, None, fl
    except Exception as e:
        return False, str(e), []

def show_requirements():
    msg = REQUIREMENTS_RU if current_lang == "ru" else REQUIREMENTS_EN
    return messagebox.askokcancel(PROJECT_NAME, msg, icon='warning')

class BgAnim:
    def __init__(self, c, w, h):
        self.c, self.w, self.h, self.on = c, w, h, False
        self.p = [{'x': random.randint(0,w), 'y': random.randint(0,h),
                   's': random.randint(1,3), 'sp': random.uniform(0.2,0.8),
                   'o': random.uniform(0.1,0.4)} for _ in range(20)]
    def start(self):
        self.on = True
        self._run()
    def stop(self):
        self.on = False
    def _run(self):
        if not self.on: return
        self.c.delete("p")
        for p in self.p:
            p['y'] -= p['sp']
            if p['y'] < -10: p['y'] = self.h+10; p['x'] = random.randint(0,self.w)
            r,g,b = hex_to_rgb(ACCENT_HEX)
            o = p['o']; gr = int(255*(1-o))
            rr = int(r*o + gr*(1-o*0.5)); gg = int(g*o + gr*(1-o*0.5)); bb = int(b*o + gr*(1-o*0.5))
            self.c.create_oval(p['x']-p['s'], p['y']-p['s'], p['x']+p['s'], p['y']+p['s'],
                             fill=f'#{rr:02x}{gg:02x}{bb:02x}', outline="", tags="p")
        self.c.after(50, self._run)

class PulseBtn:
    def __init__(self, btn, orig):
        self.btn, self.orig, self.on, self.b, self.d = btn, orig, False, 0, 1
    def start(self):
        self.on = True; self._run()
    def stop(self):
        self.on = False; self.btn.configure(bg=self.orig)
    def _run(self):
        if not self.on: return
        self.b += 0.05*self.d
        if self.b >= 1: self.b = 1; self.d = -1
        elif self.b <= 0: self.b = 0; self.d = 1
        r1,g1,b1 = hex_to_rgb(self.orig)
        r2,g2,b2 = hex_to_rgb(PULSE_COLOR)
        r = int(r1 + (r2-r1)*self.b); g = int(g1 + (g2-g1)*self.b); b = int(b1 + (b2-b1)*self.b)
        self.btn.configure(bg=f'#{r:02x}{g:02x}{b:02x}')
        self.btn.after(50, self._run)

class Taskbar:
    def __init__(self, root):
        self.root = root; self.ok = False
        try:
            import ctypes
            self.ct = ctypes
            self.tb = ctypes.windll.shell32
            self.ok = True
        except: pass
    def set(self, v, m):
        if self.ok and self.root.winfo_id():
            try: self.ct.windll.shell32.SetWindowProgressValue(self.root.winfo_id(), int(v/m*100) if m>0 else 0, 100)
            except: pass
    def normal(self):
        if self.ok and self.root.winfo_id():
            try: self.ct.windll.shell32.SetWindowProgressState(self.root.winfo_id(), 1)
            except: pass
    def none(self):
        if self.ok and self.root.winfo_id():
            try: self.ct.windll.shell32.SetWindowProgressState(self.root.winfo_id(), 0)
            except: pass
    def error(self):
        if self.ok and self.root.winfo_id():
            try: self.ct.windll.shell32.SetWindowProgressState(self.root.winfo_id(), 2)
            except: pass

class App:
    def __init__(self):
        self.r = tk.Tk()
        self.r.title(f"{PROJECT_NAME} - Установщик")
        self.r.geometry("680x560")
        self.r.resizable(False, False)
        
        self.settings = load_settings()
        self.folder = self.settings.get("last_folder", "")
        global current_theme, current_lang
        current_theme = self.settings.get("theme", "dark")
        current_lang = self.settings.get("lang", "ru")
        self._theme()
        
        self.total_dl = 0
        self.log = []
        self.pulse = None
        self.tb = Taskbar(self.r)
        
        self.r.update_idletasks()
        w,h = self.r.winfo_width(), self.r.winfo_height()
        x,y = (self.r.winfo_screenwidth()//2)-(w//2), (self.r.winfo_screenheight()//2)-(h//2)
        self.r.geometry(f"{w}x{h}+{x}+{y}")
        
        try:
            self.r.drop_target_register(tk.DND_FILES)
            self.r.dnd_bind('<<Drop>>', self._drop)
        except: pass
        
        self._styles()
        self._ui()
    
    def _theme(self):
        if current_theme == "dark":
            self.bg, self.cbg, self.fg = BG_DARK, CARD_DARK, FG_DARK
            self.t2, self.prog_t = "#999999", "#333333"
        else:
            self.bg, self.cbg, self.fg = BG_LIGHT, CARD_LIGHT, FG_LIGHT
            self.t2, self.prog_t = "#666666", "#e0e0e0"
        self.ac = ACCENT_COLOR; self.acd = ACCENT_DARK; self.bd = BORDER_COLOR
        self.btn_bg = BUTTON_BG; self.btn_fg = BUTTON_FG; self.btn_hv = BUTTON_HOVER
        self.sc = SUCCESS_COLOR; self.ec = ERROR_COLOR; self.wc = WARNING_COLOR
    
    def _styles(self):
        s = ttk.Style(); s.theme_use('default')
        s.configure("f.Horizontal.TProgressbar", thickness=18, background=self.ac, troughcolor=self.prog_t, borderwidth=0)
        s.configure("o.Horizontal.TProgressbar", thickness=6, background=self.sc, troughcolor=self.prog_t, borderwidth=0)
    
    def t(self, k):
        d = {
            "ru": {"ready":"Готов к установке","browse":"ОБЗОР","install":"УСТАНОВИТЬ СБОРКУ","installing":"ИДЁТ УСТАНОВКА...",
                   "path":"ПАПКА УСТАНОВКИ","nosel":"Не выбрана (перетащи папку сюда)","file":"ФАЙЛ","overall":"ОБЩИЙ ПРОГРЕСС",
                   "free":"Свободно","downloading_list":"Загрузка списка...","extracting":"Распаковка","downloading":"Скачивание",
                   "complete":"Установка завершена!","error":"Ошибка","warn":"Завершено с ошибками","success":"Готово",
                   "cancelled":"Отменена","nofolder":"Папка не выбрана","open":"Открыть папку","log":"Лог сохранён",
                   "total":"Всего скачано","theme_d":"☀ СВЕТЛАЯ","theme_l":"🌙 ТЁМНАЯ","lang":"EN","clear":"СБРОС",
                   "about":"О ПРОГРАММЕ","preview":"СПИСОК МОДОВ","clear_confirm":"Удалить настройки и логи?",
                   "cleared":"Настройки очищены","about_text":ABOUT_RU,"preview_title":"Список модов и архивов",
                   "notify":"Установка завершена!"},
            "en": {"ready":"Ready to install","browse":"BROWSE","install":"INSTALL PACK","installing":"INSTALLING...",
                   "path":"INSTALL FOLDER","nosel":"Not selected (drag folder here)","file":"FILE","overall":"OVERALL PROGRESS",
                   "free":"Free","downloading_list":"Loading list...","extracting":"Extracting","downloading":"Downloading",
                   "complete":"Installation complete!","error":"Error","warn":"Completed with errors","success":"Done",
                   "cancelled":"Cancelled","nofolder":"No folder selected","open":"Open folder","log":"Log saved",
                   "total":"Total downloaded","theme_d":"☀ LIGHT","theme_l":"🌙 DARK","lang":"RU","clear":"RESET",
                   "about":"ABOUT","preview":"MOD LIST","clear_confirm":"Delete settings and logs?",
                   "cleared":"Settings cleared","about_text":ABOUT_EN,"preview_title":"Mods and archives",
                   "notify":"Installation complete!"}
        }
        return d[current_lang].get(k, k)
    
    def _ui(self):
        main = tk.Frame(self.r, bg=self.bg, padx=2, pady=2)
        main.pack(fill=tk.BOTH, expand=True)
        
        self.acv = tk.Canvas(main, bg=self.bg, highlightthickness=0)
        self.acv.place(x=0, y=0, relwidth=1, relheight=1)
        self.anim = BgAnim(self.acv, 680, 560); self.anim.start()
        
        hf = tk.Frame(main, bg=self.cbg, height=80, highlightbackground=self.bd, highlightthickness=1)
        hf.pack(fill=tk.X, pady=(0,2)); hf.pack_propagate(False)
        
        for txt, cmd, x in [(self.t("about"), self._about, 5), (self.t("clear"), self._clear, 100)]:
            tk.Button(hf, text=txt, font=("Segoe UI",7), bg=self.cbg, fg=self.t2,
                     relief=tk.FLAT, cursor="hand2", borderwidth=0, command=cmd).place(x=x, y=5)
        
        for txt, cmd, x in [(self.t("lang"), self._lang, 550), (self.t("theme_d") if current_theme=="dark" else self.t("theme_l"), self._theme_toggle, 580)]:
            tk.Button(hf, text=txt, font=("Segoe UI",8,"bold") if txt in ["RU","EN"] else ("Segoe UI",8),
                     bg=self.cbg, fg=self.ac, relief=tk.FLAT, cursor="hand2", borderwidth=0, command=cmd).place(x=x, y=5)
        
        tk.Label(hf, text="⬡", font=("Segoe UI",24), fg=self.ac, bg=self.cbg).pack(pady=(5,0))
        tk.Label(hf, text=PROJECT_NAME.upper(), font=("Segoe UI",20,"bold"), fg=self.ac, bg=self.cbg).pack()
        tk.Label(hf, text="УСТАНОВЩИК СБОРКИ", font=("Segoe UI",9,"bold"), fg=self.t2, bg=self.cbg).pack()
        
        pc = tk.Frame(main, bg=self.cbg, padx=20, pady=12, highlightbackground=self.bd, highlightthickness=1)
        pc.pack(fill=tk.X, pady=2)
        tk.Label(pc, text=self.t("path"), font=("Segoe UI",7,"bold"), fg=self.t2, bg=self.cbg).pack(anchor=tk.W)
        pr = tk.Frame(pc, bg=self.cbg); pr.pack(fill=tk.X, pady=(5,0))
        self.pl = tk.Label(pr, text=self.folder or self.t("nosel"), font=("Segoe UI",9),
                           fg=self.t2 if not self.folder else self.fg, bg=self.cbg, anchor=tk.W)
        self.pl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        self.bb = tk.Button(pr, text=self.t("browse"), font=("Segoe UI",9,"bold"), bg=self.btn_bg,
                            fg=self.btn_fg, activebackground=self.btn_hv, relief=tk.FLAT, cursor="hand2",
                            padx=15, pady=5, borderwidth=0, command=self._browse)
        self.bb.pack(side=tk.RIGHT)
        self.sl = tk.Label(pc, text="", font=("Segoe UI",8), fg=self.t2, bg=self.cbg)
        self.sl.pack(anchor=tk.W, pady=(5,0))
        if self.folder: self._space()
        
        sc = tk.Frame(main, bg=self.cbg, padx=20, pady=15, highlightbackground=self.bd, highlightthickness=1)
        sc.pack(fill=tk.X, pady=2)
        sr = tk.Frame(sc, bg=self.cbg); sr.pack(fill=tk.X, pady=(0,8))
        self.sd = tk.Label(sr, text="●", font=("Segoe UI",10), fg=self.wc, bg=self.cbg)
        self.sd.pack(side=tk.LEFT, padx=(0,8))
        self.st = tk.Label(sr, text=self.t("ready"), font=("Segoe UI",11,"bold"), fg=self.fg, bg=self.cbg)
        self.st.pack(side=tk.LEFT)
        self.sp = tk.Label(sr, text="", font=("Segoe UI",9), fg=self.t2, bg=self.cbg)
        self.sp.pack(side=tk.RIGHT)
        self.cf = tk.Label(sc, text="", font=("Segoe UI",9), fg=self.t2, bg=self.cbg)
        self.cf.pack(anchor=tk.W, pady=(0,10))
        
        fp = tk.Frame(sc, bg=self.cbg); fp.pack(fill=tk.X, pady=(0,10))
        tk.Label(fp, text=self.t("file"), font=("Segoe UI",7,"bold"), fg=self.t2, bg=self.cbg).pack(anchor=tk.W)
        self.fp = ttk.Progressbar(fp, length=580, mode='determinate', style="f.Horizontal.TProgressbar")
        self.fp.pack(fill=tk.X, pady=(3,0))
        
        of = tk.Frame(sc, bg=self.cbg); of.pack(fill=tk.X)
        oh = tk.Frame(of, bg=self.cbg); oh.pack(fill=tk.X)
        tk.Label(oh, text=self.t("overall"), font=("Segoe UI",7,"bold"), fg=self.t2, bg=self.cbg).pack(side=tk.LEFT)
        self.op = tk.Label(oh, text="0%", font=("Segoe UI",9,"bold"), fg=self.ac, bg=self.cbg)
        self.op.pack(side=tk.RIGHT)
        self.opb = ttk.Progressbar(of, length=580, mode='determinate', style="o.Horizontal.TProgressbar")
        self.opb.pack(fill=tk.X, pady=(3,0))
        
        bf = tk.Frame(main, bg=self.cbg, padx=20, pady=15, highlightbackground=self.bd, highlightthickness=1)
        bf.pack(fill=tk.X, pady=2)
        self.ib = tk.Button(bf, text=self.t("install"), font=("Segoe UI",12,"bold"), bg=self.btn_bg,
                            fg=self.btn_fg, activebackground=self.btn_hv, activeforeground=self.btn_fg,
                            relief=tk.FLAT, cursor="hand2", padx=40, pady=12, borderwidth=0,
                            command=self._install)
        self.ib.pack(fill=tk.X, pady=(0,5))
        self.pv = tk.Button(bf, text=self.t("preview"), font=("Segoe UI",9), bg=self.cbg,
                            fg=self.ac, relief=tk.FLAT, cursor="hand2", borderwidth=0, command=self._preview)
        self.pv.pack()
        
        self.pulse = PulseBtn(self.ib, self.btn_bg); self.pulse.start()
        
        ff = tk.Frame(main, bg=self.cbg, padx=20, pady=10, highlightbackground=self.bd, highlightthickness=1)
        ff.pack(fill=tk.X, pady=(2,0))
        tk.Label(ff, text=f"MC {MC_VERSION} | {MC_LOADER}", font=("Segoe UI",8,"bold"),
                fg=self.ac, bg=self.cbg).pack(side=tk.LEFT)
        tk.Label(ff, text=f"{PROJECT_NAME} © 2024 | v{VERSION}", font=("Segoe UI",8),
                fg=self.t2, bg=self.cbg).pack(side=tk.RIGHT)
    
    def _about(self): messagebox.showinfo(self.t("about"), self.t("about_text"), parent=self.r)
    
    def _preview(self):
        try:
            data = requests.get(MODS_LIST_URL, timeout=10).json()
            items = data.get("mods", [])
            mods = [i for i in items if i.get("type") != "archive"]
            arch = [i for i in items if i.get("type") == "archive"]
            txt = f"=== {self.t('preview_title')} ===\n\n"
            if mods:
                txt += f"--- Моды ({len(mods)}) ---\n"
                for m in mods: txt += f"• {m['name']}\n"
            if arch:
                txt += f"\n--- Архивы ({len(arch)}) ---\n"
                for a in arch: txt += f"• {a['name']} → {a.get('extract_to','root')}\n"
            txt += f"\nВсего: {len(items)} элементов"
            messagebox.showinfo(self.t("preview"), txt, parent=self.r)
        except:
            messagebox.showerror(self.t("error"), "Не удалось загрузить список", parent=self.r)
    
    def _clear(self):
        if messagebox.askyesno(self.t("clear"), self.t("clear_confirm"), parent=self.r):
            clear_settings()
            self.folder = ""
            self.pl.configure(text=self.t("nosel"), fg=self.t2)
            self.sl.configure(text="")
            messagebox.showinfo(self.t("clear"), self.t("cleared"), parent=self.r)
    
    def _theme_toggle(self):
        global current_theme
        current_theme = "light" if current_theme == "dark" else "dark"
        self.settings["theme"] = current_theme; save_settings(self.settings)
        self._reload()
    
    def _lang(self):
        global current_lang
        current_lang = "en" if current_lang == "ru" else "ru"
        self.settings["lang"] = current_lang; save_settings(self.settings)
        self._reload()
    
    def _reload(self):
        self.anim.stop()
        if self.pulse: self.pulse.stop()
        for w in self.r.winfo_children(): w.destroy()
        self._theme(); self._styles(); self._ui()
    
    def _browse(self):
        f = select_folder(self.folder)
        if f:
            self.folder = f; self.pl.configure(text=f, fg=self.fg)
            self.settings["last_folder"] = f; save_settings(self.settings)
            self._space()
    
    def _drop(self, e):
        try:
            p = e.data.strip('{}').strip()
            if os.path.isdir(p):
                self.folder = p; self.pl.configure(text=p, fg=self.fg)
                self.settings["last_folder"] = p; save_settings(self.settings)
                self._space()
        except: pass
    
    def _space(self):
        if self.folder:
            free = get_free_space(self.folder)
            if free >= 0: self.sl.configure(text=f"{self.t('free')}: {format_size(free)}")
    
    def _upd_status(self, txt, t="info"):
        cols = {"info":self.wc, "downloading":self.ac, "extracting":self.ac, "success":self.sc, "error":self.ec}
        self.sd.configure(fg=cols.get(t, self.wc)); self.st.configure(text=txt); self.r.update()
    
    def _upd_file(self, name, pct, speed=0):
        self.fp['value'] = pct; self.cf.configure(text=f"{name}: {pct}%")
        if speed > 0: self.sp.configure(text=f"{format_size(speed)}/с")
        else: self.sp.configure(text="")
        self.r.update()
    
    def _upd_overall(self, v, m):
        self.opb['maximum'] = m; self.opb['value'] = v
        self.op.configure(text=f"{int(v/m*100) if m>0 else 0}%")
        self.tb.set(v, m); self.r.update()
    
    def _add_dl(self, s): self.total_dl += s
    
    def _disable(self):
        self.ib.configure(text=self.t("installing"), state=tk.DISABLED, bg="#555", fg="#999")
        self.bb.configure(state=tk.DISABLED, bg="#555"); self.pv.configure(state=tk.DISABLED)
        if self.pulse: self.pulse.stop()
    
    def _enable(self):
        self.ib.configure(text=self.t("install"), state=tk.NORMAL, bg=self.btn_bg, fg=self.btn_fg)
        self.bb.configure(state=tk.NORMAL, bg=self.btn_bg); self.pv.configure(state=tk.NORMAL)
        self.pulse = PulseBtn(self.ib, self.btn_bg); self.pulse.start()
    
    def _sound(self):
        try:
            import winsound; winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except: pass
    
    def _notify(self):
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(PROJECT_NAME, self.t("notify"), duration=5, threaded=True)
        except: pass
    
    def _save_log(self, folder, results, mc, ac):
        try:
            with open(os.path.join(folder, "install_log.txt"), 'w', encoding='utf-8') as f:
                f.write(f"{PROJECT_NAME} Install Log\nVersion: {VERSION}\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mods: {mc}\nArchives: {ac}\nTotal: {format_size(self.total_dl)}\n{'='*50}\n\n")
                for ok, name, err, _ in results:
                    f.write(f"[{'OK' if ok else 'ERROR: '+err}] {name}\n")
        except: pass
    
    def _install(self):
        if not self.folder:
            messagebox.showwarning("Ошибка", self.t("nofolder"), parent=self.r)
            return
        threading.Thread(target=self._install_thread, daemon=True).start()
    
    def _install_thread(self):
        self._disable(); self.total_dl = 0; self.log = []; self.tb.normal()
        try:
            if not show_requirements():
                self._enable(); self._upd_status(self.t("cancelled"), "info"); self.tb.none(); return
            
            folder = self.folder
            mf = os.path.join(folder, "mods"); os.makedirs(mf, exist_ok=True)
            
            self._upd_status(self.t("downloading_list"), "downloading")
            data = requests.get(MODS_LIST_URL, timeout=15).json()
            items = data.get("mods", [])
            mods = [i for i in items if i.get("type") != "archive"]
            arch = [i for i in items if i.get("type") == "archive"]
            total = len(mods) + len(arch)
            self._upd_overall(0, total)
            
            results = []; lock = threading.Lock(); done = 0
            
            def up(name, dl, tot, sp=0):
                self._upd_file(name, int(dl/tot*100) if tot>0 else 0, sp)
            
            def done_cb(fr):
                nonlocal done
                with lock: done += 1; self._upd_overall(done, total)
            
            for a in arch:
                self._upd_status(f"{self.t('downloading')} {a['name']}...", "downloading")
                ok, err, files = download_and_extract(a["url"], folder, a.get("extract_to","root"), up, self._add_dl)
                results.append((ok, a['name'], err, files))
                done += 1; self._upd_overall(done, total)
            
            if mods:
                self._upd_status(f"{self.t('downloading')} (0/{len(mods)})", "downloading")
                with ThreadPoolExecutor(max_workers=5) as ex:
                    fs = []
                    for m in mods:
                        dest = os.path.join(mf, m["url"].split('/')[-1].split('?')[0])
                        f = ex.submit(download_file, m["url"], dest, up, self._add_dl)
                        f.add_done_callback(done_cb); fs.append(f)
                    for f in as_completed(fs):
                        ok, err = f.result()
                        idx = len([r for r in results if not r[0] or r[0]]) - len(arch)
                        name = mods[idx]['name'] if idx < len(mods) else "?"
                        results.append((ok, name, err, [dest]))
                        dn = len([r for r in results if r[0]])
                        self._upd_status(f"{self.t('downloading')} ({dn}/{total})", "downloading")
            
            self._save_log(folder, results, len(mods), len(arch))
            errors = [(n,e) for ok,n,e,_ in results if not ok]
            
            if errors:
                em = "\n".join([f"• {n}: {e}" for n,e in errors])
                self._upd_status(self.t("warn"), "error"); self.tb.error()
                messagebox.showwarning(self.t("warn"), f"Успешно: {len(results)-len(errors)}\n{self.t('total')}: {format_size(self.total_dl)}\n\n{em}", parent=self.r)
            else:
                self._upd_status(self.t("complete"), "success")
                self.sp.configure(text=f"{self.t('total')}: {format_size(self.total_dl)}")
                self._sound(); self._notify(); self.tb.none()
                if messagebox.askyesno(self.t("success"), f"{self.t('complete')}\n\n{self.t('total')}: {format_size(self.total_dl)}\n\n{self.t('open')}?", parent=self.r):
                    try: os.startfile(folder)
                    except: subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            self._upd_status(self.t("error"), "error"); self.tb.error()
            messagebox.showerror(self.t("error"), f"Сбой:\n{e}", parent=self.r)
        finally:
            self.tb.none(); self._enable()

def main():
    App().r.mainloop()

if __name__ == "__main__":
    main()
