import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from '../App';
import { Navbar } from '../components/Navbar';
import { HeroSection } from '../components/HeroSection';
import { TerminalSimulator } from '../components/TerminalSimulator';
import { BentoGrid } from '../components/BentoGrid';
import { UseCasesSection } from '../components/UseCasesSection';
import { ComparisonTable } from '../components/ComparisonTable';
import { DownloadSection } from '../components/DownloadSection';
import { Footer } from '../components/Footer';

describe('DeepX Landing Page Component Test Suite (Light Theme)', () => {
  it('renders entire App without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
    expect(screen.getByTestId('navbar-header')).toBeInTheDocument();
    expect(screen.getByTestId('site-footer')).toBeInTheDocument();
  });

  it('renders Navbar with logo asset, correct alt attribute, and navigation links', () => {
    render(<Navbar />);
    const logoImg = screen.getByAltText('DeepX Logo');
    expect(logoImg).toBeInTheDocument();
    expect(logoImg).toHaveAttribute('src', 'log.png');

    const githubLink = screen.getByTestId('github-link');
    expect(githubLink).toHaveAttribute('href', 'https://github.com/supeston/DeepCLI');
  });

  it('renders HeroSection with transparent log.png and copy install button', () => {
    render(<HeroSection />);
    expect(screen.getByText(/Experience liftoff with/i)).toBeInTheDocument();
    expect(screen.getAllByText(/DeepX/i).length).toBeGreaterThan(0);

    const heroLogImg = screen.getByAltText('DeepX Transparent Logo');
    expect(heroLogImg).toBeInTheDocument();
    expect(heroLogImg).toHaveAttribute('src', 'log.png');

    const copyBtn = screen.getByTestId('hero-copy-cmd-btn');
    expect(copyBtn).toBeInTheDocument();
    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders TerminalSimulator and allows switching scenario tabs', () => {
    render(<TerminalSimulator />);
    expect(screen.getByTestId('terminal-body')).toBeInTheDocument();
    expect(screen.getByTestId('terminal-tab-conpty')).toBeInTheDocument();

    // Click WinRT Clipboard scenario tab
    const clipboardTab = screen.getByTestId('terminal-tab-clipboard');
    fireEvent.click(clipboardTab);

    // Click Media Inspector tab
    const mediaTab = screen.getByTestId('terminal-tab-media');
    fireEvent.click(mediaTab);

    // Copy terminal transcript
    const copyTranscriptBtn = screen.getByTestId('terminal-copy-btn');
    fireEvent.click(copyTranscriptBtn);
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

  it('renders DownloadSection with transparent log.png watermark and copy triggers', () => {
    render(<DownloadSection />);
    expect(screen.getByText(/Experience liftoff with/i)).toBeInTheDocument();
    const watermark = screen.getByAltText('DeepX Watermark');
    expect(watermark).toHaveAttribute('src', 'log.png');

    const copyBtn0 = screen.getByTestId('install-copy-btn-0');
    fireEvent.click(copyBtn0);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders Footer with creator attribution (supeston) and logo', () => {
    render(<Footer />);
    const authorLink = screen.getByTestId('footer-author-link');
    expect(authorLink).toHaveAttribute('href', 'https://github.com/supeston');
    expect(authorLink).toHaveTextContent('supeston');

    const squareLogo = screen.getByAltText('DeepX Square Logo');
    expect(squareLogo).toHaveAttribute('src', 'logo.png');
  });
});
