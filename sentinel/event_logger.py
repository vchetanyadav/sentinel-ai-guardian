import json
import os
from datetime import datetime
from pathlib import Path

class EventLogger:
    """Captures Sentinel's reasoning trace to a JSON file for later replay."""
    
    def __init__(self, run_id: str = None):
        self.run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.events = []
        self.runs_dir = Path(__file__).parent / "runs"
        self.runs_dir.mkdir(exist_ok=True)
    
    def log_plan_step(self, label: str):
        self.events.append({
            "type": "plan_step",
            "timestamp": datetime.now().isoformat(),
            "label": label,
        })
    
    def log_tool_call(self, name: str, args: dict):
        self.events.append({
            "type": "tool_call",
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "args": args,
        })
    
    def log_tool_result(self, result):
        self.events.append({
            "type": "tool_result",
            "timestamp": datetime.now().isoformat(),
            "result": self._serializable(result),
        })
    
    def log_message(self, text: str):
        self.events.append({
            "type": "message",
            "timestamp": datetime.now().isoformat(),
            "text": text,
        })
    
    def save(self):
        path = self.runs_dir / f"run_{self.run_id}.json"
        with open(path, "w") as f:
            json.dump({"run_id": self.run_id, "events": self.events}, f, indent=2, default=str)
        print(f"\n📁 Run saved to {path.relative_to(Path.cwd())}")
        return path
    
    @staticmethod
    def _serializable(obj):
        """Best-effort JSON-serializable conversion."""
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)