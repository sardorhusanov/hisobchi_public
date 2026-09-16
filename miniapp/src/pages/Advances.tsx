import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../api";
import { History } from "../components/common/History";
import { Header, MonthPicker, Select } from "../components/common/ui";
import { TransactionForm } from "../components/forms/TransactionForm";
import { today } from "../utils/format";
export default function Advances() {
  const [month, setMonth] = useState(today().slice(0, 7));
  const [worker, setWorker] = useState("");
  const [project, setProject] = useState("");
  const [add, setAdd] = useState(false);
  const workers = useQuery({
    queryKey: ["workers", "all"],
    queryFn: () => api.people("WORKER", false),
  });
  const projects = useQuery({
    queryKey: ["projects", "ACTIVE"],
    queryFn: () => api.projects(),
  });
  return (
    <>
      <Header
        title="Avans"
        subtitle="Ishchilarga oldindan to'langan pullar"
        action={
          <button className="primary" onClick={() => setAdd(true)}>
            <Plus size={18} /> Berish
          </button>
        }
      />
      <div className="filters">
        <MonthPicker value={month} onChange={setMonth} />
        <Select label="Ishchi" value={worker} onChange={setWorker}>
          <option value="">Barchasi</option>
          {workers.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </Select>
        <Select label="Loyiha" value={project} onChange={setProject}>
          <option value="">Barchasi</option>
          {projects.data?.map((p) => (
            <option key={p.project.id} value={p.project.id}>
              {p.project.name}
            </option>
          ))}
        </Select>
      </div>
      <p className="muted">Tanlangan oylik davriga tegishli avanslar.</p>
      <History
        key={`${month}-${worker}-${project}`}
        kind="advances"
        filters={{ month, worker_id: worker, project_id: project }}
      />
      {add && (
        <TransactionForm
          kind="advance"
          workerId={worker}
          onClose={() => setAdd(false)}
        />
      )}
    </>
  );
}
