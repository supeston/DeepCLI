import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TermIcon, Copy, Check, RotateCcw, Play, Pause } from 'lucide-react';

interface TaskItem {
  id: number;
  status: 'pending' | 'active' | 'done';
  text: string;
}

const ASCII_BANNER = `\
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝`;

export const TerminalSimulator: React.FC = () => {
  const [phase, setPhase] = useState<number>(0);
  const [userTyped, setUserTyped] = useState<string>('');
  const [thinkText, setThinkText] = useState<string>('');
  const [codeText, setCodeText] = useState<string>('');
  const [aiText, setAiText] = useState<string>('');
  const [tasks, setTasks] = useState<TaskItem[]>([
    { id: 1, status: 'pending', text: 'Анализ архитектуры auth.py и моделей пользователей' },
    { id: 2, status: 'pending', text: 'Реализация JWT валидации и middleware защиты' },
    { id: 3, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
  ]);
  const [taskPercent, setTaskPercent] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1);
  const [copied, setCopied] = useState<boolean>(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const userPrompt = 'Сделай рефакторинг auth.py, внедри строгую JWT валидацию и прогони pytest в ConPTY';
  const fullThink = 'Анализирую зависимости jose, datetime и fastapi. Формирую план задач...';
  const fullCode = `from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "deepx-super-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid or expired authentication token")`;
  const fullAi =
    'Рефакторинг auth.py успешно завершён. Добавлена JWT кодировка/декодировка токенов с проверкой exp-таймаута. Все 4 теста pytest выполнены со статусом PASSED (0.24s).';

  // Auto-scroll to bottom as output grows
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [userTyped, thinkText, codeText, aiText, phase]);

  // Main simulation lifecycle
  useEffect(() => {
    if (isPaused) return;

    const delay = (ms: number) => 1000 / (speed * (1000 / ms));

    // Phase 0: Start typing user prompt
    if (phase === 0) {
      if (userTyped.length < userPrompt.length) {
        const timer = setTimeout(() => {
          setUserTyped(userPrompt.slice(0, userTyped.length + 1));
        }, delay(30));
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setPhase(1), delay(400));
        return () => clearTimeout(timer);
      }
    }

    // Phase 1: Stream Think tokens
    if (phase === 1) {
      if (thinkText.length < fullThink.length) {
        const timer = setTimeout(() => {
          setThinkText(fullThink.slice(0, thinkText.length + 2));
        }, delay(25));
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setPhase(2), delay(400));
        return () => clearTimeout(timer);
      }
    }

    // Phase 2: Tasks created 0% -> tool read_file
    if (phase === 2) {
      const timer = setTimeout(() => setPhase(3), delay(700));
      return () => clearTimeout(timer);
    }

    // Phase 3: Task 1 done (33%) -> streaming code into write_file
    if (phase === 3) {
      setTasks([
        { id: 1, status: 'done', text: 'Анализ архитектуры auth.py и моделей пользователей' },
        { id: 2, status: 'active', text: 'Реализация JWT валидации и middleware защиты' },
        { id: 3, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
      ]);
      setTaskPercent(33);

      if (codeText.length < fullCode.length) {
        const timer = setTimeout(() => {
          setCodeText(fullCode.slice(0, codeText.length + 6));
        }, delay(20));
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setPhase(4), delay(600));
        return () => clearTimeout(timer);
      }
    }

    // Phase 4: Task 2 done (66%) -> run pytest in ConPTY
    if (phase === 4) {
      setTasks([
        { id: 1, status: 'done', text: 'Анализ архитектуры auth.py и моделей пользователей' },
        { id: 2, status: 'done', text: 'Реализация JWT валидации и middleware защиты' },
        { id: 3, status: 'active', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
      ]);
      setTaskPercent(66);
      const timer = setTimeout(() => setPhase(5), delay(900));
      return () => clearTimeout(timer);
    }

    // Phase 5: Task 3 done (100%) -> Stream final response
    if (phase === 5) {
      setTasks([
        { id: 1, status: 'done', text: 'Анализ архитектуры auth.py и моделей пользователей' },
        { id: 2, status: 'done', text: 'Реализация JWT валидации и middleware защиты' },
        { id: 3, status: 'done', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
      ]);
      setTaskPercent(100);

      if (aiText.length < fullAi.length) {
        const timer = setTimeout(() => {
          setAiText(fullAi.slice(0, aiText.length + 3));
        }, delay(25));
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setPhase(6), delay(3000));
        return () => clearTimeout(timer);
      }
    }

    // Phase 6: Completed state. Auto restart after 8s if not paused
    if (phase === 6) {
      const timer = setTimeout(() => {
        handleRestart();
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [phase, userTyped, thinkText, codeText, aiText, isPaused, speed]);

  const handleRestart = () => {
    setPhase(0);
    setUserTyped('');
    setThinkText('');
    setCodeText('');
    setAiText('');
    setTaskPercent(0);
    setTasks([
      { id: 1, status: 'pending', text: 'Анализ архитектуры auth.py и моделей пользователей' },
      { id: 2, status: 'pending', text: 'Реализация JWT валидации и middleware защиты' },
      { id: 3, status: 'pending', text: 'Запуск и верификация pytest test_auth.py в ConPTY' },
    ]);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(userPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const doneCount = tasks.filter((t) => t.status === 'done').length;
  const filledBars = Math.round(taskPercent / 5);
  const emptyBars = 20 - filledBars;

  return (
    <section id="terminal" className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl sm:text-4xl font-normal text-[#1F1F1F] tracking-tight mb-3">
            Live Interactive Agent
          </h2>
          <p className="text-[#5F6368] text-base font-normal">
            Autonomous multi-step reasoning, real ConPTY terminal subprocesses, and streaming Rich UI.
          </p>
        </div>

        {/* Compact Terminal Container (Not Overstretched) */}
        <div className="max-w-3xl mx-auto w-full">
          {/* Terminal Window */}
          <div className="rounded-2xl overflow-hidden bg-[#0A0D14] border border-slate-300 shadow-2xl transition-all duration-300 flex flex-col">
            {/* Window Title Bar */}
            <div className="bg-[#121622] px-4 py-3 flex items-center justify-between border-b border-white/[0.08] select-none shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
              </div>

              <div className="text-[#536DFE] text-xs font-mono font-medium flex items-center gap-2 truncate px-2">
                <TermIcon className="w-3.5 h-3.5 text-[#536DFE] shrink-0" />
                <span className="truncate">PS C:\Projects\MyAPI&gt; deepx</span>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1.5 sm:gap-2">
                <button
                  onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 3 : 1)}
                  className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 hover:bg-white/20 text-slate-300 transition-colors"
                  title="Toggle playback speed"
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
                  onClick={handleRestart}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Replay from start"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleCopy}
                  data-testid="terminal-copy-btn"
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Copy user command"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#27C93F]" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Scrollable Terminal Screen (Fixed height + own internal scrollbar) */}
            <div
              ref={scrollRef}
              data-testid="terminal-body"
              className="h-[460px] sm:h-[500px] overflow-y-auto p-4 sm:p-5 font-mono text-[11px] sm:text-xs leading-relaxed text-slate-300 space-y-4 select-text scroll-smooth"
            >
              {/* Authentic DeepCLI ASCII Banner */}
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

              {/* User Prompt (Real time typing) */}
              <div className="flex items-start text-white">
                <span className="text-[#536DFE] font-bold mr-2 select-none shrink-0">deepx&gt;</span>
                <span className="break-words">{userTyped}</span>
                {phase === 0 && <span className="w-2 h-4 bg-[#536DFE] ml-1 inline-block animate-pulse shrink-0" />}
              </div>

              {/* Phase 1+: DeepThink Thinking stream */}
              {phase >= 1 && (
                <div className="text-[#A78BFA] flex items-start gap-2 animate-in fade-in duration-200">
                  <span className="select-none">🤔</span>
                  <span>
                    [DeepThink] {thinkText}
                    {phase === 1 && <span className="w-1.5 h-3 bg-[#A78BFA] ml-1 inline-block animate-pulse" />}
                  </span>
                </div>
              )}

              {/* Phase 2+: Rich TASKS List */}
              {phase >= 2 && (
                <div className="my-2 p-3 rounded-xl bg-[#06080F] border border-[#536DFE]/40 shadow-sm animate-in fade-in duration-200">
                  <div className="flex items-center justify-between text-xs font-semibold mb-2 pb-1.5 border-b border-white/[0.06]">
                    <span className="text-[#536DFE] font-bold tracking-wider">
                      TASKS {doneCount}/3
                    </span>
                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      <span className="text-[#536DFE]">{'━'.repeat(filledBars)}</span>
                      <span className="text-[#1E293B]">{'━'.repeat(emptyBars)}</span>
                      <span className="text-[#536DFE] font-bold">{taskPercent}%</span>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    {tasks.map((task) => (
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
              )}

              {/* Phase 2+: Tool 1 (read_file) */}
              {phase >= 2 && (
                <div className="space-y-1 text-xs animate-in fade-in duration-150">
                  <div className="text-[#38BDF8] flex items-center gap-1.5">
                    <span>⚙</span>
                    <span>filesystem.read_file("src/auth.py")</span>
                  </div>
                  <div className="text-slate-400 pl-4 border-l border-[#536DFE]/30 text-[11px]">
                    ✓ Read 42 lines from src/auth.py (Detected legacy basic auth)
                  </div>
                </div>
              )}

              {/* Phase 3+: Tool 2 (write_file with streaming code) */}
              {phase >= 3 && (
                <div className="space-y-1.5 text-xs animate-in fade-in duration-150">
                  <div className="text-[#38BDF8] flex items-center gap-1.5">
                    <span>⚙</span>
                    <span>filesystem.write_file("src/auth.py", ...)</span>
                  </div>
                  {/* Rich-styled Code Block Box */}
                  <div className="rounded-lg bg-[#06080F] border border-white/[0.08] p-3 font-mono text-[11px] overflow-x-auto text-slate-200">
                    <div className="text-slate-500 text-[10px] mb-1.5 pb-1 border-b border-white/[0.06] flex items-center justify-between">
                      <span>┌── python ─────────────────────────────────</span>
                      <span className="text-slate-400">src/auth.py</span>
                    </div>
                    <pre className="text-[#38BDF8] leading-relaxed whitespace-pre-wrap">
                      {codeText}
                      {phase === 3 && <span className="w-1.5 h-3 bg-[#38BDF8] ml-1 inline-block animate-pulse" />}
                    </pre>
                  </div>
                </div>
              )}

              {/* Phase 4+: Tool 3 (ConPTY pytest execution) */}
              {phase >= 4 && (
                <div className="space-y-1.5 text-xs animate-in fade-in duration-150">
                  <div className="text-[#38BDF8] flex items-center gap-1.5">
                    <span>⚙</span>
                    <span>terminal.run_in_terminal("pytest tests/test_auth.py -v")</span>
                  </div>
                  <div className="rounded-lg bg-[#06080F] p-3 text-[11px] border-l-2 border-[#536DFE] space-y-1 text-slate-300 font-mono">
                    <div className="text-slate-400">rootdir: C:\Projects\MyAPI, configfile: pytest.ini</div>
                    <div className="text-[#34A853]">tests/test_auth.py::test_create_access_token PASSED [ 25%]</div>
                    <div className="text-[#34A853]">tests/test_auth.py::test_verify_valid_token PASSED [ 50%]</div>
                    <div className="text-[#34A853]">tests/test_auth.py::test_token_expiry_reject PASSED [ 75%]</div>
                    <div className="text-[#34A853]">tests/test_auth.py::test_invalid_signature PASSED [100%]</div>
                    <div className="text-[#34A853] font-bold pt-1 border-t border-white/[0.06]">
                      ══════════════════════ 4 passed in 0.24s ═════════════════════
                    </div>
                  </div>
                </div>
              )}

              {/* Phase 5+: Final AI Response */}
              {phase >= 5 && (
                <div className="p-3.5 rounded-xl bg-[#536DFE]/10 border border-[#536DFE]/30 text-xs sm:text-sm animate-in fade-in duration-200">
                  <div className="font-bold text-[#536DFE] mb-1 flex items-center gap-1.5">
                    <span>DeepX:</span>
                  </div>
                  <p className="leading-relaxed text-slate-200">
                    {aiText}
                    {phase === 5 && <span className="w-1.5 h-3 bg-[#536DFE] ml-1 inline-block animate-pulse" />}
                  </p>
                </div>
              )}

              {/* Blinking prompt ready for next command */}
              {phase === 6 && (
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
