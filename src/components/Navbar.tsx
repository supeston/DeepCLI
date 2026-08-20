import React, { useState, useRef } from 'react';
import {
  Menu,
  X,
  Terminal,
  ChevronDown,
  ArrowUpRight,
  Download,
  Package,
  Sparkles,
  Tag,
  BarChart3,
  History,
  Github
} from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

const NavHoverIcon: React.FC<{ icon: React.ElementType }> = ({ icon: Icon }) => (
  <span className="max-w-0 opacity-0 -translate-x-1.5 group-hover:max-w-[20px] group-hover:opacity-100 group-hover:translate-x-0 group-hover:mr-1.5 transition-all duration-300 ease-out overflow-hidden inline-flex items-center justify-center shrink-0">
    <Icon className="w-3.5 h-3.5 text-[#536DFE] shrink-0" />
  </span>
);

export const Navbar: React.FC<{ isVisible?: boolean }> = ({ isVisible = true }) => {
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
      className={`fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200 transition-all duration-500 ease-out ${
        isVisible ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0 pointer-events-none'
      }`}
      data-testid="navbar-header"
    >
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Brand Logo */}
          <div className="flex items-center gap-2 shrink-0 z-10 relative">
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

          {/* Middle Navigation (Desktop) - Staggered entrance, no wrapping, expands cleanly */}
          <nav className="hidden lg:flex items-center gap-1 xl:gap-2 text-sm font-medium text-gray-600 whitespace-nowrap">
            {/* Products Dropdown */}
            <div
              className={`relative transition-all duration-500 ease-out delay-[120ms] ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
              onMouseEnter={() => handleMouseEnter('products')}
              onMouseLeave={handleMouseLeave}
            >
              <button className="group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors whitespace-nowrap shrink-0">
                <NavHoverIcon icon={Package} />
                <span>Products</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60 ml-1 group-hover:text-[#536DFE] transition-colors" />
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
                      className="flex w-full text-left items-start gap-3 p-2.5 rounded-xl hover:bg-gray-50 text-gray-700 hover:text-gray-900 transition-colors whitespace-normal"
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
              className={`relative transition-all duration-500 ease-out delay-[190ms] ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
              onMouseEnter={() => handleMouseEnter('usecases')}
              onMouseLeave={handleMouseLeave}
            >
              <button className="group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-colors whitespace-nowrap shrink-0">
                <NavHoverIcon icon={Sparkles} />
                <span>Use Cases</span>
                <ChevronDown className="w-3.5 h-3.5 opacity-60 ml-1 group-hover:text-[#536DFE] transition-colors" />
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
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors whitespace-normal"
                    >
                      Frontend Engineering
                    </button>
                    <button
                      onClick={() => handleScrollTo('usecases')}
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors whitespace-normal"
                    >
                      Full-Stack Systems
                    </button>
                    <button
                      onClick={() => handleScrollTo('usecases')}
                      className="block w-full text-left p-2 rounded-xl hover:bg-gray-50 text-sm text-gray-700 hover:text-gray-900 transition-colors whitespace-normal"
                    >
                      Autonomous Code Review
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => handleScrollTo('pricing')}
              className={`group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-all duration-500 ease-out delay-[260ms] whitespace-nowrap shrink-0 ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
            >
              <NavHoverIcon icon={Tag} />
              <span>Pricing</span>
            </button>

            <button
              onClick={() => handleScrollTo('comparison')}
              className={`group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-all duration-500 ease-out delay-[330ms] whitespace-nowrap shrink-0 ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
            >
              <NavHoverIcon icon={BarChart3} />
              <span>Benchmarks</span>
            </button>

            <Link
              to="/logs"
              className={`group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-all duration-500 ease-out delay-[400ms] whitespace-nowrap shrink-0 ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
            >
              <NavHoverIcon icon={History} />
              <span>Updates</span>
            </Link>

            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className={`group flex items-center px-3 py-2 rounded-full hover:text-gray-900 hover:bg-gray-100 transition-all duration-500 ease-out delay-[470ms] whitespace-nowrap shrink-0 ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
              data-testid="github-link"
            >
              <NavHoverIcon icon={Github} />
              <span>GitHub</span>
              <ArrowUpRight className="w-3 h-3 opacity-60 ml-1 group-hover:text-[#536DFE] transition-colors" />
            </a>
          </nav>

          {/* Right Action - Staggered button & mobile menu */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <button
              onClick={() => handleScrollTo('download')}
              className={`google-btn-primary !px-3 !py-1.5 sm:!px-6 sm:!py-2.5 text-xs sm:text-sm font-medium gap-1.5 sm:gap-2 whitespace-nowrap shrink-0 transition-all duration-500 ease-out delay-[160ms] sm:delay-[540ms] ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
              data-testid="cta-download-btn"
            >
              <Download className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
              <span className="whitespace-nowrap">
                Download<span className="hidden sm:inline"> DeepX</span>
              </span>
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`lg:hidden p-2 rounded-full text-gray-500 hover:text-gray-900 bg-gray-100 border border-gray-200 shrink-0 transition-all duration-500 ease-out delay-[280ms] ${
                isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'
              }`}
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
              className="flex items-center gap-2 w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <Package className="w-4 h-4 text-[#536DFE]" />
              <span>Products & Features</span>
            </button>
            <button
              onClick={() => handleScrollTo('usecases')}
              className="flex items-center gap-2 w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <Sparkles className="w-4 h-4 text-[#536DFE]" />
              <span>Use Cases</span>
            </button>
            <button
              onClick={() => handleScrollTo('pricing')}
              className="flex items-center gap-2 w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <Tag className="w-4 h-4 text-[#536DFE]" />
              <span>Pricing (Free & Open Source)</span>
            </button>
            <button
              onClick={() => handleScrollTo('comparison')}
              className="flex items-center gap-2 w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <BarChart3 className="w-4 h-4 text-[#536DFE]" />
              <span>Technical Benchmarks</span>
            </button>
            <Link
              to="/logs"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <History className="w-4 h-4 text-[#536DFE]" />
              <span>Updates</span>
            </Link>
            <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
              <a
                href="https://github.com/supeston/DeepCLI"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-full text-xs font-medium text-center bg-gray-100 text-gray-700 border border-gray-200"
              >
                <Github className="w-4 h-4 text-[#536DFE]" />
                <span>GitHub Repository</span>
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
