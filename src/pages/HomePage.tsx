import React from 'react';
import { HeroSection } from '../components/HeroSection';
import { TerminalSimulator } from '../components/TerminalSimulator';
import { BentoGrid } from '../components/BentoGrid';
import { UseCasesSection } from '../components/UseCasesSection';
import { PricingSection } from '../components/PricingSection';
import { ComparisonTable } from '../components/ComparisonTable';
import { Marquee } from '../components/MotionEngine';
import { DownloadSection } from '../components/DownloadSection';

interface HomePageProps {
  onIntroComplete?: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onIntroComplete }) => {
  return (
    <>
      <HeroSection onTypingComplete={onIntroComplete} />
      <Marquee />
      <TerminalSimulator />
      <BentoGrid />
      <UseCasesSection />
      <PricingSection />
      <ComparisonTable />
      <DownloadSection />
    </>
  );
};
