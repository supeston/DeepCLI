import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';
import { Navbar } from '../components/Navbar';
import { HeroSection } from '../components/HeroSection';
import { TerminalSimulator } from '../components/TerminalSimulator';
import { BentoGrid } from '../components/BentoGrid';
import { UseCasesSection } from '../components/UseCasesSection';
import { ComparisonTable } from '../components/ComparisonTable';
import { DownloadSection } from '../components/DownloadSection';
import { Footer } from '../components/Footer';

describe('DeepX Landing Page Component Test Suite', () => {
  it('renders entire App without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
    expect(screen.getByTestId('navbar-header')).toBeInTheDocument();
    expect(screen.getByTestId('site-footer')).toBeInTheDocument();
  });

  it('renders Navbar with full_logo.png asset, correct alt attribute, and navigation links', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    const logoImg = screen.getByAltText('DeepX Logo');
    expect(logoImg).toBeInTheDocument();
    expect(logoImg).toHaveAttribute('src', 'full_logo.png');

    const githubLink = screen.getByTestId('github-link');
    expect(githubLink).toHaveAttribute('href', 'https://github.com/supeston/DeepCLI');
  });

  it('renders HeroSection with DeepX headline, DeepX artwork, and copy install button', () => {
    render(<HeroSection />);
    expect(screen.getByText(/Experience liftoff with the/i)).toBeInTheDocument();
    expect(screen.getByText(/next-gen agent platform/i)).toBeInTheDocument();

    const heroLogo = screen.getByAltText('DeepX');
    expect(heroLogo).toBeInTheDocument();
    expect(heroLogo).toHaveAttribute('src', 'full_logo.png');

    const copyBtn = screen.getByTestId('hero-copy-cmd-btn');
    expect(copyBtn).toBeInTheDocument();
    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders TerminalSimulator and allows copying command', () => {
    render(<TerminalSimulator />);
    expect(screen.getByTestId('terminal-body')).toBeInTheDocument();

    // Copy terminal prompt
    const copyBtn = screen.getByTestId('terminal-copy-btn');
    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders BentoGrid Feature Explorer and allows tab selection', () => {
    render(<BentoGrid />);
    expect(screen.getByText(/Built for developers for the/i)).toBeInTheDocument();
    expect(screen.getByTestId('feature-tab-cli')).toBeInTheDocument();

    // Switch to reasoning tab
    const reasoningTab = screen.getByTestId('feature-tab-reasoning');
    fireEvent.click(reasoningTab);
    expect(screen.getAllByText(/Zero-Telemetry Dual-Engine/i)[0]).toBeInTheDocument();
  });

  it('renders UseCasesSection with role cards and free tier pricing banner', () => {
    render(<UseCasesSection />);
    expect(screen.getByText(/Designed for every engineering workflow/i)).toBeInTheDocument();
    expect(screen.getByText(/Open Source & Free for Developers/i)).toBeInTheDocument();
  });

  it('renders ComparisonTable technical benchmark rows', () => {
    render(<ComparisonTable />);
    expect(screen.getByText(/Interactive Terminal Execution/i)).toBeInTheDocument();
    expect(screen.getByText(/Process Lifecycle & Zombie Cleanup/i)).toBeInTheDocument();
    expect(screen.getByText(/WinRT Clipboard Context/i)).toBeInTheDocument();
  });

  it('renders DownloadSection with installation steps and copy triggers', () => {
    render(<DownloadSection />);
    expect(screen.getByText(/Experience liftoff with/i)).toBeInTheDocument();

    const copyBtn0 = screen.getByTestId('install-copy-btn-0');
    fireEvent.click(copyBtn0);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders Footer with creator attribution (supeston) and full_logo.png', () => {
    render(<Footer />);
    const authorLink = screen.getByTestId('footer-author-link');
    expect(authorLink).toHaveAttribute('href', 'https://github.com/supeston');
    expect(authorLink).toHaveTextContent('supeston');

    const fullLogo = screen.getByAltText('DeepX Full Logo');
    expect(fullLogo).toHaveAttribute('src', 'full_logo.png');
  });
});
