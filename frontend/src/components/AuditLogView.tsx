import React, { useState } from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import { ShieldCheck, AlertTriangle, RefreshCw, Search } from 'lucide-react';

export const AuditLogView: React.FC = () => {
  const { auditEntries, isChainValid, refreshAuditLog } = useLastlineStore();
  const [filterText, setFilterText] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshAuditLog();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filtered = auditEntries.filter((e) => {
    const q = filterText.toLowerCase();
    return (
      e.agent.toLowerCase().includes(q) ||
      e.action.toLowerCase().includes(q) ||
      e.entry_hash.toLowerCase().includes(q) ||
      JSON.stringify(e.payload).toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-4">
      {/* Chain Integrity Banner */}
      <div
        className={`p-4 rounded border flex flex-wrap items-center justify-between gap-3 ${
          isChainValid
            ? 'bg-moss-subtle text-moss border-moss/40'
            : 'bg-brick-subtle text-brick border-brick/40'
        }`}
      >
        <div className="flex items-center space-x-3">
          {isChainValid ? (
            <ShieldCheck className="w-5 h-5 text-moss" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-brick animate-bounce" />
          )}
          <div>
            <h3 className="font-bold text-sm tracking-tight">
              {isChainValid
                ? 'CRYPTOGRAPHIC SHA-256 AUDIT CHAIN: 100% VALID & TAMPER-FREE'
                : 'SECURITY ALERT: CRYPTOGRAPHIC HASH CHAIN TAMPERING DETECTED'}
            </h3>
            <p className="text-xs opacity-90 font-mono">
              All agent assessments, state reconstructions, and operator actions are cryptographically chained.
            </p>
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="px-3 py-1.5 rounded text-xs font-mono font-semibold bg-white dark:bg-basalt text-ink dark:text-bone border border-stone/50 dark:border-basalt-subtle hover:bg-stone/20 dark:hover:bg-basalt-subtle flex items-center space-x-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>VERIFY INTEGRITY</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt flex items-center space-x-2 text-xs">
        <Search className="w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search audit trail by agent, action, hash, or payload parameters..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="w-full bg-transparent border-none focus:outline-hidden text-ink dark:text-bone font-mono"
        />
        <span className="text-text-muted font-mono shrink-0">
          {filtered.length} of {auditEntries.length} entries
        </span>
      </div>

      {/* Audit Entries List */}
      <div className="space-y-3">
        {filtered.map((entry) => (
          <div
            key={entry.entry_id}
            className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-2 shadow-xs font-mono text-xs"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone/30 dark:border-basalt-subtle/50 pb-2">
              <div className="flex items-center space-x-2">
                <span className="font-bold text-ink dark:text-bone">{entry.entry_id}</span>
                <span className="text-stone dark:text-basalt-subtle">|</span>
                <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-stone/40 dark:bg-basalt-subtle text-ink dark:text-bone">
                  {entry.agent}
                </span>
                <span className="text-sage font-bold">{entry.action}</span>
              </div>

              <span className="text-text-muted text-[11px]">
                Timestamp: T+{entry.timestamp.toFixed(1)}s ({new Date(entry.timestamp * 1000).toLocaleTimeString()})
              </span>
            </div>

            {/* Payload summary */}
            <div className="bg-bone/40 dark:bg-ink/40 p-2.5 rounded border border-stone/30 dark:border-basalt-subtle text-[11px] text-text-muted overflow-x-auto">
              <pre className="font-telemetry whitespace-pre-wrap">
                {JSON.stringify(entry.payload, null, 2)}
              </pre>
            </div>

            {/* SHA-256 Hashes Chaining */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px] text-text-muted pt-1">
              <div className="flex items-center space-x-1.5 truncate">
                <span className="font-semibold shrink-0">PREVIOUS HASH:</span>
                <span className="font-telemetry truncate text-stone-border dark:text-basalt-subtle">
                  {entry.previous_hash}
                </span>
              </div>
              <div className="flex items-center space-x-1.5 truncate">
                <span className="font-semibold shrink-0 text-sage">ENTRY HASH:</span>
                <span className="font-telemetry truncate text-sage font-bold">
                  {entry.entry_hash}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
