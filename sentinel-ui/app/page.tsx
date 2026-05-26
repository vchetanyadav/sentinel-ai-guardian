"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import IncidentFeed from "@/components/IncidentFeed";
import AgentCanvas from "@/components/AgentCanvas";
import ActionPanel from "@/components/ActionPanel";
import { fetchIncidents, fetchPendingApprovals, type Incident, type ApprovalRequest } from "@/lib/api";

export default function Cockpit() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    
    async function load() {
      try {
        const [inc, app] = await Promise.all([
          fetchIncidents(),
          fetchPendingApprovals(),
        ]);
        if (cancelled) return;
        setIncidents(inc);
        setApprovals(app);
        setSelectedIncident((prev) => prev || inc[0] || null);
      } catch (e) {
        console.error("Failed to load", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    
    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-bg-base text-text-primary">
      <TopBar incidentCount={incidents.length} pendingCount={approvals.length} />
      <main className="flex-1 grid grid-cols-[320px_1fr_400px] gap-px bg-border-subtle overflow-hidden">
        <IncidentFeed
          incidents={incidents}
          loading={loading}
          selectedId={selectedIncident?.id}
          onSelect={setSelectedIncident}
        />
        <AgentCanvas incident={selectedIncident} />
        <ActionPanel approvals={approvals} onDecided={() => {
          fetchPendingApprovals().then(setApprovals).catch(console.error);
        }} />
      </main>
    </div>
  );
}