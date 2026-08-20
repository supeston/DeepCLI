import React from 'react';
import { Github, ArrowUp } from 'lucide-react';

export const Footer: React.FC = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer data-testid="site-footer" className="border-t border-slate-800/80 bg-[#07080D] relative z-10 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo & Info */}
          <div className="flex items-center gap-3">
            <img
              src="logo.png"
              alt="DeepX Square Logo"
              className="h-7 w-7 rounded-lg object-contain"
            />
            <div className="text-left">
              <div className="text-sm font-bold text-white tracking-wide">DEEPX AGENT</div>
              <div className="text-xs text-slate-400">Autonomous Engineering AI for Windows</div>
            </div>
          </div>

          {/* Author Attribution */}
          <div className="text-xs text-slate-400 text-center flex items-center gap-1.5 flex-wrap justify-center">
            <span>Created by</span>
            <a
              href="https://github.com/supeston"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-slate-200 hover:text-[#38BDF8] underline decoration-[#536DFE]/40 underline-offset-4 transition-colors"
              data-testid="footer-author-link"
            >
              supeston
            </a>
            <span>• MIT Licensed Open Source</span>
          </div>

          {/* Actions & Scroll Up */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-[#121520] hover:bg-[#1C2132] text-slate-400 hover:text-white border border-slate-800 transition-colors"
              aria-label="GitHub Repository"
            >
              <Github className="w-4 h-4" />
            </a>
            <button
              onClick={scrollToTop}
              className="p-2 rounded-xl bg-[#121520] hover:bg-[#1C2132] text-slate-400 hover:text-white border border-slate-800 transition-colors"
              aria-label="Scroll to top"
              data-testid="footer-scroll-top"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
};
