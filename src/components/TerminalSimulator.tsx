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
  Database,
  GitMerge
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
  duration?: number;
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
      label: 'Full-Stack Refactor & Testing',
      icon: Layers,
      userPrompt: 'Сделай рефакторинг auth.py, добавь JWT валидацию и прогони pytest в ConPTY',
      steps: [
        { type: 'think', content: 'DeepThink Engine: анализирую auth.py, зависимости и pytest-окружение. Формирую план...', duration: 1800 },
        {
          type: 'tasks',
          percent: 0,
          duration: 1000,
          tasks: [
            { id: 1, status: 'active', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'pending', text: 'Генерация JWT encoder/decoder с exp' },
            { id: 3, status: 'pending', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        { type: 'tool', toolName: 'filesystem.read_file("src/auth.py")', toolOutput: '✓ Read 48 lines (Legacy plaintext session tokens detected)', duration: 1200 },
        { type: 'think', content: 'Обнаружен plaintext token, заменяю на jose.jwt реализацию.', duration: 1200 },
        {
          type: 'tasks',
          percent: 25,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'active', text: 'Генерация JWT encoder/decoder с exp' },
            { id: 3, status: 'pending', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        { type: 'tool', toolName: 'filesystem.write_file("src/auth.py", ...)', duration: 1500 },
        {
          type: 'code',
          lang: 'python',
          duration: 2000,
          code: `from jose import jwt, JWTError\nfrom datetime import datetime, timedelta\n\nSECRET_KEY = "deepx-token"\nALGORITHM = "HS256"\n\ndef create_access_token(data: dict, expires: timedelta = None) -> str:\n    to_encode = data.copy()\n    expire = datetime.utcnow() + (expires or timedelta(hours=12))\n    to_encode.update({"exp": expire})\n    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)`
        },
        {
          type: 'tasks',
          percent: 50,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с exp' },
            { id: 3, status: 'active', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'pending', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        { type: 'tool', toolName: 'filesystem.replace_file_content("src/middleware.py", ...)', toolOutput: '✓ Injected JWT header verification and HTTP 401 Unauthorized guard', duration: 1500 },
        {
          type: 'tasks',
          percent: 75,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с exp' },
            { id: 3, status: 'done', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'active', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        { type: 'tool', toolName: 'terminal.run_in_terminal("pytest tests/test_auth.py -v")', duration: 2500, toolOutput: 'rootdir: C:\\Projects\\AuthAPI, configfile: pytest.ini\n✓ tests/test_auth.py::test_create_jwt PASSED        [ 25%]\n✓ tests/test_auth.py::test_verify_valid_token PASSED   [ 50%]\n✓ tests/test_auth.py::test_expired_token PASSED        [ 75%]\n✓ tests/test_auth.py::test_middleware_guard PASSED     [100%]\n══════════════════════ 4 passed in 0.32s ═════════════════════' },
        {
          type: 'tasks',
          percent: 100,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ зависимостей и устаревшей логики auth.py' },
            { id: 2, status: 'done', text: 'Генерация JWT encoder/decoder с exp' },
            { id: 3, status: 'done', text: 'Добавление FastAPI AuthBearer middleware' },
            { id: 4, status: 'done', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        { type: 'ai', content: 'Рефакторинг auth.py завершён. Добавлена строгая JWT валидация с проверкой времени жизни токена и middleware. Все 4 теста pytest пройдены успешно.' },
      ],
    },
    {
      id: 'clipboard',
      label: 'Clipboard Vision Analysis',
      icon: Clipboard,
      userPrompt: 'Посмотри скриншот ошибки в буфере обмена (Win+V), найди причину и закоммить фикс',
      steps: [
        { type: 'think', content: 'DeepThink Engine: обращаюсь к Windows.ApplicationModel.DataTransfer.Clipboard API...', duration: 1500 },
        {
          type: 'tasks',
          percent: 0,
          duration: 1000,
          tasks: [
            { id: 1, status: 'active', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'pending', text: 'Vision-анализ трассировки стека и поиск файла' },
            { id: 3, status: 'pending', text: 'Исправление NullReferenceException' },
            { id: 4, status: 'pending', text: 'Создание Git коммита с фиксом' },
          ],
        },
        { type: 'tool', toolName: 'clipboard.get_clipboard_image()', toolOutput: '✓ Captured active clipboard bitmap (1920x1080, 2.4 MB, Format: CF_DIBV5)', duration: 1400 },
        { type: 'think', content: 'Изображение успешно получено. Отправляю в Vision Engine для OCR-анализа стека вызовов.', duration: 1800 },
        {
          type: 'tasks',
          percent: 25,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'active', text: 'Vision-анализ трассировки стека и поиск файла' },
            { id: 3, status: 'pending', text: 'Исправление NullReferenceException' },
            { id: 4, status: 'pending', text: 'Создание Git коммита с фиксом' },
          ],
        },
        { type: 'output', content: '👁 Vision Engine: обнаружена ошибка NullReferenceException в UserService.cs:92 (свойство profile.Settings равно null)', duration: 2500 },
        {
          type: 'tasks',
          percent: 50,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и поиск файла' },
            { id: 3, status: 'active', text: 'Исправление NullReferenceException' },
            { id: 4, status: 'pending', text: 'Создание Git коммита с фиксом' },
          ],
        },
        { type: 'tool', toolName: 'filesystem.replace_file_content("Services/UserService.cs", ...)', toolOutput: '✓ Added null-conditional coalescing: user?.Profile?.Settings ?? DefaultSettings', duration: 1500 },
        {
          type: 'tasks',
          percent: 75,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и поиск файла' },
            { id: 3, status: 'done', text: 'Исправление NullReferenceException' },
            { id: 4, status: 'active', text: 'Создание Git коммита с фиксом' },
          ],
        },
        { type: 'tool', toolName: 'terminal.run_in_terminal("git commit -am \\"fix(user): safeguard profile null reference\\"")', toolOutput: '[main 9cf3a1e] fix(user): safeguard profile null reference\n 1 file changed, 4 insertions(+), 1 deletion(-)', duration: 2000 },
        {
          type: 'tasks',
          percent: 100,
          duration: 800,
          tasks: [
            { id: 1, status: 'done', text: 'Чтение bitmap буфера через WinRT Clipboard API' },
            { id: 2, status: 'done', text: 'Vision-анализ трассировки стека и поиск файла' },
            { id: 3, status: 'done', text: 'Исправление NullReferenceException' },
            { id: 4, status: 'done', text: 'Создание Git коммита с фиксом' },
          ],
        },
        { type: 'ai', content: 'Скриншот из буфера успешно обработан. В UserService.cs добавлен безопасный null-check и создан коммит 9cf3a1e.' },
      ],
    },
    {
      id: 'docker',
      label: 'Docker Crash Debugging',
      icon: Database,
      userPrompt: 'Почини докер-компоуз, контейнер db падает с exit code 137',
      steps: [
        { type: 'think', content: 'DeepThink Engine: Exit code 137 означает OOM (Out Of Memory). Анализирую docker-compose.yml и логи контейнера db...', duration: 2000 },
        { type: 'tool', toolName: 'terminal.run_in_terminal("docker compose logs --tail=50 db")', toolOutput: '... \nFATAL ERROR: cannot allocate memory for shared pool\nOut of Memory: Killed process 1 (postgres)', duration: 2200 },
        { type: 'tool', toolName: 'filesystem.read_file("docker-compose.yml")', toolOutput: '✓ Read 32 lines. Service "db" has memory_limit: 128m', duration: 1000 },
        { type: 'think', content: 'PostgreSQL требует больше памяти, 128m слишком мало для инициализации. Увеличиваю лимит и перезапускаю.', duration: 1500 },
        { type: 'code', lang: 'yaml', duration: 1500, code: `  db:\n    image: postgres:15-alpine\n    environment:\n      POSTGRES_PASSWORD: secret\n    deploy:\n      resources:\n        limits:\n          memory: 512M  # Increased from 128m\n    ports:\n      - "5432:5432"` },
        { type: 'tool', toolName: 'filesystem.replace_file_content("docker-compose.yml", ...)', toolOutput: '✓ Memory limit updated to 512M', duration: 1200 },
        { type: 'tool', toolName: 'terminal.run_in_terminal("docker compose up -d db")', toolOutput: 'Recreating db ... done\nAttaching to db\ndb  | PostgreSQL init process complete; ready for start up.', duration: 3000 },
        { type: 'ai', content: 'Контейнер БД падал из-за нехватки памяти (OOM Killed). Я увеличил лимит памяти для PostgreSQL с 128M до 512M в docker-compose.yml и успешно перезапустил контейнер.' },
      ],
    },
    {
      id: 'git-merge',
      label: 'Conflict Auto-Resolution',
      icon: GitMerge,
      userPrompt: 'Разреши git conflict в файле src/router.tsx, аккуратно совмести изменения из обеих веток',
      steps: [
        { type: 'think', content: 'DeepThink Engine: анализирую Git status и маркеры конфликта в src/router.tsx...', duration: 1500 },
        { type: 'tool', toolName: 'terminal.run_in_terminal("git status")', toolOutput: 'Unmerged paths:\n  (use "git add <file>..." to mark resolution)\n\tboth modified:   src/router.tsx', duration: 1200 },
        { type: 'tool', toolName: 'filesystem.read_file("src/router.tsx")', toolOutput: '✓ Found conflict markers (<<<<<<< HEAD ... ======= ... >>>>>>> feature/auth)', duration: 1000 },
        { type: 'think', content: 'В HEAD добавлены новые роуты Dashboard и Settings. В feature/auth добавлен Middleware-обёртка <ProtectedRoute>. Совмещаю AST деревья React...', duration: 2500 },
        { type: 'code', lang: 'tsx', duration: 2200, code: `// Resolved Conflict:\n<BrowserRouter>\n  <Routes>\n    <Route path="/" element={<Home />} />\n    {/* From feature/auth branch */}\n    <Route element={<ProtectedRoute />}>\n      {/* From HEAD branch */}\n      <Route path="/dashboard" element={<Dashboard />} />\n      <Route path="/settings" element={<Settings />} />\n    </Route>\n  </Routes>\n</BrowserRouter>` },
        { type: 'tool', toolName: 'filesystem.write_file("src/router.tsx", ...)', toolOutput: '✓ Conflict resolved and written cleanly', duration: 1200 },
        { type: 'tool', toolName: 'terminal.run_in_terminal("git add src/router.tsx && git commit -m \\"chore: resolve merge conflict in router\\"")', toolOutput: '[feature/auth 2b8e11a] chore: resolve merge conflict in router', duration: 1800 },
        { type: 'ai', content: 'Конфликт разрешён! Я обернул добавленные вами новые роуты (Dashboard, Settings) в компонент ProtectedRoute из ветки feature/auth, сохранив изменения обеих сторон. Коммит слияния создан.' },
      ],
    },
    {
      id: 'daemon',
      label: 'Background Process Monitoring',
      icon: Cpu,
      userPrompt: 'Запусти сервер приложения в фоне, отправь проверочный payload и убедись в 200 OK',
      steps: [
        { type: 'think', content: 'DeepThink Engine: создаю изолированную Windows ConPTY сессию для фонового сервера...', duration: 1500 },
        { type: 'tool', toolName: 'terminal.spawn_background_process("uvicorn app:main --port 8000")', toolOutput: '✓ Background Task [task-1082] spawned. Monitoring ConPTY pipe stream...', duration: 1200 },
        { type: 'output', content: 'INFO: Started server process [PID 14208]\nINFO: Waiting for application startup.\nINFO: Application startup complete. Uvicorn running on http://127.0.0.1:8000', duration: 2500 },
        { type: 'tool', toolName: 'web.http_request("POST", "http://127.0.0.1:8000/healthcheck")', toolOutput: '✓ Response 200 OK {"status": "healthy", "latency_ms": 1.2, "db": "connected"}', duration: 1500 },
        { type: 'ai', content: 'Фоновый сервер отработал штатно, эндпоинт /healthcheck вернул 200 OK (1.2ms). Сессия ConPTY корректно закрыта без утечек дескрипторов.' },
      ],
    },
    {
      id: 'browser',
      label: 'Headless Stealth OSINT',
      icon: Globe,
      userPrompt: 'Собери документацию по FastAPI 0.115 и сохрани выжимку в docs.md',
      steps: [
        { type: 'think', content: 'DeepThink Engine: инициализирую Playwright со стелс-профилем для обхода Cloudflare защиты...', duration: 1800 },
        { type: 'tool', toolName: 'browser.navigate("https://fastapi.tiangolo.com/release-notes/")', toolOutput: '✓ Headless Playwright ready. Page loaded in 420ms (Title: "FastAPI Release Notes")', duration: 2000 },
        { type: 'tool', toolName: 'filesystem.write_file("docs/fastapi_0115.md", ...)', toolOutput: '✓ Created docs/fastapi_0115.md (Key changes: Pydantic V2 migration, async lifespan handlers)', duration: 1500 },
        { type: 'ai', content: 'Документация собрана и структурирована в docs/fastapi_0115.md. Описаны новые возможности async lifespan и Pydantic V2 интеграции.' },
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

  // Random typing effect for user prompt
  useEffect(() => {
    setTypedUser('');
    setCurrentStepIndex(0);
  }, [activeScenarioId]);

  useEffect(() => {
    if (isPaused || typedUser.length >= scenario.userPrompt.length) return;

    // Faster typing speed, realistically random (20-60ms per character)
    const baseDelay = Math.random() * 40 + 20;
    const timer = setTimeout(() => {
      setTypedUser(scenario.userPrompt.slice(0, typedUser.length + 1));
    }, baseDelay / speed);

    return () => clearTimeout(timer);
  }, [typedUser, isPaused, scenario, speed]);

  // Intelligent step advancement based on step type durations
  useEffect(() => {
    // Only start advancing steps if typing is complete
    if (isPaused || currentStepIndex >= scenario.steps.length || typedUser.length < scenario.userPrompt.length) return;

    const currentStep = scenario.steps[currentStepIndex];
    
    // Default fallback durations if not specified
    let baseDelay = 1000;
    if (currentStep.type === 'think') baseDelay = 1800;
    else if (currentStep.type === 'tasks') baseDelay = 1000;
    else if (currentStep.type === 'tool') baseDelay = 1500;
    else if (currentStep.type === 'code') baseDelay = 2000;
    else if (currentStep.type === 'output') baseDelay = 1500;
    else if (currentStep.type === 'ai') baseDelay = 2500;

    if (currentStep.duration) {
      baseDelay = currentStep.duration;
    }

    const actualDelay = baseDelay / speed;

    const timer = setTimeout(() => {
      setCurrentStepIndex((prev) => prev + 1);
    }, actualDelay);

    return () => clearTimeout(timer);
  }, [currentStepIndex, isPaused, typedUser, scenario, speed]);

  // Smooth Auto-scroll (jsdom compatible)
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
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl sm:text-4xl font-normal text-[#1F1F1F] tracking-tight mb-4">
            Real-Time Terminal Execution
          </h2>
          <p className="text-[#5F6368] text-base sm:text-lg font-normal">
            Autonomous multi-task decomposition, live ConPTY terminal subprocesses, WinRT clipboard integration, and complex Git operations.
          </p>
        </div>

        {/* Interactive Scenario Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-4xl mx-auto">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isActive = activeScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                onClick={() => setActiveScenarioId(sc.id)}
                data-testid={`terminal-scenario-${sc.id}`}
                className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-full text-xs sm:text-sm font-medium transition-all ${
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
        <div className="max-w-[800px] mx-auto w-full transition-all duration-300">
          <div className="rounded-2xl overflow-hidden bg-[#0A0D14] border border-slate-300 shadow-2xl flex flex-col transition-all duration-500">
            {/* Title Bar */}
            <div className="bg-[#121622] px-4 py-3 flex items-center justify-between border-b border-white/[0.08] select-none shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56] hover:bg-[#ff4e45] transition-colors" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E] hover:bg-[#ffb00f] transition-colors" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F] hover:bg-[#1fb835] transition-colors" />
              </div>

              <div className="text-[#536DFE] text-xs font-mono font-medium flex items-center gap-2 px-2 truncate cursor-default">
                <TermIcon className="w-3.5 h-3.5 text-[#536DFE] shrink-0" />
                <span className="truncate opacity-80 hover:opacity-100 transition-opacity">PS C:\Projects\DeepApp&gt; deepx</span>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1 sm:gap-2">
                <button
                  onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 3 : 1)}
                  className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 hover:bg-white/20 text-slate-300 transition-colors"
                  title="Playback Speed"
                >
                  {speed}x
                </button>
                <button
                  onClick={() => setIsPaused(!isPaused)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title={isPaused ? 'Resume' : 'Pause'}
                >
                  {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={handleReplay}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Replay Scenario"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleCopy}
                  data-testid="terminal-copy-btn"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors relative"
                  title="Copy Prompt"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#27C93F]" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied && (
                    <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#27C93F] text-black text-[10px] font-bold px-2 py-1 rounded animate-in fade-in slide-in-from-bottom-2">
                      Copied!
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Terminal Body with Custom Scrollbar */}
            <div
              ref={scrollRef}
              data-testid="terminal-body"
              className="h-[480px] sm:h-[560px] overflow-y-auto p-4 sm:p-6 font-mono text-[11px] sm:text-xs leading-relaxed text-slate-300 space-y-4 select-text custom-scrollbar scroll-smooth bg-[#0A0D14]"
            >
              {/* Authentic ASCII Banner */}
              <div className="p-4 rounded-xl bg-[#06080F] border border-[#536DFE]/30 text-center select-none shadow-lg mb-6">
                <pre className="text-[#536DFE] font-bold text-[8px] sm:text-[10px] leading-tight inline-block opacity-90 drop-shadow-[0_0_8px_rgba(83,109,254,0.3)]">
                  {ASCII_BANNER}
                </pre>
                <div className="mt-3 text-[10px] sm:text-[11px] text-slate-300 font-medium border-t border-white/[0.06] pt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#38BDF8] animate-pulse" />
                    Mode: <span className="text-[#38BDF8] font-bold">EXPERT</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#A78BFA]" />
                    Style: <span className="text-[#A78BFA] font-bold">CODER</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#34A853]" />
                    DeepThink: <span className="text-[#34A853] font-bold">ON</span>
                  </span>
                </div>
              </div>

              {/* User Input Line */}
              <div className="flex items-start text-white bg-white/[0.02] p-2 rounded-lg border border-white/[0.05]">
                <span className="text-[#536DFE] font-bold mr-2 select-none shrink-0">deepx&gt;</span>
                <span className="break-words font-medium">{typedUser}</span>
                {typedUser.length < scenario.userPrompt.length && (
                  <span className="w-2 h-4 bg-[#536DFE] ml-1 inline-block animate-pulse shrink-0 translate-y-0.5" />
                )}
              </div>

              {/* Scenario Steps Stream */}
              <div className="space-y-4">
                {scenario.steps.slice(0, currentStepIndex).map((step, idx) => {
                  if (step.type === 'think') {
                    return (
                      <div key={idx} className="text-[#A78BFA] flex items-start gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <span className="select-none text-sm opacity-80">🤔</span>
                        <span className="leading-relaxed"><strong className="opacity-70 font-normal">[DeepThink]</strong> {step.content}</span>
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
                        className="my-3 p-4 rounded-xl bg-gradient-to-b from-[#06080F] to-[#0A0D14] border border-[#536DFE]/40 shadow-lg animate-in fade-in slide-in-from-bottom-2 duration-300"
                      >
                        <div className="flex items-center justify-between text-xs font-semibold mb-3 pb-2 border-b border-white/[0.08]">
                          <span className="text-[#536DFE] font-bold tracking-wider flex items-center gap-1.5">
                            <Layers className="w-3.5 h-3.5" />
                            TASKS {done}/{total}
                          </span>
                          <div className="flex items-center gap-2 font-mono text-[11px] bg-black/40 px-2 py-1 rounded-md border border-white/5">
                            <span className="text-[#536DFE] tracking-tighter">{'━'.repeat(filled)}</span>
                            <span className="text-[#1E293B] tracking-tighter">{'━'.repeat(empty)}</span>
                            <span className="text-[#536DFE] font-bold ml-1 w-8 text-right">{pct}%</span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          {step.tasks.map((task) => (
                            <div key={task.id} className="flex items-start gap-2.5 text-xs">
                              <span className="text-slate-600 font-mono w-4 shrink-0 text-right">{task.id}.</span>
                              {task.status === 'done' ? (
                                <span className="text-[#34A853] font-bold shrink-0">[✓]</span>
                              ) : task.status === 'active' ? (
                                <span className="text-[#FDE68A] font-bold shrink-0 animate-pulse drop-shadow-[0_0_4px_rgba(253,230,138,0.5)]">[▶]</span>
                              ) : (
                                <span className="text-slate-600 shrink-0">[ ]</span>
                              )}
                              <span
                                className={`transition-colors duration-300 ${
                                  task.status === 'done'
                                    ? 'text-slate-500 line-through decoration-slate-600'
                                    : task.status === 'active'
                                    ? 'text-[#FDE68A] font-medium'
                                    : 'text-slate-400'
                                }`}
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
                      <div key={idx} className="space-y-1.5 text-xs animate-in fade-in slide-in-from-left-2 duration-300">
                        <div className="text-[#38BDF8] flex items-center gap-2 font-medium bg-[#38BDF8]/10 w-fit px-2 py-1 rounded border border-[#38BDF8]/20">
                          <span className="animate-spin-slow">⚙</span>
                          <span>{step.toolName}</span>
                        </div>
                        {step.toolOutput && (
                          <div className="text-slate-400 pl-4 py-1 border-l-2 border-[#536DFE]/40 text-[11px] whitespace-pre-wrap ml-2">
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
                        className="rounded-xl bg-[#030408] border border-white/[0.1] font-mono text-[11px] overflow-hidden text-slate-200 animate-in fade-in zoom-in-95 duration-400 shadow-xl my-2"
                      >
                        <div className="bg-[#121622] px-3 py-1.5 border-b border-white/[0.08] flex items-center justify-between">
                          <span className="text-slate-400 font-semibold uppercase tracking-wider text-[9px]">{step.lang}</span>
                          <div className="flex gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-white/10" />
                            <span className="w-2 h-2 rounded-full bg-white/10" />
                          </div>
                        </div>
                        <pre className="p-4 overflow-x-auto">
                          <code className="text-[#38BDF8] leading-relaxed whitespace-pre-wrap">
                            {/* Simple syntax highlighting mock for visuals */}
                            {step.code.split('\n').map((line, i) => (
                              <div key={i} className="table-row">
                                <span className="table-cell text-right pr-4 text-slate-600 select-none">{i + 1}</span>
                                <span className="table-cell" dangerouslySetInnerHTML={{
                                  __html: line
                                    .replace(/([A-Z_]+)(?=\s*=)/g, '<span class="text-[#A78BFA]">$1</span>') // constants
                                    .replace(/(def|from|import|return)\b/g, '<span class="text-[#F97316]">$1</span>') // keywords
                                    .replace(/(".*?")/g, '<span class="text-[#34A853]">$1</span>') // strings
                                    .replace(/(\/\/.*|#.*)/g, '<span class="text-slate-500 italic">$1</span>') // comments
                                    .replace(/(&lt;[a-zA-Z0-9]+.*?&gt;|&lt;\/[a-zA-Z0-9]+&gt;)/g, '<span class="text-[#536DFE]">$1</span>') // JSX tags
                                }}></span>
                              </div>
                            ))}
                          </code>
                        </pre>
                      </div>
                    );
                  }

                  if (step.type === 'output' && step.content) {
                    return (
                      <div
                        key={idx}
                        className="rounded-lg bg-black/40 p-3 text-[11px] border-l-2 border-[#536DFE] text-slate-300 font-mono whitespace-pre-wrap animate-in fade-in slide-in-from-bottom-1"
                      >
                        {step.content}
                      </div>
                    );
                  }

                  if (step.type === 'ai') {
                    return (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-gradient-to-r from-[#536DFE]/10 to-transparent border border-[#536DFE]/30 text-xs sm:text-sm animate-in fade-in slide-in-from-bottom-2 duration-500 shadow-[inset_0_0_20px_rgba(83,109,254,0.05)]"
                      >
                        <div className="font-bold text-[#536DFE] mb-1.5 flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#536DFE] animate-pulse" />
                          DeepX:
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
                <div className="flex items-center text-white pt-4 animate-in fade-in duration-1000">
                  <span className="text-[#536DFE] font-bold mr-2 select-none shrink-0">deepx&gt;</span>
                  <span className="w-2 h-4 bg-[#536DFE] inline-block animate-pulse shadow-[0_0_8px_rgba(83,109,254,0.6)]" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
