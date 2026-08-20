import React, { useRef, useState } from 'react';
import {
  Terminal,
  Clipboard,
  Film,
  ShieldCheck,
  Zap,
  Cpu,
  Layers,
} from 'lucide-react';

interface BentoCardProps {
  title: string;
  badge: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
  gradient: string;
  className?: string;
  children?: React.ReactNode;
}

const BentoCard: React.FC<BentoCardProps> = ({
  title,
  badge,
  description,
  icon,
  tags,
  gradient,
  className = '',
  children,
}) => {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      data-testid={`bento-card-${badge.toLowerCase().replace(/\s+/g, '-')}`}
      className={`relative rounded-3xl p-7 bg-[#0E111A]/90 border border-slate-800/80 hover:border-[#536DFE]/50 transition-all duration-300 overflow-hidden group shadow-xl backdrop-blur-xl ${className}`}
    >
      {/* Specular Mouse Glow Light */}
      {isHovered && (
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            background: `radial-gradient(400px circle at ${mousePos.x}px ${mousePos.y}px, rgba(83, 109, 254, 0.18), transparent 80%)`,
          }}
        />
      )}

      {/* Ambient Corner Gradient */}
      <div
        className={`absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl ${gradient} opacity-10 rounded-full blur-3xl group-hover:opacity-20 transition-opacity duration-500`}
      />

      <div className="relative z-10 flex flex-col justify-between h-full">
        <div>
          {/* Header & Badge */}
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-2xl bg-[#171B28] border border-slate-700/60 text-[#38BDF8] group-hover:text-white group-hover:scale-110 transition-all duration-200">
              {icon}
            </div>
            <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-full bg-[#536DFE]/15 text-[#38BDF8] border border-[#536DFE]/30">
              {badge}
            </span>
          </div>

          {/* Title & Description */}
          <h3 className="text-xl font-bold text-white mb-2 group-hover:text-[#38BDF8] transition-colors duration-150">
            {title}
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed mb-6 font-normal">
            {description}
          </p>

          {children}
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 pt-4 border-t border-slate-800/60 mt-auto">
          {tags.map((tag, idx) => (
            <span
              key={idx}
              className="text-[11px] font-mono px-2.5 py-0.5 rounded-lg bg-[#141824] text-slate-400 border border-slate-800"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export const BentoGrid: React.FC = () => {
  return (
    <section id="features" className="py-24 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#536DFE]/15 text-[#38BDF8] border border-[#536DFE]/30 mb-4">
            <Layers className="w-3.5 h-3.5" />
            <span>CORE ARCHITECTURE</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Engineered for Deep Autonomy
          </h2>
          <p className="text-slate-300 text-base sm:text-lg">
            Every layer of DeepX is designed to bypass standard agent bottlenecks—from kernel-grade terminal controls to zero-telemetry browser engines.
          </p>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1: ConPTY + Job Objects */}
          <BentoCard
            title="ConPTY & Windows Job Objects"
            badge="INTERACTIVE TERMINAL"
            description="Replaces naive subprocess calls with a full Windows Pseudo-Console. Detects prompts, sends interactive keystrokes, and binds processes to Win32 Job Objects to eliminate process leaks."
            icon={<Terminal className="w-6 h-6" />}
            tags={['pywinpty', 'JOB_OBJECT_LIMIT_KILL', 'ANSI VT100', 'send_input']}
            gradient="from-[#536DFE] to-[#38BDF8]"
          >
            <div className="p-3 rounded-xl bg-[#090B12] border border-slate-800 font-mono text-xs text-slate-400 mb-2">
              <span className="text-[#38BDF8]">def</span> <span className="text-white">spawn_session</span>(): <br />
              &nbsp;&nbsp;hJob = kernel32.<span className="text-[#A78BFA]">CreateJobObjectW</span>(...) <br />
              &nbsp;&nbsp;pty = <span className="text-[#10B981]">PtyProcess.spawn</span>(argv)
            </div>
          </BentoCard>

          {/* Card 2: WinRT Clipboard History */}
          <BentoCard
            title="WinRT Clipboard History"
            badge="WIN + V INTEGRATION"
            description="Deep integration with Windows Runtime DataTransfer APIs. Reads multi-slot clipboard items, extracts raw bitmap screenshots directly to PNG, and manages history natively."
            icon={<Clipboard className="w-6 h-6" />}
            tags={['WinRT winsdk', 'DataReader Streams', 'Pillow PNG', 'Win+V Sync']}
            gradient="from-[#A78BFA] to-[#38BDF8]"
          >
            <div className="p-3 rounded-xl bg-[#090B12] border border-slate-800 font-mono text-xs text-slate-400 mb-2">
              <span className="text-[#38BDF8]">await</span> Clipboard.<span className="text-[#A78BFA]">get_history_items_async</span>() <br />
              <span className="text-slate-500"># Extracts text, codes, URLs &amp; bitmaps</span>
            </div>
          </BentoCard>

          {/* Card 3: Dual-Engine DeepSeek */}
          <BentoCard
            title="Dual-Engine DeepSeek & Stealth"
            badge="ZERO-CENSORSHIP"
            description="Direct Playwright DOM streaming backend with Playwright Stealth 2.x anti-detection. Features Instant mode for quick loops and Expert DeepThink for complex architectural reasoning."
            icon={<Zap className="w-6 h-6" />}
            tags={['Playwright Stealth', 'Instant / Expert', 'DOM Streaming', 'Zero Censorship']}
            gradient="from-[#38BDF8] to-[#10B981]"
          >
            <div className="p-3 rounded-xl bg-[#090B12] border border-slate-800 font-mono text-xs text-slate-400 mb-2">
              <span className="text-[#10B981]">✓</span> Stealth Fingerprint Masked <br />
              <span className="text-[#10B981]">✓</span> Token-by-Token Adaptive Stream
            </div>
          </BentoCard>

          {/* Card 4: Media Inspector Subsystem */}
          <BentoCard
            title="Deep Media Inspector"
            badge="MEDIA METADATA"
            description="Autonomous technical inspection of video, audio, and photo assets. Extracts container formats, video codecs (H.265/AV1/ProRes), 10-bit HDR color spaces, framerates, and EXIF/GPS."
            icon={<Film className="w-6 h-6" />}
            tags={['PyMediaInfo', 'ffprobe JSON', '10-bit HDR', 'EXIF / IPTC']}
            gradient="from-[#F59E0B] to-[#536DFE]"
          />

          {/* Card 5: Self-Correction Loop */}
          <BentoCard
            title="Verification Barriers"
            badge="SELF-CORRECTION"
            description="Dual ReAct loops enforce automatic AST and bytecode syntax verification (py_compile, node --check, JSON schema) before returning code to user, eliminating syntax errors."
            icon={<ShieldCheck className="w-6 h-6" />}
            tags={['Verification Barrier', 'py_compile Check', 'AST Validator', 'Loop Detection']}
            gradient="from-[#10B981] to-[#38BDF8]"
          />

          {/* Card 6: 1-Click Zero-Dependency Launcher */}
          <BentoCard
            title="1-Click Windows Launcher"
            badge="SEAMLESS SETUP"
            description="Single run_cli.vbs launcher with automated deepx/install.py engine. Creates isolated .venv, downloads Playwright Chromium, and runs in Windows Terminal with zero manual steps."
            icon={<Cpu className="w-6 h-6" />}
            tags={['run_cli.vbs', 'Auto .venv', 'Windows Terminal', 'PYTHONDONTWRITEBYTECODE']}
            gradient="from-[#6366F1] to-[#EC4899]"
          />
        </div>
      </div>
    </section>
  );
};
