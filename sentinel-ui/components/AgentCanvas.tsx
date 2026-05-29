"use client";

import { useEffect, useState, useRef } from "react";
import type { Incident, Run, RunEvent } from "@/lib/api";
import { fetchRuns, fetchRun, triggerSentinel, streamSentinelEvents } from "@/lib/api";
import PlanTree from "./PlanTree";
import { Play, Radio } from "lucide-react";

export default function AgentCanvas({ incident }: { incident: Incident | null }) {
  const [fixtureRun, setFixtureRun] = useState<Run | null>(null);
  const [liveEvents, setLiveEvents] = useState<RunEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    fetchRuns().then((runs) => {
      if (runs.length) fetchRun(runs[0].run_id).then(setFixtureRun);
    }).catch(console.error);
    
    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
  }, []);

  async function handleTrigger() {
    setLiveEvents([]);
    setIsStreaming(true);
    
    try {
      const { run_id } = await triggerSentinel();
      cleanupRef.current = streamSentinelEvents(
        run_id,
        (ev) => setLiveEvents((prev) => [...prev, ev]),
        () => setIsStreaming(false),
      );
    } catch (e) {
      console.error(e);
      setIsStreaming(false);
    }
  }

  // Show live events if streaming, else fixture, else placeholder
  const displayEvents = liveEvents.length > 0 ? liveEvents : fixtureRun?.events || [];
  const showingLive = liveEvents.length > 0;

  if (!incident && !showingLive) {
    return (
      <section className="bg-bg-base p-8 flex items-center justify-center text-text-muted">
        <div className="text-center">
          <p className="mb-4">Select an incident from the left to view Sentinel&apos;s reasoning.</p>
          <p className="text-xs mb-6">Or trigger a fresh diagnostic run:</p>
          <button
            onClick={handleTrigger}
            disabled={isStreaming}
            className="px-4 py-2 bg-accent text-bg-base font-semibold rounded hover:bg-accent/90 transition disabled:opacity-50 inline-flex items-center gap-2"
          >
            <Play className="w-4 h-4" /> Trigger Sentinel
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-bg-base overflow-y-auto">
      <header className="px-6 py-4 border-b border-border-subtle flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {showingLive ? (
            <>
              <div className="text-xs text-status-warn uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Radio className="w-3 h-3 animate-pulse" />
                Live Run
              </div>
              <h2 className="text-xl font-semibold">Sentinel diagnostic in progress…</h2>
              <p className="text-sm text-text-secondary mt-2">
                {liveEvents.length} events received · {isStreaming ? "streaming" : "completed"}
              </p>
            </>
          ) : incident ? (
            <>
              <div className="text-xs text-text-muted uppercase tracking-wider mb-1">
                {incident.id} · {incident.severity}
              </div>
              <h2 className="text-xl font-semibold">{incident.title}</h2>
              <p className="text-sm text-text-secondary mt-2">{incident.hypothesis}</p>
            </>
          ) : null}
        </div>
        <button
          onClick={handleTrigger}
          disabled={isStreaming}
          className="px-3 py-2 bg-accent text-bg-base text-sm font-semibold rounded hover:bg-accent/90 transition disabled:opacity-50 inline-flex items-center gap-2 flex-shrink-0"
        >
          {isStreaming ? (
            <><Radio className="w-4 h-4 animate-pulse" /> Running…</>
          ) : (
            <><Play className="w-4 h-4" /> Trigger Sentinel</>
          )}
        </button>
      </header>
      
      <div className="p-6">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-4">
          {showingLive ? "Live reasoning trace" : "Sentinel's reasoning trace"}
        </h3>
        {displayEvents.length > 0 ? (
          <PlanTree events={displayEvents} />
        ) : (
          <div className="text-sm text-text-muted">Loading reasoning trace…</div>
        )}
      </div>
      
      {incident?.postmortem && !showingLive && (
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