# DeepCLI

Интерактивный консольный интерфейс (CLI) на Python для работы с автономными ИИ-агентами на базе DeepSeek / OpenAI-совместимых моделей API.

Проект предоставляет терминальную средой взаимодействия с агентом, который поддерживает автовызов инструментов (Tool Calling), выполнение команд ОС, управление файловой системой, веб-скрапинг и интеграцию с внешними сервисами OSINT.

## Основной функционал

- **Автономный агентный цикл:** Итеративное решение задач с контролем выполнения действий и верификацией результатов.
- **Инструменты файловой системы:** Чтение, создание, модификация файлов, сопоставление разностей (diff), упаковывание в архив.
- **Выполнение системных команд:** Запуск консольных команд (PowerShell / Cmd) с перехватом вывода и таймаутами.
- **Интеграция OSINT:**
  - `dadata_osint.py` — проверка контрагентов, адресов, организаций и физлиц через DaData API.
  - `funstat_osint.py` — поиск информации по открытым источникам через Funstat API.
- **Веб-браузинг:** Взаимодействие с веб-страницами через Playwright.
- **Голосовой ввод:** Поддержка распознавания речи через локальный Whisper (опционально).

## Структура проекта

- `deep_cli.py` — Основная точка входа, обработка ввода пользователя и рендеринг интерфейса (rich + prompt_toolkit).
- `deep_api.py` — Клиент взаимодействия с моделью API и сессией браузера.
- `dadata_osint.py` — Модуль взаимодействия с API DaData.
- `funstat_osint.py` — Модуль взаимодействия с API Funstat.
- `system_prompt.txt` / `system_prompt_nothink.txt` — Системные промпты агента.
- `run_cli.vbs` — Вспомогательный VBS-скрипт для быстрого запуска в Windows.
- `.env` — Файл конфигурации переменных окружения и ключей API.

## Установка и запуск

1. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/supeston/DeepCLI.git
   cd DeepCLI
   ```

2. **Настройка окружения:**

   Создайте виртуальное окружение и установите необходимые зависимости:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Linux/macOS
   # venv\Scripts\activate   # Для Windows
   ```

   Установите необходимые пакеты (rich, prompt_toolkit, pyperclip, playwright, requests и т.д.):

   ```bash
   pip install rich prompt_toolkit pyperclip playwright requests python-dotenv
   playwright install
   ```

3. **Конфигурация `.env`:**

   Укажите ключи API в файле `.env`:

   ```env
   FUNSTAT_API_TOKEN=your_funstat_api_token_here
   DADATA_API_KEY=your_dadata_api_key_here
   DADATA_SECRET_KEY=your_dadata_secret_key_here
   DADATA_ALLOW_PAID=false
   ```

4. **Запуск:**

   ```bash
   python deep_cli.py
   ```
