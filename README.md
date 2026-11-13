# DEEPX CLI (`v3.1.0`)

Автономный терминальный агент и workspace-оркестратор на базе DeepSeek (`DeepSeek-V4.1-Flash`). Работает поверх изолированной браузерной сессии `chat.deepseek.com` через Playwright — API-ключ DeepSeek не требуется.

```text
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝
```

`v3.1.0`  ·  `DeepSeek-V4.1-Flash (284B / 13B)`  ·  `Zero API-Key Web Bridge`  ·  `Windows Terminal / Win32 Console`

---

## Быстрый старт

### 1. Установка в систему одной командой (Windows)

```powershell
irm https://raw.githubusercontent.com/supeston/DeepCLI/main/install.ps1 | iex
```

Скрипт устанавливает DEEPX CLI в `%LOCALAPPDATA%\DeepX\app`, настраивает `.venv` и Chromium и закрепляет глобальную команду `deepx` в `PATH`. После установки введите `deepx` в любой папке — агент автоматически переключится в Windows Terminal (если установлен) и закроет прежнее окно классической консоли.

### 2. Локальный запуск через `run_cli.vbs`

1. Клонируйте или распакуйте репозиторий и откройте `run_cli.vbs`.
2. Лаунчер автоматически найдёт Python 3.10+ (или установит Python 3.11), настроит `.venv`, принудительно откроет Windows Terminal (или классическую консоль на системах до Windows 11 без WT) и запустит интерактивный **Control Hub** с навигацией стрелками (`↑`/`↓`, `Enter`):
   - запуск агента (`DEEPX AGENT`),
   - проверка и установка обновлений с GitHub,
   - проверка и восстановление зависимостей и Chromium,
   - установка / удаление глобальной команды `deepx`.
3. При первом запуске агента авторизуйтесь в `chat.deepseek.com` — сессия сохранится в `deepx/core/state.json`.

### Ручная установка

```bash
git clone https://github.com/supeston/DeepCLI.git
cd DeepCLI
python deepx/install.py
deepx
```

### Ключи запуска CLI

```text
--headful        Открыть окно браузера DeepSeek в видимом режиме
--launcher       Открыть интерактивный TUI-лаунчер DEEPX Control Hub
--cwd PATH       Задать рабочую директорию сессии
--state PATH     Указать альтернативный путь к state.json
--install-cmd    Установить глобальную команду deepx в PATH пользователя
--uninstall-cmd  Удалить глобальную команду deepx из PATH
--no-relaunch    Остаться в текущем окне терминала без перехода в Windows Terminal
--version        Показать установленную версию и выйти
--update         Проверить обновления на GitHub и установить свежую версию
```

---

## Что нового в v3.1.0

- **▸ Интерактивный VBS-лаунчер (`run_cli.vbs` + `deepx/launcher.py`)**: legacy `start.bat` полностью удалён; `run_cli.vbs` открывает отдельный Rich TUI-лаунчер **CONTROL HUB** с баннером, проверкой обновлений, диагностикой зависимостей, переключением глобальной команды `deepx` и управлением стрелками (`↑`/`↓`).
- **▸ Системная команда `deepx` и авто-переход в Windows Terminal**: установка одной командой (`install.ps1` или `--install-cmd`) добавляет `deepx` в `PATH`. При вызове из классической консоли (`conhost.exe`) и наличии `wt.exe` сессия автоматически открывается в Windows Terminal с 24-bit TrueColor, сохраняя рабочую директорию и закрывая старое окно.
- **▸ Мгновенное закрытие без зависаний и стабильная работа в обоих терминалах**: отключён QuickEdit-фриз (`Выбрать DEEPX AGENT`), исправлен Win32 close handler (`SetProcessShutdownParameters` + очистка дочерних процессов), добавлены таймауты закрытия Playwright и демон-потоки ввода — окно закрывается мгновенно без `(Не отвечает)`.

## Что нового в v3.0.0

- **▸ Автообновления и версионирование**: при старте CLI проверяет свежую версию на GitHub и показывает уведомление `update to X.Y.Z` прямо внутри баннера. Обновление ставится командой `/update` (или `--update`) без перезаписи `.env`, `state.json`, `.venv` и `.deepx`.
- **▸ Минималистичный TUI и единая строка статуса**: статус текущего действия обновляется на месте с таймером (`| Читаю main.py... (0.4s)`), сырые JSON-вызовы инструментов и длинные технические логи скрыты из чата.
- **▸ Нулевой контекст проекта (AST Repo Map)**: при старте и `/cd` агент строит компактную карту структуры проекта с сигнатурами классов и функций и подгружает `DEEPX.md` / `AGENTS.md`.
- **▸ Надёжные чекпоинты и `/undo`**: изменённые за ход файлы сохраняются в `.deepx_history` и откатываются одной командой `/undo`, а `/compact` сжимает устаревшие выводы инструментов.
- **▸ Режим `plan` и точный парсер**: `/mode plan` блокирует запись в файлы и мутирующие команды на этапе проектирования; потоковый парсер корректно склеивает Markdown и не повреждает строковые литералы.
- **▸ Параллельное чтение и `grep_search`**: read-only инструменты выполняются конкурентно в одном батче, добавлен быстрый поиск совпадений по файлам.

---

## Режимы и профили

### Режимы мышления (`/mode`)

