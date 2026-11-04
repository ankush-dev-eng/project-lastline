import React, { useState } from 'react';
import { ShieldAlert, Activity, Cpu, Radio, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  return (
    <div className={`min-h-screen ${isDark ? 'dark bg-ink text-bone' : 'bg-bone text-ink'} transition-colors duration-200`}>
      {/* Top Advisory Banner */}
      <header className="border-b border-stone dark:border-basalt-subtle bg-bone-subtle dark:bg-basalt px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold tracking-tight text-lg text-ink dark:text-bone">PROJECT LASTLINE</span>
            <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-stone dark:bg-basalt-subtle text-ink dark:text-bone">
              v0.1.0-alpha
            </span>
          </div>
          <span className="text-stone-border dark:text-basalt-subtle">|</span>
          <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brick-subtle text-brick border border-brick/30">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>SANDBOX – ADVISORY ONLY (ZERO ACTUATION)</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-moss animate-pulse"></span>
            <span className="text-moss font-semibold">DIGITAL TWIN ONLINE</span>
          </div>
          <button
            onClick={() => setIsDark(!isDark)}
            className="text-xs px-3 py-1.5 rounded border border-stone dark:border-basalt-subtle hover:bg-stone/20 dark:hover:bg-basalt-subtle font-mono transition-colors"
          >
            {isDark ? 'LIGHT THEME' : 'DARK THEME'}
          </button>
        </div>
      </header>

      {/* Main Scaffold Grid */}
      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Status Card 1 */}
          <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-2">
              <span>PHYSICAL RECONSTRUCTION</span>
              <Activity className="w-4 h-4 text-sage" />
            </div>
            <div className="text-2xl font-bold font-telemetry text-sage">NOMINAL</div>
            <div className="text-xs text-text-muted mt-1">Hydraulic WLS state estimator ready</div>
          </div>

          {/* Status Card 2 */}
          <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-2">
              <span>TELEMETRY TRUST</span>
              <Cpu className="w-4 h-4 text-moss" />
            </div>
            <div className="text-2xl font-bold font-telemetry text-moss">100.0%</div>
            <div className="text-xs text-text-muted mt-1">All sensors within physical envelope</div>
          </div>

          {/* Status Card 3 */}
          <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-2">
              <span>CYBER SENTINEL</span>
              <Radio className="w-4 h-4 text-brass" />
            </div>
            <div className="text-2xl font-bold font-telemetry text-brass">STANDBY</div>
            <div className="text-xs text-text-muted mt-1">Listening on SCADA/PLC telemetry feed</div>
          </div>

          {/* Status Card 4 */}
          <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
            <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-2">
              <span>SAFETY INVARIANT</span>
              <CheckCircle2 className="w-4 h-4 text-moss" />
            </div>
            <div className="text-2xl font-bold font-telemetry text-moss">ENFORCED</div>
            <div className="text-xs text-text-muted mt-1">Zero write-capable control endpoints</div>
          </div>
        </div>

        {/* Welcome & Overview Panel */}
        <div className="p-6 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-4">
          <h2 className="text-xl font-bold tracking-tight">Critical Water Infrastructure Cyber-Resilience Operations</h2>
          <p className="text-sm text-text-muted leading-relaxed">
            PROJECT LASTLINE couples hydraulic physics constraints with machine learning state estimators to overcome operational blindness during SCADA compromise. When telemetry cannot be trusted, LASTLINE identifies compromised instrumentation, estimates true system pressures and storage volumes, and computes verified emergency fallback procedures for human operators.
          </p>
        </div>
      </main>
    </div>
  );
};

export default App;
