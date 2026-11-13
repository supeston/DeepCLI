import React from 'react';
import { Check, Minus, Layers } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

export const ComparisonTable: React.FC = () => {
  const rows = [
    {
      feature: 'Pricing & Token Billing',
      deepx: '100% Free (Zero Bills)',
      antigravity: 'Free tier / $100/mo Ultra',
      claudeCode: 'Paid API ($2–$10/M) & Pro ($20/mo)',
      grokBuild: 'SuperGrok ($30/mo) / $2–$6/M API',
      codex: 'Plus ($20/mo) & API (~$1.75–$14/M)',
      isHighlight: true,
    },
    {
      feature: 'Terminal Execution Engine',
      deepx: 'Native Windows ConPTY + VBS Hub',
      antigravity: 'Local VS Code Fork / Cloud Sandboxes',
      claudeCode: 'Native Win/Mac/Linux (WSL2 optional)',
      grokBuild: 'Native Rust TUI (Win/Mac/Linux)',
      codex: 'Local Terminal Agent CLI',
    },
    {
      feature: 'WinRT Clipboard & Vision (Win+V / Win+Shift+S)',
      deepx: true,
      antigravity: 'File & Image Paste',
      claudeCode: 'Ctrl+V Image Paste',
      grokBuild: 'Multimodal Image Input',
      codex: 'File & Image Input',
    },
    {
      feature: 'Telemetry & Code Privacy',
      deepx: 'Zero Telemetry (100% Local)',
      antigravity: 'Google AI & Cloud Terms',
      claudeCode: 'No training on API by default',
      grokBuild: 'xAI Policy (training opt-out)',
      codex: 'No training on API/Enterprise',
      isHighlight: true,
    },
    {
      feature: 'Supported Reasoning Engines',
      deepx: 'DeepSeek-V4-Pro / V4.1-Flash',
      antigravity: 'Gemini 3.7 Flash / 3.6 Flash',
      claudeCode: 'Sonnet 5 / Opus 5 / Fable 5',
      grokBuild: 'Grok 4.6 Reasoning & grok-build',
      codex: 'GPT-5.6 Sol / Terra / Luna',
    },
    {
      feature: 'One-Click Native Setup & Auto-Update',
      deepx: 'install.ps1 + /update + Ban Guard',
      antigravity: 'Desktop App / Cloud CLI',
      claudeCode: 'Native Installer (no Node.js)',
      grokBuild: 'PowerShell / curl One-liner',
      codex: 'PowerShell / curl / npm',
    },
  ];

  const renderCell = (val: string | boolean, isDeepX: boolean = false) => {
    if (typeof val === 'boolean') {
      return val ? (
        <Check className={`w-5 h-5 mx-auto ${isDeepX ? 'text-[#536DFE]' : 'text-slate-500'}`} />
      ) : (
        <Minus className="w-5 h-5 text-slate-300 mx-auto" />
      );
    }

    if (isDeepX) {
      return (
        <span className="inline-block text-xs font-mono font-medium text-[#536DFE] bg-[#536DFE]/10 px-2.5 py-1 rounded-md whitespace-nowrap">
          {val}
        </span>
      );
    }

    return (
      <span className="text-xs font-medium text-slate-600 bg-slate-100/90 px-2 py-1 rounded-md whitespace-nowrap">
        {val}
      </span>
    );
  };

  return (
    <section id="comparison" className="py-24 deepx-section-band border-t border-slate-200/80 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <ScrollReveal direction="up" delay={100}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-[#536DFE]/10 text-[#536DFE] text-xs font-mono font-medium mb-4 border border-[#536DFE]/20">
              <Layers className="w-3.5 h-3.5" />
              <span>v3.1.0 Architectural Breakdown</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-normal text-[#111318] tracking-tight mb-4">
              Technical Benchmarks & Comparison
            </h2>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200}>
            <TextScrollReveal
              text="Objective comparison of execution environments, telemetry policies, billing models, and Windows ConPTY integration for current v3.1.0 architecture."
              className="text-[#475569] font-normal text-base sm:text-lg"
              highlightWords={['execution', 'telemetry', 'billing', 'ConPTY']}
            />
          </ScrollReveal>
        </div>

        <ScrollReveal direction="up" delay={300}>
          <div className="deepx-card overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[840px]">
                <thead>
                  <tr className="border-b border-slate-200/90 bg-slate-50/85">
                    <th className="p-5 text-xs font-medium text-slate-500 w-1/4">
                      Capability / Feature
                    </th>
                    <th className="p-5 text-xs font-semibold text-[#536DFE] bg-[#536DFE]/10 text-center border-x border-[#536DFE]/20">
                      DeepX CLI
                    </th>
                    <th className="p-5 text-xs font-medium text-slate-700 text-center">
                      Antigravity
                    </th>
                    <th className="p-5 text-xs font-medium text-slate-700 text-center">
                      Claude Code
                    </th>
                    <th className="p-5 text-xs font-medium text-slate-700 text-center">
                      Grok Build
                    </th>
                    <th className="p-5 text-xs font-medium text-slate-700 text-center">
                      Codex
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map((row, i) => (
                    <tr
                      key={i}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        row.isHighlight ? 'bg-[#536DFE]/[0.02]' : ''
                      }`}
                    >
                      <td className="p-5 text-sm font-medium text-[#111318]">
                        {row.feature}
                      </td>
                      <td className="p-5 bg-[#536DFE]/[0.06] text-center border-x border-[#536DFE]/20">
                        {renderCell(row.deepx, true)}
                      </td>
                      <td className="p-5 text-center">
                        {renderCell(row.antigravity)}
                      </td>
                      <td className="p-5 text-center">
                        {renderCell(row.claudeCode)}
                      </td>
                      <td className="p-5 text-center">
                        {renderCell(row.grokBuild)}
                      </td>
                      <td className="p-5 text-center">
                        {renderCell(row.codex)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
