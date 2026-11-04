import React, { useEffect } from 'react';
import { useLastlineStore } from './store/useLastlineStore';
import { useLiveStream } from './hooks/useLiveStream';
import { AdvisoryHeader } from './components/AdvisoryHeader';
import { ReplayControlBar } from './components/ReplayControlBar';
import { OperationsMap } from './components/OperationsMap';
import { NodeInspectorDrawer } from './components/NodeInspectorDrawer';
import { AgentReasoningView } from './components/AgentReasoningView';
import { TwinLabView } from './components/TwinLabView';
import { RecommendationPanel } from './components/RecommendationPanel';
import { AuditLogView } from './components/AuditLogView';
import { ShieldCheck, Info } from 'lucide-react';

export const App: React.FC = () => {
  const { isDark, activeView, selectedElementId, initStore } = useLastlineStore();

  // Initialize store and establish WebSocket stream
  useEffect(() => {
    initStore();
  }, [initStore]);

  useLiveStream(true);

  return (
    <div
      className={`min-h-screen flex flex-col ${
        isDark ? 'dark bg-ink text-bone' : 'bg-bone text-ink'
      } transition-colors duration-200`}
    >
      {/* 1. Top Advisory Header */}
      <AdvisoryHeader />

      {/* 2. Scenario & Simulation Transport Scrubber */}
      <ReplayControlBar />

      {/* 3. Main Operational Perspective */}
      <main className="flex-1 p-5 max-w-7xl w-full mx-auto space-y-5">
        {activeView === 'OPERATIONS_MAP' && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
              <div className="lg:col-span-2 space-y-4">
                <OperationsMap />
              </div>
              <div className="space-y-4">
                {selectedElementId && <NodeInspectorDrawer />}
                <RecommendationPanel />
              </div>
            </div>
          </div>
        )}

        {activeView === 'AGENT_REASONING' && <AgentReasoningView />}

        {activeView === 'TWIN_LAB' && <TwinLabView />}

        {activeView === 'AUDIT_LOG' && <AuditLogView />}
      </main>

      {/* 4. Advisory Safety Footer */}
      <footer className="border-t border-stone dark:border-basalt-subtle bg-bone-subtle dark:bg-basalt px-5 py-3 text-xs font-mono text-text-muted flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-moss" />
          <span>PROJECT LASTLINE • ADVISORY-ONLY WATER CYBER-RESILIENCE PLATFORM</span>
        </div>

        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1">
            <Info className="w-3.5 h-3.5 text-sage" />
            <span>EPANET & WNTR Digital Twin Engine</span>
          </span>
          <span>|</span>
          <span>Zero Actuation Guarantee</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
