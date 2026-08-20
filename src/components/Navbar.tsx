import React, { useState, useEffect } from 'react';
import { ChevronDown, Download, Menu, X, ArrowUpRight, Terminal, Bot, Code2 } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      data-testid="navbar-header"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#090A0F]/80 backdrop-blur-2xl border-b border-white/[0.08] py-3.5 shadow-2xl shadow-black/60'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <a
            href="#"
            className="flex items-center gap-3 group transition-transform duration-200"
            data-testid="nav-logo-link"
          >
            <img
              src="full_logo.png"
              alt="DeepX Logo"
              className="h-8 sm:h-9 w-auto max-w-[170px] object-contain"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
                const fallback = document.getElementById('navbar-fallback-brand');
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div id="navbar-fallback-brand" className="hidden items-center gap-2">
              <img src="logo.png" alt="DeepX Icon" className="h-8 w-8 rounded-lg" />
              <span className="font-medium text-lg tracking-tight text-white">Antigravity</span>
            </div>
            <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-[#8AB4F8] border border-blue-500/20">
              Antigravity 2.6
            </span>
          </a>

          {/* Center Navigation Links (Google Antigravity style) */}
          <nav className="hidden lg:flex items-center gap-1 text-[14px] font-normal text-[#9AA0A6]">
            {/* Products Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setActiveDropdown('products')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-white hover:bg-white/[0.05] transition-colors">
                <span>Products</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'products' && (
                <div className="absolute top-full left-0 mt-1 w-72 p-3 bg-[#121520]/95 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="text-[11px] font-semibold text-slate-400 px-3 py-1.5 uppercase tracking-wider">
                    Core Surfaces
                  </div>
                  <a
                    href="#features"
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-white/[0.06] text-slate-200 hover:text-white transition-colors"
                  >
                    <Terminal className="w-4 h-4 text-[#8AB4F8] mt-1 shrink-0" />
                    <div>
                      <div className="font-medium text-sm text-white">DeepX CLI</div>
                      <div className="text-xs text-slate-400">Terminal-first ConPTY agent</div>
                    </div>
                  </a>
                  <a
                    href="#features"
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-white/[0.06] text-slate-200 hover:text-white transition-colors"
                  >
                    <Bot className="w-4 h-4 text-[#C58AF9] mt-1 shrink-0" />
                    <div>
                      <div className="font-medium text-sm text-white">DeepX Manager</div>
                      <div className="text-xs text-slate-400">Parallel multi-agent hub</div>
                    </div>
                  </a>
                  <a
                    href="#features"
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-white/[0.06] text-slate-200 hover:text-white transition-colors"
                  >
                    <Code2 className="w-4 h-4 text-[#34A853] mt-1 shrink-0" />
                    <div>
                      <div className="font-medium text-sm text-white">DeepX SDK</div>
                      <div className="text-xs text-slate-400">Python agent harness</div>
                    </div>
                  </a>
                </div>
              )}
            </div>

            {/* Use Cases Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setActiveDropdown('usecases')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-white hover:bg-white/[0.05] transition-colors">
                <span>Use Cases</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'usecases' && (
                <div className="absolute top-full left-0 mt-1 w-64 p-3 bg-[#121520]/95 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl animate-in fade-in slide-in-from-top-2 duration-150">
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-white/[0.06] text-sm text-slate-200 hover:text-white">
                    Frontend Engineering
                  </a>
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-white/[0.06] text-sm text-slate-200 hover:text-white">
                    Full-Stack Systems
                  </a>
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-white/[0.06] text-sm text-slate-200 hover:text-white">
                    Autonomous Code Review
                  </a>
                </div>
              )}
            </div>

            <a href="#pricing" className="px-3 py-2 rounded-full hover:text-white hover:bg-white/[0.05] transition-colors">
              Pricing
            </a>
            <a href="#comparison" className="px-3 py-2 rounded-full hover:text-white hover:bg-white/[0.05] transition-colors">
              Benchmarks
            </a>
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2 rounded-full hover:text-white hover:bg-white/[0.05] transition-colors inline-flex items-center gap-1"
              data-testid="github-link"
            >
              <span>GitHub</span>
              <ArrowUpRight className="w-3 h-3 opacity-60" />
            </a>
          </nav>

          {/* Right Action: Google Antigravity Download Pill */}
          <div className="flex items-center gap-3">
            <a
              href="#download"
              className="google-btn-primary text-xs sm:text-sm font-medium"
              data-testid="cta-download-btn"
            >
              <Download className="w-4 h-4" />
              <span>Download DeepX</span>
            </a>

            {/* Mobile hamburger toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-full text-slate-300 hover:text-white bg-white/[0.05] border border-white/10"
              aria-label="Toggle navigation"
              data-testid="mobile-menu-toggle"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div
            data-testid="mobile-menu-dropdown"
            className="lg:hidden mt-3 p-5 rounded-3xl bg-[#111420]/95 backdrop-blur-2xl border border-white/10 space-y-3 shadow-2xl animate-in fade-in slide-in-from-top-2"
          >
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-slate-200 hover:text-white"
            >
              Products & Features
            </a>
            <a
              href="#usecases"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-slate-200 hover:text-white"
            >
              Use Cases
            </a>
            <a
              href="#pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-slate-200 hover:text-white"
            >
              Pricing (Free & Open Source)
            </a>
            <a
              href="#comparison"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-slate-200 hover:text-white"
            >
              Technical Benchmarks
            </a>
            <div className="pt-3 border-t border-white/10 flex flex-col gap-2">
              <a
                href="https://github.com/supeston/DeepCLI"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-2.5 rounded-full text-xs font-medium text-center bg-white/[0.05] text-white border border-white/10"
              >
                GitHub Repository
              </a>
              <a
                href="#download"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-2.5 rounded-full text-xs font-semibold text-center bg-[#1a73e8] text-white shadow-lg shadow-[#1a73e8]/30"
              >
                Download for Windows
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
