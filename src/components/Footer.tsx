import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 py-12" data-testid="site-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center">
            <img
              src="full_logo.png"
              alt="DeepX Full Logo"
              className="h-9 sm:h-10 w-auto object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'logo.png';
              }}
            />
          </div>

          <div className="text-sm font-medium text-slate-500">
            Created by{' '}
            <a
              href="https://github.com/supeston"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#536DFE] hover:underline font-semibold"
              data-testid="footer-author-link"
            >
              supeston
            </a>
          </div>

          <div className="flex items-center gap-6 text-sm font-medium text-slate-500">
            <a href="https://github.com/supeston/DeepCLI" className="hover:text-slate-900 transition-colors">
              GitHub
            </a>
            <a href="https://github.com/supeston/DeepCLI/issues" className="hover:text-slate-900 transition-colors">
              Issues
            </a>
            <a href="https://github.com/supeston/DeepCLI/blob/main/LICENSE" className="hover:text-slate-900 transition-colors">
              License (MIT)
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
