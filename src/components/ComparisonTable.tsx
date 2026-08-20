import React from 'react';
import { Check, Minus } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

export const ComparisonTable: React.FC = () => {
  const rows = [
    { feature: 'Interactive Terminal Execution (ConPTY)', deepx: true, others: false },
    { feature: 'WinRT Clipboard Context (Win+Shift+S)', deepx: true, others: false },
    { feature: 'Process Lifecycle & Zombie Cleanup', deepx: true, others: false },
    { feature: 'Zero Telemetry & Local Only', deepx: true, others: 'Partial' },
    { feature: 'Auto-scaffolding Python Environments', deepx: true, others: false },
  ];

  return (
    <section id="comparison" className="py-24 bg-white overflow-hidden">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <ScrollReveal direction="up" delay={100}>
            <h2 className="text-3xl sm:text-4xl font-normal text-[#1F1F1F] tracking-tight mb-4">
              Technical Benchmarks
            </h2>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200}>
            <TextScrollReveal
              text="Why Windows developers choose DeepX over standard web-based AI tools."
              className="text-[#5F6368] font-normal"
              highlightWords={['Windows', 'developers', 'DeepX']}
            />
          </ScrollReveal>
        </div>

        <ScrollReveal direction="up" delay={300}>
          <div className="antigravity-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="p-6 text-sm font-medium text-slate-500 w-1/2">Capability</th>
                    <th className="p-6 text-sm font-semibold text-[#1F1F1F] bg-[#536DFE]/10 text-center w-1/4">DeepX CLI</th>
                    <th className="p-6 text-sm font-medium text-slate-500 text-center w-1/4">Standard Agents</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map((row, i) => (
                    <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                      <td className="p-6 text-sm text-slate-700">{row.feature}</td>
                      <td className="p-6 bg-[#536DFE]/5 text-center">
                        {row.deepx ? (
                          <Check className="w-5 h-5 text-[#536DFE] mx-auto" />
                        ) : (
                          <Minus className="w-5 h-5 text-slate-300 mx-auto" />
                        )}
                      </td>
                      <td className="p-6 text-center">
                        {row.others === true ? (
                          <Check className="w-5 h-5 text-slate-400 mx-auto" />
                        ) : row.others === false ? (
                          <Minus className="w-5 h-5 text-slate-300 mx-auto" />
                        ) : (
                          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded-md">
                            {row.others}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
