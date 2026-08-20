import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { TerminalSimulator } from './components/TerminalSimulator';
import { BentoGrid } from './components/BentoGrid';
import { UseCasesSection } from './components/UseCasesSection';
import { ComparisonTable } from './components/ComparisonTable';
import { DownloadSection } from './components/DownloadSection';
import { Footer } from './components/Footer';

export function App() {
  return (
    <div className="relative min-h-screen bg-white text-[#202124] selection:bg-[#1a73e8]/20 selection:text-[#1a73e8]">
      {/* Google Antigravity Navigation */}
      <Navbar />

      {/* Main Content Layout */}
      <main className="relative z-10">
        <HeroSection />
        <TerminalSimulator />
        <BentoGrid />
        <UseCasesSection />
        <ComparisonTable />
        <DownloadSection />
      </main>

      {/* Google Antigravity Footer */}
      <Footer />
    </div>
  );
}

export default App;
