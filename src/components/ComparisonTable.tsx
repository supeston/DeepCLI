import React, { useEffect, useState } from 'react';
import { Check, Layers } from 'lucide-react';
import { ScrollReveal, TextScrollReveal } from './ScrollReveal';

const RIVALS = [
  { id: 'antigravity', name: 'Antigravity' },
  { id: 'claude', name: 'Claude Code' },
  { id: 'grok', name: 'Grok Build' },
  { id: 'codex', name: 'Codex' },
] as const;

type RivalId = (typeof RIVALS)[number]['id'];

interface Row {
  feature: string;
  deepx: string;
  rivals: Record<RivalId, string>;
}

const ROWS: Row[] = [
  {
    feature: 'Pricing & Token Billing',
    deepx: '100% Free (Zero Bills)',
    rivals: {
      antigravity: 'Free · Pro $19.99 · Ultra $99.99–$199.99',
      claude: 'Pro $20 · Max $100 · Ultra $200 or API',
      grok: 'Subscription tiers or API $2–$6/M (Grok 4.7)',
      codex: 'Plus $20 · Pro $100–$500 or API key',
    },
  },
  {
    feature: 'Terminal Execution Engine',
    deepx: 'Native Windows ConPTY + VBS Hub',
    rivals: {
      antigravity: 'agy CLI + desktop IDE & SDK',
      claude: 'Native Win/Mac/Linux (WSL2 optional)',
      grok: 'Native Rust TUI (Win/Mac/Linux)',
      codex: 'Local terminal agent CLI',
    },
  },
  {
    feature: 'WinRT Clipboard & Vision (Win+V / Win+Shift+S)',
    deepx: 'Native WinRT clipboard image capture',
    rivals: {
      antigravity: 'File & image paste',
      claude: 'Ctrl+V image paste',
      grok: 'Multimodal image input',
      codex: 'File & image input',
    },
  },
  {
    feature: 'Telemetry & Code Privacy',
    deepx: 'Zero Telemetry (100% Local)',
    rivals: {
      antigravity: 'Google AI & Cloud terms',
      claude: 'Consumer: training on by default (opt-out) · API: none',
      grok: 'xAI policy (training opt-out)',
      codex: 'No training on API / Enterprise',
    },
  },
  {
    feature: 'Supported Reasoning Engines',
    deepx: 'DeepSeek-V4-Pro / V4.1-Flash',
    rivals: {
      antigravity: 'Gemini 4 Carbon / Argon / Hydrogen · 3.8 Flash',
      claude: 'Opus 5.5 / Sonnet 5.5 / Haiku 5.5 · Fable 5.2',
      grok: 'Grok 4.7 · grok-build-0.1',
      codex: 'GPT-6.1 Sol · GPT-6 Luna',
    },
  },
  {
    feature: 'One-Click Native Setup & Auto-Update',
    deepx: 'install.ps1 + /update + Ban Guard',
    rivals: {
      antigravity: 'Desktop app / agy CLI',
      claude: 'irm install.ps1 · winget (no Node.js)',
      grok: 'PowerShell / curl one-liner',
      codex: 'npm / desktop app',
    },
  },
];

const AUTO_MS = 5200;

export const ComparisonTable: React.FC = () => {
  const [vs, setVs] = useState(0);
  const [auto, setAuto] = useState(true);
  const [hover, setHover] = useState(false);

  useEffect(() => {
    if (!auto || hover || typeof window === 'undefined') return;
    if (typeof process !== 'undefined' && process.env?.NODE_ENV === 'test') return;
    const id = window.setTimeout(() => setVs((v) => (v + 1) % RIVALS.length), AUTO_MS);
    return () => window.clearTimeout(id);
  }, [auto, hover, vs]);

  const pick = (i: number) => {
    setAuto(false);
    setVs(i);
  };

  const rival = RIVALS[vs];

  return (
    <section id="comparison" className="py-24 deepx-section-band border-t border-slate-200/80 overflow-hidden">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14 max-w-3xl mx-auto">
          <ScrollReveal direction="up" delay={100}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-[#536DFE]/10 text-[#536DFE] text-xs font-mono font-medium mb-4 border border-[#536DFE]/20">
              <Layers className="w-3.5 h-3.5" />
              <span>v3.1.0 · data as of November 2026</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-normal text-[#111318] tracking-tight mb-4">
              Technical Benchmarks &amp; Comparison
            </h2>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200}>
            <TextScrollReveal
              text="Pick an opponent. DeepX stays put, the other side rolls: execution, telemetry, billing and Windows ConPTY integration, head to head."
              className="text-[#475569] font-normal text-base sm:text-lg"
              highlightWords={['execution', 'telemetry', 'billing', 'ConPTY']}
            />
          </ScrollReveal>
        </div>

        <ScrollReveal direction="up" delay={250}>
          <div className="cmp" onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
            <div className="cmp-chips" role="tablist" aria-label="Compare DeepX with">
              <span className="cmp-pill" style={{ transform: `translateX(${vs * 100}%)` }}>
                {auto && !hover && (
                  <i key={vs} className="cmp-pill-timer" style={{ animationDuration: `${AUTO_MS}ms` }} />
                )}
              </span>
              {RIVALS.map((r, i) => (
                <button
                  key={r.id}
                  role="tab"
                  aria-selected={vs === i}
                  className={vs === i ? 'on' : ''}
                  onClick={() => pick(i)}
                  data-testid={`cmp-chip-${r.id}`}
                >
                  {r.name}
                </button>
              ))}
            </div>

            <div className="cmp-head">
              <div className="cmp-side cmp-side-deepx">
                <span className="cmp-dot" />
                DeepX CLI
              </div>
              <div className="cmp-vs">vs</div>
              <div className="cmp-side cmp-side-rival">
                <span key={rival.id} className="cmp-roll">
                  {rival.name}
                </span>
              </div>
            </div>

            <div className="cmp-rows">
              {ROWS.map((row, i) => (
                <div key={row.feature} className="cmp-row">
                  <div className="cmp-cell cmp-cell-deepx">
                    <Check className="cmp-check" />
                    <span>{row.deepx}</span>
                  </div>
                  <div className="cmp-label">{row.feature}</div>
                  <div className="cmp-cell cmp-cell-rival">
                    <span key={`${rival.id}-${i}`} className="cmp-roll" style={{ animationDelay: `${i * 70}ms` }}>
                      {row.rivals[rival.id]}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>

        <p className="mt-6 text-center text-[11px] font-mono text-slate-400">
          Plans and model names from public vendor pages, November 2026. Verify before purchase.
        </p>
      </div>
    </section>
  );
};
