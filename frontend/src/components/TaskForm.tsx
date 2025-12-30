import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { Task } from "../api/types";

type Props = { onCreated: (t: Task) => void };

export function TaskForm({ onCreated }: Props) {
  const [name, setName] = useState("Example: Weekly competitor scan");
  const [cron, setCron] = useState("*/15 * * * *");
  const [timezone, setTimezone] = useState("UTC");
  const [web, setWeb] = useState(false);
  const [status, setStatus] = useState<"enabled" | "disabled">("enabled");
  const [prompt, setPrompt] = useState(
    "Find 3 notable product updates in my space from the last week and output a table with: company, update, url, date.",
  );

  const m = useMutation({
    mutationFn: () =>
      api<Task>("/api/tasks", {
        method: "POST",
        body: JSON.stringify({
          name,
          prompt,
          cron_expression: cron,
          timezone,
          web_search_enabled: web,
          status,
        }),
      }),
    onSuccess: (t) => onCreated(t),
  });

  return (
    <div className="row" style={{ flexDirection: "column", alignItems: "stretch" }}>
      {m.isError && <div className="badge badgeBad">{String(m.error)}</div>}
      {m.isSuccess && <div className="badge badgeOk">Created.</div>}

      <div>
        <div className="label">Name</div>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div className="grid2">
        <div>
          <div className="label">Cron expression</div>
          <input className="input" value={cron} onChange={(e) => setCron(e.target.value)} />
          <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
            Example: <span className="mono">*/15 * * * *</span>
          </div>
        </div>
        <div>
          <div className="label">Timezone</div>
          <input className="input" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
          <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
            Example: <span className="mono">UTC</span> or <span className="mono">America/Los_Angeles</span>
          </div>
        </div>
      </div>

      <div className="grid2">
        <div>
          <div className="label">Status</div>
          <select className="select" value={status} onChange={(e) => setStatus(e.target.value as "enabled" | "disabled")}>
            <option value="enabled">enabled</option>
            <option value="disabled">disabled</option>
          </select>
        </div>
        <div>
          <div className="label">Web search</div>
          <select className="select" value={web ? "on" : "off"} onChange={(e) => setWeb(e.target.value === "on")}>
            <option value="off">off</option>
            <option value="on">on</option>
          </select>
        </div>
      </div>

      <div>
        <div className="label">Prompt</div>
        <textarea className="textarea" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </div>

      <button className="btn btnPrimary" onClick={() => m.mutate()} disabled={m.isPending}>
        {m.isPending ? "Creating..." : "Create task"}
      </button>
    </div>
  );
}


