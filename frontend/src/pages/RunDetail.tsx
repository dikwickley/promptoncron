import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Result, Run } from "../api/types";

function coerceCell(v: unknown) {
  if (v === null || v === undefined) return "";
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") return String(v);
  return JSON.stringify(v);
}

export function RunDetail() {
  const { runId } = useParams();
  if (!runId) return <div className="pill pillBad">Missing runId</div>;

  const runQ = useQuery({
    queryKey: ["run", runId],
    queryFn: () => api<Run>(`/api/runs/${runId}`),
    refetchInterval: 2000,
  });

  const resultQ = useQuery({
    queryKey: ["result", runId],
    queryFn: () => api<Result>(`/api/runs/${runId}/result`),
    retry: false,
    refetchInterval: 2000,
  });

  const webQ = useQuery({
    queryKey: ["web", runId],
    queryFn: () => api<{ run_id: string; query: string; results: unknown[] }>(`/api/runs/${runId}/web_search_snapshot`),
    retry: false,
  });

  const run = runQ.data;
  const result = resultQ.data;

  return (
    <div className="row" style={{ flexDirection: "column", alignItems: "stretch" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <Link className="btn btnGhost" to={run ? `/tasks/${run.task_id}` : "/"}>
          ← Back
        </Link>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div>
            <div className="cardTitle">Run</div>
            <div className="cardDesc">
              {run ? (
                <>
                  <span className="mono">{run.id}</span> • status: {run.status} • scheduled:{" "}
                  <span className="mono">{run.scheduled_for}</span>
                </>
              ) : (
                "Loading..."
              )}
            </div>
          </div>
          {run?.error_message && <div className="badge badgeBad">{run.error_message}</div>}
        </div>
        <div className="cardBody">
          {runQ.isError && <div className="badge badgeBad">{String(runQ.error)}</div>}

          <div className="grid2">
            <div>
              <div className="label">LLM model</div>
              <div className="mono">{run?.llm_model ?? "-"}</div>
            </div>
            <div>
              <div className="label">Token usage</div>
              <div className="mono">{run?.token_usage ? JSON.stringify(run.token_usage) : "-"}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div className="cardTitle">Result</div>
          {result?.summary && <div className="badge">{result.summary}</div>}
        </div>
        <div className="cardBody">
          {resultQ.isError && <div className="muted">No result yet.</div>}

          {result && (
            <table>
              <thead>
                <tr>
                  {result.columns.map((c) => (
                    <th key={c.key}>{c.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, idx) => (
                  <tr key={idx}>
                    {result.columns.map((c) => (
                      <td key={c.key} className="mono">
                        {coerceCell(row[c.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {result && (
            <details style={{ marginTop: 12 }}>
              <summary className="muted">Raw JSON</summary>
              <pre className="mono" style={{ whiteSpace: "pre-wrap" }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>

      <div className="card">
        <div className="cardHeader">
          <div className="cardTitle">Web search snapshot</div>
          <div className="badge">{webQ.data ? "captured" : "none"}</div>
        </div>
        <div className="cardBody">
          {webQ.data ? (
            <>
              <div className="label">Query</div>
              <div className="mono">{webQ.data.query}</div>
              <details style={{ marginTop: 12 }}>
                <summary className="muted">Results JSON</summary>
                <pre className="mono" style={{ whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(webQ.data.results, null, 2)}
                </pre>
              </details>
            </>
          ) : (
            <div className="muted">Not enabled or not available.</div>
          )}
        </div>
      </div>
    </div>
  );
}


