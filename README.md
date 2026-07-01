
```markdown
# 🎮 Универсальный установщик модов Minecraft

Создай свой собственный установщик модов за **5 минут**. Без знаний программирования.

Create your own mod installer in **5 minutes**. No coding required.

![version](https://img.shields.io/badge/version-1.0.0-yellow)
![python](https://img.shields.io/badge/python-3.8+-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Что умеет / Features

| 🇷🇺 Русский | 🇬🇧 English |
|-------------|-------------|
| 📥 Скачивание модов с прямых ссылок | 📥 Download mods from direct links |
| 📦 Распаковка ZIP-архивов с конфигами | 📦 Extract config ZIP archives |
| 🎨 Тёмная и светлая тема | 🎨 Dark / Light theme |
| 🌍 Русский и английский язык | 🌍 Russian / English language |
| 🖱️ Drag & Drop папки | 🖱️ Drag & Drop folder |
| 📊 Прогресс-бар в таскбаре | 📊 Taskbar progress bar |
| 🔔 Уведомление о завершении | 🔔 Completion notification |
| 📝 Лог установки | 📝 Install log |
| 💾 Запоминание папки | 💾 Remembers last folder |
| ⚡ Многопоточная загрузка | ⚡ Multi-threaded downloads |
| 🎯 Кнопка "О программе" | 🎯 "About" button |
| 📋 Предпросмотр модов | 📋 Mod list preview |

---

## 🚀 Инструкция / Quick Start

### 🇷🇺 Русский

**Шаг 1.** Скачай и установи Python с [python.org](https://python.org) (галка "Add to PATH")

**Шаг 2.** Открой командную строку (`Win+R` → `cmd`) и введи:
```
pip install requests nuitka
```

**Шаг 3.** Скачай этот репозиторий: **Code** → **Download ZIP** → распакуй

**Шаг 4.** Открой `main.py` в блокноте, найди секцию `КОНФИГУРАЦИЯ` и поменяй:
```python
PROJECT_NAME = "Твой Проект"        # Название
MODS_LIST_URL = "https://..."       # Ссылка на твой JSON
MC_VERSION = "1.21.1"              # Версия Minecraft
MC_LOADER = "NeoForge"             # Загрузчик
ACCENT_HEX = "#ffcc00"             # Цвет
```

**Шаг 5.** Отредактируй `mods_list.json` — добавь свои моды

**Шаг 6.** Собери EXE командой:
```
nuitka --onefile --windows-disable-console --windows-icon-from-ico=icon.ico --lto=yes --output-dir=build main.py
```

**Шаг 7.** EXE готов в папке `build`. Раздавай!

---

### 🇬🇧 English

**Step 1.** Install Python from [python.org](https://python.org) (check "Add to PATH")

**Step 2.** Open command prompt (`Win+R` → `cmd`) and run:
```
pip install requests nuitka
```

**Step 3.** Download this repo: **Code** → **Download ZIP** → extract

**Step 4.** Open `main.py` in Notepad, find `CONFIGURATION` section and change:
```python
PROJECT_NAME = "My Mod Pack"        # Name
MODS_LIST_URL = "https://..."       # Your JSON link
MC_VERSION = "1.21.1"              # Minecraft version
MC_LOADER = "NeoForge"             # Loader
ACCENT_HEX = "#ffcc00"             # Color
```

**Step 5.** Edit `mods_list.json` — add your mods

**Step 6.** Build EXE:
```
nuitka --onefile --windows-disable-console --windows-icon-from-ico=icon.ico --lto=yes --output-dir=build main.py
```

**Step 7.** EXE is in `build` folder. Share!

---

## 📋 Формат mods_list.json / Format

```json
{
    "mods": [
        {
            "name": "Название / Name",
            "url": "https://прямая.ссылка/direct.link.jar"
        },
        {
            "name": "Конфиги / Configs",
            "url": "https://ссылка/link.zip",
            "type": "archive",
            "extract_to": "root"
        }
    ]
}
```

| Поле / Field | Тип / Type | Обязательно / Required | Описание / Description |
|--------------|------------|------------------------|------------------------|
| `name` | текст / text | Да / Yes | Название / Name |
| `url` | текст / text | Да / Yes | Прямая ссылка / Direct link |
| `type` | текст / text | Нет / No | `"archive"` для ZIP / for ZIP |
| `extract_to` | текст / text | Нет / No | `"root"`, `"mods"`, `"config"` |

---

## 🎨 Цвета / Colors

Поменяй `ACCENT_HEX` в `main.py` / Change `ACCENT_HEX` in `main.py`:

| Цвет / Color | Код / Code |
|--------------|------------|
| 🟠 Оранжевый / Orange | `#ff5722` |
| 🟢 Зелёный / Green | `#4caf50` |
| 🔵 Синий / Blue | `#2196f3` |
| 🟣 Фиолетовый / Purple | `#9c27b0` |
| 🔴 Красный / Red | `#f44336` |
| 🩷 Розовый / Pink | `#e91e63` |
| 🟡 Жёлтый / Yellow | `#ffcc00` |

---

## ❓ FAQ

**В: Можно ли использовать моды с CurseForge?**  
**Q: Can I use CurseForge mods?**  
О/A: Да, если есть прямая ссылка. Лучше используй Modrinth. / Yes, with direct link. Better use Modrinth.

**В: Архив должен быть ZIP?**  
**Q: Does the archive have to be ZIP?**  
О/A: Да, только ZIP. / Yes, ZIP only.

**В: Сколько весит EXE?**  
**Q: How big is the EXE?**  
О/A: ~15-20 МБ / MB.

**В: Это бесплатно?**  
**Q: Is it free?**  
О/A: Да, MIT License. / Yes, MIT License.

**В: Где взять прямые ссылки на моды?**  
**Q: Where to get direct mod links?**  
О/A: [Modrinth](https://modrinth.com) → мод → Versions → копируй ссылку из браузера. / Mod → Versions → copy browser URL.

---

## 📄 Лицензия / License

MIT License — делай что хочешь, указывай авторство. / Do whatever you want, just give credit.

---
