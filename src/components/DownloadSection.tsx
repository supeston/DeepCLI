import React, { useState } from 'react';
import { Download, Copy, Check, CheckCircle2 } from 'lucide-react';

export const DownloadSection: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const steps = [
    {
      title: '1. Clone Repository',
      code: 'git clone https://github.com/supeston/DeepCLI.git\ncd DeepCLI',
    },
    {
      title: '2. Launch in 1 Click (Windows)',
      code: 'cscript run_cli.vbs\n# Or double-click run_cli.vbs in File Explorer',
    },
    {
      title: '3. Alternative: Run via Python Module',
      code: 'python deepx/install.py\npython -m deepx',
    },
  ];

  const handleCopy = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="download" className="py-24 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto rounded-3xl bg-gradient-to-b from-[#111524] to-[#0B0E17] border border-[#536DFE]/30 p-8 sm:p-12 shadow-2xl relative overflow-hidden">
          {/* Ambient Glows */}
          <div className="absolute -top-32 -left-32 w-80 h-80 bg-[#536DFE]/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-[#38BDF8]/20 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <div className="text-center max-w-2xl mx-auto mb-10">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#536DFE]/20 text-[#38BDF8] border border-[#536DFE]/40 mb-4">
                <Download className="w-3.5 h-3.5" />
                <span>INSTANT DEPLOYMENT</span>
              </div>
              <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
                Get DeepX Running in 60 Seconds
              </h2>
              <p className="text-slate-300 text-sm sm:text-base">
                No complex environment setup needed. The automated installer configures dependencies, isolated virtual environment, and browser stealth out of the box.
              </p>
            </div>

            {/* Installation Steps */}
            <div className="space-y-4 mb-10">
              {steps.map((step, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl bg-[#080A10]/90 border border-slate-800/80 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {step.title}
                    </div>
                    <pre className="font-mono text-xs sm:text-sm text-slate-200 whitespace-pre-wrap select-all">
                      {step.code}
                    </pre>
                  </div>
                  <button
                    onClick={() => handleCopy(step.code, idx)}
                    className="self-end sm:self-center px-3 py-1.5 rounded-xl bg-[#141926] hover:bg-[#1E2538] text-slate-300 hover:text-white border border-slate-700 transition-colors flex items-center gap-1.5 text-xs font-medium"
                    data-testid={`install-copy-btn-${idx}`}
                  >
                    {copiedIndex === idx ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-[#10B981]" />
                        <span className="text-[#10B981]">Copied</span>
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

            {/* System Requirements & Features */}
            <div className="pt-8 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-medium text-slate-400">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                <span>Windows 10 / 11 (64-bit)</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                <span>Python 3.10+ (Auto .venv)</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                <span>100% Open Source (MIT)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
