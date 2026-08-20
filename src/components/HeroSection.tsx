import React, { useState } from 'react';
import { Monitor, ArrowRight, Copy, Check } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

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
          {/* Centered Brand Artwork */}
          <ScrollReveal direction="down" delay={100}>
            <div className="flex items-center justify-center gap-3 mb-6">
              <img
                src="full_logo.png"
                alt="DeepX"
                className="h-10 sm:h-12 w-auto object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'logo.png';
                }}
              />
            </div>
          </ScrollReveal>

          {/* Main Headline */}
          <ScrollReveal direction="up" delay={200}>
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-[#1F1F1F] mb-6 leading-[1.08]">
              Experience liftoff with the{' '}
              <span className="font-medium">next-gen agent platform</span>
            </h1>
          </ScrollReveal>

          {/* Subtitle with dynamic scroll-revealed words */}
          <ScrollReveal direction="up" delay={300}>
            <TextScrollReveal
              text="DeepX is built for developer trust. Execute interactive workflows with native Windows ConPTY, capture rich context via WinRT Clipboard History, and harness zero-telemetry Dual-Engine reasoning."
              className="text-lg sm:text-xl text-[#5F6368] mb-10 max-w-3xl mx-auto font-normal"
              highlightWords={['Windows', 'ConPTY', 'WinRT', 'Clipboard', 'History', 'Dual-Engine']}
            />
          </ScrollReveal>

          {/* Action CTAs */}
          <ScrollReveal direction="up" delay={400}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
              <button
                onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full sm:w-auto google-btn-primary px-8 py-3.5 text-sm font-medium"
                data-testid="hero-primary-cta"
              >
                <Monitor className="w-4 h-4" />
                <span>Download for Windows</span>
              </button>

              <button
                onClick={() => document.getElementById('terminal')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full sm:w-auto google-btn-secondary px-8 py-3.5 text-sm font-medium"
              >
                <span>Explore platform</span>
                <ArrowRight className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </ScrollReveal>

          {/* 1-Click Code Box */}
          <ScrollReveal direction="up" delay={500}>
            <div className="max-w-xl mx-auto mb-8">
              <div className="flex items-center justify-between p-3.5 pl-5 rounded-2xl bg-white border border-gray-200 shadow-lg shadow-gray-200/50">
                <div className="flex items-center gap-3 overflow-hidden text-xs font-mono text-gray-600">
                  <span className="text-[#536DFE] select-none font-bold">PS&gt;</span>
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
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
};
