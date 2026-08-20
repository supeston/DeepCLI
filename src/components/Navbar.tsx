import React, { useState, useRef } from 'react';
import { Menu, X, Terminal, ChevronDown, ArrowUpRight, Download } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

export const Navbar: React.FC = () => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const handleMouseEnter = (menu: string) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setActiveDropdown(menu);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setActiveDropdown(null);
    }, 180);
  };

  const handleScrollTo = (id: string) => {
    setMobileMenuOpen(false);
    setActiveDropdown(null);
    if (location.pathname !== '/') {
      navigate('/');
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200"
      data-testid="navbar-header"
    >
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex items-center justify-between">
          {/* Left: Brand Logo */}
          <div className="flex items-center gap-2 lg:w-48 z-10 relative">
            <div className="relative group/logo">
              <Link to="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
                <img
                  src="full_logo.png"
                  alt="DeepX Logo"
                  className="h-8 sm:h-9 w-auto object-contain cursor-pointer"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'logo.png';
                  }}
                />
              </Link>
            </div>
          </div>

          {/* Middle Navigation (Desktop) */}
          <nav className="hidden lg:flex items-center gap-1.5 text-sm font-medium text-gray-600">
            {/* Products Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => handleMouseEnter('products')}
              onMouseLeave={handleMouseLeave}
            >
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
                <span>Products</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'products' && (
                <div
                  className="absolute top-full left-0 pt-2 w-64 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
                  onMouseEnter={() => handleMouseEnter('products')}
                  onMouseLeave={handleMouseLeave}
                >
                  <div className="p-3 bg-white rounded-2xl border border-gray-200 shadow-xl">
                    <div className="text-[11px] font-semibold text-gray-400 px-3 py-1.5 uppercase tracking-wider">
                      Core Surfaces
                    </div>
                    <button
                      onClick={() => handleScrollTo('terminal')}
                      className="flex w-full text-left items-start gap-3 p-2.5 rounded-xl hover:bg-gray-50 text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      <Terminal className="w-4 h-4 text-[#536DFE] mt-1 shrink-0" />
                      <div>
                        <div className="font-medium text-sm text-gray-900">DeepX CLI</div>
                        <div className="text-xs text-gray-500">Terminal-first ConPTY agent</div>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Use Cases Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => handleMouseEnter('usecases')}
              onMouseLeave={handleMouseLeave}
            >
              <button className="flex items-center gap-1 px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
                <span>Use Cases</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60" />
              </button>

              {activeDropdown === 'usecases' && (
                <div
                  className="absolute top-full left-0 pt-2 w-64 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
                  onMouseEnter={() => handleMouseEnter('usecases')}
                  onMouseLeave={handleMouseLeave}
                >
                  <div className="p-3 bg-white rounded-2xl border border-gray-200 shadow-xl space-y-1">
                    <button
                      onClick={() => handleScrollTo('usecases')}
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      Frontend Engineering
                    </button>
                    <button
                      onClick={() => handleScrollTo('usecases')}
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      Full-Stack Systems
                    </button>
                    <button
                      onClick={() => handleScrollTo('usecases')}
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      Autonomous Code Review
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button onClick={() => handleScrollTo('pricing')} className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
              Pricing
            </button>
            <button onClick={() => handleScrollTo('comparison')} className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
              Benchmarks
            </button>
            <Link to="/logs" className="px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors">
              Updates
            </Link>
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

          {/* Right Action */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleScrollTo('download')}
              className="google-btn-primary text-xs sm:text-sm font-medium"
              data-testid="cta-download-btn"
            >
              <Download className="w-4 h-4" />
              <span>Download DeepX</span>
            </button>

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
            <button
              onClick={() => handleScrollTo('features')}
              className="block w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Products & Features
            </button>
            <button
              onClick={() => handleScrollTo('usecases')}
              className="block w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Use Cases
            </button>
            <button
              onClick={() => handleScrollTo('pricing')}
              className="block w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Pricing (Free & Open Source)
            </button>
            <button
              onClick={() => handleScrollTo('comparison')}
              className="block w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Technical Benchmarks
            </button>
            <Link
              to="/logs"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Updates
            </Link>
            <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
              <a
                href="https://github.com/supeston/DeepCLI"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-2.5 rounded-full text-xs font-medium text-center bg-gray-100 text-gray-700 border border-gray-200"
              >
                GitHub Repository
              </a>
              <button
                onClick={() => handleScrollTo('download')}
                className="w-full py-2.5 rounded-full text-xs font-semibold text-center bg-[#536DFE] text-white shadow-md shadow-[#536DFE]/30"
              >
                Download for Windows
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
