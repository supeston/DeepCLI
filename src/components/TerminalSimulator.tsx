import React, { useState, useEffect } from 'react';
import { Terminal as TermIcon, Copy, Check, MousePointerClick, Maximize2, X, Minus } from 'lucide-react';

type TerminalScenario = 'conpty' | 'clipboard' | 'media';

export const TerminalSimulator: React.FC = () => {
  const [activeScenario, setActiveScenario] = useState<TerminalScenario>('conpty');
  const [typedText, setTypedText] = useState('');
  const [copied, setCopied] = useState(false);

  const scenarios = {
    conpty: {
      label: 'ConPTY Execution',
      icon: TermIcon,
      command: 'deepx run --cmd "npm run build"',
      output: [
        'Initialize Windows ConPTY (Pseudo-Console) engine...',
        'Spawning background process: npm run build',
        '\x1b[36m> vite build\x1b[0m',
        'transforming (1200) node_modules/react-dom/index.js...',
        '✓ 1597 modules transformed.',
        '\x1b[32mBuild completed in 2.60s. Zero Zombie Processes remaining.\x1b[0m',
        'Agent observation: Build succeeded. Artifacts placed in /dist.',
      ],
    },
    clipboard: {
      label: 'WinRT Clipboard',
      icon: MousePointerClick,
      command: 'deepx context read --source=clipboard --type=image',
      output: [
        'WINRT API READY.',
        'Accessing Windows.ApplicationModel.DataTransfer.Clipboard...',
        'Found active image payload in clipboard history (Format: CF_DIBV5).',
        'Extracting bitmap bytes...',
        '\x1b[32mSuccess: Captured 1920x1080 Image (2.1MB).\x1b[0m',
        'Passing binary image buffer to Vision Engine for multimodal reasoning...',
        'Agent observation: The image contains a stack trace pointing to a NullReferenceException in app.tsx:42.',
      ],
    },
    media: {
      label: 'Media Inspection',
      icon: Maximize2,
      command: 'deepx analyze --file=demo_recording.mp4',
      output: [
        'PYMEDIAINFO / FFPROBE initialized.',
        'Probing media container: demo_recording.mp4',
        'Codec: H.264 (High Profile) | Resolution: 3840x2160 | FPS: 60',
        'Audio: AAC-LC 48kHz Stereo',
        'Extracting keyframes at 1s intervals for vision analysis...',
        '\x1b[32mProcessed 45 keyframes successfully.\x1b[0m',
        'Agent observation: Video demonstrates the bug occurring right after the user clicks the "Submit" button at 00:12.',
      ],
    },
  };

  useEffect(() => {
    setTypedText('');
    let i = 0;
    const cmd = scenarios[activeScenario].command;
    const interval = setInterval(() => {
      setTypedText(cmd.slice(0, i));
      i++;
      if (i > cmd.length) clearInterval(interval);
    }, 30);
    return () => clearInterval(interval);
  }, [activeScenario]);

  const handleCopy = () => {
    const fullText = `PS> ${scenarios[activeScenario].command}\n` + scenarios[activeScenario].output.join('\n');
    navigator.clipboard.writeText(fullText.replace(/\x1b\[[0-9;]*m/g, ''));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-24 bg-gray-50 border-y border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-normal text-gray-900 tracking-tight mb-4">
            Native Windows Integration
          </h2>
          <p className="text-gray-600 text-lg font-normal">
            DeepX doesn't just read code. It executes real commands in ConPTY and inspects your Windows clipboard via WinRT, acting as a true desktop pair programmer.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
            {(Object.entries(scenarios) as [TerminalScenario, typeof scenarios['conpty']][]).map(([key, data]) => {
              const Icon = data.icon;
              const isActive = activeScenario === key;
              return (
                <button
                  key={key}
                  onClick={() => setActiveScenario(key)}
                  data-testid={`terminal-tab-${key}`}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[#1a73e8] text-white shadow-md'
                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{data.label}</span>
                </button>
              );
            })}
          </div>

          {/* Terminal Window (Dark inside light theme) */}
          <div className="rounded-xl overflow-hidden bg-[#0A0D14] border border-gray-300 shadow-2xl">
            {/* Terminal Header */}
            <div className="bg-[#12151E] px-4 py-3 flex items-center justify-between border-b border-white/5 select-none">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56] border border-[#E0443E]" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E] border border-[#DEA123]" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F] border border-[#1AAB29]" />
              </div>
              <div className="text-[#8AB4F8] text-xs font-mono font-medium flex items-center gap-2">
                <TermIcon className="w-3.5 h-3.5" />
                deepx.exe
              </div>
              <button
                onClick={handleCopy}
                data-testid="terminal-copy-btn"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Copy terminal output"
              >
                {copied ? <Check className="w-4 h-4 text-[#27C93F]" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            {/* Terminal Body */}
            <div className="p-5 font-mono text-sm leading-relaxed overflow-x-auto" data-testid="terminal-body">
              <div className="flex items-start text-gray-300 mb-4">
                <span className="text-[#8AB4F8] font-bold mr-3 select-none">PS&gt;</span>
                <span className="text-white">{typedText}</span>
                {typedText.length === scenarios[activeScenario].command.length && (
                  <span className="w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
                )}
              </div>

              {typedText.length === scenarios[activeScenario].command.length && (
                <div className="space-y-1.5 animate-in fade-in duration-500 delay-150 fill-mode-backwards">
                  {scenarios[activeScenario].output.map((line, idx) => (
                    <div
                      key={idx}
                      className="text-gray-400"
                      dangerouslySetInnerHTML={{
                        __html: line
                          .replace(/\x1b\[36m/g, '<span class="text-cyan-400">')
                          .replace(/\x1b\[32m/g, '<span class="text-green-400">')
                          .replace(/\x1b\[0m/g, '</span>'),
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