| Режим | DeepThink | Запись / команды | Назначение |
| :--- | :--- | :--- | :--- |
| `instant` | `OFF` | Разрешены | Быстрые правки, скрипты, повседневные задачи |
| `think` | `ON` | Разрешены | Сложная отладка, рефакторинг, многошаговая логика |
| `plan` | `ON` | Read-only | Анализ архитектуры и планирование без изменения файлов |

Переключение через `/mode` сохраняет историю текущей переписки.

### Профили агента (`/style`)

| Профиль | Фокус | Ключевые инструменты |
| :--- | :--- | :--- |
| `coder` | Разработка и автоматизация | Файлы, `grep_search`, `run_python`, ConPTY `run_cmd`, фоновые задачи, VDS/SSH, браузер |
| `universal` | Аналитика, тексты, документы | Файлы, Python, веб-поиск, `make_docx`, `make_excel`, `make_pptx`, браузер |
| `osinter` | OSINT и проверка контрагентов | DuckDuckGo, `fetch_url`, браузер, `dadata_osint`, `funstat_osint`, защита директории DEEPX |

---

## Команды и управление

```text
/mode <instant|think|plan>       Переключить режим работы (сохраняет контекст)
/style <coder|universal|osinter> Сменить профиль (открывает чистый чат)
/think [on|off]                  Включить или выключить DeepThink
/search [on|off]                 Включить или выключить встроенный веб-поиск
/cd <path>                       Сменить рабочую директорию и перестроить AST-карту
/compact                         Сжать старые выводы инструментов в истории
/undo                            Откатить изменения файлов за последний ход
/status                          Показать версию, режим, профиль, папку и статус обновлений
/update [check | --force]        Проверить и установить обновление с GitHub
/stealth                         Проверить playwright-stealth и сигналы отпечатка браузера
/menu                            Открыть TUI-меню настроек
/new                             Начать новый диалог
/copy                            Скопировать последний ответ в буфер обмена
/clear                           Очистить экран и перерисовать баннер
/help                            Справка по командам
/exit, /quit                     Выйти из DEEPX CLI
```

Горячие клавиши:
- `Tab` — автодополнение slash-команд.
- `Ctrl+X` — прервать текущую генерацию или шаг агента без потери сессии.
- `Ctrl+C` — запрос подтверждения выхода (`[y/N]`).

---

## Инструментарий

- **▸ Файловая система и поиск**: `read_file` (с поддержкой диапазонов строк и вложения изображений), `edit_file` (проверка уникальности фрагмента и AST/compile-валидация `.py`), `write_file`, `list_dir`, `file_info`, `grep_search`.
- **▸ Терминал и процессы**: интерактивный ConPTY (`run_cmd`, `send_input`, `kill_cmd` с UTF-8 `chcp 65001`), фоновые процессы (`run_background_cmd`, `task_status`, `task_log`, `kill_background_cmd`), изолированный `run_python`.
- **▸ Автономный браузер**: `browser_action` на базе Playwright Chromium (`playwright-stealth`, работа по `ref`, загрузка и скачивание файлов, скриншоты, JS-оценка).
- **▸ Сеть, VDS и документы**: `web_search` (DuckDuckGo), `fetch_url`, SSH/SFTP-пул `vds_deploy` (профили, `exec`, `script`, `upload`/`download`), `make_docx`, `make_excel`, `make_pptx`, `zip_pack`/`unzip_pack`, `inspect_media`.
- **▸ Память и задачи**: `todo` (живая панель прогресса), `project_memory` (`.deepx_project_memory.json`), интеграция с буфером обмена Windows (`Win+V` history) и модули OSINT (`dadata_osint`, `funstat_osint`).

---

## Конфигурация (`.env`)

Ключ от DeepSeek не нужен. Переменные окружения в `.env` (или `deepx/core/.env`, шаблон — `.env.example`) используются только для опциональных интеграций:

```ini
# OSINT: Telegram (telelog / funstat)
FUNSTAT_API_TOKEN=

# OSINT: ЕГРЮЛ, банки и адреса (dadata.ru)
DADATA_API_KEY=
DADATA_SECRET_KEY=
DADATA_ALLOW_PAID=false

# Профиль VDS по умолчанию (опционально)
VDS_HOST=
VDS_USER=root
VDS_PORT=22
VDS_PASSWORD=
VDS_KEY_PATH=
```

---

## Структура репозитория

```text
DeepCLI/
  deepx/
    agent/      # оркестратор runner.py, промпты, чекпоинты, AST repo_map, автодополнение
    api/        # Playwright-мост к DeepSeek Web (deep_api.py)
    core/       # конфиг, константы, версионирование, автообновление, Windows Terminal handoff
    parser/     # потоковый парсер tool calls и аргументов
    tools/      # ФС, grep, ConPTY, Python, браузер, VDS, документы, OSINT, медиа, буфер
    ui/         # баннер Rich, потоковый рендер Markdown, single-line статус, терминал
    launcher.py # интерактивный Rich TUI-лаунчер Control Hub со стрелочным меню
    install.py  # установщик окружения, self-check зависимостей и команда deepx
    main.py     # CLI entrypoint (--launcher, --install-cmd, --version, --update)
  tests/        # unit и live ConPTY тесты
  VERSION       # текущая версия для локальной проверки и автообновления
  install.ps1   # установка в систему одной командой (Windows)
  run_cli.vbs   # VBS-лаунчер с принудительным запуском в Windows Terminal
```

---

## Лицензия

MIT License — подробности в файле [LICENSE](LICENSE).
