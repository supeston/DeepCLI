import React, { useEffect, useRef } from 'react';

interface SignalPulse {
  axis: 'h' | 'v';
  lineIndex: number;
  pos: number;
  speed: number;
  length: number;
  hue: string;
  alpha: number;
}

interface FloatingNode {
  gx: number;
  gy: number;
  phase: number;
  speed: number;
  label?: string;
}

export const ParticleCanvas: React.FC<{ className?: string }> = ({ className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx || typeof ctx.save !== 'function') return;

    let animationFrameId: number;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = window.innerWidth;
    let height = window.innerHeight;

    const setupSize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      if (typeof ctx.setTransform === 'function') {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    };
    setupSize();

    // Spring-interpolated pointer & scroll state for fluid Awwwards-style motion
    const pointer = {
      targetX: width * 0.5,
      targetY: height * 0.38,
      x: width * 0.5,
      y: height * 0.38,
      vx: 0,
      vy: 0,
      active: false,
    };

    let scrollY = window.scrollY || 0;
    let smoothScroll = scrollY;
    let scrollVelocity = 0;

    const gridStep = width < 640 ? 64 : 84;
    const cols = Math.ceil(width / gridStep) + 2;
    const rows = Math.ceil(height / gridStep) + 2;

    // Signal pulses traveling along architectural grid tracks
    const pulsePalette = ['#536DFE', '#38BDF8', '#6366F1'];
    const pulseCount = Math.min(Math.max(Math.floor((width * height) / 65000), 10), 24);
    const pulses: SignalPulse[] = [];

    for (let i = 0; i < pulseCount; i++) {
      const axis = i % 2 === 0 ? 'h' : 'v';
      pulses.push({
        axis,
        lineIndex: Math.floor(Math.random() * (axis === 'h' ? rows : cols)),
        pos: Math.random() * (axis === 'h' ? width : height),
        speed: (Math.random() * 1.1 + 0.55) * (Math.random() > 0.5 ? 1 : -1),
        length: Math.random() * 90 + 64,
        hue: pulsePalette[i % pulsePalette.length],
        alpha: Math.random() * 0.32 + 0.18,
      });
    }

    // Subtle telemetry coordinate markers at selected grid intersections
    const coordLabels = ['AST::0x01', 'ConPTY', 'STEALTH::2.x', 'UTF-8', 'V4.1', 'Win32::VT', 'CRC::OK'];
    const nodes: FloatingNode[] = [];
    for (let i = 0; i < 14; i++) {
      nodes.push({
        gx: Math.floor(Math.random() * Math.max(cols - 1, 2)) + 1,
        gy: Math.floor(Math.random() * Math.max(rows - 1, 2)) + 1,
        phase: Math.random() * Math.PI * 2,
        speed: Math.random() * 0.018 + 0.008,
        label: i < coordLabels.length ? coordLabels[i] : undefined,
      });
    }

    const handleResize = () => {
      setupSize();
    };

    const handleMouseMove = (e: MouseEvent) => {
      pointer.targetX = e.clientX;
      pointer.targetY = e.clientY;
      pointer.active = true;
    };

    const handleMouseLeave = () => {
      pointer.active = false;
    };

    const handleScroll = () => {
      scrollY = window.scrollY || 0;
    };

    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    let tick = 0;

    // Displace any coordinate (x, y) smoothly with a magnetic lens field around pointer
    const displacePoint = (x: number, y: number): [number, number, number] => {
      const dx = x - pointer.x;
      const dy = y - pointer.y;
      const distSq = dx * dx + dy * dy;
      const radius = 260;
      const radiusSq = radius * radius;
      if (distSq >= radiusSq || distSq < 0.001) {
        return [x, y, 0];
      }
      const dist = Math.sqrt(distSq);
      const t = 1 - dist / radius;
      // Smooth cubic falloff
      const falloff = t * t * (3 - 2 * t);
      const push = falloff * (pointer.active ? 18 : 7);
      const nx = dx / dist;
      const ny = dy / dist;
      return [x + nx * push, y + ny * push, falloff];
    };

    const render = () => {
      tick += 0.012;

      // Ambient autonomous Lissajous drift when cursor is idle
      if (!pointer.active) {
        pointer.targetX = width * (0.5 + Math.cos(tick * 0.55) * 0.24);
        pointer.targetY = height * (0.42 + Math.sin(tick * 0.75) * 0.2);
      }

      const prevX = pointer.x;
      const prevY = pointer.y;
      pointer.x += (pointer.targetX - pointer.x) * 0.085;
      pointer.y += (pointer.targetY - pointer.y) * 0.085;
      pointer.vx = pointer.x - prevX;
      pointer.vy = pointer.y - prevY;

      const prevScroll = smoothScroll;
      smoothScroll += (scrollY - smoothScroll) * 0.12;
      scrollVelocity = Math.min(Math.abs(smoothScroll - prevScroll), 36);

      ctx.clearRect(0, 0, width, height);

      // 1. Ambient kinetic spotlight following cursor
      if (typeof ctx.createRadialGradient === 'function') {
        const spotRadius = Math.max(width, height) * 0.46;
        const grad = ctx.createRadialGradient(
          pointer.x,
          pointer.y,
          12,
          pointer.x,
          pointer.y,
          spotRadius
        );
        grad.addColorStop(0, 'rgba(83, 109, 254, 0.075)');
        grad.addColorStop(0.45, 'rgba(56, 189, 248, 0.032)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        ctx.save();
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);
        ctx.restore();
      }

      const parallaxOffsetY = -((smoothScroll * 0.22) % gridStep);
      const curCols = Math.ceil(width / gridStep) + 2;
      const curRows = Math.ceil(height / gridStep) + 2;

      // 2. Warped Architectural Coordinate Grid (Horizontal + Vertical)
      ctx.save();
      ctx.lineWidth = 0.75;

      // Horizontal lines
      for (let r = 0; r <= curRows; r++) {
        const baseY = r * gridStep + parallaxOffsetY;
        if (baseY < -gridStep || baseY > height + gridStep) continue;
        ctx.beginPath();
        const segments = Math.ceil(width / 36);
        for (let s = 0; s <= segments; s++) {
          const sx = (s / segments) * width;
          const [wx, wy] = displacePoint(sx, baseY);
          if (s === 0) ctx.moveTo(wx, wy);
          else ctx.lineTo(wx, wy);
        }
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.14)';
        ctx.stroke();
      }

      // Vertical lines
      for (let c = 0; c <= curCols; c++) {
        const baseX = c * gridStep;
        if (baseX < -gridStep || baseX > width + gridStep) continue;
        ctx.beginPath();
        const segments = Math.ceil(height / 36);
        for (let s = 0; s <= segments; s++) {
          const sy = (s / segments) * height;
          const [wx, wy] = displacePoint(baseX, sy);
          if (s === 0) ctx.moveTo(wx, wy);
          else ctx.lineTo(wx, wy);
        }
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.14)';
        ctx.stroke();
      }
      ctx.restore();

      // 3. Precision Crosshairs (+) & Kinetic Vectors at Grid Intersections
      for (let r = 0; r <= curRows; r++) {
        const baseY = r * gridStep + parallaxOffsetY;
        if (baseY < -20 || baseY > height + 20) continue;
        for (let c = 0; c <= curCols; c++) {
          const baseX = c * gridStep;
          if (baseX < -20 || baseX > width + 20) continue;

          const [wx, wy, influence] = displacePoint(baseX, baseY);

          if (influence > 0.03) {
            // Active magnetic crosshair near pointer
            const arm = 3 + influence * 4.5;
            ctx.save();
            ctx.strokeStyle = '#536DFE';
            ctx.globalAlpha = 0.18 + influence * 0.55;
            ctx.lineWidth = 1.1;
            ctx.beginPath();
            ctx.moveTo(wx - arm, wy);
            ctx.lineTo(wx + arm, wy);
            ctx.moveTo(wx, wy - arm);
            ctx.lineTo(wx, wy + arm);
            ctx.stroke();

            // Subtle vector tether toward original anchor
            if (influence > 0.22) {
              ctx.beginPath();
              ctx.moveTo(baseX, baseY);
              ctx.lineTo(wx, wy);
              ctx.strokeStyle = '#38BDF8';
              ctx.globalAlpha = influence * 0.28;
              ctx.lineWidth = 0.8;
              ctx.stroke();
            }
            ctx.restore();
          } else if ((r + c) % 2 === 0) {
            // Quiet structural intersection micro-dot
            ctx.save();
            ctx.fillStyle = '#64748B';
            ctx.globalAlpha = 0.22;
            ctx.beginPath();
            ctx.arc(wx, wy, 1.1, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          }
        }
      }

      // 4. Signal Pulses Flowing Along Grid Tracks
      const speedBoost = 1 + scrollVelocity * 0.06;
      for (let i = 0; i < pulses.length; i++) {
        const p = pulses[i];
        p.pos += p.speed * speedBoost;

        if (p.axis === 'h') {
          const trackY = ((p.lineIndex % Math.max(curRows, 1)) * gridStep) + parallaxOffsetY;
          if (p.speed > 0 && p.pos - p.length > width) p.pos = -p.length;
          if (p.speed < 0 && p.pos + p.length < 0) p.pos = width + p.length;

          const [x1, y1] = displacePoint(p.pos - p.length * 0.5, trackY);
          const [x2, y2] = displacePoint(p.pos + p.length * 0.5, trackY);

          ctx.save();
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.strokeStyle = p.hue;
          ctx.globalAlpha = p.alpha;
          ctx.lineWidth = 1.6;
          ctx.stroke();

          // Leading head node
          const headX = p.speed > 0 ? x2 : x1;
          const headY = p.speed > 0 ? y2 : y1;
          ctx.fillStyle = p.hue;
          ctx.globalAlpha = Math.min(1, p.alpha * 2.1);
          ctx.beginPath();
          ctx.arc(headX, headY, 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else {
          const trackX = (p.lineIndex % Math.max(curCols, 1)) * gridStep;
          if (p.speed > 0 && p.pos - p.length > height) p.pos = -p.length;
          if (p.speed < 0 && p.pos + p.length < 0) p.pos = height + p.length;

          const [x1, y1] = displacePoint(trackX, p.pos - p.length * 0.5);
          const [x2, y2] = displacePoint(trackX, p.pos + p.length * 0.5);

          ctx.save();
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.strokeStyle = p.hue;
          ctx.globalAlpha = p.alpha;
          ctx.lineWidth = 1.6;
          ctx.stroke();

          const headX = p.speed > 0 ? x2 : x1;
          const headY = p.speed > 0 ? y2 : y1;
          ctx.fillStyle = p.hue;
          ctx.globalAlpha = Math.min(1, p.alpha * 2.1);
          ctx.beginPath();
          ctx.arc(headX, headY, 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
      }

      // 5. Architectural Node Markers & Micro-Telemetry
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.phase += n.speed;
        const bx = (n.gx % Math.max(curCols, 2)) * gridStep;
        const by = ((n.gy % Math.max(curRows, 2)) * gridStep) + parallaxOffsetY;
        if (by < 24 || by > height - 24) continue;

        const [wx, wy, inf] = displacePoint(bx, by);
        const pulse = (Math.sin(n.phase) + 1) * 0.5;

        ctx.save();
        ctx.strokeStyle = '#536DFE';
        ctx.globalAlpha = 0.14 + pulse * 0.16 + inf * 0.35;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(wx - 4, wy - 4, 8, 8, 2);
        ctx.stroke();

        if (n.label && width >= 768 && (inf > 0.12 || pulse > 0.72)) {
          ctx.font = '500 9px "Google Sans Code", ui-monospace, SFMono-Regular, monospace';
          ctx.fillStyle = '#64748B';
          ctx.globalAlpha = 0.28 + inf * 0.45;
          ctx.fillText(n.label, wx + 8, wy + 3);
        }
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      data-testid="particle-canvas"
      className={`fixed inset-0 pointer-events-none z-0 ${className}`}
    />
  );
};
