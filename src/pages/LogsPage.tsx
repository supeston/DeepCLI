import React from 'react';
import { ScrollReveal } from '../components/ScrollReveal';

export const LogsPage: React.FC = () => {
  const logs = [
    {
      version: 'v2.6.0',
      date: 'Aug 20, 2026',
      changes: [
        'Massive revamp of Terminal Simulator with realistic variable typing and execution speeds.',
        'Added Syntax Highlighting for code blocks in Terminal Simulator.',
        'Introduced two complex scenarios: Docker OOM Debugging and Git Conflict Resolution.',
        'Refined Navbar UI dropdown logic with improved hover-bridge.',
        'Antigravity typography scroll animations applied across the platform.',
        'Brand identity solidified strictly as DeepX, maintaining the authentic #536DFE aesthetics.'
      ]
    },
    {
      version: 'v2.5.1',
      date: 'Aug 18, 2026',
      changes: [
        'Patched WinRT clipboard memory leak on continuous polling.',
        'Improved Playwright stealth masking to evade advanced Cloudflare challenges.',
        'Fixed an issue where ConPTY would sometimes hang when the child process abruptly terminated.'
      ]
    },
    {
      version: 'v2.5.0',
      date: 'Aug 15, 2026',
      changes: [
        'Initial DeepX public test launch.',
        'Added zero-telemetry Dual-Engine reasoning core.',
        'Introduced the Visual Clipboard architecture for immediate context feeding.',
        'Added baseline UI components and landing page.'
      ]
    }
  ];

  return (
    <div className="relative pt-32 pb-16 min-h-screen">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <ScrollReveal direction="down">
          <div className="mb-12">
            <h1 className="text-4xl sm:text-5xl font-normal text-[#1F1F1F] tracking-tight mb-4">
              Platform Updates
            </h1>
            <p className="text-lg text-[#5F6368] font-normal">
              Stay up-to-date with the latest features, fixes, and architectural improvements to DeepX.
            </p>
          </div>
        </ScrollReveal>

        <div className="space-y-12 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
          {logs.map((log, index) => (
            <ScrollReveal key={log.version} direction="up" delay={index * 100}>
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-[#536DFE] text-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-lg z-10 shadow-gray-200/50">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                    <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" />
                  </svg>
                </div>
                
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-6 rounded-2xl border border-gray-200 shadow-lg shadow-gray-200/50">
                  <div className="flex items-center justify-between mb-4">
                    <span className="px-3 py-1 bg-[#536DFE]/10 text-[#536DFE] text-sm font-bold rounded-full">
                      {log.version}
                    </span>
                    <time className="text-sm text-gray-500 font-medium">{log.date}</time>
                  </div>
                  <ul className="space-y-3">
                    {log.changes.map((change, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#536DFE] shrink-0 mt-1.5" />
                        <span>{change}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </div>
  );
};
