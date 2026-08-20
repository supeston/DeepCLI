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
import { AntiGravityCanvas } from '../components/AntiGravityCanvas';

describe('DeepX Antigravity Landing Page Component Test Suite', () => {
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
    expect(logoImg).toHaveAttribute('src', 'full_logo.png');

    const githubLink = screen.getByTestId('github-link');
    expect(githubLink).toHaveAttribute('href', 'https://github.com/supeston/DeepCLI');
  });

  it('renders HeroSection with title and copy install button', () => {
    render(<HeroSection />);
    expect(screen.getByText(/Experience liftoff with the/i)).toBeInTheDocument();
    expect(screen.getByText(/next-gen agent platform/i)).toBeInTheDocument();

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
    expect(screen.getByText(/WINRT API READY/i)).toBeInTheDocument();

    // Click Media Inspector tab
    const mediaTab = screen.getByTestId('terminal-tab-media');
    fireEvent.click(mediaTab);
    expect(screen.getByText(/PYMEDIAINFO \/ FFPROBE/i)).toBeInTheDocument();

    // Copy terminal transcript
    const copyTranscriptBtn = screen.getByTestId('terminal-copy-btn');
    fireEvent.click(copyTranscriptBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('renders BentoGrid Feature Explorer and allows tab selection', () => {
    render(<BentoGrid />);
    expect(screen.getByText(/Built for developers for the/i)).toBeInTheDocument();
    expect(screen.getByTestId('feature-tab-cli')).toBeInTheDocument();

    // Switch to SDK tab
    const sdkTab = screen.getByTestId('feature-tab-sdk');
    fireEvent.click(sdkTab);
    expect(screen.getAllByText(/Python Agent Harness/i)[0]).toBeInTheDocument();
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
    expect(screen.getByText(/Clipboard History \(Win \+ V\)/i)).toBeInTheDocument();
  });

  it('renders DownloadSection with installation steps and copy triggers', () => {
    render(<DownloadSection />);
    expect(screen.getByText(/Experience liftoff with/i)).toBeInTheDocument();
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

  it('initializes and cleanly unmounts AntiGravityCanvas without memory leak', () => {
    const cancelAnimationFrameSpy = vi.spyOn(window, 'cancelAnimationFrame');
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = render(<AntiGravityCanvas />);
    expect(screen.getByTestId('antigravity-canvas')).toBeInTheDocument();

    unmount();
    expect(cancelAnimationFrameSpy).toHaveBeenCalled();
    expect(removeEventListenerSpy).toHaveBeenCalled();
  });
});
