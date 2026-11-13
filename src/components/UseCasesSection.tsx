import React from 'react';
import { Layout, Database, Code2, ArrowRight } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

export const UseCasesSection: React.FC = () => {
  const cases = [
    {
      title: 'Coder Profile · AST & ConPTY',
      icon: Code2,
      color: 'text-[#536DFE]',
      bg: 'bg-[#536DFE]/10',
      desc: 'Indexes repository symbols on turn zero, reads bounded file slices in parallel, executes real pytest/build loops in Windows ConPTY, and stores .deepx_history checkpoints for instant /undo rollback.',
      tags: ['AST Repo Map', '/mode plan', '/undo Checkpoints'],
    },
    {
      title: 'Full-Stack & VDS DevOps',
      icon: Database,
      color: 'text-[#536DFE]',
      bg: 'bg-[#536DFE]/10',
      desc: 'Spawns persistent background tasks, inspects Docker & uvicorn logs live, and deploys directly to remote Linux servers over Paramiko SSH/SFTP via vds_cmd and vds_deploy.',
      tags: ['ConPTY Daemons', 'Paramiko SSH/SFTP', 'Docker'],
    },
    {
      title: 'OSINTer & Stealth Web Engine',
      icon: Layout,
      color: 'text-[#536DFE]',
      bg: 'bg-[#536DFE]/10',
      desc: 'Built-in Playwright Stealth 2.x browser automation, DaData EGRUL/INN lookup, Funstat Telegram intelligence, and WinRT clipboard vision capture (Win+Shift+S).',
      tags: ['Playwright Stealth 2.x', 'DaData & Funstat', 'WinRT Vision'],
    },
  ];

  return (
    <section id="usecases" className="py-24 deepx-section-band border-y border-slate-200/80 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <ScrollReveal direction="up" delay={100}>
            <h2 className="text-3xl sm:text-4xl font-normal text-[#111318] tracking-tight mb-4">
              Designed for every engineering workflow
            </h2>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200}>
            <TextScrollReveal
              text="Switch between specialized agent profiles (/style coder, universal, osinter) and execution modes (/mode instant, think, plan) without losing context."
              className="text-[#475569] text-lg font-normal"
              highlightWords={['coder,', 'universal,', 'osinter)', 'instant,', 'think,', 'plan)']}
            />
          </ScrollReveal>
        </div>

        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {cases.map((c, i) => {
            const Icon = c.icon;
            return (
              <ScrollReveal key={i} direction="up" delay={150 * (i + 1)}>
                <div
                  onClick={() => document.getElementById('terminal')?.scrollIntoView({ behavior: 'smooth' })}
                  className="deepx-card p-8 group cursor-pointer h-full flex flex-col justify-between"
                >
                  <div>
                    <div className={`w-12 h-12 rounded-xl ${c.bg} flex items-center justify-center mb-6 border border-[#536DFE]/15`}>
                      <Icon className={`w-6 h-6 ${c.color}`} />
                    </div>
                    <h3 className="text-xl font-medium text-[#111318] mb-3 group-hover:text-[#536DFE] transition-colors">
                      {c.title}
                    </h3>
                    <p className="text-[#475569] text-sm leading-relaxed mb-6">
                      {c.desc}
                    </p>
                  </div>
                  <div>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {c.tags.map((t) => (
                        <span
                          key={t}
                          className="px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-slate-100/90 text-slate-700 border border-slate-200/80"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 text-sm font-medium text-[#536DFE]">
                      <span>Inspect in Terminal Simulator</span>
                      <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
                    </div>
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </div>

        {/* Free Tier Banner */}
        <ScrollReveal direction="up" delay={400}>
          <div className="mt-16 deepx-card p-8 sm:p-12 flex flex-col md:flex-row items-center justify-between gap-8">
            <div>
              <h3 className="text-2xl font-normal text-[#111318] mb-2">
                Open Source & Free for Developers
              </h3>
              <p className="text-[#475569]">
                DeepX is available at no charge under the MIT License. Run it locally with zero API keys or token fees — powered by Playwright Stealth 2.x session emulation.
              </p>
            </div>
            <a
              href="https://github.com/supeston/DeepCLI"
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 google-btn-secondary"
            >
              View on GitHub
            </a>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
