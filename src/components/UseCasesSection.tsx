import React from 'react';
import { Layout, Database, Cpu, Check, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export const UseCasesSection: React.FC = () => {
  const useCases = [
    {
      role: 'Frontend',
      title: 'Rapid UI Engineering & Visual QA',
      description:
        'Build and iterate on React, Vite, Tailwind, and Next.js interfaces. DeepX runs headless Playwright testing, validates DOM elements, and eliminates client-side errors before presenting code.',
      icon: <Layout className="w-5 h-5 text-[#8AB4F8]" />,
      highlights: ['Automated Vitest & React Testing', 'Playwright Headless Smoke QA', 'Zero CSS & AST syntax regression'],
    },
    {
      role: 'Fullstack',
      title: 'Kernel-Grade Backend & Microservices',
      description:
        'Orchestrate async FastAPI, Django, Node.js, and Docker processes. ConPTY handles interactive prompts while Win32 Job Objects guarantee that background processes never turn into zombies in Task Manager.',
      icon: <Database className="w-5 h-5 text-[#34A853]" />,
      highlights: ['JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE', 'Interactive CLI Prompts [y/N]', 'Dual-Engine DeepSeek Streaming'],
    },
    {
      role: 'Science & AI',
      title: 'Multimedia & Autonomous Data Pipelines',
      description:
        'Technical inspection of 4K/HDR video containers, audio codecs, EXIF metadata, and automated data scripts with immediate bytecode compilation verification.',
      icon: <Cpu className="w-5 h-5 text-[#C58AF9]" />,
      highlights: ['PyMediaInfo / ffprobe Metadata', 'Native WinRT Win+V Bitmap Sync', 'Verification AST Compiler Barrier'],
    },
  ];

  return (
    <section id="usecases" className="py-20 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-[#8AB4F8] border border-blue-500/20 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>VERSATILE CAPABILITIES</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-normal text-white tracking-tight mb-4">
            Designed for every engineering workflow
          </h2>
          <p className="text-[#9AA0A6] text-sm sm:text-base">
            From single-file scripts to large-scale monorepos, DeepX provides the right balance of speed and deep architectural reasoning.
          </p>
        </div>

        {/* Use Cases Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {useCases.map((uc, idx) => (
            <div
              key={idx}
              className="antigravity-card p-8 flex flex-col justify-between hover:scale-[1.02] transition-transform duration-300"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="p-3 rounded-2xl bg-white/[0.05] border border-white/10">{uc.icon}</div>
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-white/[0.05] text-[#8AB4F8] border border-white/10">
                    {uc.role}
                  </span>
                </div>
                <h3 className="text-xl font-medium text-white mb-3">{uc.title}</h3>
                <p className="text-sm text-[#9AA0A6] leading-relaxed mb-6 font-normal">
                  {uc.description}
                </p>
              </div>

              <div className="pt-4 border-t border-white/[0.08] space-y-2">
                {uc.highlights.map((h, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-slate-300 font-normal">
                    <Check className="w-3.5 h-3.5 text-[#34A853] shrink-0" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Pricing / Solutions Banner (Google Antigravity style) */}
        <div id="pricing" className="antigravity-card p-8 sm:p-12 rounded-[32px] text-center max-w-4xl mx-auto border border-blue-500/20 bg-gradient-to-b from-[#111628] to-[#0A0D18]">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-[#34A853]/15 text-[#34A853] border border-[#34A853]/30 mb-4">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>AVAILABLE AT NO CHARGE</span>
          </div>
          <h3 className="text-2xl sm:text-4xl font-medium text-white mb-3">
            Open Source &amp; Free for Developers
          </h3>
          <p className="text-sm sm:text-base text-[#9AA0A6] max-w-2xl mx-auto mb-8 font-normal">
            DeepX Antigravity is released under the permissive MIT License. No proprietary tokens or mandatory subscription fees.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="#download" className="google-btn-primary text-sm font-medium">
              <span>Get Started Free</span>
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="google-btn-secondary text-sm font-medium"
            >
              <span>View Source on GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
