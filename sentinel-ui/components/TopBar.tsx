import { Shield, Activity } from "lucide-react";

export default function TopBar({ incidentCount, pendingCount }: {
  incidentCount: number;
  pendingCount: number;
}) {
  return (
    <header className="bg-bg-panel border-b border-border-subtle px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-accent" />
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Sentinel</h1>
          <p className="text-xs text-text-muted">AI Observability Agent · Gemini 3.1 + Phoenix</p>
        </div>
      </div>
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2 text-text-secondary">
          <Activity className="w-4 h-4 text-status-ok" />
          <span>Watching <span className="text-text-primary font-medium">refundbot-prod</span></span>
        </div>
        <div className="text-text-secondary">
          {incidentCount} incidents · {pendingCount > 0 ? (
            <span className="text-status-warn font-medium">{pendingCount} pending approval</span>
          ) : (
            <span className="text-text-muted">no pending actions</span>
          )}
        </div>
      </div>
    </header>
  );
}