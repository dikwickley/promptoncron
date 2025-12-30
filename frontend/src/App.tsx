import { Link, Route, Routes } from "react-router-dom";
import { TasksList } from "./pages/TasksList";
import { TaskDetail } from "./pages/TaskDetail";
import { RunDetail } from "./pages/RunDetail";

export function App() {
  return (
    <>
      <header className="topbar">
        <div className="topbarInner">
          <div className="brand">
            <Link to="/" className="brandLink">
              promptoncron
            </Link>
            <span className="brandSub">Scheduled structured LLM runs</span>
          </div>
          <div className="row">
            <a className="btn btnGhost" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
              API docs
            </a>
          </div>
        </div>
      </header>

      <div className="container">
        <Routes>
          <Route path="/" element={<TasksList />} />
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
          <Route path="/runs/:runId" element={<RunDetail />} />
        </Routes>
      </div>
    </>
  );
}


