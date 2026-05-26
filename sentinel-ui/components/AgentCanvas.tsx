"use client";

import { useEffect, useState } from "react";
import type { Incident, Run } from "@/lib/api";
import { fetchRuns, fetchRun } from "@/lib/api";
import PlanTree from "./PlanTree";

export default function AgentCanvas({ incident }: { incident: Incident | null }) {
  const [fixtureRun, setFixtureRun] = useState<Run | null>(null);

  useEffect(() => {
    fetchRuns().then((runs) => {
      if (runs.length) fetchRun(runs[0].run_id).then(setFixtureRun);
    }).catch(console.error);
  }, []);

  if (!incident) {
    return (
      <section className="bg-bg-base p-8 flex items-center justify-center text-text-muted">
        Select an incident from the left to view Sentinel&apos;s reasoning.
      </section>
    );
  }

  return (
    <section className="bg-bg-base overflow-y-auto">
      <header className="px-6 py-4 border-b border-border-subtle">
        <div className="text-xs text-text-muted uppercase tracking-wider mb-1">
          {incident.id} · {incident.severity}
        </div>
        <h2 className="text-xl font-semibold">{incident.title}</h2>
        <p className="text-sm text-text-secondary mt-2">{incident.hypothesis}</p>
      </header>
      
      <div className="p-6">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-4">
          Sentinel&apos;s reasoning trace
        </h3>
        {fixtureRun ? (
          <PlanTree events={fixtureRun.events} />
        ) : (
          <div className="text-sm text-text-muted">Loading reasoning trace…</div>
        )}
      </div>
      
      {incident.postmortem && (
        <div className="px-6 pb-6">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-2">Postmortem</h3>
          <div className="rounded-md border border-border-subtle bg-bg-panel p-4 text-sm leading-relaxed">
            {incident.postmortem}
          </div>
        </div>
      )}
    </section>
  );
}
