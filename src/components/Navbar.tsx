import React, { useState } from 'react';
import { Menu, X, Terminal, ChevronDown, ArrowUpRight, Download } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200"
      data-testid="navbar-header"
    >
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex items-center justify-between">
          {/* Left: Brand Logo & Pills */}
          <div className="flex items-center gap-4">
            <a href="/" className="flex items-center gap-2 group">
              <img
                src="log.png"
                alt="DeepX Logo"
                className="h-7 w-auto object-contain transition-transform duration-300 group-hover:scale-105"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'logo.png';
                }}
              />
              <span className="text-2xl font-medium tracking-tight text-gray-900 group-hover:text-[#1a73e8] transition-colors">
                deepx
              </span>
            </a>

            {/* Antigravity style pill */}
            <div className="hidden md:flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#1a73e8]/10 text-[#1a73e8] border border-[#1a73e8]/20">
              DeepX 2.6
            </div>
          </div>

          {/* Middle Navigation (Desktop) */}
          <nav className="hidden lg:flex items-center gap-1.5 text-sm font-medium text-gray-600">
            {/* Products Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setActiveDropdown('products')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
                <span>Products</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'products' && (
                <div className="absolute top-full left-0 mt-1 w-64 p-3 bg-white rounded-2xl border border-gray-200 shadow-xl animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="text-[11px] font-semibold text-gray-400 px-3 py-1.5 uppercase tracking-wider">
                    Core Surfaces
                  </div>
                  <a
                    href="#features"
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-gray-50 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <Terminal className="w-4 h-4 text-[#1a73e8] mt-1 shrink-0" />
                    <div>
                      <div className="font-medium text-sm text-gray-900">DeepX CLI</div>
                      <div className="text-xs text-gray-500">Terminal-first ConPTY agent</div>
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
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
                <span>Use Cases</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'usecases' && (
                <div className="absolute top-full left-0 mt-1 w-64 p-3 bg-white rounded-2xl border border-gray-200 shadow-xl animate-in fade-in slide-in-from-top-2 duration-150">
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900">
                    Frontend Engineering
                  </a>
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900">
                    Full-Stack Systems
                  </a>
                  <a href="#usecases" className="block p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900">
                    Autonomous Code Review
                  </a>
                </div>
              )}
            </div>

            <a href="#pricing" className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
              Pricing
            </a>
            <a href="#comparison" className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
              Benchmarks
            </a>
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors inline-flex items-center gap-1"
              data-testid="github-link"
            >
              <span>GitHub</span>
              <ArrowUpRight className="w-3 h-3 opacity-60" />
            </a>
          </nav>

          {/* Right Action: Download Pill */}
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
              className="lg:hidden p-2 rounded-full text-gray-500 hover:text-gray-900 bg-gray-100 border border-gray-200"
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
            className="lg:hidden mt-3 p-5 rounded-3xl bg-white border border-gray-200 space-y-3 shadow-xl animate-in fade-in slide-in-from-top-2"
          >
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Products & Features
            </a>
            <a
              href="#usecases"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Use Cases
            </a>
            <a
              href="#pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Pricing (Free & Open Source)
            </a>
            <a
              href="#comparison"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Technical Benchmarks
            </a>
            <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
              <a
                href="https://github.com/supeston/DeepCLI"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-2.5 rounded-full text-xs font-medium text-center bg-gray-100 text-gray-700 border border-gray-200"
              >
                GitHub Repository
              </a>
              <a
                href="#download"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-2.5 rounded-full text-xs font-semibold text-center bg-[#1a73e8] text-white shadow-md shadow-[#1a73e8]/30"
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
