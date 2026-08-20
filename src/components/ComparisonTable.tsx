import React from 'react';
import { Check, Minus } from 'lucide-react';

export const ComparisonTable: React.FC = () => {
  const rows = [
    { feature: 'Interactive Terminal Execution (ConPTY)', deepx: true, others: false },
    { feature: 'WinRT Clipboard Context (Win+Shift+S)', deepx: true, others: false },
    { feature: 'Process Lifecycle & Zombie Cleanup', deepx: true, others: false },
    { feature: 'Zero Telemetry & Local Only', deepx: true, others: 'Partial' },
    { feature: 'Auto-scaffolding Python Environments', deepx: true, others: false },
  ];

  return (
    <section id="comparison" className="py-24 bg-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-normal text-gray-900 tracking-tight mb-4">
            Technical Benchmarks
          </h2>
          <p className="text-gray-600">
            Why Windows developers choose DeepX over standard web-based AI tools.
          </p>
        </div>

        <div className="antigravity-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="p-6 text-sm font-medium text-gray-500 w-1/2">Capability</th>
                  <th className="p-6 text-sm font-semibold text-gray-900 bg-blue-50/50 text-center w-1/4">DeepX CLI</th>
                  <th className="p-6 text-sm font-medium text-gray-500 text-center w-1/4">Standard Agents</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                    <td className="p-6 text-sm text-gray-700">{row.feature}</td>
                    <td className="p-6 bg-blue-50/30 text-center">
                      {row.deepx ? (
                        <Check className="w-5 h-5 text-[#1a73e8] mx-auto" />
                      ) : (
                        <Minus className="w-5 h-5 text-gray-300 mx-auto" />
                      )}
                    </td>
                    <td className="p-6 text-center">
                      {row.others === true ? (
                        <Check className="w-5 h-5 text-gray-400 mx-auto" />
                      ) : row.others === false ? (
                        <Minus className="w-5 h-5 text-gray-300 mx-auto" />
                      ) : (
                        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
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
      </div>
    </section>
  );
};
