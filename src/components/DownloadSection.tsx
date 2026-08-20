import React, { useState } from 'react';
import { Copy, Check, CheckCircle2 } from 'lucide-react';

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
    <section id="download" className="py-24 relative z-10 bg-slate-50 border-y border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto rounded-[32px] bg-white border border-slate-200 p-8 sm:p-14 shadow-xl relative overflow-hidden">
          <div className="relative z-10">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-3xl sm:text-5xl font-normal text-[#1F1F1F] tracking-tight mb-4">
                Experience liftoff with <span className="text-[#536DFE] font-medium">DeepX</span>
              </h2>
              <p className="text-[#5F6368] text-sm sm:text-base font-normal">
                Available for Windows 10 & 11 (64-bit). The automated installer initializes an isolated environment, browser stealth, and terminal tooling in seconds.
              </p>
            </div>

            {/* Installation Steps */}
            <div className="space-y-4 mb-10">
              {steps.map((step, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl bg-slate-50 border border-slate-200 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      {step.title}
                    </div>
                    <pre className="font-mono text-xs sm:text-sm text-slate-800 whitespace-pre-wrap select-all">
                      {step.code}
                    </pre>
                  </div>
                  <button
                    onClick={() => handleCopy(step.code, idx)}
                    className="self-end sm:self-center px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-sm transition-colors flex items-center gap-1.5 text-xs font-medium"
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
            <div className="pt-8 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-medium text-slate-500">
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
      </div>
    </section>
  );
};
