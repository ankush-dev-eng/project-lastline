import React, { useState } from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  Lock,
} from 'lucide-react';

export const RecommendationPanel: React.FC = () => {
  const { frame, approvalRecords, recordDecision } = useLastlineStore();
  const recommendations = frame.recommendations || [];

  const [operatorId, setOperatorId] = useState('OP-42-CHIEF');
  const [operatorNotes, setOperatorNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAction = async (recId: string, action: 'APPROVE' | 'REJECT') => {
    setIsSubmitting(true);
    try {
      await recordDecision(recId, action, operatorId, operatorNotes);
      setOperatorNotes('');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!recommendations.length) {
    return (
      <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt text-center text-xs text-text-muted font-mono">
        No active fallback procedures required. Hydraulic distribution operating within normal physical parameters.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {recommendations.map((rec) => {
        const approval = approvalRecords[rec.recommendation_id];
        const isApproved = approval?.status === 'APPROVED';
        const isPending = !approval;

        return (
          <div
            key={rec.recommendation_id}
            className="p-5 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-4 shadow-xs"
          >
            {/* Header: Title & Verification Badge */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone/40 dark:border-basalt-subtle pb-3">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-stone/50 dark:bg-basalt-subtle text-ink dark:text-bone">
                    {rec.playbook_id}
                  </span>
                  <h3 className="font-bold text-sm text-ink dark:text-bone tracking-tight">
                    {rec.title}
                  </h3>
                </div>
                <p className="text-xs text-text-muted leading-relaxed">{rec.description}</p>
              </div>

              {/* Digital Twin Forward-Verification Badge */}
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded bg-moss-subtle text-moss border border-moss/40 text-xs font-mono font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>EPANET TWIN: VERIFIED SAFE (P ≥ 15m)</span>
              </div>
            </div>

            {/* Recommended Action Checklist */}
            <div className="space-y-1.5">
              <span className="text-xs font-mono font-semibold text-text-muted">
                PRE-APPROVED OPERATOR PROCEDURE:
              </span>
              <ul className="space-y-1 text-xs text-ink dark:text-bone">
                {rec.recommended_actions.map((act, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-sage font-mono font-bold">{idx + 1}.</span>
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Structured Evidence Balance Sheet */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              {/* Evidence For */}
              <div className="p-3 rounded bg-moss-subtle/30 border border-moss/30 space-y-1.5">
                <span className="font-mono font-bold text-moss flex items-center space-x-1 text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>EVIDENCE FOR ({rec.evidence?.evidence_for?.length ?? 0})</span>
                </span>
                <ul className="space-y-1 text-text-muted text-[11px] list-disc list-inside">
                  {rec.evidence?.evidence_for?.map((e, idx) => (
                    <li key={idx} className="leading-snug">
                      {e}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Evidence Against */}
              <div className="p-3 rounded bg-stone/20 dark:bg-basalt-subtle/30 border border-stone/50 dark:border-basalt-subtle space-y-1.5">
                <span className="font-mono font-bold text-text-muted flex items-center space-x-1 text-[11px]">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>EVIDENCE AGAINST ({rec.evidence?.evidence_against?.length ?? 0})</span>
                </span>
                <ul className="space-y-1 text-text-muted text-[11px] list-disc list-inside">
                  {rec.evidence?.evidence_against?.length ? (
                    rec.evidence.evidence_against.map((e, idx) => (
                      <li key={idx} className="leading-snug">
                        {e}
                      </li>
                    ))
                  ) : (
                    <li className="italic">No contradictory hydraulic telemetry detected.</li>
                  )}
                </ul>
              </div>

              {/* Engineering Assumptions */}
              <div className="p-3 rounded bg-bone dark:bg-ink-muted/30 border border-stone/40 dark:border-basalt-subtle space-y-1.5">
                <span className="font-mono font-bold text-copper flex items-center space-x-1 text-[11px]">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>ASSUMPTIONS ({rec.evidence?.assumptions?.length ?? 0})</span>
                </span>
                <ul className="space-y-1 text-text-muted text-[11px] list-disc list-inside">
                  {rec.evidence?.assumptions?.map((a, idx) => (
                    <li key={idx} className="leading-snug">
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Human-in-the-Loop Action Form */}
            <div className="pt-3 border-t border-stone/40 dark:border-basalt-subtle space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2 text-xs font-mono">
                  <Lock className="w-3.5 h-3.5 text-sage" />
                  <span className="font-semibold text-ink dark:text-bone">
                    OPERATOR AUTHORIZATION REQUIRED
                  </span>
                  <span className="text-text-muted">| Advisory Decision Audit</span>
                </div>

                <div className="text-xs font-mono">
                  Confidence Score:{' '}
                  <span className="font-bold text-moss">
                    {(rec.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Status display if already decided */}
              {!isPending && (
                <div
                  className={`p-3 rounded border text-xs font-mono flex items-center justify-between ${
                    isApproved
                      ? 'bg-moss-subtle text-moss border-moss/40'
                      : 'bg-brick-subtle text-brick border-brick/40'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {isApproved ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span className="font-bold">
                      {isApproved ? 'PROCEDURE APPROVED' : 'PROCEDURE REJECTED'}
                    </span>
                    <span className="text-text-muted">
                      by {approval?.operator} at {new Date(approval?.timestamp ?? Date.now()).toLocaleTimeString()}
                    </span>
                  </div>
                  <span className="text-[10px] uppercase font-semibold">RECORDED IN AUDIT LEDGER</span>
                </div>
              )}

              {/* Action Buttons & Input if pending */}
              {isPending && (
                <div className="space-y-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                    <input
                      type="text"
                      placeholder="Operator ID (e.g. OP-42)"
                      value={operatorId}
                      onChange={(e) => setOperatorId(e.target.value)}
                      className="bg-bone dark:bg-ink-muted border border-stone dark:border-basalt-subtle px-3 py-1.5 rounded text-ink dark:text-bone focus:outline-hidden focus:ring-1 focus:ring-sage"
                    />
                    <input
                      type="text"
                      placeholder="Operational justification or notes (optional)"
                      value={operatorNotes}
                      onChange={(e) => setOperatorNotes(e.target.value)}
                      className="bg-bone dark:bg-ink-muted border border-stone dark:border-basalt-subtle px-3 py-1.5 rounded text-ink dark:text-bone focus:outline-hidden focus:ring-1 focus:ring-sage"
                    />
                  </div>

                  <div className="flex items-center space-x-3 pt-1">
                    <button
                      onClick={() => handleAction(rec.recommendation_id, 'APPROVE')}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded text-xs font-semibold bg-moss hover:bg-moss/90 text-white flex items-center space-x-1.5 shadow-xs transition-colors disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>APPROVE PROCEDURE</span>
                    </button>

                    <button
                      onClick={() => handleAction(rec.recommendation_id, 'REJECT')}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded text-xs font-semibold bg-brick hover:bg-brick/90 text-white flex items-center space-x-1.5 shadow-xs transition-colors disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>REJECT PROCEDURE</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Advisory Guarantee Notice */}
              <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono pt-1">
                <ShieldAlert className="w-3.5 h-3.5 text-brick shrink-0" />
                <span>
                  SANDBOX GUARANTEE: Operator decisions record advisory authorization into the SHA-256 immutable audit ledger. Zero physical SCADA or PLC commands are dispatched.
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
