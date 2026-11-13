import React from 'react';
import { ScrollReveal } from '../components/ScrollReveal';

export const LogsPage: React.FC = () => {
  const logs = [
    {
      version: 'v3.1.0',
      date: 'Nov 13, 2026',
      changes: [
        'Added instant in-place login continuation: after signing into DeepSeek in the browser window, DeepX immediately attaches the session in the active terminal without restarting or closing the window.',
        'Added DeepSeek Account Ban Guard: automatically detects account suspension banners (RU/EN/ZH), extracts the exact ban expiration timestamp and masked account email, clears the blocked state.json, and renders a structured diagnostic panel.',
        'Replaced legacy start.bat with self-healing run_cli.vbs and Rich Interactive Control Hub (deepx/launcher.py) with Win32 ReadConsoleInputW arrow-key navigation, update check, dependency diagnostics, and global command toggle.',
        'Added one-command PowerShell system installer (install.ps1) and global deepx PATH command with automatic classic-console to Windows Terminal handoff.',
        'Hardened both Windows Terminal (24-bit TrueColor) and classic conhost.exe: disabled QuickEdit freeze, fixed Win32 console close handler with child-process cleanup, and bounded Playwright shutdown timeouts.'
      ]
    },
    {
      version: 'v3.0.0',
      date: 'Nov 13, 2026',
      changes: [
        'Restored framed Rich ASCII banner (#536DFE) with narrow-terminal fallback, workspace path indicator, and unified /help, /status, /menu, and prompt palette.',
        'Added GitHub version checking with in-banner "update to X.Y.Z" notice plus safe /update command and --update CLI flag preserving .env, state.json, .venv, and .deepx data.',
        'Introduced zero-turn AST Repo Map indexing, DEEPX.md / AGENTS.md instruction loading, /mode plan read-only planning, /undo file checkpoints, /compact folding, and grep_search.',
        'Replaced raw tool JSON and console dumps with in-place single-line progress status, clean Markdown streaming, hardened tool parser, and Windows ConPTY Ctrl+X / Ctrl+C stability fixes.'
      ]
    },
    {
      version: 'v2.6.0',
      date: 'Aug 20, 2026',
      changes: [
        'Interactive Terminal Simulator with variable typing and execution speeds.',
        'Added syntax highlighting for code blocks in Terminal Simulator.',
        'Introduced Docker OOM Debugging and Git Conflict Resolution scenarios.',
        'Refined Navbar dropdown logic and scroll reveal animations.'
      ]
    },
    {
      version: 'v2.5.1',
      date: 'Aug 18, 2026',
      changes: [
        'Patched WinRT clipboard memory leak on continuous polling.',
        'Improved Playwright stealth masking for Cloudflare challenges.',
        'Fixed ConPTY child-process termination handling.'
      ]
    },
    {
      version: 'v2.5.0',
      date: 'Aug 15, 2026',
      changes: [
        'Initial DeepX public release.',
        'Added zero-telemetry Dual-Engine reasoning core.',
        'Introduced WinRT Visual Clipboard integration.'
      ]
    }
  ];

  return (
    <div className="relative pt-32 pb-16 min-h-screen deepx-section-clear">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <ScrollReveal direction="down">
          <div className="mb-12">
            <h1 className="text-4xl sm:text-5xl font-normal text-[#111318] tracking-tight mb-4">
              Platform Updates
            </h1>
            <p className="text-lg text-[#475569] font-normal">
              Release notes, architectural changes, and core stability fixes for DeepX CLI.
            </p>
          </div>
        </ScrollReveal>

        <div className="space-y-12 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
          {logs.map((log, index) => (
            <ScrollReveal key={log.version} direction="up" delay={index * 100}>
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-[#536DFE] text-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-lg z-10">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                    <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" />
                  </svg>
                </div>

                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] deepx-card p-6 shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <span className="px-3 py-1 bg-[#536DFE]/10 text-[#536DFE] text-sm font-mono font-semibold rounded-md">
                      {log.version}
                    </span>
                    <time className="text-sm text-slate-500 font-mono">{log.date}</time>
                  </div>
                  <ul className="space-y-3">
                    {log.changes.map((change, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-sm text-[#475569]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#536DFE] shrink-0 mt-2" />
                        <span>{change}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </div>
  );
};
