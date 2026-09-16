import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../api";
import type { Project } from "../types/models";
import { ProjectCard } from "../components/common/ProjectCard";
import {
  Empty,
  ErrorState,
  Header,
  Loading,
  Tabs,
} from "../components/common/ui";
import { ProjectForm } from "../components/forms/ProjectForm";
export default function Projects() {
  const [status, setStatus] = useState<Project["status"]>("ACTIVE");
  const [add, setAdd] = useState(false);
  const data = useQuery({
    queryKey: ["projects", status],
    queryFn: () => api.projects(status),
  });
  return (
    <>
      <Header
        title="Loyihalar"
        subtitle="Ishlar, tushumlar va qoldiqlar"
        action={
          <button className="primary" onClick={() => setAdd(true)}>
            <Plus size={18} /> Qo'shish
          </button>
        }
      />
      <Tabs
        value={status}
        onChange={(v) => setStatus(v as Project["status"])}
        items={[
          ["ACTIVE", "Faol"],
          ["COMPLETED", "Tugallangan"],
        ]}
      />
      {data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} retry={() => void data.refetch()} />
      ) : !data.data.length ? (
        <Empty
          text="Bu bo'limda loyihalar yo'q."
          action={
            status === "ACTIVE" && (
              <button className="secondary" onClick={() => setAdd(true)}>
                Loyiha qo'shish
              </button>
            )
          }
        />
      ) : (
        <div className="project-grid">
          {data.data.map((p) => (
            <ProjectCard key={p.project.id} data={p} />
          ))}
        </div>
      )}
      {add && <ProjectForm onClose={() => setAdd(false)} />}
    </>
  );
}
