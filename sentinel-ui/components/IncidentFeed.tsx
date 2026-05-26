import type { Incident } from "@/lib/api";
import { AlertCircle, CheckCircle2, XCircle, Clock } from "lucide-react";

const sevColors: Record<string, string> = {
  high: "border-l-status-err",
  medium: "border-l-status-warn",
  low: "border-l-status-info",
};

const statusIcon: Record<string, React.ReactNode> = {
  resolved: <CheckCircle2 className="w-3.5 h-3.5 text-status-ok" />,
  investigating: <Clock className="w-3.5 h-3.5 text-status-warn animate-pulse" />,
  rollback_failed: <XCircle className="w-3.5 h-3.5 text-status-err" />,
  rejected_by_human: <XCircle className="w-3.5 h-3.5 text-text-muted" />,
};

function timeAgo(iso?: string): string {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  const min = Math.floor(ms / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

export default function IncidentFeed({ incidents, loading, selectedId, onSelect }: {
  incidents: Incident[];
  loading: boolean;
  selectedId?: string;
  onSelect: (i: Incident) => void;
}) {
  return (
    <aside className="bg-bg-panel overflow-y-auto">
      <header className="px-4 py-3 border-b border-border-subtle sticky top-0 bg-bg-panel z-10">
        <h2 className="text-xs uppercase tracking-wider text-text-muted">Incidents</h2>
      </header>
      <div className="divide-y divide-border-subtle">
        {loading && <div className="px-4 py-8 text-sm text-text-muted">Loading…</div>}
        {!loading && incidents.length === 0 && (
          <div className="px-4 py-8 text-sm text-text-muted">No incidents yet.</div>
        )}
        {incidents.map((inc) => (
          <button
            key={inc.id}
            onClick={() => onSelect(inc)}
            className={`w-full text-left px-4 py-3 hover:bg-bg-elevated transition-colors border-l-2 ${
                sevColors[inc.severity] || ""
            } ${selectedId === inc.id ? "bg-bg-elevated" : ""}`}
            style={{ borderLeftColor: sevColors[inc.severity] ? undefined : "transparent" }}
          >
            <div className="text-sm font-medium leading-tight mb-1.5">{inc.title}</div>
            <div className="flex items-center gap-2 text-xs text-text-muted">
              {statusIcon[inc.status] || <AlertCircle className="w-3.5 h-3.5 text-text-muted" />}
              <span>{inc.status}</span>
              <span>·</span>
              <span>{timeAgo(inc.created_at)}</span>
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}