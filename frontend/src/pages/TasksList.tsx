import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Task } from "../api/types";
import { TaskForm } from "../components/TaskForm";

export function TasksList() {
  const qc = useQueryClient();
  const tasksQ = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api<Task[]>("/api/tasks"),
    refetchInterval: 2000,
  });

  const delM = useMutation({
    mutationFn: (taskId: string) => api<{ ok: boolean }>(`/api/tasks/${taskId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  return (
    <div className="grid2">
      <div className="card">
        <div className="cardHeader">
          <div>
            <div className="cardTitle">Tasks</div>
            <div className="cardDesc">Create a task and it will run on schedule.</div>
          </div>
          <div className="badge">{tasksQ.data?.length ?? 0} total</div>
        </div>
        <div className="cardBody">
          {tasksQ.isLoading && <div className="muted">Loading...</div>}
          {tasksQ.isError && <div className="badge badgeBad">{String(tasksQ.error)}</div>}
          {tasksQ.data && tasksQ.data.length === 0 && <div className="muted">No tasks yet.</div>}

          {tasksQ.data && tasksQ.data.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Schedule</th>
                  <th>Status</th>
                  <th>Next run</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tasksQ.data.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <Link to={`/tasks/${t.id}`} style={{ fontWeight: 700 }}>
                        {t.name}
                      </Link>
                      <div className="muted" style={{ fontSize: 12 }}>
                        web search: {t.web_search_enabled ? "on" : "off"}
                      </div>
                    </td>
                    <td className="mono">{t.cron_expression}</td>
                    <td>
                      <span className={`badge ${t.status === "enabled" ? "badgeOk" : ""}`}>{t.status}</span>
                    </td>
                    <td className="mono">{t.next_run_at ?? "-"}</td>
                    <td style={{ textAlign: "right" }}>
                      <button className="btn btnDanger" onClick={() => delM.mutate(t.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div>
            <div className="cardTitle">Create Task</div>
            <div className="cardDesc">Minimum interval: 15 minutes.</div>
          </div>
        </div>
        <div className="cardBody">
          <TaskForm onCreated={() => qc.invalidateQueries({ queryKey: ["tasks"] })} />
        </div>
      </div>
    </div>
  );
}


