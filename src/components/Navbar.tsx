import React, { useState, useEffect } from 'react';
import { Github, Terminal, Menu, X, ArrowUpRight } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
          ? 'bg-[#090A0F]/85 backdrop-blur-xl border-b border-[#536DFE]/20 py-3 shadow-2xl shadow-black/50'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <a
            href="#"
            className="flex items-center gap-3 group transition-transform duration-200 hover:scale-[1.02]"
            data-testid="nav-logo-link"
          >
            <img
              src="full_logo.png"
              alt="DeepX Logo"
              className="h-9 w-auto max-w-[170px] object-contain"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
                const fallback = document.getElementById('navbar-fallback-brand');
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div id="navbar-fallback-brand" className="hidden items-center gap-2">
              <img src="logo.png" alt="DeepX Icon" className="h-8 w-8 rounded-lg" />
              <span className="font-bold text-xl tracking-tight text-white">DEEPX</span>
            </div>
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#536DFE]/15 text-[#38BDF8] border border-[#536DFE]/30">
              v2.6
            </span>
          </a>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-white transition-colors duration-150">
              Features
            </a>
            <a href="#architecture" className="hover:text-white transition-colors duration-150">
              Architecture
            </a>
            <a href="#terminal" className="hover:text-white transition-colors duration-150">
              Live Terminal
            </a>
            <a href="#comparison" className="hover:text-white transition-colors duration-150">
              Benchmarks
            </a>
            <a href="#download" className="hover:text-white transition-colors duration-150">
              Installation
            </a>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium text-slate-300 bg-[#131722] hover:bg-[#1C2233] border border-slate-700/60 hover:border-[#536DFE]/40 transition-all duration-200"
              data-testid="github-link"
            >
              <Github className="w-4 h-4 text-slate-300" />
              <span>GitHub</span>
              <ArrowUpRight className="w-3 h-3 text-slate-400" />
            </a>

            <a
              href="#download"
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold text-white bg-gradient-to-r from-[#536DFE] to-[#38BDF8] hover:from-[#657DFE] hover:to-[#4FCBFF] shadow-lg shadow-[#536DFE]/25 transition-all duration-200 transform hover:-translate-y-0.5"
              data-testid="cta-download-btn"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Launch DeepX</span>
            </a>
          </div>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg bg-[#131722] text-slate-300 hover:text-white border border-slate-800"
              aria-label="Toggle Navigation Menu"
              data-testid="mobile-menu-toggle"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div
            data-testid="mobile-menu-dropdown"
            className="md:hidden mt-3 p-4 rounded-2xl glass-panel border border-[#536DFE]/30 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200"
          >
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-200 hover:text-[#38BDF8] py-1"
            >
              Features
            </a>
            <a
              href="#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-200 hover:text-[#38BDF8] py-1"
            >
              Architecture
            </a>
            <a
              href="#terminal"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-200 hover:text-[#38BDF8] py-1"
            >
              Live Terminal
            </a>
            <a
              href="#comparison"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-200 hover:text-[#38BDF8] py-1"
            >
              Benchmarks
            </a>
            <a
              href="#download"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-200 hover:text-[#38BDF8] py-1"
            >
              Installation
            </a>
            <div className="pt-2 border-t border-slate-800 flex gap-2">
              <a
                href="https://github.com/supeston/DeepCLI"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex justify-center items-center gap-1.5 py-2 rounded-xl text-xs font-medium bg-[#131722] text-slate-200 border border-slate-700"
              >
                <Github className="w-4 h-4" />
                GitHub
              </a>
              <a
                href="#download"
                onClick={() => setMobileMenuOpen(false)}
                className="flex-1 inline-flex justify-center items-center gap-1.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-[#536DFE] to-[#38BDF8] text-white"
              >
                <Terminal className="w-4 h-4" />
                Get Started
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
