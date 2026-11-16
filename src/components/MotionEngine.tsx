import React, { useEffect, useState } from 'react';

const CARD_VARIANTS = ['rise', 'left', 'right', 'zoom', 'flip'];
const RAIL = [
  { id: 'terminal', label: 'Terminal' },
  { id: 'features', label: 'Features' },
  { id: 'usecases', label: 'Use cases' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'comparison', label: 'Compare' },
  { id: 'download', label: 'Download' },
];

const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export const MotionEngine: React.FC = () => {
  const [active, setActive] = useState<string>('');
  const [railIds, setRailIds] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const root = document.documentElement;
    if (reduce) return;
    root.classList.add('m-on');

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
        main.querySelectorAll('tbody tr').forEach((r, i) => mark(r, 'row', i));
        main.querySelectorAll('.deepx-card li').forEach((l) => {
          const sibs = l.parentElement ? Array.from(l.parentElement.children) : [];
          mark(l, 'li', sibs.indexOf(l) + 2);
        });
        main.querySelectorAll('.deepx-card svg.lucide, .deepx-card img').forEach((n, i) => mark(n, 'pop', 1 + (i % 3)));
      }
      document.querySelectorAll('footer').forEach((f) => {
        mark(f, 'foot');
        f.querySelectorAll('a').forEach((a, i) => mark(a, 'li', i));
      });
      setRailIds(RAIL.filter((r) => document.getElementById(r.id)).map((r) => r.id));
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

    let sy = window.scrollY;
    let vel = 0;
    let ticking = true;
    let raf = 0;
    const bar = document.getElementById('m-progress');
    const aura = document.getElementById('m-aura');
    const ring = document.getElementById('m-ring');
    let mx = window.innerWidth / 2, my = window.innerHeight / 2;
    let ax = mx, ay = my, rx = mx, ry = my;
    let marqueeX = 0;

    const frame = () => {
      raf = requestAnimationFrame(frame);
      const y = window.scrollY;
      vel += (y - sy - vel) * 0.12;
      sy = y;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.transform = `scaleX(${max > 0 ? clamp(y / max, 0, 1) : 0})`;

      const hero = document.querySelector<HTMLElement>('main section[class*="min-h-"] > div');
      if (hero) {
        const p = clamp(y / (window.innerHeight * 0.9), 0, 1);
        hero.style.translate = `0 ${p * 90}px`;
        hero.style.scale = `${1 - p * 0.06}`;
        hero.style.filter = p > 0.01 ? `blur(${p * 5}px)` : '';
        hero.style.opacity = `${1 - p * 0.85}`;
      }

      document.querySelectorAll<HTMLElement>('[data-m="section"][data-in]').forEach((s) => {
        const r = s.getBoundingClientRect();
        if (r.bottom < -200 || r.top > window.innerHeight + 200) return;
        const c = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
        s.style.setProperty('--sp', `${(c * -40).toFixed(1)}px`);
      });

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

      let cur = '';
      for (const r of RAIL) {
        const el = document.getElementById(r.id);
        if (!el) continue;
        if (el.getBoundingClientRect().top < window.innerHeight * 0.45) cur = r.id;
      }
      setActive((prev) => (prev === cur ? prev : cur));
    };
    raf = requestAnimationFrame(frame);

    const onMove = (e: PointerEvent) => {
      mx = e.clientX;
      my = e.clientY;
      if (aura && aura.style.opacity !== '1') aura.style.opacity = '1';
      if (ring && ring.style.opacity !== '1') ring.style.opacity = '1';
      const t = e.target as HTMLElement | null;
      if (!t || !t.closest) return;
      const hot = t.closest('a,button,[role="button"],.cursor-pointer');
      ring?.classList.toggle('hot', !!hot);

      const card = t.closest<HTMLElement>('.deepx-card');
      if (card) {
        const r = card.getBoundingClientRect();
        const px = e.clientX - r.left, py = e.clientY - r.top;
        card.style.setProperty('--mx', `${px}px`);
        card.style.setProperty('--my', `${py}px`);
        if (r.width < 520 && r.height < 520) {
          const rxd = ((py / r.height) - 0.5) * -7;
          const ryd = ((px / r.width) - 0.5) * 7;
          card.style.transform = `perspective(900px) rotateX(${rxd.toFixed(2)}deg) rotateY(${ryd.toFixed(2)}deg)`;
        }
      }
      document.querySelectorAll<HTMLElement>('.deepx-card').forEach((c) => {
        if (c !== card && c.style.transform) c.style.transform = '';
      });

      document.querySelectorAll<HTMLElement>('.google-btn-primary,.google-btn-indigo,.google-btn-secondary').forEach((b) => {
        const r = b.getBoundingClientRect();
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        const dx = e.clientX - cx, dy = e.clientY - cy;
        const dist = Math.hypot(dx, dy);
        const reach = Math.max(r.width, r.height) * 0.9;
        b.style.translate = dist < reach ? `${(dx * 0.22).toFixed(1)}px ${(dy * 0.3).toFixed(1)}px` : '';
      });
    };
    const onLeave = () => {
      if (aura) aura.style.opacity = '0';
      if (ring) ring.style.opacity = '0';
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
      ticking = false;
      void ticking;
      cancelAnimationFrame(raf);
      io.disconnect();
      mo.disconnect();
      clearTimeout(safety);
      window.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', onLeave);
      root.classList.remove('m-on');
    };
  }, []);

  return (
    <>
      <div id="m-progress" aria-hidden="true" />
      <div id="m-aura" aria-hidden="true" />
      <div id="m-ring" aria-hidden="true" />
      {railIds.length > 0 && (
        <nav className="m-rail" aria-label="Sections">
          {RAIL.filter((r) => railIds.includes(r.id)).map((r) => (
            <button
              key={r.id}
              type="button"
              className={active === r.id ? 'on' : ''}
              onClick={() => document.getElementById(r.id)?.scrollIntoView({ behavior: 'smooth' })}
              aria-label={r.label}
            >
              <span>{r.label}</span>
              <i />
            </button>
          ))}
        </nav>
      )}
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
