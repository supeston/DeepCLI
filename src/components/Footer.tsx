import React from 'react';
import { Github, ArrowUp } from 'lucide-react';

export const Footer: React.FC = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer data-testid="site-footer" className="border-t border-white/[0.08] bg-[#07090E] relative z-10 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Navigation Grid (Google Antigravity style) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {/* Brand Info */}
          <div className="col-span-2 md:col-span-1 space-y-4">
            <div className="flex items-center gap-3">
              <img
                src="logo.png"
                alt="DeepX Square Logo"
                className="h-8 w-8 rounded-lg object-contain"
              />
              <span className="text-base font-medium text-white tracking-tight">Antigravity DeepX</span>
            </div>
            <p className="text-xs text-[#9AA0A6] leading-relaxed font-normal">
              Autonomous engineering platform for Windows. Built for developer trust and deep terminal control.
            </p>
          </div>

          {/* Product Column */}
          <div className="space-y-3 text-xs">
            <div className="font-semibold text-white uppercase tracking-wider text-[11px]">Product</div>
            <ul className="space-y-2 text-[#9AA0A6]">
              <li><a href="#features" className="hover:text-white transition-colors">DeepX CLI</a></li>
              <li><a href="#features" className="hover:text-white transition-colors">DeepX Manager</a></li>
              <li><a href="#features" className="hover:text-white transition-colors">DeepX SDK</a></li>
              <li><a href="#comparison" className="hover:text-white transition-colors">Benchmarks</a></li>
            </ul>
          </div>

          {/* Resources Column */}
          <div className="space-y-3 text-xs">
            <div className="font-semibold text-white uppercase tracking-wider text-[11px]">Resources</div>
            <ul className="space-y-2 text-[#9AA0A6]">
              <li><a href="https://github.com/supeston/DeepCLI" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="https://github.com/supeston/DeepCLI" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub Repository</a></li>
              <li><a href="https://github.com/supeston/DeepCLI/releases" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Releases</a></li>
              <li><a href="#download" className="hover:text-white transition-colors">Quick Install</a></li>
            </ul>
          </div>

          {/* Creator Column */}
          <div className="space-y-3 text-xs">
            <div className="font-semibold text-white uppercase tracking-wider text-[11px]">Creator</div>
            <div className="text-[#9AA0A6] space-y-2">
              <div>
                Created by{' '}
                <a
                  href="https://github.com/supeston"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold text-white hover:text-[#8AB4F8] underline decoration-blue-500/40 underline-offset-4 transition-colors"
                  data-testid="footer-author-link"
                >
                  supeston
                </a>
              </div>
              <div className="text-[11px] text-slate-500">MIT Licensed Open Source</div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#9AA0A6]">
          <div>
            © 2026 DeepX Antigravity. Built with Google Antigravity Design System.
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-slate-400 hover:text-white border border-white/10 transition-colors"
              aria-label="GitHub Repository"
            >
              <Github className="w-4 h-4" />
            </a>
            <button
              onClick={scrollToTop}
              className="p-2 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-slate-400 hover:text-white border border-white/10 transition-colors"
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
