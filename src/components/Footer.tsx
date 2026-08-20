import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-12" data-testid="site-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <img
              src="logo.png"
              alt="DeepX Square Logo"
              className="w-8 h-8 rounded-lg shadow-sm"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'log.png';
              }}
            />
            <span className="text-xl font-medium tracking-tight text-gray-900">
              DeepX
            </span>
          </div>

          <div className="text-sm font-medium text-gray-500">
            Created by{' '}
            <a
              href="https://github.com/supeston"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#1a73e8] hover:underline"
              data-testid="footer-author-link"
            >
              supeston
            </a>
          </div>

          <div className="flex items-center gap-6 text-sm font-medium text-gray-500">
            <a href="https://github.com/supeston/DeepCLI" className="hover:text-gray-900 transition-colors">
              GitHub
            </a>
            <a href="https://github.com/supeston/DeepCLI/issues" className="hover:text-gray-900 transition-colors">
              Issues
            </a>
            <a href="https://github.com/supeston/DeepCLI/blob/main/LICENSE" className="hover:text-gray-900 transition-colors">
              License (MIT)
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
