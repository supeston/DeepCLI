import React, { useState } from 'react';
import { Layers, Check } from 'lucide-react';

export const BentoGrid: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);

  const features = [
    {
      id: 'cli',
      title: 'DeepX CLI & ConPTY Runtime',
      subtitle: 'Terminal-First Surface',
      description:
        'The lightweight, fast, terminal-first surface to work with DeepX Antigravity agents. Run autonomous coding agents, execute interactive shell commands directly with Windows ConPTY, and manage background subagents all from your keyboard.',
      tags: ['pywinpty ConPTY', 'Win32 Job Objects', 'Prompt Detection', 'Zero Zombie Processes'],
      codeSnippet: `# Interactive Windows ConPTY Session
pty = PtyProcess.spawn(["cmd.exe", "/c", "npm run deploy"])
pty.send_input("y\\n")  # Auto-evaluates interactive prompt`,
    },
    {
      id: 'manager',
      title: 'DeepX Agent Manager',
      subtitle: 'Multi-Agent Command Center',
      description:
        'Your command center to manage multiple local agents in parallel. Group conversations into Projects, operate across multiple workspaces, and automate routine tasks with scheduled messages.',
      tags: ['Parallel Subagents', 'Context Isolation', 'Cron Scheduler', 'Zero Memory Leaks'],
      codeSnippet: `# Multi-agent Parallel Orchestration
subagents = invoke_subagents([
    {"name": "researcher", "role": "Codebase Auditor"},
    {"name": "tester", "role": "Vitest Runner"}
])`,
    },
    {
      id: 'sdk',
      title: 'DeepX SDK & Verification Barriers',
      subtitle: 'Python Agent Harness',
      description:
        "Prototype custom agents leveraging DeepX's harness with minimal code. Python scripts to iterate on agentic applications, automate software engineering tasks, and enforce AST bytecode compilation before returning code.",
      tags: ['Verification Barrier', 'py_compile Check', 'AST Validator', 'Self-Correction Loop'],
      codeSnippet: `# Dual ReAct Verification Loop
verify_syntax("service.py")
# => Checked with py_compile & AST validator before user return`,
    },
    {
      id: 'multimodal',
      title: 'WinRT & Media Multimodal Engine',
      subtitle: 'Native Windows Integration',
      description:
        'The fully-featured agentic runtime with native WinRT Clipboard History (Win+V), deep Media Inspector for containers, codecs, and 10-bit HDR video, and Playwright Stealth DOM streaming.',
      tags: ['WinRT Win+V', 'PyMediaInfo / ffprobe', 'Playwright Stealth', 'Zero Censorship'],
      codeSnippet: `# WinRT Clipboard History Integration
items = await Clipboard.get_history_items_async()
# => Extracts text, codes, and Bitmap PNG screenshots`,
    },
  ];

  const current = features[activeTab];

  return (
    <section id="features" className="py-24 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header (Google Antigravity style) */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-[#8AB4F8] border border-blue-500/20 mb-4">
            <Layers className="w-3.5 h-3.5" />
            <span>CORE SURFACES</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-normal text-white tracking-tight mb-4">
            Built for developers for the <span className="text-google-gradient font-medium">agent-first era</span>
          </h2>
          <p className="text-[#9AA0A6] text-base sm:text-lg font-normal">
            Whether you are running rapid terminal loops or orchestrating multi-agent systems, DeepX Antigravity gives you uncompromising Windows control.
          </p>
        </div>

        {/* Interactive Feature Explorer (Google Antigravity Split Layout) */}
        <div className="antigravity-card p-6 sm:p-10 border border-white/10 rounded-[32px] overflow-hidden">
          {/* Tab Selector */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 p-1.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] mb-8">
            {features.map((item, idx) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(idx)}
                data-testid={`feature-tab-${item.id}`}
                className={`py-3 px-4 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 text-left flex flex-col gap-1 ${
                  activeTab === idx
                    ? 'bg-[#1a73e8] text-white shadow-lg shadow-blue-500/25'
                    : 'text-[#9AA0A6] hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <span className="font-semibold truncate">{item.title.split('&')[0]}</span>
                <span className={`text-[11px] opacity-75 truncate ${activeTab === idx ? 'text-white' : 'text-slate-500'}`}>
                  {item.subtitle}
                </span>
              </button>
            ))}
          </div>

          {/* Active Content Showcase */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Description Column */}
            <div className="lg:col-span-6 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/[0.05] text-[#8AB4F8] border border-white/10">
                <span>{current.subtitle}</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-medium text-white tracking-tight">
                {current.title}
              </h3>
              <p className="text-base text-[#9AA0A6] leading-relaxed font-normal">
                {current.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 pt-2">
                {current.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 text-xs font-mono px-3 py-1 rounded-lg bg-white/[0.04] text-slate-300 border border-white/[0.08]"
                  >
                    <Check className="w-3.5 h-3.5 text-[#34A853]" />
                    <span>{tag}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Right Interactive Code / Visual Card */}
            <div className="lg:col-span-6">
              <div className="rounded-2xl bg-[#090A0F]/95 border border-white/10 p-5 shadow-2xl overflow-hidden font-mono text-xs text-slate-200">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.08] text-slate-400">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#EA4335]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#FBBC05]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#34A853]" />
                    <span className="text-[11px] ml-2 text-slate-400 font-semibold">{current.id}.py</span>
                  </div>
                  <span className="text-[10px] text-[#8AB4F8]">DeepX Antigravity 2.6</span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {current.codeSnippet}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
