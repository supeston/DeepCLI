import React, { useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

interface TerminalScenario {
  id: string;
  title: string;
  command: string;
  promptText: string;
  badge: { text: string; color: string };
  output: Array<{ text: string; type?: 'cmd' | 'info' | 'success' | 'warn' | 'dim' | 'highlight' }>;
}

const SCENARIOS: TerminalScenario[] = [
  {
    id: 'conpty',
    title: 'Interactive ConPTY',
    command: 'run_cmd "npm run deploy"',
    promptText: 'DeepX orchestrates interactive terminal session via Windows ConPTY',
    badge: { text: 'WAITING_FOR_INPUT RESOLVED', color: 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/40' },
    output: [
      { text: '› run_cmd "npm run deploy"', type: 'cmd' },
      { text: '[ConPTY Session #1 Initialized | JobObject Limit: KILL_ON_CLOSE]', type: 'dim' },
      { text: '$ vite build --mode production', type: 'info' },
      { text: '✓ 142 modules transformed. Output: dist/ (84.2 kB)', type: 'success' },
      { text: '? Are you sure you want to deploy to production cluster? [y/N]: ', type: 'warn' },
      { text: '[Interactive ConPTY: Prompt detected -> DeepX auto-evaluates & sends: "y"]', type: 'highlight' },
      { text: 'Deploying release v2.6.0 to edge cluster... 100%', type: 'info' },
      { text: '✓ Deployment successful! URL: https://deepx.prod', type: 'success' },
    ],
  },
  {
    id: 'clipboard',
    title: 'WinRT Clipboard (Win+V)',
    command: 'get_clipboard_history limit=5',
    promptText: 'Direct query to Windows Runtime DataTransfer API',
    badge: { text: 'WINRT API READY', color: 'bg-[#38BDF8]/20 text-[#38BDF8] border-[#38BDF8]/40' },
    output: [
      { text: '› get_clipboard_history limit=5', type: 'cmd' },
      { text: '=== Windows Clipboard History (5 items indexed) ===', type: 'info' },
      { text: '[1] code/python | "from winsdk.windows.applicationmodel.datatransfer import Clipboard"', type: 'highlight' },
      { text: '[2] image/png   | Bitmap screenshot (1920x1080) -> extracted to .deepx/cache/clip_1.png', type: 'success' },
      { text: '[3] url         | "https://github.com/supeston/DeepCLI"', type: 'info' },
      { text: '[4] json        | { "agent_style": "coder", "think": true }', type: 'dim' },
      { text: '✓ Selected item #2 parsed and fed into multimodal vision inspector', type: 'success' },
    ],
  },
  {
    id: 'media',
    title: 'Media Inspector',
    command: 'inspect_media "render_demo.mp4"',
    promptText: 'Extracts deep technical container, audio, and video stream metadata',
    badge: { text: 'PYMEDIAINFO / FFPROBE', color: 'bg-[#A78BFA]/20 text-[#A78BFA] border-[#A78BFA]/40' },
    output: [
      { text: '› inspect_media "render_demo.mp4"', type: 'cmd' },
      { text: '=== Video Stream Analysis: render_demo.mp4 ===', type: 'info' },
      { text: '• Video Codec: HEVC / H.265 (Main 10 Profile @ Level 5.1)', type: 'highlight' },
      { text: '• Resolution: 3840 x 2160 (4K UHD, 16:9 Aspect Ratio)', type: 'info' },
      { text: '• Framerate: 60.000 FPS (Constant Framerate)', type: 'info' },
      { text: '• Color Depth: 10-bit HDR (BT.2020 / SMPTE ST 2084 PQ)', type: 'warn' },
      { text: '• Audio: E-AC-3 (Dolby Digital Plus), 6 channels, 48 kHz @ 640 kbps', type: 'dim' },
      { text: '✓ Full metadata verified without ffmpeg overhead', type: 'success' },
    ],
  },
  {
    id: 'verify',
    title: 'Self-Correction Loop',
    command: 'write_file "app.py" & verify',
    promptText: 'Verification Barriers enforce syntax compilation before finalizing answer',
    badge: { text: 'ZERO-BUG POLICY', color: 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/40' },
    output: [
      { text: '› write_file "service.py" ...', type: 'cmd' },
      { text: '[Syntax Check: py_compile running on service.py...]', type: 'dim' },
      { text: '✖ SyntaxError: unexpected indent on line 24', type: 'warn' },
      { text: '[Verification Barrier triggered: DeepX automatically enters strategy correction]', type: 'highlight' },
      { text: '› edit_file "service.py" target="    def start():" replacement="  def start():"', type: 'cmd' },
      { text: '✓ [Syntax Check: OK (Clean bytecode compiled)]', type: 'success' },
      { text: '✓ File saved and verified cleanly before user presentation', type: 'success' },
    ],
  },
];

export const TerminalSimulator: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('conpty');
  const [copied, setCopied] = useState<boolean>(false);

  const scenario = SCENARIOS.find((s) => s.id === activeTab) || SCENARIOS[0];

  const handleCopyTranscript = () => {
    const text = scenario.output.map((l) => l.text).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="terminal" className="py-20 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#536DFE]/15 text-[#38BDF8] border border-[#536DFE]/30 mb-4">
            <Terminal className="w-3.5 h-3.5" />
            <span>INTERACTIVE CLI SIMULATOR</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
            See DeepX in Action
          </h2>
          <p className="text-slate-300 text-sm sm:text-base">
            Watch how DeepX handles interactive processes, Windows clipboard memory, and automated code self-verification in real time.
          </p>
        </div>

        {/* Terminal Window Container */}
        <div className="max-w-4xl mx-auto rounded-2xl bg-[#0B0D14] border border-[#536DFE]/30 shadow-2xl shadow-black/80 overflow-hidden backdrop-blur-xl">
          {/* Title Bar */}
          <div className="px-4 py-3 bg-[#111420] border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 mr-3">
                <span className="w-3 h-3 rounded-full bg-[#EF4444]/80"></span>
                <span className="w-3 h-3 rounded-full bg-[#F59E0B]/80"></span>
                <span className="w-3 h-3 rounded-full bg-[#10B981]/80"></span>
              </div>
              <span className="text-xs font-mono text-slate-300 font-semibold flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-[#536DFE]" />
                DEEPX AGENT — Windows Terminal (ConPTY)
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`text-[11px] font-mono px-2 py-0.5 rounded border ${scenario.badge.color}`}
              >
                {scenario.badge.text}
              </span>
              <button
                onClick={handleCopyTranscript}
                className="p-1.5 rounded-lg bg-[#181D2B] hover:bg-[#232A3E] text-slate-300 hover:text-white transition-colors"
                title="Copy Terminal Transcript"
                data-testid="terminal-copy-btn"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#10B981]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Scenario Tabs */}
          <div className="flex overflow-x-auto border-b border-slate-800/80 bg-[#0E111B] px-3 gap-1 scrollbar-none">
            {SCENARIOS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                data-testid={`terminal-tab-${tab.id}`}
                className={`px-3.5 py-2 text-xs font-mono whitespace-nowrap transition-all duration-150 border-b-2 flex items-center gap-1.5 ${
                  activeTab === tab.id
                    ? 'border-[#536DFE] text-white font-bold bg-[#141926]'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#121622]'
                }`}
              >
                <span>{tab.title}</span>
              </button>
            ))}
          </div>

          {/* Terminal Body */}
          <div
            data-testid="terminal-body"
            className="p-6 font-mono text-xs sm:text-sm text-slate-200 space-y-2.5 min-h-[320px] max-h-[460px] overflow-y-auto bg-[#07090E]/95"
          >
            <div className="text-slate-500 mb-4 pb-2 border-b border-slate-800/50 flex items-center justify-between">
              <span># {scenario.promptText}</span>
              <span className="text-[10px] text-slate-600">PID: 8192 [JobObjectBound]</span>
            </div>

            {scenario.output.map((line, idx) => {
              let colorClass = 'text-slate-300';
              if (line.type === 'cmd') colorClass = 'text-[#38BDF8] font-bold';
              else if (line.type === 'success') colorClass = 'text-[#10B981]';
              else if (line.type === 'warn') colorClass = 'text-[#F59E0B] font-semibold';
              else if (line.type === 'dim') colorClass = 'text-slate-500';
              else if (line.type === 'highlight') colorClass = 'text-[#A78BFA] font-medium bg-[#A78BFA]/10 px-1 py-0.5 rounded';

              return (
                <div key={idx} className={`leading-relaxed ${colorClass}`}>
                  {line.text}
                </div>
              );
            })}

            {/* Terminal Cursor Line */}
            <div className="flex items-center gap-2 pt-3 text-slate-400">
              <span className="text-[#536DFE] font-bold">DEEPX ›</span>
              <span className="w-2 h-4 bg-[#38BDF8] animate-pulse inline-block"></span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
