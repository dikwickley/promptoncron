import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Run, Task } from "../api/types";

export function TaskDetail() {
  const { taskId } = useParams();
  const qc = useQueryClient();
  if (!taskId) return <div className="pill pillBad">Missing taskId</div>;

  const taskQ = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api<Task>(`/api/tasks/${taskId}`),
    refetchInterval: 2000,
  });

  const runsQ = useQuery({
    queryKey: ["taskRuns", taskId],
    queryFn: () => api<Run[]>(`/api/tasks/${taskId}/runs`),
    refetchInterval: 2000,
  });

  const triggerM = useMutation({
    mutationFn: () => api<Run>(`/api/tasks/${taskId}/run`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["taskRuns", taskId] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const task = taskQ.data;

  return (
    <div className="row" style={{ flexDirection: "column", alignItems: "stretch" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <Link className="btn btnGhost" to="/">
          ← Back
        </Link>
        <button className="btn btnPrimary" onClick={() => triggerM.mutate()} disabled={triggerM.isPending}>
          {triggerM.isPending ? "Queueing..." : "Run now"}
        </button>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div>
            <div className="cardTitle" style={{ fontSize: 18 }}>
              {task?.name ?? "Task"}
            </div>
            <div className="cardDesc">
              {task ? (
                <>
                  <span className="mono">{task.cron_expression}</span> • {task.timezone} • web search:{" "}
                  {task.web_search_enabled ? "on" : "off"} • status: {task.status}
                </>
              ) : (
                "Loading..."
              )}
            </div>
          </div>
          {task?.next_run_at && <div className="badge">next: {task.next_run_at}</div>}
        </div>
        <div className="cardBody">
          {taskQ.isError && <div className="badge badgeBad">{String(taskQ.error)}</div>}
          <div className="label">Prompt</div>
          <textarea className="textarea mono" value={task?.prompt ?? ""} readOnly style={{ minHeight: 160 }} />
        </div>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div className="cardTitle">Runs</div>
          <div className="badge">{runsQ.data?.length ?? 0}</div>
        </div>
        <div className="cardBody">
          {runsQ.isLoading && <div className="muted">Loading...</div>}
          {runsQ.isError && <div className="badge badgeBad">{String(runsQ.error)}</div>}
          {runsQ.data && runsQ.data.length === 0 && <div className="muted">No runs yet.</div>}

          {runsQ.data && runsQ.data.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Scheduled</th>
                  <th>Status</th>
                  <th>Model</th>
                  <th>Error</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {runsQ.data.map((r) => (
                  <tr key={r.id}>
                    <td className="mono">{r.scheduled_for}</td>
                    <td>
                      <span className={`badge ${r.status === "success" ? "badgeOk" : r.status === "failed" ? "badgeBad" : ""}`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="mono">{r.llm_model ?? "-"}</td>
                    <td className="mono">{r.error_message ?? "-"}</td>
                    <td style={{ textAlign: "right" }}>
                      <Link className="btn" to={`/runs/${r.id}`}>
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}


