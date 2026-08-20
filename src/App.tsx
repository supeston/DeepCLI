import { Navbar } from './components/Navbar';
import { AntiGravityCanvas } from './components/AntiGravityCanvas';
import { HeroSection } from './components/HeroSection';
import { TerminalSimulator } from './components/TerminalSimulator';
import { BentoGrid } from './components/BentoGrid';
import { UseCasesSection } from './components/UseCasesSection';
import { ComparisonTable } from './components/ComparisonTable';
import { DownloadSection } from './components/DownloadSection';
import { Footer } from './components/Footer';

export function App() {
  return (
    <div className="relative min-h-screen bg-[#090A0F] text-[#E8EAED] selection:bg-[#1a73e8]/30 selection:text-[#8AB4F8]">
      {/* Background Interactive Antigravity Particle Field */}
      <AntiGravityCanvas />

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
