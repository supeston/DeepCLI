import React, { useState } from 'react';
import { Copy, Check, CheckCircle2 } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

export const DownloadSection: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const steps = [
    {
      title: '1. One-Line System Install (PowerShell)',
      code: 'irm https://raw.githubusercontent.com/supeston/DeepCLI/main/install.ps1 | iex',
    },
    {
      title: '2. Launch Agent or Interactive Control Hub',
      code: 'deepx\n# Or double-click run_cli.vbs for the Rich Control Hub in Windows Terminal',
    },
    {
      title: '3. In-App Self-Update & Launcher Flags',
      code: 'deepx --update\ndeepx --launcher',
    },
  ];

  const handleCopy = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="download" className="py-24 relative z-10 deepx-section-clear border-y border-slate-200/80 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal direction="up" delay={150}>
          <div className="max-w-4xl mx-auto deepx-card p-8 sm:p-14 shadow-xl relative overflow-hidden">
            <div className="relative z-10">
              <div className="text-center max-w-2xl mx-auto mb-12">
                <h2 className="text-3xl sm:text-5xl font-normal text-[#111318] tracking-tight mb-4">
                  Experience liftoff with <span className="text-[#536DFE] font-medium">DeepX</span>
                </h2>
                <TextScrollReveal
                  text="Built for Windows 10 & 11 (64-bit). Provisions an isolated .venv, configures Playwright Stealth 2.x, and registers the global deepx command in seconds."
                  className="text-[#475569] text-sm sm:text-base font-normal"
                  highlightWords={['Windows', 'isolated', '.venv,', 'Playwright', 'Stealth', 'deepx']}
                />
              </div>

              {/* Installation Steps */}
              <div className="space-y-4 mb-10">
                {steps.map((step, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl bg-slate-50/90 border border-slate-200/80 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="text-xs font-medium text-slate-500">
                        {step.title}
                      </div>
                      <pre className="font-mono text-xs sm:text-sm text-[#111318] whitespace-pre-wrap select-all">
                        {step.code}
                      </pre>
                    </div>
                    <button
                      onClick={() => handleCopy(step.code, idx)}
                      className="self-end sm:self-center px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-sm transition-colors flex items-center gap-1.5 text-xs font-medium cursor-pointer"
                      data-testid={`install-copy-btn-${idx}`}
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-[#34A853]" />
                          <span className="text-[#34A853]">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>

              {/* System Badges */}
              <div className="pt-8 border-t border-slate-200/70 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-medium text-slate-600">
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#34A853]" />
                  <span>Windows 10 / 11 (64-bit)</span>
                </div>
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#34A853]" />
                  <span>Python 3.10+ (Auto .venv)</span>
                </div>
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#34A853]" />
                  <span>100% Free Open Source (MIT)</span>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
