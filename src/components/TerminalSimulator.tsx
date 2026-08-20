import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal as TermIcon,
  Copy,
  Check,
  RotateCcw,
  Play,
  Pause,
  Layers,
  Clipboard,
  Cpu,
  Globe,
} from 'lucide-react';

interface TaskItem {
  id: number;
  status: 'pending' | 'active' | 'done';
  text: string;
}

interface ScenarioStep {
  type: 'think' | 'tasks' | 'tool' | 'code' | 'output' | 'ai';
  content?: string;
  tasks?: TaskItem[];
  percent?: number;
  toolName?: string;
  toolOutput?: string;
  lang?: string;
  code?: string;
}

interface Scenario {
  id: string;
  label: string;
  icon: React.ElementType;
  userPrompt: string;
  steps: ScenarioStep[];
}

const ASCII_BANNER = `\
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝`;

export const TerminalSimulator: React.FC = () => {
  const scenarios: Scenario[] = [
    {
      id: 'refactor',
      label: 'Full-Stack Refactor & ConPTY Tests',
      icon: Layers,
      userPrompt: 'Сделай рефакторинг auth.py, добавь JWT валидацию и прогони pytest в ConPTY',
      steps: [
        {
          type: 'think',
          content: 'DeepThink Engine: анализирую auth.py, модели пользователей и pytest-окружение. Формирую план задач...',
        },
        {
          type: 'tasks',
          percent: 0,
          tasks: [
            { id: 1, status: 'active', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'pending', text: 'Генерация JWT encoder/decoder с тайм-аутом exp' },
            { id: 3, status: 'pending', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.read_file("src/auth.py")',
          toolOutput: '✓ Read 48 lines from src/auth.py (Legacy plaintext session tokens detected)',
        },
        {
          type: 'tasks',
          percent: 25,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'active', text: 'Генерация JWT encoder/decoder с тайм-аутом exp' },
            { id: 3, status: 'pending', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.write_file("src/auth.py", ...)',
        },
        {
          type: 'code',
          lang: 'python',
          code: `from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "deepx-token-secret"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=12))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)`,
        },
        {
          type: 'tasks',
          percent: 50,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с тайм-аутом exp' },
            { id: 3, status: 'active', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.replace_file_content("src/middleware.py", ...)',
          toolOutput: '✓ Injected JWT header verification and HTTP 401 Unauthorized guard',
        },
        {
          type: 'tasks',
          percent: 75,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с тайм-аутом exp' },
            { id: 3, status: 'done', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'active', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
          ],
        },
        {
          type: 'tool',
          toolName: 'terminal.run_in_terminal("pytest tests/test_auth.py -v")',
          toolOutput:
            'rootdir: C:\\Projects\\AuthAPI, configfile: pytest.ini\n✓ tests/test_auth.py::test_create_jwt PASSED        [ 25%]\n✓ tests/test_auth.py::test_verify_valid_token PASSED   [ 50%]\n✓ tests/test_auth.py::test_expired_token PASSED        [ 75%]\n✓ tests/test_auth.py::test_middleware_guard PASSED     [100%]\n══════════════════════ 4 passed in 0.32s ═════════════════════',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с тайм-аутом exp' },
            { id: 3, status: 'done', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'done', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
          ],
        },
        {
          type: 'ai',
          content:
            'Рефакторинг auth.py завершён. Добавлена строгая JWT валидация с проверкой времени жизни токена и middleware. Все 4 теста pytest пройдены успешно.',
        },
      ],
    },
    {
      id: 'clipboard',
      label: 'WinRT Clipboard & Vision Analysis',
      icon: Clipboard,
      userPrompt: 'Посмотри скриншот ошибки в буфере обмена (Win+V), найди причину и закоммить фикс',
      steps: [
        {
          type: 'think',
          content: 'DeepThink Engine: обращаюсь к Windows.ApplicationModel.DataTransfer.Clipboard API для извлечения bitmap...',
        },
        {
          type: 'tasks',
          percent: 0,
          tasks: [
            { id: 1, status: 'active', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'pending', text: 'Vision-анализ трассировки стека и определение файла' },
            { id: 3, status: 'pending', text: 'Устранение NullReferenceException в UserService.cs' },
            { id: 4, status: 'pending', text: 'Создание чистого Git коммита с описанием' },
          ],
        },
        {
          type: 'tool',
          toolName: 'clipboard.get_clipboard_image()',
          toolOutput: '✓ Captured active clipboard bitmap (1920x1080, 2.4 MB, Format: CF_DIBV5)',
        },
        {
          type: 'tasks',
          percent: 25,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'active', text: 'Vision-анализ трассировки стека и определение файла' },
            { id: 3, status: 'pending', text: 'Устранение NullReferenceException в UserService.cs' },
            { id: 4, status: 'pending', text: 'Создание чистого Git коммита с описанием' },
          ],
        },
        {
          type: 'output',
          content: '👁 Vision Engine: обнаружена ошибка NullReferenceException в UserService.cs:92 (свойство profile.Settings равно null)',
        },
        {
          type: 'tasks',
          percent: 50,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и определение файла' },
            { id: 3, status: 'active', text: 'Устранение NullReferenceException в UserService.cs' },
            { id: 4, status: 'pending', text: 'Создание чистого Git коммита с описанием' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.replace_file_content("Services/UserService.cs", ...)',
          toolOutput: '✓ Added null-conditional coalescing: user?.Profile?.Settings ?? DefaultSettings',
        },
        {
          type: 'tasks',
          percent: 75,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и определение файла' },
            { id: 3, status: 'done', text: 'Устранение NullReferenceException в UserService.cs' },
            { id: 4, status: 'active', text: 'Создание чистого Git коммита с описанием' },
          ],
        },
        {
          type: 'tool',
          toolName: 'terminal.run_in_terminal("git commit -am \\"fix(user): safeguard profile null reference\\"")',
          toolOutput: '[main 9cf3a1e] fix(user): safeguard profile null reference\n 1 file changed, 4 insertions(+), 1 deletion(-)',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и определение файла' },
            { id: 3, status: 'done', text: 'Устранение NullReferenceException в UserService.cs' },
            { id: 4, status: 'done', text: 'Создание чистого Git коммита с описанием' },
          ],
        },
        {
          type: 'ai',
          content: 'Скриншот из буфера успешно обработан. В UserService.cs добавлен безопасный null-check и создан коммит 9cf3a1e.',
        },
      ],
    },
    {
      id: 'daemon',
      label: 'ConPTY Daemon & Process Supervisor',
      icon: Cpu,
      userPrompt: 'Запусти сервер приложения в фоне, отправь проверочный payload и убедись в 200 OK',
      steps: [
        {
          type: 'think',
          content: 'DeepThink Engine: создаю изолированную Windows ConPTY сессию для фонового сервера...',
        },
        {
          type: 'tasks',
          percent: 0,
          tasks: [
            { id: 1, status: 'active', text: 'Запуск uvicorn app:main в фоновом ConPTY процессе' },
            { id: 2, status: 'pending', text: 'Ожидание готовности сокета http://127.0.0.1:8000' },
            { id: 3, status: 'pending', text: 'Отправка HTTP POST /healthcheck запроса' },
            { id: 4, status: 'pending', text: 'Корректная остановка и очистка процессов-зомби' },
          ],
        },
        {
          type: 'tool',
          toolName: 'terminal.spawn_background_process("uvicorn app:main --port 8000")',
          toolOutput: '✓ Background Task [task-1082] spawned. Monitoring ConPTY pipe stream...',
        },
        {
          type: 'tasks',
          percent: 33,
          tasks: [
            { id: 1, status: 'done', text: 'Запуск uvicorn app:main в фоновом ConPTY процессе' },
            { id: 2, status: 'active', text: 'Ожидание готовности сокета http://127.0.0.1:8000' },
            { id: 3, status: 'pending', text: 'Отправка HTTP POST /healthcheck запроса' },
            { id: 4, status: 'pending', text: 'Корректная остановка и очистка процессов-зомби' },
          ],
        },
        {
          type: 'output',
          content: 'INFO: Started server process [PID 14208]\nINFO: Waiting for application startup.\nINFO: Application startup complete. Uvicorn running on http://127.0.0.1:8000',
        },
        {
          type: 'tasks',
          percent: 66,
          tasks: [
            { id: 1, status: 'done', text: 'Запуск uvicorn app:main в фоновом ConPTY процессе' },
            { id: 2, status: 'done', text: 'Ожидание готовности сокета http://127.0.0.1:8000' },
            { id: 3, status: 'active', text: 'Отправка HTTP POST /healthcheck запроса' },
            { id: 4, status: 'pending', text: 'Корректная остановка и очистка процессов-зомби' },
          ],
        },
        {
          type: 'tool',
          toolName: 'web.http_request("POST", "http://127.0.0.1:8000/healthcheck")',
          toolOutput: '✓ Response 200 OK {"status": "healthy", "latency_ms": 1.2, "db": "connected"}',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Запуск uvicorn app:main в фоновом ConPTY процессе' },
            { id: 2, status: 'done', text: 'Ожидание готовности сокета http://127.0.0.1:8000' },
            { id: 3, status: 'done', text: 'Отправка HTTP POST /healthcheck запроса' },
            { id: 4, status: 'done', text: 'Корректная остановка и очистка процессов-зомби' },
          ],
        },
        {
          type: 'ai',
          content: 'Фоновый сервер отработал штатно, эндпоинт /healthcheck вернул 200 OK (1.2ms). Сессия ConPTY корректно закрыта без утечек дескрипторов.',
        },
      ],
    },
    {
      id: 'browser',
      label: 'Headless Stealth Browser & OSINT',
      icon: Globe,
      userPrompt: 'Собери актуальную документацию по FastAPI 0.115 и сохрани выжимку в docs.md',
      steps: [
        {
          type: 'think',
          content: 'DeepThink Engine: инициализирую антидетект-браузер со стелс-профилем для обхода Cloudflare защиты...',
        },
        {
          type: 'tasks',
          percent: 0,
          tasks: [
            { id: 1, status: 'active', text: 'Инициализация браузера с stealth-профилем' },
            { id: 2, status: 'pending', text: 'Навигация и парсинг release notes FastAPI' },
            { id: 3, status: 'pending', text: 'Синтез изменений и запись в docs/fastapi_0115.md' },
          ],
        },
        {
          type: 'tool',
          toolName: 'browser.navigate("https://fastapi.tiangolo.com/release-notes/")',
          toolOutput: '✓ Headless Playwright ready. Page loaded in 420ms (Title: "FastAPI Release Notes")',
        },
        {
          type: 'tasks',
          percent: 50,
          tasks: [
            { id: 1, status: 'done', text: 'Инициализация браузера с stealth-профилем' },
            { id: 2, status: 'active', text: 'Навигация и парсинг release notes FastAPI' },
            { id: 3, status: 'pending', text: 'Синтез изменений и запись в docs/fastapi_0115.md' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.write_file("docs/fastapi_0115.md", ...)',
          toolOutput: '✓ Created docs/fastapi_0115.md (Key changes: Pydantic V2 migration, async lifespan handlers)',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Инициализация браузера с stealth-профилем' },
            { id: 2, status: 'done', text: 'Навигация и парсинг release notes FastAPI' },
            { id: 3, status: 'done', text: 'Синтез изменений и запись в docs/fastapi_0115.md' },
          ],
        },
        {
          type: 'ai',
          content: 'Документация собрана и структурирована в docs/fastapi_0115.md. Описаны новые возможности async lifespan и Pydantic V2 интеграции.',
        },
      ],
    },
  ];

  const [activeScenarioId, setActiveScenarioId] = useState<string>('refactor');
  const [typedUser, setTypedUser] = useState<string>('');
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1);
  const [copied, setCopied] = useState<boolean>(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const scenario = scenarios.find((s) => s.id === activeScenarioId) || scenarios[0];

  // Reset and play on scenario change
  useEffect(() => {
    setCurrentStepIndex(0);
    setTypedUser('');

    let charIdx = 0;
    const prompt = scenario.userPrompt;
    const delay = 1000 / (speed * 40);

    const typeTimer = setInterval(() => {
      if (isPaused) return;
      charIdx++;
      setTypedUser(prompt.slice(0, charIdx));

      if (charIdx >= prompt.length) {
        clearInterval(typeTimer);

        // Advance steps
        let step = 0;
        const stepTimer = setInterval(() => {
          if (isPaused) return;
          step++;
          setCurrentStepIndex(step);

          if (step >= scenario.steps.length) {
            clearInterval(stepTimer);
          }
        }, 1000 / (speed * 2));
      }
    }, delay);

    return () => {
      clearInterval(typeTimer);
    };
  }, [activeScenarioId, speed]);

  // Auto-scroll inside terminal container only
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [typedUser, currentStepIndex]);

  const handleCopy = () => {
    navigator.clipboard.writeText(scenario.userPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReplay = () => {
    const current = activeScenarioId;
    setActiveScenarioId('');
    setTimeout(() => setActiveScenarioId(current), 10);
  };

  return (
    <section id="terminal" className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-3xl sm:text-4xl font-normal text-[#1F1F1F] tracking-tight mb-3">
            Real-Time Terminal Execution
          </h2>
          <p className="text-[#5F6368] text-base font-normal">
            Autonomous multi-task decomposition, live ConPTY terminal subprocesses, and WinRT clipboard integration.
          </p>
        </div>

        {/* Interactive Scenario Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isActive = activeScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                onClick={() => setActiveScenarioId(sc.id)}
                data-testid={`terminal-scenario-${sc.id}`}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#1F1F1F] text-white shadow-md scale-105'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#536DFE]' : 'text-slate-400'}`} />
                <span>{sc.label}</span>
              </button>
            );
          })}
        </div>

        {/* Compact Terminal Window with Independent Scroll */}
        <div className="max-w-3xl mx-auto w-full">
          <div className="rounded-2xl overflow-hidden bg-[#0A0D14] border border-slate-300 shadow-2xl flex flex-col">
            {/* Title Bar */}
            <div className="bg-[#121622] px-4 py-3 flex items-center justify-between border-b border-white/[0.08] select-none shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
              </div>

              <div className="text-[#536DFE] text-xs font-mono font-medium flex items-center gap-2 px-2 truncate">
                <TermIcon className="w-3.5 h-3.5 text-[#536DFE] shrink-0" />
                <span className="truncate">PS C:\Projects\DeepApp&gt; deepx</span>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1.5 sm:gap-2">
                <button
                  onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 3 : 1)}
                  className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 hover:bg-white/20 text-slate-300 transition-colors"
                  title="Playback Speed"
                >
                  {speed}x
                </button>
                <button
                  onClick={() => setIsPaused(!isPaused)}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title={isPaused ? 'Resume' : 'Pause'}
                >
                  {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={handleReplay}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Replay Scenario"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleCopy}
                  data-testid="terminal-copy-btn"
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Copy Prompt"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#27C93F]" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Terminal Body with Custom Scrollbar */}
            <div
              ref={scrollRef}
              data-testid="terminal-body"
              className="h-[480px] sm:h-[520px] overflow-y-auto p-4 sm:p-5 font-mono text-[11px] sm:text-xs leading-relaxed text-slate-300 space-y-4 select-text scroll-smooth"
            >
              {/* Authentic ASCII Banner */}
              <div className="p-3 rounded-xl bg-[#06080F] border border-[#536DFE]/40 text-center select-none shadow-sm">
                <pre className="text-[#536DFE] font-bold text-[8px] sm:text-[10px] leading-tight inline-block">
                  {ASCII_BANNER}
                </pre>
                <div className="mt-2 text-[10px] sm:text-xs text-slate-300 font-medium border-t border-white/[0.06] pt-1.5 flex flex-wrap items-center justify-center gap-x-3 gap-y-1">
                  <span>
                    Mode: <span className="text-[#38BDF8] font-bold">EXPERT</span>
                  </span>
                  <span>
                    Style: <span className="text-[#A78BFA] font-bold">CODER</span>
                  </span>
                  <span>
                    DeepThink: <span className="text-[#38BDF8] font-bold">ON</span>
                  </span>
                  <span>
                    Search: <span className="text-[#38BDF8] font-bold">ON</span>
                  </span>
                </div>
              </div>

              {/* User Input Line */}
              <div className="flex items-start text-white">
                <span className="text-[#536DFE] font-bold mr-2 select-none shrink-0">deepx&gt;</span>
                <span className="break-words">{typedUser}</span>
                {typedUser.length < scenario.userPrompt.length && (
                  <span className="w-2 h-4 bg-[#536DFE] ml-1 inline-block animate-pulse shrink-0" />
                )}
              </div>

              {/* Scenario Steps Stream */}
              <div className="space-y-3">
                {scenario.steps.slice(0, currentStepIndex).map((step, idx) => {
                  if (step.type === 'think') {
                    return (
                      <div key={idx} className="text-[#A78BFA] flex items-start gap-2 animate-in fade-in duration-200">
                        <span className="select-none">🤔</span>
                        <span>[DeepThink] {step.content}</span>
                      </div>
                    );
                  }

                  if (step.type === 'tasks' && step.tasks) {
                    const done = step.tasks.filter((t) => t.status === 'done').length;
                    const total = step.tasks.length;
                    const pct = step.percent || 0;
                    const filled = Math.round(pct / 5);
                    const empty = 20 - filled;

                    return (
                      <div
                        key={idx}
                        className="my-2 p-3 rounded-xl bg-[#06080F] border border-[#536DFE]/40 shadow-sm animate-in fade-in duration-200"
                      >
                        <div className="flex items-center justify-between text-xs font-semibold mb-2 pb-1.5 border-b border-white/[0.06]">
                          <span className="text-[#536DFE] font-bold tracking-wider">
                            TASKS {done}/{total}
                          </span>
                          <div className="flex items-center gap-2 font-mono text-[11px]">
                            <span className="text-[#536DFE]">{'━'.repeat(filled)}</span>
                            <span className="text-[#1E293B]">{'━'.repeat(empty)}</span>
                            <span className="text-[#536DFE] font-bold">{pct}%</span>
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          {step.tasks.map((task) => (
                            <div key={task.id} className="flex items-start gap-2 text-xs">
                              <span className="text-slate-500 font-mono w-3 shrink-0">{task.id}</span>
                              {task.status === 'done' ? (
                                <span className="text-[#34A853] font-bold shrink-0">[✓]</span>
                              ) : task.status === 'active' ? (
                                <span className="text-[#FDE68A] font-bold shrink-0 animate-pulse">[▶]</span>
                              ) : (
                                <span className="text-slate-600 shrink-0">[ ]</span>
                              )}
                              <span
                                className={
                                  task.status === 'done'
                                    ? 'text-slate-400 line-through'
                                    : task.status === 'active'
                                    ? 'text-[#FDE68A] font-medium'
                                    : 'text-slate-300'
                                }
                              >
                                {task.text}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }

                  if (step.type === 'tool') {
                    return (
                      <div key={idx} className="space-y-1 text-xs animate-in fade-in duration-150">
                        <div className="text-[#38BDF8] flex items-center gap-1.5">
                          <span>⚙</span>
                          <span>{step.toolName}</span>
                        </div>
                        {step.toolOutput && (
                          <div className="text-slate-400 pl-4 border-l border-[#536DFE]/30 text-[11px] whitespace-pre-wrap">
                            {step.toolOutput}
                          </div>
                        )}
                      </div>
                    );
                  }

                  if (step.type === 'code' && step.code) {
                    return (
                      <div
                        key={idx}
                        className="rounded-lg bg-[#06080F] border border-white/[0.08] p-3 font-mono text-[11px] overflow-x-auto text-slate-200 animate-in fade-in"
                      >
                        <div className="text-slate-500 text-[10px] mb-1.5 pb-1 border-b border-white/[0.06] flex items-center justify-between">
                          <span>┌── {step.lang} ─────────────────────────────────</span>
                        </div>
                        <pre className="text-[#38BDF8] leading-relaxed whitespace-pre-wrap">{step.code}</pre>
                      </div>
                    );
                  }

                  if (step.type === 'output' && step.content) {
                    return (
                      <div
                        key={idx}
                        className="rounded-lg bg-[#06080F] p-2.5 text-[11px] border-l-2 border-[#536DFE] text-slate-300 font-mono whitespace-pre-wrap animate-in fade-in"
                      >
                        {step.content}
                      </div>
                    );
                  }

                  if (step.type === 'ai') {
                    return (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-[#536DFE]/10 border border-[#536DFE]/30 text-xs sm:text-sm animate-in fade-in duration-200"
                      >
                        <div className="font-bold text-[#536DFE] mb-1 flex items-center gap-1.5">
                          <span>DeepX:</span>
                        </div>
                        <p className="leading-relaxed text-slate-200">{step.content}</p>
                      </div>
                    );
                  }

                  return null;
                })}
              </div>

              {/* Ready prompt cursor */}
              {currentStepIndex >= scenario.steps.length && (
                <div className="flex items-center text-white pt-2 animate-in fade-in">
                  <span className="text-[#536DFE] font-bold mr-2 select-none shrink-0">deepx&gt;</span>
                  <span className="w-2 h-4 bg-[#536DFE] inline-block animate-pulse" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
