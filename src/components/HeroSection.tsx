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
    <section className="relative pt-28 pb-16 md:pt-40 md:pb-24 overflow-hidden bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo Showcase */}
          <div className="relative inline-block mb-8">
            <div className="absolute inset-0 bg-[#1a73e8]/5 rounded-full blur-3xl pointer-events-none w-32 h-32" />
            <img
              src="log.png"
              alt="DeepX Transparent Logo"
              className="relative z-10 w-24 h-24 sm:w-28 sm:h-28 mx-auto object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'logo.png';
              }}
            />
          </div>

          {/* DeepX Pill Label */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-[#1a73e8]/10 border border-[#1a73e8]/20 text-[#1a73e8] mb-8 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#1a73e8]" />
            <span>DeepX Agent Harness 2.6</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-gray-900 mb-8 leading-[1.08]">
            Experience liftoff with{' '}
            <span className="text-blue-gradient font-medium">DeepX</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed font-normal">
            DeepX is built for developer trust. Execute interactive workflows with native{' '}
            <span className="text-gray-900 font-medium">Windows ConPTY</span>, capture rich context via{' '}
            <span className="text-gray-900 font-medium">WinRT Clipboard History</span>, and harness zero-telemetry Dual-Engine reasoning.
          </p>

          {/* Action CTAs */}
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
              <ArrowRight className="w-4 h-4 text-[#1a73e8]" />
            </a>
          </div>

          {/* 1-Click Code Box */}
          <div className="max-w-xl mx-auto mb-16">
            <div className="flex items-center justify-between p-3.5 pl-5 rounded-2xl bg-white border border-gray-200 shadow-lg shadow-gray-200/50">
              <div className="flex items-center gap-3 overflow-hidden text-xs font-mono text-gray-600">
                <span className="text-[#1a73e8] select-none font-bold">PS&gt;</span>
                <span className="truncate">{installCmd}</span>
              </div>
              <button
                onClick={handleCopy}
                className="ml-3 p-2 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-900 border border-gray-200 transition-colors flex items-center gap-1.5 text-xs font-medium"
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
