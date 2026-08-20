import React, { useState } from 'react';
import { Terminal, Copy, Check, Sparkles, ArrowRight } from 'lucide-react';

export const HeroSection: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const installCmd = 'git clone https://github.com/supeston/DeepCLI.git && cd DeepCLI && cscript run_cli.vbs';

  const handleCopy = () => {
    navigator.clipboard.writeText(installCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Top Pill Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#536DFE]/10 border border-[#536DFE]/30 text-[#38BDF8] mb-8 animate-pulse-slow">
            <Sparkles className="w-3.5 h-3.5 text-[#536DFE]" />
            <span>DEEPX 2.6 • KERNEL-GRADE WINDOWS AI AGENT</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
            Next-Gen Autonomous{' '}
            <span className="text-gradient">Windows AI Agent</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-slate-300 mb-10 max-w-3xl mx-auto leading-relaxed font-normal">
            Equipped with true interactive <span className="text-white font-medium">Windows ConPTY</span>, native{' '}
            <span className="text-white font-medium">WinRT Clipboard History</span>, deep{' '}
            <span className="text-white font-medium">Media Inspection</span>, and zero-telemetry Dual-Engine intelligence.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <a
              href="#download"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-2xl text-sm font-semibold text-white bg-gradient-to-r from-[#536DFE] via-[#4361EE] to-[#38BDF8] hover:opacity-95 shadow-xl shadow-[#536DFE]/30 transition-all duration-200 transform hover:-translate-y-0.5"
              data-testid="hero-primary-cta"
            >
              <Terminal className="w-4 h-4" />
              <span>Get DeepX for Windows</span>
              <ArrowRight className="w-4 h-4" />
            </a>

            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-semibold text-slate-200 bg-[#131722]/80 hover:bg-[#1A2030] border border-slate-700/80 hover:border-[#536DFE]/50 transition-all duration-200"
            >
              <span>Explore GitHub Repository</span>
            </a>
          </div>

          {/* Interactive 1-Click Code Box */}
          <div className="max-w-xl mx-auto mb-16">
            <div className="flex items-center justify-between p-3 pl-4 rounded-xl bg-[#0E111A]/90 border border-[#536DFE]/25 shadow-2xl backdrop-blur-md">
              <div className="flex items-center gap-3 overflow-hidden text-xs font-mono text-slate-300">
                <span className="text-[#38BDF8] select-none font-bold">PS&gt;</span>
                <span className="truncate">{installCmd}</span>
              </div>
              <button
                onClick={handleCopy}
                className="ml-3 p-2 rounded-lg bg-[#181D2B] hover:bg-[#23293D] text-slate-300 hover:text-white transition-colors duration-150 flex items-center gap-1.5 text-xs font-medium"
                aria-label="Copy install command"
                data-testid="hero-copy-cmd-btn"
              >
                {copied ? (
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
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-2xl glass-panel border border-slate-800">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#38BDF8] mb-1">ConPTY</div>
              <div className="text-xs text-slate-400 font-medium">True Interactive Terminal</div>
            </div>
            <div className="p-4 rounded-2xl glass-panel border border-slate-800">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#A78BFA] mb-1">Win + V</div>
              <div className="text-xs text-slate-400 font-medium">WinRT Clipboard History</div>
            </div>
            <div className="p-4 rounded-2xl glass-panel border border-slate-800">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#10B981] mb-1">0 Process Leaks</div>
              <div className="text-xs text-slate-400 font-medium">Win32 Job Object Kill</div>
            </div>
            <div className="p-4 rounded-2xl glass-panel border border-slate-800">
              <div className="text-2xl sm:text-3xl font-extrabold text-white mb-1">100% Local</div>
              <div className="text-xs text-slate-400 font-medium">Playwright Stealth Engine</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
