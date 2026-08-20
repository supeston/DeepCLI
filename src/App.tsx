import { Navbar } from './components/Navbar';
import { AntiGravityCanvas } from './components/AntiGravityCanvas';
import { HeroSection } from './components/HeroSection';
import { TerminalSimulator } from './components/TerminalSimulator';
import { BentoGrid } from './components/BentoGrid';
import { ComparisonTable } from './components/ComparisonTable';
import { DownloadSection } from './components/DownloadSection';
import { Footer } from './components/Footer';

export function App() {
  return (
    <div className="relative min-h-screen bg-[#090A0F] text-slate-100 selection:bg-[#536DFE]/30 selection:text-[#38BDF8]">
      {/* Background Interactive Canvas Particle Field */}
      <AntiGravityCanvas />

      {/* Navigation */}
      <Navbar />

      {/* Main Content Layout */}
      <main className="relative z-10">
        <HeroSection />
        <TerminalSimulator />
        <BentoGrid />
        <ComparisonTable />
        <DownloadSection />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
