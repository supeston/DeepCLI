import React, { useState } from 'react';
import { Terminal, Bot, Workflow, MousePointerClick, ArrowRight } from 'lucide-react';

type FeatureTab = 'cli' | 'reasoning' | 'workflows' | 'clipboard';

export const BentoGrid: React.FC = () => {
  const [activeTab, setActiveTab] = useState<FeatureTab>('cli');

  const tabs = [
    { id: 'cli', label: 'Command Line', icon: Terminal, color: 'text-[#1a73e8]' },
    { id: 'reasoning', label: 'Dual-Engine', icon: Bot, color: 'text-[#1a73e8]' },
    { id: 'workflows', label: 'Automation', icon: Workflow, color: 'text-[#1a73e8]' },
    { id: 'clipboard', label: 'Clipboard', icon: MousePointerClick, color: 'text-[#1a73e8]' },
  ] as const;

  const content: Record<FeatureTab, { title: string; desc: string; metrics: { label: string; val: string }[] }> = {
    cli: {
      title: 'Terminal-first Interactive Agent',
      desc: 'Execute directly in your Windows console. DeepX utilizes ConPTY to run real build commands, tests, and scripts natively without emulators. It observes the output stream in real-time, handling errors before you even see them.',
      metrics: [
        { label: 'Latency', val: '< 10ms' },
        { label: 'Integration', val: 'ConPTY' },
      ],
    },
    reasoning: {
      title: 'Zero-Telemetry Dual-Engine',
      desc: 'Separates planning from execution. The primary engine orchestrates workflows and manages state, while a secondary ultra-fast inference engine handles syntax generation and validation. 100% local tracking with zero cloud telemetry.',
      metrics: [
        { label: 'Architecture', val: 'Agentic' },
        { label: 'Telemetry', val: '0%' },
      ],
    },
    workflows: {
      title: 'End-to-End Task Automation',
      desc: 'Delegate complex refactoring, bug hunting, or scaffolding. DeepX reads your workspace, formulates an execution plan, spawns necessary terminal processes, validates the result, and commits via Git automatically.',
      metrics: [
        { label: 'Context', val: 'Infinite' },
        { label: 'Validation', val: 'Auto' },
      ],
    },
    clipboard: {
      title: 'WinRT Multimodal Context',
      desc: 'Seamlessly pass images to the agent without saving files. Hit Win+Shift+S, take a snippet of a broken UI or a graphical bug, and DeepX reads it directly from your Windows Clipboard using the WinRT API.',
      metrics: [
        { label: 'API', val: 'WinRT' },
        { label: 'Modality', val: 'Vision' },
      ],
    },
  };

  return (
    <section id="features" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase bg-blue-50 text-[#1a73e8] border border-blue-100 mb-6">
            Feature Explorer
          </div>
          <h2 className="text-4xl sm:text-5xl font-normal tracking-tight text-gray-900 mb-6">
            Built for developers for the <br className="hidden sm:block" />
            <span className="text-blue-gradient font-medium">CLI era</span>
          </h2>
          <p className="text-lg text-gray-600 font-normal">
            DeepX is a unified Command Line tool. No complex SDKs or web dashboards required. Just one binary in your Windows terminal.
          </p>
        </div>

        {/* Feature Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 mb-12">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                data-testid={`feature-tab-${tab.id}`}
                className={`flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'bg-gray-900 text-white shadow-lg scale-105'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : tab.color}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Active Feature Content */}
        <div className="antigravity-card p-8 sm:p-12 animate-in fade-in zoom-in-95 duration-300 relative overflow-hidden">
          {/* Subtle background glow */}
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-blue-50 rounded-full blur-3xl pointer-events-none" />

          <div className="grid lg:grid-cols-2 gap-12 items-center relative z-10">
            <div>
              <h3 className="text-3xl font-normal text-gray-900 mb-6">
                {content[activeTab].title}
              </h3>
              <p className="text-gray-600 text-lg leading-relaxed mb-8">
                {content[activeTab].desc}
              </p>

              <div className="grid grid-cols-2 gap-6 mb-8">
                {content[activeTab].metrics.map((m, i) => (
                  <div key={i} className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                    <div className="text-2xl font-medium text-[#1a73e8] mb-1">{m.val}</div>
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">{m.label}</div>
                  </div>
                ))}
              </div>

              <a
                href="#download"
                className="inline-flex items-center gap-2 text-sm font-medium text-[#1a73e8] hover:text-[#1557b0] transition-colors"
              >
                <span>Learn more about {tabs.find((t) => t.id === activeTab)?.label}</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            {/* Visual Placeholder (Replaces complex graphics for clean CLI look) */}
            <div className="bg-gray-50 rounded-3xl border border-gray-200 aspect-square flex items-center justify-center p-8 relative overflow-hidden shadow-inner">
              <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:20px_20px] opacity-50" />
              <div className="relative z-10 w-full max-w-sm">
                <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-6">
                  <div className="flex items-center gap-3 border-b border-gray-100 pb-4 mb-4">
                    <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
                      <Terminal className="w-5 h-5 text-[#1a73e8]" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">DeepX Windows</div>
                      <div className="text-xs text-gray-500">Active Session</div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="h-2 bg-gray-100 rounded-full w-3/4" />
                    <div className="h-2 bg-gray-100 rounded-full w-1/2" />
                    <div className="h-2 bg-gray-100 rounded-full w-5/6" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
