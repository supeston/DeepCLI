import React from 'react';
import { Check, Zap, Shield, Cpu, ArrowRight } from 'lucide-react';
import { ScrollReveal } from './ScrollReveal';

export const PricingSection: React.FC = () => {
  return (
    <section id="pricing" className="py-24 deepx-section-clear border-t border-slate-200/80 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <ScrollReveal direction="down">
            <h2 className="text-3xl sm:text-5xl font-normal text-[#111318] tracking-tight mb-6">
              Experience Flagship Intelligence. <br />
              <span className="font-medium text-[#536DFE]">Completely Free. Zero API Costs.</span>
            </h2>
            <p className="text-lg text-[#475569] font-normal leading-relaxed">
              DeepX connects directly to DeepSeek via Playwright Stealth 2.x browser session emulation. Once you sign in, the session attaches in the same terminal window immediately—with automatic state.json persistence and built-in account suspension diagnostics.
            </p>
          </ScrollReveal>
        </div>

        {/* Pricing & Architecture Grid */}
        <div className="grid lg:grid-cols-12 gap-8 items-stretch max-w-6xl mx-auto">
          {/* Main Free Tier Card */}
          <div className="lg:col-span-7">
            <ScrollReveal direction="up" delay={150}>
              <div className="deepx-card p-8 sm:p-10 h-full flex flex-col justify-between border border-[#536DFE]/35 relative shadow-xl">
                <div className="absolute top-6 right-6">
                  <span className="px-3 py-1 bg-[#536DFE]/10 text-[#536DFE] border border-[#536DFE]/25 text-xs font-mono font-medium rounded-full">
                    Unlimited
                  </span>
                </div>

                <div>
                  <div className="text-xs font-mono font-medium text-[#536DFE] mb-2">
                    Community Edition · MIT License
                  </div>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-5xl font-mono font-normal text-[#111318] tracking-tight">$0</span>
                    <span className="text-slate-500 font-medium">/ lifetime, zero token billing</span>
                  </div>
                  <p className="text-sm text-[#475569] mb-8 leading-relaxed">
                    No API keys, no per-token invoices, and no credit card required. Everything runs locally on your Windows machine.
                  </p>

                  <div className="space-y-4 mb-8">
                    {[
                      {
                        title: 'Instant Post-Login Handoff & Ban Guard',
                        desc: 'Attaches your session in-place immediately after login without restarting the terminal, and displays exact expiration timestamps if a DeepSeek account is suspended.',
                      },
                      {
                        title: 'Playwright Stealth 2.x Session Engine',
                        desc: 'Persists authenticated cookies and tokens in local state.json with automatic re-authentication if a session expires.',
                      },
                      {
                        title: 'Zero-Telemetry Local Execution',
                        desc: 'Your repository files, AST map, .deepx_history checkpoints, and VDS credentials stay strictly on your disk.',
                      },
                      {
                        title: 'Windows Terminal & ConPTY Native',
                        desc: 'Includes run_cli.vbs Control Hub, one-line install.ps1 setup, global deepx command, and in-app /update.',
                      },
                    ].map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-3.5">
                        <div className="w-5 h-5 rounded-full bg-[#536DFE]/10 flex items-center justify-center shrink-0 mt-0.5 text-[#536DFE]">
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-[#111318]">{feature.title}</div>
                          <div className="text-xs text-[#475569] leading-relaxed">{feature.desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                  className="w-full google-btn-indigo py-3.5 text-sm font-medium justify-center cursor-pointer"
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
              <div className="deepx-card p-6 sm:p-8">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-[#536DFE]/10 text-[#536DFE] flex items-center justify-center">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-[#111318] text-sm">DeepSeek-V4-Pro</span>
                  </div>
                  <span className="text-[11px] font-mono font-medium bg-[#536DFE]/10 text-[#536DFE] px-2.5 py-0.5 rounded-md">
                    1.6T / 49B
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
                  1.6T total / 49B active parameters (/mode think & /mode plan). Built for multi-file architectural refactoring, deep debugging, and closed-loop verification.
                </p>
              </div>
            </ScrollReveal>

            {/* DeepSeek-V4.1-Flash Card */}
            <ScrollReveal direction="up" delay={350}>
              <div className="deepx-card p-6 sm:p-8">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-[#38BDF8]/10 text-[#0284C7] flex items-center justify-center">
                      <Zap className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-[#111318] text-sm">DeepSeek-V4.1-Flash</span>
                  </div>
                  <span className="text-[11px] font-mono font-medium bg-[#38BDF8]/10 text-[#0284C7] px-2.5 py-0.5 rounded-md">
                    284B / 13B
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
                  284B total / 13B active parameters (/mode instant). Low-latency token streaming for rapid code edits, shell automation, and OSINT lookups.
                </p>
              </div>
            </ScrollReveal>

            {/* Zero Friction Card */}
            <ScrollReveal direction="up" delay={450}>
              <div className="rounded-2xl p-6 sm:p-8 bg-[#0A0D14] text-white border border-slate-800 shadow-xl">
                <div className="flex items-center gap-2 text-xs font-mono text-[#536DFE] font-medium mb-2">
                  <Shield className="w-4 h-4" />
                  <span>One-Command PowerShell Bootstrap</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Run install.ps1 or double-click run_cli.vbs. DeepX provisions its own .venv, installs Playwright Chromium, and registers the global deepx command automatically.
                </p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </div>
    </section>
  );
};
