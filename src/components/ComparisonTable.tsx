import React from 'react';
import { Check, X, Shield, Sparkles } from 'lucide-react';

export const ComparisonTable: React.FC = () => {
  const comparisons = [
    {
      feature: 'Interactive Terminal Execution',
      deepx: 'Native Windows ConPTY with bidirectional stdin & prompt detection',
      others: 'subprocess.Popen (hangs on [y/n] / password prompts)',
      highlight: true,
    },
    {
      feature: 'Process Lifecycle & Zombie Cleanup',
      deepx: 'Win32 Job Objects (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)',
      others: 'None (leaves orphaned node/python servers in Task Manager)',
      highlight: true,
    },
    {
      feature: 'Clipboard History (Win + V)',
      deepx: 'Official WinRT API with multi-slot search & Bitmap PNG extraction',
      others: 'Limited to single last text string (pyperclip)',
      highlight: true,
    },
    {
      feature: 'Code Self-Correction Barrier',
      deepx: 'Automatic py_compile, node --check, and AST verification before answer',
      others: 'Blind file write without compilation verification',
      highlight: false,
    },
    {
      feature: 'Media Metadata Inspector',
      deepx: 'Direct pymediainfo/ffprobe container, codec, HDR & EXIF extraction',
      others: 'Requires manual ffmpeg commands or external scripts',
      highlight: false,
    },
    {
      feature: 'Zero-Censorship Reasoning',
      deepx: 'Dual-Engine DeepSeek (Instant / Expert DeepThink) via Playwright Stealth',
      others: 'Strict API filters & moralizing refusals',
      highlight: true,
    },
    {
      feature: '1-Click Zero-Dependency Setup',
      deepx: 'Single run_cli.vbs with automated virtual environment & Chromium bootstrap',
      others: 'Complex manual virtualenv, pip, and system PATH configuration',
      highlight: false,
    },
  ];

  return (
    <section id="comparison" className="py-20 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#536DFE]/15 text-[#38BDF8] border border-[#536DFE]/30 mb-4">
            <Shield className="w-3.5 h-3.5" />
            <span>TECHNICAL BENCHMARKS</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
            Why Engineers Choose DeepX
          </h2>
          <p className="text-slate-300 text-sm sm:text-base">
            See how DeepX stacks up against standard LLM wrappers and generic coding assistants.
          </p>
        </div>

        {/* Table Container */}
        <div className="max-w-5xl mx-auto rounded-3xl glass-panel border border-slate-800 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0E111B]">
                  <th className="py-5 px-6 text-sm font-bold text-slate-300 w-1/3">Capability</th>
                  <th className="py-5 px-6 text-sm font-bold text-[#38BDF8] bg-[#536DFE]/10 border-x border-[#536DFE]/20 w-1/3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#536DFE]" />
                      <span>DeepX Agent v2.6</span>
                    </div>
                  </th>
                  <th className="py-5 px-6 text-sm font-bold text-slate-400 w-1/3">Standard AI Assistants</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs sm:text-sm">
                {comparisons.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#131724]/50 transition-colors">
                    <td className="py-4 px-6 font-medium text-white">{row.feature}</td>
                    <td className="py-4 px-6 bg-[#536DFE]/5 border-x border-[#536DFE]/15 font-medium text-slate-100">
                      <div className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
                        <span>{row.deepx}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-slate-400">
                      <div className="flex items-start gap-2">
                        <X className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                        <span>{row.others}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
};
