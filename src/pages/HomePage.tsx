import React from 'react';
import { HeroSection } from '../components/HeroSection';
import { TerminalSimulator } from '../components/TerminalSimulator';
import { BentoGrid } from '../components/BentoGrid';
import { UseCasesSection } from '../components/UseCasesSection';
import { PricingSection } from '../components/PricingSection';
import { ComparisonTable } from '../components/ComparisonTable';
import { DownloadSection } from '../components/DownloadSection';

export const HomePage: React.FC = () => {
  return (
    <>
      <HeroSection />
      <TerminalSimulator />
      <BentoGrid />
      <UseCasesSection />
      <PricingSection />
      <ComparisonTable />
      <DownloadSection />
    </>
  );
};
