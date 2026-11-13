# DEEPX CLI (`v3.0.0`)

Автономный терминальный агент и workspace-оркестратор на базе DeepSeek (`DeepSeek-V4.1-Flash`). Работает поверх изолированной браузерной сессии `chat.deepseek.com` через Playwright — API-ключ DeepSeek не требуется.

```text
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝
```

`v3.0.0`  ·  `DeepSeek-V4.1-Flash (284B / 13B)`  ·  `Zero API-Key Web Bridge`  ·  `Windows / Linux`

---

## Быстрый старт

### Windows (рекомендуемый способ)

1. Запустите `start.bat` (или `run_cli.vbs` для открытия в Windows Terminal).
2. При первом запуске скрипт автоматически найдёт Python 3.10+ (или установит Python 3.11), создаст `.venv`, установит зависимости из `requirements.txt`, скачает Playwright Chromium и откроет окно входа.
3. Авторизуйтесь в `chat.deepseek.com` — сессия сохранится в `deepx/core/state.json`.

### Ручная установка

```bash
git clone https://github.com/supeston/DeepCLI.git
cd DeepCLI
python deepx/install.py
.venv/Scripts/python.exe deepx/deep_cli.py
```

### Ключи запуска CLI

```text
--headful     Открыть окно браузера DeepSeek в видимом режиме
--state PATH  Указать альтернативный путь к state.json
--version     Показать установленную версию и выйти
--update      Проверить обновления на GitHub и установить свежую версию
```

---

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
    core/       # конфиг, константы, версионирование и автообновление (version.py, updater.py)
    parser/     # потоковый парсер tool calls и аргументов
    tools/      # ФС, grep, ConPTY, Python, браузер, VDS, документы, OSINT, медиа, буфер
    ui/         # баннер Rich, потоковый рендер Markdown, single-line статус, терминал
    install.py  # установщик окружения и self-check импортов
    main.py     # CLI entrypoint (--headful, --state, --version, --update)
  tests/        # unit и live ConPTY тесты
  VERSION       # текущая версия для локальной проверки и автообновления
  start.bat     # запуск на Windows с автоподготовкой .venv
  run_cli.vbs   # запуск start.bat в Windows Terminal (110x30)
```

---

## Лицензия

MIT License — подробности в файле [LICENSE](LICENSE).
