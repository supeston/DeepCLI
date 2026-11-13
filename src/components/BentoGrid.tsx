import React, { useState } from 'react';
import { Terminal, Bot, Workflow, MousePointerClick, ArrowRight, ShieldCheck, CheckCircle2, Layers } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

type FeatureTab = 'cli' | 'reasoning' | 'workflows' | 'clipboard';

export const BentoGrid: React.FC = () => {
  const [activeTab, setActiveTab] = useState<FeatureTab>('cli');

  const tabs = [
    { id: 'cli', label: 'Command Line', icon: Terminal, color: 'text-[#536DFE]' },
    { id: 'reasoning', label: 'Dual-Engine', icon: Bot, color: 'text-[#536DFE]' },
    { id: 'workflows', label: 'Automation', icon: Workflow, color: 'text-[#536DFE]' },
    { id: 'clipboard', label: 'Clipboard', icon: MousePointerClick, color: 'text-[#536DFE]' },
  ] as const;

  const content: Record<
    FeatureTab,
    {
      title: string;
      desc: string;
      metrics: { label: string; val: string }[];
      specTag: string;
      terminalTitle: string;
      previewLines: { prefix: string; text: string; tone: string }[];
      footerStatus: string;
    }
  > = {
    cli: {
      title: 'Terminal-first Interactive Agent',
      desc: 'Launches into Windows Terminal (24-bit TrueColor) via run_cli.vbs Control Hub or the global deepx command. Streams clean Markdown with an in-place single-line status bar, zero raw JSON leaks, and automatic .deepx_history checkpoints for instant /undo rollback.',
      metrics: [
        { label: 'Release', val: 'v3.1.0' },
        { label: 'Runtime', val: 'Win32 ConPTY' },
      ],
      specTag: 'LAUNCHER + CONPTY ENGINE',
      terminalTitle: 'DEEPX CONTROL HUB · Windows Terminal',
      previewLines: [
        { prefix: '▸ [1]', text: 'Launch DEEPX Agent (24-bit TrueColor)', tone: 'text-white font-medium bg-[#536DFE]/20 border border-[#536DFE]/40' },
        { prefix: '  [2]', text: 'Check & Install Updates (v3.1.0 up to date)', tone: 'text-slate-300' },
        { prefix: '  [3]', text: 'Verify Dependencies & Playwright Stealth 2.x', tone: 'text-slate-300' },
        { prefix: '  [4]', text: "Global 'deepx' Command [installed in PATH]", tone: 'text-[#10B981]' },
      ],
      footerStatus: 'In-place status · [00:01] Правлю runner.py · /undo ready',
    },
    reasoning: {
      title: 'Zero-Telemetry Dual-Engine',
      desc: 'Switches cleanly between instant, think, and read-only plan modes without losing conversation state. Indexes your repository AST and DEEPX.md instructions on turn zero, and runs 100% locally with zero telemetry.',
      metrics: [
        { label: 'Modes', val: 'Fast / Think / Plan' },
        { label: 'Telemetry', val: '0%' },
      ],
      specTag: 'AST REPO MAP + PLAN MODE',
      terminalTitle: 'ZERO-TURN AST INDEXER · /mode plan',
      previewLines: [
        { prefix: 'AST', text: 'deepx/agent/runner.py · DeepCLIApp (18 methods)', tone: 'text-[#38BDF8]' },
        { prefix: 'AST', text: 'deepx/api/deep_api.py · DeepAPI + BanGuard', tone: 'text-[#38BDF8]' },
        { prefix: 'CFG', text: 'Loaded DEEPX.md project rules (zero-turn seed)', tone: 'text-[#A78BFA]' },
        { prefix: '[plan] ›', text: 'Write mutation tools locked until /mode think', tone: 'text-slate-200 font-medium' },
      ],
      footerStatus: 'Context preserved across /mode instant · think · plan',
    },
    workflows: {
      title: 'End-to-End Task Automation',
      desc: 'Dispatches parallel read-only batches (read_file, grep_search, list_dir), enforces closed-loop test verification after every file mutation, folds long sessions via /compact, and updates in-place via /update while keeping .env and state.json intact.',
      metrics: [
        { label: 'Rollbacks', val: '/undo' },
        { label: 'Self-Sync', val: '/update' },
      ],
      specTag: 'CLOSED-LOOP VERIFICATION',
      terminalTitle: 'PARALLEL BATCH + PYTEST VERIFICATION',
      previewLines: [
        { prefix: 'BATCH', text: 'read_file + grep_search (+3 parallel reads)', tone: 'text-[#38BDF8]' },
        { prefix: 'EDIT', text: 'edit_file("deepx/api/deep_api.py") · checkpoint saved', tone: 'text-slate-200' },
        { prefix: 'TEST', text: 'run_cmd("pytest -q tests") -> 59 passed in 1.4s', tone: 'text-[#10B981]' },
        { prefix: 'SYNC', text: '/update preserves .env, state.json, vds_profiles.json', tone: 'text-[#A78BFA]' },
      ],
      footerStatus: 'Zero unverified edits · automatic checkpointing',
    },
    clipboard: {
      title: 'WinRT Vision & Session Guard',
      desc: 'Reads screenshots directly from the Windows Clipboard (Win+Shift+S) via WinRT APIs. Includes instant post-login continuation in the same terminal window and automatic detection of DeepSeek account suspensions with exact ban expiration timestamps.',
      metrics: [
        { label: 'Clipboard', val: 'WinRT API' },
        { label: 'Auth Guard', val: 'Auto-Resume' },
      ],
      specTag: 'WINRT VISION + ACCOUNT BAN GUARD',
      terminalTitle: 'SESSION GUARD · Instant Auth & Ban Detector',
      previewLines: [
        { prefix: '[+]', text: 'Login confirmed -> session attached in current terminal', tone: 'text-[#10B981]' },
        { prefix: '[!]', text: 'Ban Guard: detects account suspension & exact date/time', tone: 'text-[#FBBF24]' },
        { prefix: 'IMG', text: 'get_clipboard_image() · 1920x1080 CF_DIBV5 attached', tone: 'text-[#38BDF8]' },
        { prefix: 'SSH', text: 'vds_cmd / vds_deploy · persistent Paramiko pool', tone: 'text-slate-300' },
      ],
      footerStatus: 'No terminal restart after login · auto state.json recovery',
    },
  };

  const active = content[activeTab];

  return (
    <section id="features" className="py-24 deepx-section-clear overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <ScrollReveal direction="up" delay={100}>
            <h2 className="text-4xl sm:text-5xl font-normal tracking-tight text-[#111318] mb-6">
              Built for developers for the <br className="hidden sm:block" />
              <span className="text-[#536DFE] font-medium">CLI era</span>
            </h2>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200}>
            <TextScrollReveal
              text="DeepX runs directly inside Windows Terminal and ConPTY. Launch via the interactive VBS Control Hub or type deepx from any directory."
              className="text-lg text-[#475569] font-normal"
              highlightWords={['Windows', 'Terminal', 'ConPTY.', 'Control', 'Hub', 'deepx']}
            />
          </ScrollReveal>
        </div>

        {/* Feature Tabs */}
        <ScrollReveal direction="up" delay={250}>
          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 mb-12">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  data-testid={`feature-tab-${tab.id}`}
                  className={`flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium transition-colors duration-200 cursor-pointer ${
                    isActive
                      ? 'bg-[#111318] text-white shadow-md'
                      : 'bg-white/85 text-slate-600 hover:bg-white border border-slate-200/90'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#536DFE]' : tab.color}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </ScrollReveal>

        {/* Active Feature Content */}
        <ScrollReveal direction="up" delay={350}>
          <div className="deepx-card p-8 sm:p-12 relative overflow-hidden">
            <div className="grid lg:grid-cols-12 gap-10 lg:gap-12 items-center relative z-10">
              <div className="lg:col-span-6">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200/80 text-[11px] font-mono font-medium mb-4">
                  <Layers className="w-3.5 h-3.5 text-[#536DFE]" />
                  <span>{active.specTag}</span>
                </div>
                <h3 className="text-3xl font-normal text-[#111318] mb-5 tracking-tight">
                  {active.title}
                </h3>
                <p className="text-[#475569] text-base sm:text-lg leading-relaxed mb-8 font-normal">
                  {active.desc}
                </p>

                <div className="grid grid-cols-2 gap-4 mb-8">
                  {active.metrics.map((m, i) => (
                    <div key={i} className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/70">
                      <div className="text-2xl font-mono font-medium text-[#111318] mb-1">{m.val}</div>
                      <div className="text-xs font-medium text-slate-500">{m.label}</div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                  className="inline-flex items-center gap-2 text-sm font-medium text-[#536DFE] hover:text-[#3D5AFE] transition-colors cursor-pointer"
                >
                  <span>Install {tabs.find((t) => t.id === activeTab)?.label} workflow</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              {/* Authentic Product Surface Preview (No skeleton bars) */}
              <div className="lg:col-span-6">
                <div className="rounded-2xl bg-[#0A0D14] border border-slate-800 shadow-2xl overflow-hidden font-mono text-xs">
                  <div className="bg-[#121622] px-4 py-3 border-b border-white/[0.08] flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F56]" />
                      <span className="w-2.5 h-2.5 rounded-full bg-[#FFBD2E]" />
                      <span className="w-2.5 h-2.5 rounded-full bg-[#27C93F]" />
                    </div>
                    <span className="text-[11px] text-slate-300 font-medium truncate">
                      {active.terminalTitle}
                    </span>
                    <ShieldCheck className="w-4 h-4 text-[#536DFE]" />
                  </div>

                  <div className="p-5 sm:p-6 space-y-2.5">
                    {active.previewLines.map((row, idx) => (
                      <div
                        key={idx}
                        className={`px-3.5 py-2.5 rounded-xl flex items-center gap-3 ${
                          idx === 0 ? row.tone : `bg-white/[0.03] border border-white/[0.06] ${row.tone}`
                        }`}
                      >
                        <span className="text-[#536DFE] font-semibold shrink-0">{row.prefix}</span>
                        <span className="truncate">{row.text}</span>
                      </div>
                    ))}
                  </div>

                  <div className="px-5 py-3 bg-[#06080F] border-t border-white/[0.07] flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-2 truncate">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
                      <span className="truncate">{active.footerStatus}</span>
                    </span>
                    <span className="text-[#536DFE] shrink-0 ml-2">UTF-8 · OK</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
