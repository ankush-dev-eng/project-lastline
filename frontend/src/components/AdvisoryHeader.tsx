import React from 'react';
import { ShieldAlert, Sun, Moon, Map, GitFork, FlaskConical, FileText } from 'lucide-react';
import { useLastlineStore } from '../store/useLastlineStore';
import type { ViewMode } from '../types';

export const AdvisoryHeader: React.FC = () => {
  const { isDark, toggleTheme, activeView, setActiveView, connectionStatus } = useLastlineStore();

  const navItems: { mode: ViewMode; label: string; icon: React.ReactNode }[] = [
    { mode: 'OPERATIONS_MAP', label: 'Operations Map', icon: <Map className="w-3.5 h-3.5" /> },
    { mode: 'AGENT_REASONING', label: 'Agent Reasoning', icon: <GitFork className="w-3.5 h-3.5" /> },
    { mode: 'TWIN_LAB', label: 'Digital Twin Lab', icon: <FlaskConical className="w-3.5 h-3.5" /> },
    { mode: 'AUDIT_LOG', label: 'Audit Ledger', icon: <FileText className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="border-b border-stone dark:border-basalt-subtle bg-bone-subtle dark:bg-basalt px-5 py-2.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
      {/* Brand & Advisory Guardrail */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="font-bold tracking-tight text-base text-ink dark:text-bone">
            PROJECT LASTLINE
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-stone dark:bg-basalt-subtle text-ink dark:text-bone border border-stone-border dark:border-basalt-subtle">
            v0.8.0
          </span>
        </div>

        <span className="text-stone dark:text-basalt-subtle">|</span>

        {/* Mandatory Advisory Safety Pill */}
        <div
          data-testid="advisory-pill"
          className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brick-subtle text-brick border border-brick/40"
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span className="tracking-wide">SANDBOX – ADVISORY ONLY (ZERO PHYSICAL ACTUATION)</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav aria-label="Main Navigation" className="flex items-center space-x-1 bg-stone/40 dark:bg-ink-muted/50 p-1 rounded-md border border-stone dark:border-basalt-subtle">
        {navItems.map((item) => (
          <button
            key={item.mode}
            onClick={() => setActiveView(item.mode)}
            className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeView === item.mode
                ? 'bg-white dark:bg-basalt text-ink dark:text-bone shadow-xs font-semibold'
                : 'text-text-muted hover:text-ink dark:hover:text-bone hover:bg-stone/30 dark:hover:bg-basalt-subtle/50'
            }`}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Status & Theme Toggle */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              connectionStatus === 'LIVE'
                ? 'bg-moss animate-pulse'
                : connectionStatus === 'CONNECTING'
                ? 'bg-brass'
                : 'bg-brick'
            }`}
          />
          <span className="text-text-muted">
            {connectionStatus === 'LIVE'
              ? 'TWIN STREAM ONLINE'
              : connectionStatus === 'CONNECTING'
              ? 'CONNECTING...'
              : 'STREAM OFFLINE'}
          </span>
        </div>

        <button
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          className="p-1.5 rounded border border-stone dark:border-basalt-subtle hover:bg-stone/30 dark:hover:bg-basalt-subtle text-ink dark:text-bone transition-colors"
          title={isDark ? 'Light Mode' : 'Dark Mode'}
        >
          {isDark ? <Sun className="w-4 h-4 text-brass" /> : <Moon className="w-4 h-4 text-basalt" />}
        </button>
      </div>
    </header>
  );
};
