"use client";

import { useState } from "react";
import { AlertTriangle, Check, X } from "lucide-react";
import type { ApprovalRequest } from "@/lib/api";
import { decideApproval } from "@/lib/api";

export default function ActionPanel({ approvals, onDecided }: {
  approvals: ApprovalRequest[];
  onDecided: () => void;
}) {
  const [working, setWorking] = useState<string | null>(null);
  const top = approvals[0];

  async function decide(requestId: string, d: "approve" | "reject") {
    setWorking(requestId);
    try {
      await decideApproval(requestId, d);
      onDecided();
    } catch (e) {
      console.error(e);
    } finally {
      setWorking(null);
    }
  }

  if (!top) {
    return (
      <aside className="bg-bg-panel p-6 text-sm">
        <div className="flex items-center gap-2 mb-2">
          <Check className="w-4 h-4 text-status-ok" />
          <span className="text-text-secondary">No pending actions</span>
        </div>
        <p className="text-text-muted text-xs leading-relaxed">
          Sentinel will request approval here when it needs to remediate an incident.
        </p>
      </aside>
    );
  }

  return (
    <aside className="bg-bg-panel flex flex-col">
      <header className="px-4 py-3 border-b border-border-subtle">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-status-warn">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Approval Required</span>
        </div>
        <h3 className="text-base font-semibold mt-1 leading-snug">{top.proposed_action}</h3>
      </header>
      <div className="flex-1 px-4 py-4 overflow-y-auto">
        <div className="mb-3">
          <div className="text-xs text-text-muted mb-1">Incident</div>
          <div className="text-sm font-mono text-text-secondary">{top.incident_id}</div>
        </div>
        <div className="mb-4">
          <div className="text-xs text-text-muted mb-1">Rationale</div>
          <p className="text-sm leading-relaxed text-text-primary">{top.rationale}</p>
        </div>
      </div>
      <footer className="p-4 border-t border-border-subtle grid grid-cols-2 gap-2">
        <button
          disabled={!!working}
          onClick={() => decide(top.request_id, "reject")}
          className="py-2 rounded bg-bg-elevated hover:bg-status-err/20 hover:text-status-err transition flex items-center justify-center gap-1.5 text-sm disabled:opacity-50"
        >
          <X className="w-4 h-4" /> Reject
        </button>
        <button
          disabled={!!working}
          onClick={() => decide(top.request_id, "approve")}
          className="py-2 rounded bg-accent text-bg-base font-semibold hover:bg-accent/90 transition flex items-center justify-center gap-1.5 text-sm disabled:opacity-50"
        >
          <Check className="w-4 h-4" /> Approve &amp; Execute
        </button>
      </footer>
    </aside>
  );
}