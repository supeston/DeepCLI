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
    <div className="relative min-h-screen bg-white text-[#1F1F1F] selection:bg-[#536DFE]/20 selection:text-[#536DFE]">
      {/* Google Antigravity Light Particle Field */}
      <AntiGravityCanvas />

      {/* Navigation */}
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

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
