import React from 'react';
import { Layout, Database, Code2, ArrowRight } from 'lucide-react';

export const UseCasesSection: React.FC = () => {
  const cases = [
    {
      title: 'Frontend Engineering',
      icon: Layout,
      color: 'text-[#1a73e8]',
      bg: 'bg-[#1a73e8]/10',
      desc: 'Rapidly scaffold React components, debug CSS layouts, and optimize Tailwind configs from the terminal.',
      tags: ['React', 'Tailwind', 'Vite'],
    },
    {
      title: 'Full-Stack Systems',
      icon: Database,
      color: 'text-[#1a73e8]',
      bg: 'bg-[#1a73e8]/10',
      desc: 'Generate robust backend APIs, configure database schemas, and orchestrate Docker containers seamlessly.',
      tags: ['Node.js', 'Python', 'SQL'],
    },
    {
      title: 'Autonomous Refactoring',
      icon: Code2,
      color: 'text-[#1a73e8]',
      bg: 'bg-[#1a73e8]/10',
      desc: 'Point DeepX to a legacy codebase. It will analyze dependencies, apply modern patterns, and commit changes.',
      tags: ['Git', 'Clean Code', 'Testing'],
    },
  ];

  return (
    <section id="usecases" className="py-24 bg-gray-50 border-y border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-normal text-gray-900 tracking-tight mb-4">
            Designed for every engineering workflow
          </h2>
          <p className="text-gray-600 text-lg">
            Whether you are scaffolding a new web app or modernizing a legacy system, DeepX adapts to your tech stack via natural language commands.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {cases.map((c, i) => {
            const Icon = c.icon;
            return (
              <div
                key={i}
                className="antigravity-card p-8 group cursor-pointer hover:-translate-y-1 transition-transform duration-300"
              >
                <div className={`w-14 h-14 rounded-2xl ${c.bg} flex items-center justify-center mb-6`}>
                  <Icon className={`w-7 h-7 ${c.color}`} />
                </div>
                <h3 className="text-xl font-medium text-gray-900 mb-3 group-hover:text-[#1a73e8] transition-colors">
                  {c.title}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed mb-6">
                  {c.desc}
                </p>
                <div className="flex flex-wrap gap-2 mb-8">
                  {c.tags.map((t) => (
                    <span key={t} className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-gray-100 text-gray-600 border border-gray-200">
                      {t}
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-2 text-sm font-medium text-[#1a73e8] opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                  <span>Explore use case</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Free Tier Banner */}
        <div className="mt-16 rounded-3xl bg-white border border-gray-200 p-8 sm:p-12 flex flex-col md:flex-row items-center justify-between gap-8 shadow-sm">
          <div>
            <h3 className="text-2xl font-normal text-gray-900 mb-2">
              Open Source & Free for Developers
            </h3>
            <p className="text-gray-600">
              DeepX is available at no charge under the MIT License. Run it locally with your own API keys.
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
      </div>
    </section>
  );
};
