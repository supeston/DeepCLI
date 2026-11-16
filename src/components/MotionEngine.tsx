import React, { useEffect, useRef, useState } from 'react';
import Lenis from 'lenis';

const CARD_VARIANTS = ['rise', 'left', 'right', 'zoom', 'flip'];
const RAIL = [
  { id: 'terminal', label: 'Terminal' },
  { id: 'features', label: 'Features' },
  { id: 'usecases', label: 'Use cases' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'comparison', label: 'Compare' },
  { id: 'download', label: 'Download' },
];
const STEP = 30;

const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export const MotionEngine: React.FC = () => {
  const [railIds, setRailIds] = useState<string[]>([]);
  const railRef = useRef<HTMLElement | null>(null);
  const thumbRef = useRef<HTMLDivElement | null>(null);
  const fillRef = useRef<HTMLDivElement | null>(null);
  const labelRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const root = document.documentElement;
    if (reduce) return;
    root.classList.add('m-on');

    const lenis = new Lenis({ lerp: 0.065, smoothWheel: true, wheelMultiplier: 0.9, autoRaf: false });
    const origScrollIntoView = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function (this: Element, arg?: boolean | ScrollIntoViewOptions) {
      if (arg && typeof arg === 'object' && arg.behavior === 'smooth') {
        lenis.scrollTo(this as HTMLElement, { offset: -72, duration: 1.7, easing: (t: number) => 1 - Math.pow(1 - t, 4) });
      } else {
        origScrollIntoView.call(this, arg as boolean | ScrollIntoViewOptions | undefined);
      }
    };
    const onHash = () => lenis.scrollTo(0, { immediate: true, force: true });
    window.addEventListener('hashchange', onHash);

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            (e.target as HTMLElement).setAttribute('data-in', '');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -6% 0px' }
    );

    const mark = (el: Element, kind: string, idx = 0, variant?: string) => {
      if (el.hasAttribute('data-m')) return;
      el.setAttribute('data-m', kind);
      if (variant) el.setAttribute('data-v', variant);
      (el as HTMLElement).style.setProperty('--d', `${Math.min(idx, 10) * 70}ms`);
      io.observe(el);
    };

    let heroEl: HTMLElement | null = null;
    let secEls: HTMLElement[] = [];
    let unfoldEls: HTMLElement[] = [];
    let btnEls: HTMLElement[] = [];

    const scan = () => {
      const main = document.querySelector('main');
      if (main) {
        main.querySelectorAll('section').forEach((s) => {
          if (!s.className.includes('min-h-')) mark(s, 'section');
        });
        main.querySelectorAll('h1,h2').forEach((h) => {
          if (!h.closest('section')?.className.includes('min-h-')) mark(h, 'head');
        });
        main.querySelectorAll('h3').forEach((h) => mark(h, 'sub'));
        main.querySelectorAll('section').forEach((s) => {
          if (s.className.includes('min-h-')) return;
          s.querySelectorAll('.deepx-card').forEach((c, i) => mark(c, 'card', i % 3, CARD_VARIANTS[i % CARD_VARIANTS.length]));
        });
        main.querySelectorAll('.deepx-card').forEach((c, i) => {
          if (!c.closest('section')) mark(c, 'card', i % 3, CARD_VARIANTS[i % CARD_VARIANTS.length]);
        });
        main.querySelectorAll('.cmp-row').forEach((r, i) => mark(r, 'row', i));
        main.querySelectorAll('.deepx-card li').forEach((l) => {
          const sibs = l.parentElement ? Array.from(l.parentElement.children) : [];
          mark(l, 'li', sibs.indexOf(l) + 2);
        });
        main.querySelectorAll('.deepx-card svg.lucide, .deepx-card img').forEach((n, i) => mark(n, 'pop', 1 + (i % 3)));
        main.querySelectorAll('.overflow-y-auto').forEach((n) => n.setAttribute('data-lenis-prevent', ''));
      }
      document.querySelectorAll('footer').forEach((f) => {
        mark(f, 'foot');
        f.querySelectorAll('a').forEach((a, i) => mark(a, 'li', i));
      });
      heroEl = document.querySelector<HTMLElement>('main section[class*="min-h-"] > div');
      secEls = Array.from(document.querySelectorAll<HTMLElement>('[data-m="section"]'));
      unfoldEls = Array.from(document.querySelectorAll<HTMLElement>('[data-unfold]'));
      btnEls = Array.from(document.querySelectorAll<HTMLElement>('.google-btn-primary,.google-btn-indigo,.google-btn-secondary'));
      setRailIds((prev) => {
        const next = RAIL.filter((r) => document.getElementById(r.id)).map((r) => r.id);
        return prev.join() === next.join() ? prev : next;
      });
    };

    let scanQueued = false;
    const queueScan = () => {
      if (scanQueued) return;
      scanQueued = true;
      requestAnimationFrame(() => {
        scanQueued = false;
        scan();
      });
    };
    scan();
    const mo = new MutationObserver(queueScan);
    mo.observe(document.body, { childList: true, subtree: true });

    let vel = 0;
    let raf = 0;
    const bar = document.getElementById('m-progress');
    const aura = document.getElementById('m-aura');
    const ring = document.getElementById('m-ring');
    let mx = window.innerWidth / 2, my = window.innerHeight / 2;
    let ax = mx, ay = my, rx = mx, ry = my;
    let marqueeX = 0;
    let tf = 0;
    let lastIdx = -1;
    let barP = 0;

    const frame = (time: number) => {
      raf = requestAnimationFrame(frame);
      lenis.raf(time);
      const y = window.scrollY;
      vel += (lenis.velocity - vel) * 0.12;
      const vh = window.innerHeight;
      const max = document.documentElement.scrollHeight - vh;
      const target = max > 0 ? clamp(y / max, 0, 1) : 0;
      barP += (target - barP) * 0.14;
      if (bar) bar.style.transform = `scaleX(${barP.toFixed(4)})`;

      if (heroEl) {
        const p = clamp(y / (vh * 0.9), 0, 1);
        heroEl.style.translate = `0 ${(p * 90).toFixed(1)}px`;
        heroEl.style.scale = `${(1 - p * 0.06).toFixed(4)}`;
        heroEl.style.filter = p > 0.01 ? `blur(${(p * 5).toFixed(2)}px)` : '';
        heroEl.style.opacity = `${(1 - p * 0.85).toFixed(3)}`;
      }

      for (const s of secEls) {
        if (!s.hasAttribute('data-in')) continue;
        const r = s.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) continue;
        s.style.setProperty('--sp', `${(((r.top + r.height / 2 - vh / 2) / vh) * -40).toFixed(1)}px`);
      }

      for (const u of unfoldEls) {
        const r = u.getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) continue;
        const p = clamp((vh - r.top) / (vh * 0.75), 0, 1);
        const e = 1 - Math.pow(1 - p, 3);
        u.style.transform = `perspective(1400px) rotateX(${((1 - e) * 16).toFixed(2)}deg) translateY(${((1 - e) * 60).toFixed(1)}px) scale(${(0.9 + 0.1 * e).toFixed(4)})`;
        u.style.transformOrigin = '50% 0%';
      }

      marqueeX -= 0.6 + Math.abs(vel) * 0.35;
      document.querySelectorAll<HTMLElement>('[data-marquee]').forEach((t) => {
        const w = t.scrollWidth / 2;
        if (w > 0) {
          if (-marqueeX >= w) marqueeX += w;
          t.style.transform = `translate3d(${marqueeX}px,0,0) skewX(${clamp(-vel * 0.15, -8, 8)}deg)`;
        }
      });

      if (fine) {
        ax += (mx - ax) * 0.08;
        ay += (my - ay) * 0.08;
        rx += (mx - rx) * 0.22;
        ry += (my - ry) * 0.22;
        if (aura) aura.style.transform = `translate3d(${ax - 260}px,${ay - 260}px,0)`;
        if (ring) ring.style.transform = `translate3d(${rx - 18}px,${ry - 18}px,0)`;
      }

      const rail = railRef.current;
      const thumb = thumbRef.current;
      if (rail && thumb) {
        const els = RAIL.map((r) => document.getElementById(r.id));
        const present = els.map((e, i) => ({ e, i })).filter((o) => o.e) as { e: HTMLElement; i: number }[];
        if (present.length) {
          const ref = vh * 0.5;
          const tops = present.map((o) => o.e.getBoundingClientRect().top);
          let idx = -1;
          for (let k = 0; k < tops.length; k++) if (tops[k] <= ref) idx = k;
          let f = 0;
          if (idx >= 0) {
            f = idx >= tops.length - 1 ? tops.length - 1 : idx + clamp((ref - tops[idx]) / (tops[idx + 1] - tops[idx]), 0, 1);
          }
          tf += (f - tf) * 0.1;
          const py = tf * STEP;
          thumb.style.transform = `translate3d(-50%,${py.toFixed(2)}px,0)`;
          if (fillRef.current) fillRef.current.style.transform = `scaleY(${(py / Math.max(1, (present.length - 1) * STEP)).toFixed(4)})`;
          const near = clamp(Math.round(tf), 0, present.length - 1);
          if (near !== lastIdx) {
            lastIdx = near;
            if (labelRef.current) labelRef.current.textContent = RAIL[present[near].i].label;
            rail.querySelectorAll('button').forEach((b, bi) => b.classList.toggle('on', bi === near));
          }
          rail.style.opacity = y > vh * 0.5 ? '1' : '0';
          rail.style.pointerEvents = y > vh * 0.5 ? 'auto' : 'none';
        }
      }
    };
    raf = requestAnimationFrame(frame);

    let lastCard: HTMLElement | null = null;
    const onMove = (e: PointerEvent) => {
      mx = e.clientX;
      my = e.clientY;
      if (aura && aura.style.opacity !== '1') aura.style.opacity = '1';
      if (ring && ring.style.opacity !== '1') ring.style.opacity = '1';
      const t = e.target as HTMLElement | null;
      if (!t || !t.closest) return;
      ring?.classList.toggle('hot', !!t.closest('a,button,[role="button"],.cursor-pointer'));

      const card = t.closest<HTMLElement>('.deepx-card');
      if (lastCard && lastCard !== card) lastCard.style.transform = '';
      lastCard = card;
      if (card) {
        const r = card.getBoundingClientRect();
        const px = e.clientX - r.left, py = e.clientY - r.top;
        card.style.setProperty('--mx', `${px}px`);
        card.style.setProperty('--my', `${py}px`);
        if (r.width < 520 && r.height < 520) {
          card.style.transform = `perspective(900px) rotateX(${(((py / r.height) - 0.5) * -6).toFixed(2)}deg) rotateY(${(((px / r.width) - 0.5) * 6).toFixed(2)}deg)`;
        }
      }

      for (const b of btnEls) {
        const r = b.getBoundingClientRect();
        if (r.width > 260) {
          if (b.style.translate) b.style.translate = '';
          continue;
        }
        const pad = 22;
        const inside = e.clientX > r.left - pad && e.clientX < r.right + pad && e.clientY > r.top - pad && e.clientY < r.bottom + pad;
        if (inside) {
          const dx = clamp((e.clientX - (r.left + r.width / 2)) * 0.14, -6, 6);
          const dy = clamp((e.clientY - (r.top + r.height / 2)) * 0.2, -4, 4);
          b.style.translate = `${dx.toFixed(1)}px ${dy.toFixed(1)}px`;
        } else if (b.style.translate) {
          b.style.translate = '';
        }
      }
    };
    const onLeave = () => {
      if (aura) aura.style.opacity = '0';
      if (ring) ring.style.opacity = '0';
      btnEls.forEach((b) => (b.style.translate = ''));
    };
    if (fine) {
      window.addEventListener('pointermove', onMove, { passive: true });
      document.documentElement.addEventListener('pointerleave', onLeave);
    }

    const safety = window.setTimeout(() => {
      document.querySelectorAll('[data-m]:not([data-in])').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) el.setAttribute('data-in', '');
      });
    }, 2500);

    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      mo.disconnect();
      clearTimeout(safety);
      lenis.destroy();
      Element.prototype.scrollIntoView = origScrollIntoView;
      window.removeEventListener('hashchange', onHash);
      window.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', onLeave);
      root.classList.remove('m-on');
    };
  }, []);

  const items = RAIL.filter((r) => railIds.includes(r.id));

  return (
    <>
      <div id="m-progress" aria-hidden="true" />
      <div id="m-aura" aria-hidden="true" />
      <div id="m-ring" aria-hidden="true" />
      <nav className="m-rail" ref={railRef} aria-label="Sections" style={{ opacity: 0 }}>
        <div className="m-rail-track" style={{ height: Math.max(0, items.length - 1) * STEP }}>
          <div className="m-rail-line" />
          <div className="m-rail-fill" ref={fillRef} style={{ height: Math.max(0, items.length - 1) * STEP }} />
          {items.map((r, i) => (
            <button
              key={r.id}
              type="button"
              className="m-rail-dot"
              style={{ top: i * STEP }}
              onClick={() => document.getElementById(r.id)?.scrollIntoView({ behavior: 'smooth' })}
              aria-label={r.label}
            />
          ))}
          <div className="m-rail-thumb" ref={thumbRef}>
            <span ref={labelRef}>{items[0]?.label}</span>
          </div>
        </div>
      </nav>
    </>
  );
};

const WORDS = ['ConPTY', 'Playwright Stealth', 'WinRT Clipboard', 'Autonomous Agent', 'Windows Terminal', 'DeepSeek', 'Rich TUI', 'Global deepx', 'Checkpoints', 'Repo Map'];

export const Marquee: React.FC = () => {
  const row = [...WORDS, ...WORDS];
  return (
    <div className="m-marquee" aria-hidden="true">
      <div data-marquee className="m-marquee-track">
        {row.concat(row).map((w, i) => (
          <span key={i}>
            {w}
            <b />
          </span>
        ))}
      </div>
    </div>
  );
};

export default MotionEngine;
