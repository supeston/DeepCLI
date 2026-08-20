import React from 'react';
import { Check, Zap, Shield, Cpu, ArrowRight } from 'lucide-react';
import { ScrollReveal } from './ScrollReveal';

export const PricingSection: React.FC = () => {
  return (
    <section id="pricing" className="py-24 bg-white border-t border-slate-200 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <ScrollReveal direction="down">
            <h2 className="text-3xl sm:text-5xl font-normal text-[#1F1F1F] tracking-tight mb-6">
              Experience Flagship Intelligence. <br />
              <span className="font-medium text-[#536DFE]">Completely Free. Zero API Costs.</span>
            </h2>
            <p className="text-lg text-[#5F6368] font-normal leading-relaxed">
              DeepX is built with a native wrapper over DeepSeek infrastructure. It seamlessly emulates API sessions to provide unlimited, free direct access to flagship reasoning models—completely bypassing paid token limits, tier paywalls, and billing subscriptions.
            </p>
          </ScrollReveal>
        </div>

        {/* Pricing & Architecture Grid */}
        <div className="grid lg:grid-cols-12 gap-8 items-stretch max-w-6xl mx-auto">
          {/* Main Free Tier Card */}
          <div className="lg:col-span-7">
            <ScrollReveal direction="up" delay={150}>
              <div className="deepx-card p-8 sm:p-10 h-full flex flex-col justify-between border-2 border-[#536DFE]/40 relative bg-gradient-to-b from-white via-white to-slate-50 shadow-xl">
                <div className="absolute top-6 right-6">
                  <span className="px-3 py-1 bg-[#536DFE] text-white text-xs font-bold rounded-full uppercase tracking-wider shadow-sm">
                    Unlimited
                  </span>
                </div>

                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#536DFE] mb-2">
                    Community Edition
                  </div>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-5xl font-normal text-[#1F1F1F] tracking-tight">$0</span>
                    <span className="text-slate-500 font-medium">/ lifetime, no subscription required</span>
                  </div>
                  <p className="text-sm text-slate-600 mb-8 leading-relaxed">
                    Zero paywalls, zero token overages, and no credit card required. Everything runs locally with full flagship access out of the box.
                  </p>

                  <div className="space-y-4 mb-8">
                    {[
                      {
                        title: 'Free Flagship Model Access',
                        desc: 'Direct interaction with DeepSeek flagship models with high-speed token streaming.',
                      },
                      {
                        title: 'Session Emulation Engine',
                        desc: 'Bypasses commercial API limits and paid quota restrictions via built-in proxy emulation.',
                      },
                      {
                        title: 'Zero-Telemetry & Local Security',
                        desc: 'Your codebase and conversational context never leave your machine or get sent to third-party trackers.',
                      },
                      {
                        title: 'Native Windows Integration',
                        desc: 'Full ConPTY terminal support, background task management, and WinRT clipboard synchronization.',
                      },
                    ].map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-3.5">
                        <div className="w-5 h-5 rounded-full bg-[#536DFE]/10 flex items-center justify-center shrink-0 mt-0.5 text-[#536DFE]">
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-900">{feature.title}</div>
                          <div className="text-xs text-slate-500 leading-relaxed">{feature.desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                  className="w-full google-btn-indigo py-3.5 text-sm font-semibold justify-center shadow-lg shadow-[#536DFE]/25 cursor-pointer"
                >
                  <span>Download DeepX Free</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </ScrollReveal>
          </div>

          {/* Model Cards & Architecture Highlights */}
          <div className="lg:col-span-5 flex flex-col justify-between gap-6">
            {/* DeepSeek-V4-Pro Card */}
            <ScrollReveal direction="up" delay={250}>
              <div className="deepx-card p-6 sm:p-8 bg-slate-50 border border-slate-200 hover:border-[#536DFE]/40 transition-all">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-[#536DFE]/10 text-[#536DFE] flex items-center justify-center">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <span className="font-semibold text-slate-900 text-sm">DeepSeek-V4-Pro</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold bg-[#536DFE]/10 text-[#536DFE] px-2 py-0.5 rounded-full">
                    1.6T / 49B
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  1.6T total / 49B active params. Performance rivaling the world's top closed-source models. Built for complex codebase reasoning, full refactors, and architectural planning.
                </p>
              </div>
            </ScrollReveal>

            {/* DeepSeek-V4-Flash Card */}
            <ScrollReveal direction="up" delay={350}>
              <div className="deepx-card p-6 sm:p-8 bg-slate-50 border border-slate-200 hover:border-[#536DFE]/40 transition-all">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-[#38BDF8]/10 text-[#38BDF8] flex items-center justify-center">
                      <Zap className="w-4 h-4" />
                    </div>
                    <span className="font-semibold text-slate-900 text-sm">DeepSeek-V4-Flash</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold bg-[#38BDF8]/10 text-[#0284C7] px-2 py-0.5 rounded-full">
                    284B / 13B
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  284B total / 13B active params. Your fast, efficient, and economical choice. Rapid response streaming with exceptional accuracy for everyday scripts, debugging, and terminal automation.
                </p>
              </div>
            </ScrollReveal>

            {/* Zero Friction Card */}
            <ScrollReveal direction="up" delay={450}>
              <div className="deepx-card p-6 sm:p-8 bg-[#0F172A] text-white border border-slate-800 shadow-xl">
                <div className="flex items-center gap-2 text-xs font-mono text-[#536DFE] font-bold uppercase tracking-wider mb-2">
                  <Shield className="w-4 h-4" />
                  <span>No Keys, No Cards, Instant Liftoff</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  No billing setup or credit card input. Clone the repository, start the CLI, and immediately experience frontier AI capabilities.
                </p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </div>
    </section>
  );
};
