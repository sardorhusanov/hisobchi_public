import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { ArrowDownLeft, ArrowUpRight, Pencil } from "lucide-react";
import { api } from "../api";
import { useRefresh } from "../hooks/data";
import { History } from "../components/common/History";
import {
  Confirm,
  ErrorState,
  Header,
  Loading,
  MoneyStat,
  Tabs,
} from "../components/common/ui";
import { ProjectForm } from "../components/forms/ProjectForm";
import { TransactionForm } from "../components/forms/TransactionForm";
export default function ProjectDetails() {
  const { id = "" } = useParams();
  const [tab, setTab] = useState("overview");
  const [kind, setKind] = useState<"income" | "expense" | null>(null);
  const [edit, setEdit] = useState(false);
  const [complete, setComplete] = useState(false);
  const refresh = useRefresh();
  const data = useQuery({
    queryKey: ["project", id],
    queryFn: () => api.project(id),
  });
  if (data.isPending) return <Loading />;
  if (data.error)
    return <ErrorState error={data.error} retry={() => void data.refetch()} />;
  const p = data.data;
  return (
    <>
      <Header
        title={p.project.name}
        subtitle={
          p.project.status === "ACTIVE" ? "Faol loyiha" : "Tugallangan loyiha"
        }
        back="/projects"
        action={
          <button
            className="icon-button"
            aria-label="Loyihani tahrirlash"
            onClick={() => setEdit(true)}
          >
            <Pencil size={19} />
          </button>
        }
      />
      <div className="stats-grid">
        <MoneyStat label="Tushum" value={p.income} />
        <MoneyStat label="Xarajat" value={p.expenses} />
        <MoneyStat label="Qoldiq" value={p.balance} accent />
      </div>
      {p.project.status === "ACTIVE" && (
        <div className="actions">
          <button className="primary" onClick={() => setKind("income")}>
            <ArrowDownLeft size={18} /> Pul tushumi
          </button>
          <button className="secondary" onClick={() => setKind("expense")}>
            <ArrowUpRight size={18} /> Xarajat
          </button>
        </div>
      )}
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["overview", "Umumiy"],
          ["income", "Tushumlar"],
          ["expenses", "Xarajatlar"],
          ["report", "Hisobot"],
        ]}
      />
      {tab === "overview" && (
        <section className="card">
          <h2>Loyiha haqida</h2>
          <p>{p.project.description || "Tavsif kiritilmagan."}</p>
          <p className="muted">
            Qoldiq — tushumlardan loyiha xarajatlari ayrilgani. Ishchi oyligi va
            avanslar avtomatik ayrilmaydi.
          </p>
          {p.project.status === "ACTIVE" && (
            <button
              className="secondary full"
              onClick={() => setComplete(true)}
            >
              Loyihani tugatish
            </button>
          )}
        </section>
      )}
      {(tab === "income" || tab === "report") && (
        <History kind="income" filters={{ project_id: id }} projectContext />
      )}
      {(tab === "expenses" || tab === "report") && (
        <History kind="expenses" filters={{ project_id: id }} projectContext />
      )}
      {kind && (
        <TransactionForm
          kind={kind}
          projectId={id}
          onClose={() => setKind(null)}
        />
      )}{" "}
      {edit && (
        <ProjectForm project={p.project} onClose={() => setEdit(false)} />
      )}{" "}
      {complete && (
        <Confirm
          title="Loyihani tugatish?"
          description="Loyiha tarixi saqlanadi. Yangi tushum va xarajat kiritish yopiladi."
          onClose={() => setComplete(false)}
          confirm={async () => {
            await api.editProject(id, { status: "COMPLETED" });
            await refresh();
            setComplete(false);
          }}
        />
      )}
    </>
  );
}
