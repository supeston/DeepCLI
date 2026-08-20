import { useState } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ParticleCanvas } from './components/ParticleCanvas';
import { Footer } from './components/Footer';

import { HomePage } from './pages/HomePage';
import { LogsPage } from './pages/LogsPage';

export function App() {
  const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';
  const [introComplete, setIntroComplete] = useState(isTest);

  return (
    <HashRouter>
      <div className="relative min-h-screen bg-white text-[#1F1F1F] selection:bg-[#536DFE]/20 selection:text-[#536DFE]">
        {/* DeepX Particle Field */}
        <ParticleCanvas />

        {/* Navigation - slides down from top after hero headline typing completes */}
        <Navbar isVisible={introComplete} />

        {/* Main Content Layout */}
        <main className="relative z-10">
          <Routes>
            <Route path="/" element={<HomePage onIntroComplete={() => setIntroComplete(true)} />} />
            <Route path="/logs" element={<LogsPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </HashRouter>
  );
}

export default App;
