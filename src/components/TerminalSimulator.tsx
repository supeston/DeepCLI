import React, { useState, useEffect } from 'react';
import { Terminal as TermIcon, Copy, Check, RotateCcw } from 'lucide-react';

interface ScenarioStep {
  type: 'banner' | 'user' | 'think' | 'tasks' | 'tool' | 'ai';
  content?: string;
  tasks?: { id: number; status: 'done' | 'active' | 'pending'; text: string }[];
  percent?: number;
  toolName?: string;
  toolOutput?: string;
}

interface Scenario {
  id: string;
  label: string;
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
      label: 'Autonomous Refactoring & Tests',
      userPrompt: 'Сделай рефакторинг auth.py, добавь JWT валидацию и прогони pytest в ConPTY',
      steps: [
        { type: 'banner' },
        { type: 'user' },
        {
          type: 'think',
          content: 'DeepThink Engine: анализирую auth.py и тестовое окружение. Формирую план задач...',
        },
        {
          type: 'tasks',
          percent: 0,
          tasks: [
            { id: 1, status: 'pending', text: 'Анализ структуры auth.py и зависимостей' },
            { id: 2, status: 'pending', text: 'Реализация JWT валидации и middleware' },
            { id: 3, status: 'pending', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.read_file("src/auth.py")',
          toolOutput: '✓ Read 48 lines from src/auth.py',
        },
        {
          type: 'tasks',
          percent: 33,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ структуры auth.py и зависимостей' },
            { id: 2, status: 'active', text: 'Реализация JWT валидации и middleware' },
            { id: 3, status: 'pending', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.write_file("src/auth.py", ...)',
          toolOutput: '✓ Applied JWT token encoding/decoding & auth middleware',
        },
        {
          type: 'tasks',
          percent: 66,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ структуры auth.py и зависимостей' },
            { id: 2, status: 'done', text: 'Реализация JWT валидации и middleware' },
            { id: 3, status: 'active', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        {
          type: 'tool',
          toolName: 'terminal.run_in_terminal("pytest tests/test_auth.py")',
          toolOutput:
            '✓ test_auth.py::test_token_valid PASSED\n✓ test_auth.py::test_token_expired PASSED\n✓ test_auth.py::test_middleware_guard PASSED\n════════════ 3 passed in 0.34s ════════════',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ структуры auth.py и зависимостей' },
            { id: 2, status: 'done', text: 'Реализация JWT валидации и middleware' },
            { id: 3, status: 'done', text: 'Запуск и верификация pytest test_auth.py' },
          ],
        },
        {
          type: 'ai',
          content:
            'Рефакторинг auth.py завершён. Добавлена строгая JWT валидация с проверкой времени жизни токена и middleware. Все 3 теста pytest пройдены успешно.',
        },
      ],
    },
    {
      id: 'conpty',
      label: 'ConPTY Interactive Terminal',
      userPrompt: 'Запусти билд проекта и устрани ошибку TypeScript',
      steps: [
        { type: 'banner' },
        { type: 'user' },
        {
          type: 'think',
          content: 'DeepThink Engine: запускаю сборку через интерактивный Windows ConPTY...',
        },
        {
          type: 'tool',
          toolName: 'terminal.run_in_terminal("npm run build")',
          toolOutput:
            'error TS2322: Type "string" is not assignable to type "number".\nsrc/services/api.ts:42:5 - error TS2322',
        },
        {
          type: 'tasks',
          percent: 50,
          tasks: [
            { id: 1, status: 'done', text: 'Диагностика ошибки типизации в api.ts:42' },
            { id: 2, status: 'active', text: 'Корректировка интерфейса и повторный билд' },
          ],
        },
        {
          type: 'tool',
          toolName: 'filesystem.replace_file_content("src/services/api.ts", ...)',
          toolOutput: '✓ Fixed port property type from string to number',
        },
        {
          type: 'tool',
          toolName: 'terminal.run_in_terminal("npm run build")',
          toolOutput:
            'vite v6.4.3 building for production...\n✓ 1596 modules transformed.\ndist/index.html 1.38 kB\n✓ built in 1.82s',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Диагностика ошибки типизации в api.ts:42' },
            { id: 2, status: 'done', text: 'Корректировка интерфейса и повторный билд' },
          ],
        },
        {
          type: 'ai',
          content:
            'Ошибка TS2322 исправлена. Повторная сборка в ConPTY завершилась успешно (0 ошибок, билд в /dist готов).',
        },
      ],
    },
    {
      id: 'clipboard',
      label: 'WinRT Clipboard & Vision',
      userPrompt: 'Посмотри скриншот ошибки в буфере обмена (Win+V) и исправь баг',
      steps: [
        { type: 'banner' },
        { type: 'user' },
        {
          type: 'think',
          content: 'DeepThink Engine: запрашиваю Windows.ApplicationModel.DataTransfer.Clipboard API...',
        },
        {
          type: 'tool',
          toolName: 'clipboard.get_clipboard_image()',
          toolOutput:
            '✓ WinRT API: Captured 1920x1080 PNG from clipboard history\n✓ Vision Engine: Detected NullReferenceException in UserController.cs:88',
        },
        {
          type: 'tasks',
          percent: 100,
          tasks: [
            { id: 1, status: 'done', text: 'Анализ снимка экрана из WinRT Clipboard' },
            { id: 2, status: 'done', text: 'Добавление null-check проверки в UserController.cs' },
          ],
        },
        {
          type: 'ai',
          content:
            'Скриншот из буфера проанализирован. В UserController.cs:88 отсутствовала проверка `user?.Profile`. Баг устранён.',
        },
      ],
    },
  ];

  const [activeTab, setActiveTab] = useState<string>('refactor');
  const [stepIndex, setStepIndex] = useState<number>(0);
  const [typedUserText, setTypedUserText] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  const currentScenario = scenarios.find((s) => s.id === activeTab) || scenarios[0];

  useEffect(() => {
    setStepIndex(0);
    setTypedUserText('');

    let charIdx = 0;
    const prompt = currentScenario.userPrompt;
    const typeInterval = setInterval(() => {
      charIdx++;
      setTypedUserText(prompt.slice(0, charIdx));
      if (charIdx >= prompt.length) {
        clearInterval(typeInterval);
        // Step progression
        let currentStep = 1;
        const stepInterval = setInterval(() => {
          currentStep++;
          setStepIndex(currentStep);
          if (currentStep >= currentScenario.steps.length) {
            clearInterval(stepInterval);
          }
        }, 450);
      }
    }, 25);

    return () => {
      clearInterval(typeInterval);
    };
  }, [activeTab]);

  const handleCopy = () => {
    navigator.clipboard.writeText(currentScenario.userPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-20 bg-gray-50 border-y border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl sm:text-4xl font-normal text-[#1F1F1F] tracking-tight mb-4">
            Terminal-First Intelligence
          </h2>
          <p className="text-[#5F6368] text-base sm:text-lg font-normal">
            DeepX operates directly inside your Windows terminal. It builds task plans, executes ConPTY commands, and streams rich feedback in real time.
          </p>
        </div>

        {/* Scenario Switcher Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          {scenarios.map((sc) => {
            const isActive = activeTab === sc.id;
            return (
              <button
                key={sc.id}
                onClick={() => setActiveTab(sc.id)}
                data-testid={`terminal-tab-${sc.id}`}
                className={`px-4 py-2 rounded-full text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#536DFE] text-white shadow-md'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                {sc.label}
              </button>
            );
          })}
        </div>

        {/* Terminal Window (Real DeepCLI UI) */}
        <div className="max-w-4xl mx-auto rounded-2xl overflow-hidden bg-[#0C101A] border border-gray-300 shadow-2xl">
          {/* Header */}
          <div className="bg-[#141926] px-4 py-3 flex items-center justify-between border-b border-white/[0.08] select-none">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
              <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
              <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
            </div>
            <div className="text-[#536DFE] text-xs font-mono font-medium flex items-center gap-1.5">
              <TermIcon className="w-3.5 h-3.5 text-[#536DFE]" />
              <span>deepx (Active Session)</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const curr = activeTab;
                  setActiveTab('');
                  setTimeout(() => setActiveTab(curr), 10);
                }}
                className="text-gray-400 hover:text-white transition-colors"
                title="Replay animation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleCopy}
                data-testid="terminal-copy-btn"
                className="text-gray-400 hover:text-white transition-colors"
                title="Copy prompt"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#27C93F]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-5 font-mono text-xs sm:text-sm leading-relaxed overflow-x-auto" data-testid="terminal-body">
            {/* ASCII Banner */}
            <div className="mb-4 p-3 rounded-xl bg-[#080B12] border border-[#536DFE]/40 text-center">
              <pre className="text-[#536DFE] font-bold text-[9px] sm:text-[11px] leading-tight select-none inline-block">
                {ASCII_BANNER}
              </pre>
              <div className="mt-2 text-[10px] sm:text-xs text-slate-300 font-medium">
                Mode: <span className="text-[#38BDF8] font-bold">EXPERT</span> | Style:{' '}
                <span className="text-[#A78BFA] font-bold">CODER</span> | DeepThink:{' '}
                <span className="text-[#38BDF8] font-bold">ON</span> | Search:{' '}
                <span className="text-[#38BDF8] font-bold">ON</span>
              </div>
            </div>

            {/* User Prompt Line */}
            <div className="flex items-start text-white mb-4">
              <span className="text-[#536DFE] font-bold mr-2 select-none">deepx&gt;</span>
              <span>{typedUserText}</span>
              {typedUserText.length < currentScenario.userPrompt.length && (
                <span className="w-2 h-4 bg-[#536DFE] ml-1 animate-pulse" />
              )}
            </div>

            {/* Dynamic Steps */}
            <div className="space-y-3">
              {currentScenario.steps.slice(2, stepIndex + 1).map((step, idx) => {
                if (step.type === 'think') {
                  return (
                    <div key={idx} className="text-[#A78BFA] text-xs flex items-center gap-2 animate-in fade-in">
                      <span>🤔</span>
                      <span>{step.content}</span>
                    </div>
                  );
                }

                if (step.type === 'tasks' && step.tasks) {
                  const doneCount = step.tasks.filter((t) => t.status === 'done').length;
                  const total = step.tasks.length;
                  const pct = step.percent || 0;
                  const filled = Math.round(pct / 5);
                  const empty = 20 - filled;

                  return (
                    <div
                      key={idx}
                      className="my-3 p-3 rounded-xl bg-[#080B12] border border-[#536DFE]/40 animate-in fade-in"
                    >
                      <div className="flex items-center justify-between text-xs font-semibold mb-2 pb-1.5 border-b border-white/[0.06]">
                        <span className="text-[#536DFE] uppercase tracking-wider">
                          TASKS {doneCount}/{total}
                        </span>
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-[#536DFE]">{'━'.repeat(filled)}</span>
                          <span className="text-[#1E293B]">{'━'.repeat(empty)}</span>
                          <span className="text-[#536DFE] font-bold">{pct}%</span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        {step.tasks.map((task) => (
                          <div key={task.id} className="flex items-center gap-2.5 text-xs">
                            <span className="text-slate-500 font-mono w-4">{task.id}</span>
                            {task.status === 'done' ? (
                              <span className="text-[#34A853] font-bold">[✓]</span>
                            ) : task.status === 'active' ? (
                              <span className="text-[#FDE68A] font-bold">[▶]</span>
                            ) : (
                              <span className="text-slate-500">[ ]</span>
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
                    <div key={idx} className="space-y-1 text-xs animate-in fade-in">
                      <div className="text-[#38BDF8] font-mono flex items-center gap-1.5">
                        <span>⚙</span>
                        <span>{step.toolName}</span>
                      </div>
                      {step.toolOutput && (
                        <pre className="text-slate-300 font-mono text-[11px] sm:text-xs pl-4 border-l border-[#536DFE]/30 whitespace-pre-wrap">
                          {step.toolOutput}
                        </pre>
                      )}
                    </div>
                  );
                }

                if (step.type === 'ai') {
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#536DFE]/10 border border-[#536DFE]/30 text-white text-xs sm:text-sm animate-in fade-in"
                    >
                      <div className="font-bold text-[#536DFE] mb-1">DeepX:</div>
                      <p className="leading-relaxed text-slate-200">{step.content}</p>
                    </div>
                  );
                }

                return null;
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
