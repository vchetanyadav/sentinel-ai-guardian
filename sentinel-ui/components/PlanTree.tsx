"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, CheckCircle2, Wrench } from "lucide-react";
import type { RunEvent } from "@/lib/api";

type Block = {
  step?: RunEvent;
  toolCall?: RunEvent;
  toolResult?: RunEvent;
};

export default function PlanTree({ events }: { events: RunEvent[] }) {
  const blocks: Block[] = [];
  let current: Block | null = null;
  for (const ev of events) {
    if (ev.type === "plan_step") {
      if (current) blocks.push(current);
      current = { step: ev };
    } else if (ev.type === "tool_call" && current) {
      current.toolCall = ev;
    } else if (ev.type === "tool_result" && current) {
      current.toolResult = ev;
    }
  }
  if (current) blocks.push(current);
  
  return (
    <div className="space-y-2 font-mono text-sm">
      <AnimatePresence>
        {blocks.map((block, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.2 }}
          >
            <PlanStepRow block={block} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function PlanStepRow({ block }: { block: Block }) {
  const [expanded, setExpanded] = useState(false);
  const hasTool = !!block.toolCall;
  
  return (
    <div className="rounded-md border border-border-subtle bg-bg-panel overflow-hidden">
      <button
        onClick={() => hasTool && setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-bg-elevated transition text-left"
      >
        <CheckCircle2 className="w-4 h-4 text-status-ok flex-shrink-0" />
        <span className="flex-1 text-text-primary">{block.step?.label}</span>
        {hasTool && (
          <span className="flex items-center gap-1 text-xs text-text-muted">
            <Wrench className="w-3 h-3" />
            <span>{block.toolCall?.name}</span>
            <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`} />
          </span>
        )}
      </button>
      <AnimatePresence>
        {expanded && hasTool && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border-subtle overflow-hidden"
          >
            <div className="p-3 space-y-3 text-xs">
              <div>
                <div className="text-text-muted mb-1">→ {block.toolCall?.name}</div>
                <pre className="bg-bg-elevated rounded p-2 overflow-x-auto text-[11px]">
                  {JSON.stringify(block.toolCall?.args, null, 2)}
                </pre>
              </div>
              {block.toolResult && (
                <div>
                  <div className="text-text-muted mb-1">← result</div>
                  <pre className="bg-bg-elevated rounded p-2 overflow-x-auto text-[11px] max-h-48">
                    {JSON.stringify(block.toolResult.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}