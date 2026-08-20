import React, { useState } from 'react';
import { Download, ArrowRight, Copy, Check, Sparkles } from 'lucide-react';

export const HeroSection: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const installCmd = 'git clone https://github.com/supeston/DeepCLI.git && cd DeepCLI && cscript run_cli.vbs';

  const handleCopy = () => {
    navigator.clipboard.writeText(installCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative pt-32 pb-16 md:pt-44 md:pb-24 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Antigravity Pill Label */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-blue-500/10 border border-blue-500/20 text-[#8AB4F8] mb-8 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#8AB4F8]" />
            <span>Google Antigravity Agent Harness 2.6</span>
          </div>

          {/* Main Headline (Google Antigravity style) */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-white mb-8 leading-[1.08]">
            Experience liftoff with the{' '}
            <span className="text-google-gradient font-medium">next-gen agent platform</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-[#9AA0A6] mb-10 max-w-3xl mx-auto leading-relaxed font-normal">
            DeepX Antigravity is built for developer trust. Execute interactive workflows with native{' '}
            <span className="text-white font-medium">Windows ConPTY</span>, capture rich context via{' '}
            <span className="text-white font-medium">WinRT Clipboard History</span>, and harness zero-telemetry Dual-Engine reasoning.
          </p>

          {/* Action CTAs (Google Antigravity style) */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
            <a
              href="#download"
              className="w-full sm:w-auto google-btn-primary px-8 py-3.5 text-sm font-medium"
              data-testid="hero-primary-cta"
            >
              <Download className="w-4 h-4" />
              <span>Download for Windows</span>
            </a>

            <a
              href="#features"
              className="w-full sm:w-auto google-btn-secondary px-8 py-3.5 text-sm font-medium"
            >
              <span>Explore Platform</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </a>
          </div>

          {/* 1-Click Code Box */}
          <div className="max-w-xl mx-auto mb-16">
            <div className="flex items-center justify-between p-3.5 pl-5 rounded-2xl bg-[#111420]/90 border border-white/10 shadow-2xl backdrop-blur-xl">
              <div className="flex items-center gap-3 overflow-hidden text-xs font-mono text-slate-300">
                <span className="text-[#8AB4F8] select-none font-bold">PS&gt;</span>
                <span className="truncate">{installCmd}</span>
              </div>
              <button
                onClick={handleCopy}
                className="ml-3 p-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-slate-300 hover:text-white transition-colors flex items-center gap-1.5 text-xs font-medium"
                aria-label="Copy install command"
                data-testid="hero-copy-cmd-btn"
              >
                {copied ? (
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
          </div>
        </div>
      </div>
    </section>
  );
};
